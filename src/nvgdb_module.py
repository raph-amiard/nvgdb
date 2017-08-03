from __future__ import print_function

from neovim import attach
from os import environ, path as P
import gdb

DEBUG = False


def split(nvim, vertical=False, new_file=True):
    """
    Split windows, focus on the new window, and return the new window.

    :rtype: neovim.api.window.Window
    """
    cmds = Cmds(["vsplit" if vertical else "split"])
    if new_file:
        cmds.append("enew")
    cmds.run(nvim)

    return nvim.current.window


def vsplit(nvim, new_file=True):
    """
    Vertically split windows, focus on the new window, and return the new
    window.

    :rtype: neovim.api.window.Window
    """
    return split(nvim, True, new_file)


class Cmd(object):
    """
    Base class for a vim command.
    """

    def __init__(self, strn, *windows):
        """
        A vim command is a string plus a list of windows. Windows will be
        transformed into window numbers when the command is ran.
        """
        self.strn = strn
        self.windows = windows

    def render(self):
        return self.strn.format(*[w.number for w in self.windows])

    def run(self, nvim):
        if DEBUG:
            print("<Command '{}'>".format(self.render()))
        nvim.command(self.render())

    def __str__(self):
        return self.render()

    # Static methods that return vim commands

    @staticmethod
    def normal(command_strn):
        """
        Send normal commands to vim

        :rtype: Cmd
        """
        return Cmd('execute "normal! {}"'.format(command_strn))

    @staticmethod
    def focus_on(window):
        """
        Return a Cmds that will focus on given nvim window

        :rtype: Cmd
        """
        return Cmd("{}wincmd w", window)

    @staticmethod
    def center_on_line(line_no):
        """
        Will center the currently focused window on line line_no.

        :rtype: Cmd
        """
        return Cmds([str(line_no), Cmd.normal("z."), "redraw!"])

    @staticmethod
    def edit_file(file_name):
        """
        Edit given file.

        :rtype: Cmd
        """
        return Cmd("edit {}".format(file_name))


class Cmds(list, Cmd):
    """
    Cmd that represents a group of commands. Since it is also a vim command
    itself, it is composable easily.
    """

    def render(self):
        return " | ".join([str(cmd) for cmd in self])


class GdbPlugin(object):
    """
    Main class for the gdb plug-in that interfaces with vim.

    This class supports extensions. You can subclass GdbPluginExtension and
    call register_extension with an instance of your class.
    """

    def __init__(self, nvim):
        gdb.events.stop.connect(self.on_stop)

        try:
            gdb.events.before_prompt.connect(self.on_stop)
        except Exception, e:
            print("WARNING: Your GDB version is too old. nvgdb won't work"
                  " correctly. please update !")

        self.current_filename = ""
        self.nvim = nvim
        self.hl_source = nvim.new_highlight_source()

        # Global config
        Cmds([
            # Deactivate swap files
            "set noswapfile",
            "set splitright",
            "set splitbelow",
            "highlight NvgdbCurrent ctermbg=202 guibg=#ff5f00",
            "set nocursorline"
        ]).run(self.nvim)

        # Create windows
        self.main_window = self.nvim.current.window
        self.code_window = vsplit(self.nvim)
        Cmd.focus_on(self.main_window).run(self.nvim)

        self.extensions = []

    def on_stop(self, event=None):
        """
        Main event handler for the plug-in, called everytime gdb stops.
        """
        try:
            f = gdb.selected_frame()
        except gdb.error:
            # If we get an error here, just return
            return

        cmds = Cmds()

        # Main job of the plug-in: Open the debugged file in a split and focus
        # vim on the correct line.
        sal = f.find_sal()
        if sal and sal.symtab:
            filename = sal.symtab.filename
            cmds.append(Cmd.focus_on(self.code_window))

            if P.exists(filename):
                if self.current_filename != filename:
                    cmds.append(Cmd.edit_file(filename))
                    self.current_filename = filename

                # Go to line and center
                cmds.append(Cmd.center_on_line(sal.line))
                buf = self.code_window.buffer
                buf.clear_highlight(self.hl_source)
                buf.add_highlight("NvgdbCurrent", sal.line - 1, 0, -1, src_id=self.hl_source)

        # Allow every extension to register commands
        for ext in self.extensions:
            cmds += ext.on_stop(self, event)

        # Focus on the main window
        cmds.append(Cmd.focus_on(self.main_window))

        cmds.run(self.nvim)
        return cmds

    def register_extension(self, plugin):
        self.extensions.append(plugin)


class GdbPluginExtension(object):
    """
    Abstract base class for an extension to the gdb plug-in.
    """

    def on_stop(self, gdb_plugin, event=None):
        raise NotImplementedError()


class LangkitGdbExtension(GdbPluginExtension):
    """
    Extension that implements langkit support for the base gdb plug-in. This
    extension will be automatically loaded if langkit is detected.
    """

    def __init__(self):
        self.is_init = False
        self.ctx = None
        self.current_dsl_filename = ""

    def init(self, gdb_plugin):

        self.nvim = gdb_plugin.nvim

        if not self.is_init:
            Cmd.focus_on(gdb_plugin.main_window).run(self.nvim)
            self.dsl_code_window = vsplit(self.nvim)
            Cmd.focus_on(gdb_plugin.main_window).run(self.nvim)

            self.state_window = split(self.nvim)
            Cmds([
                Cmd.focus_on(self.state_window),
                Cmd("set filetype=lalstate"),
                Cmd.focus_on(gdb_plugin.main_window),
                Cmd.normal("i")
            ]).run(self.nvim)
            self.is_init = True

    def get_context(self):
        if not self.ctx:
            try:
                from langkit.gdb import get_current_gdb_context
                self.ctx = get_current_gdb_context()
            except ImportError:
                pass

        return self.ctx

    def on_stop(self, gdb_plugin, event=None):

        cmds = Cmds()

        ctx = self.get_context()
        state = ctx.decode_state() if ctx else None

        if ctx:
            self.init(gdb_plugin)

        if state:
            # If we have a state here, we are in DSL land, and want to show the
            # current execution line.
            current_scope = state.scopes and state.scopes[-1]
            if current_scope:
                _, current_expr = current_scope.sorted_expressions()
                if current_expr and current_expr.dsl_sloc:
                    sloc = current_expr.dsl_sloc
                    cmds.append(Cmd.focus_on(self.dsl_code_window))
                    if self.current_dsl_filename != sloc.filename:
                        cmds.append(Cmd.edit_file(sloc.filename))
                        self.current_dsl_filename = sloc.filename

                    cmds.append(Cmd.center_on_line(sloc.line_no))
                    buf = self.dsl_code_window.buffer
                    buf.clear_highlight(gdb_plugin.hl_source)
                    buf.add_highlight(
                        "NvgdbCurrent", sloc.line_no - 1, 0, -1, src_id=gdb_plugin.hl_source
                    )
                    cmds.append(Cmd.focus_on(gdb_plugin.main_window))

            from langkit.gdb.commands import StatePrinter
            pr = StatePrinter(ctx, with_locs=True, with_ellipsis=False)
            state_str = pr.render().splitlines()
            if state_str:
                self.state_window.buffer[:] = state_str
        return cmds


def main():
    listen_address = environ['NVIM_LISTEN_ADDRESS']
    nvim = attach('socket', path=listen_address)
    plugin = GdbPlugin(nvim)
    plugin.register_extension(LangkitGdbExtension())
    gdb.nvim_plugin = plugin
