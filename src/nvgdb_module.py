from neovim import attach
from os import environ
import gdb

listen_address = environ['NVIM_LISTEN_ADDRESS']
nvim = attach('socket', path=listen_address)


class VimCmds(list):

    def render(self):
        return " | ".join(self)

    def run(self):
        nvim.command(self.render())


VimCmds([
    "set noswapfile",
    'vsplit', 'vsplit', 'split',
    "wincmd j", "enew", "wincmd l", "enew", "wincmd l", "enew", "wincmd h",
    "wincmd h"
]).run()


class GdbPlugin(object):

    def __init__(self):
        gdb.events.stop.connect(self.stop_event_handler)
        self.current_filename = ""
        self.current_dsl_filename = ""
        self.ctx = None

    def get_context(self):
        if not self.ctx:
            from langkit.gdb import get_current_gdb_context
            self.ctx = get_current_gdb_context()

        return self.ctx

    def stop_event_handler(self, event=None):
        cmds = self.on_stop(event)
        cmds.append("redraw!")
        cmds.run()

    def on_stop(self, event=None):
        try:
            f = gdb.selected_frame()
        except gdb.error:
            pass

        sal = f.find_sal()
        filename = sal.symtab.filename
        cmds = VimCmds(["wincmd l"])

        if self.current_filename != filename:
            cmds.append("edit {}".format(filename))
            self.current_filename = filename

        # Go to line and center
        cmds += [str(sal.line), "execute \"normal! z.\""]

        ctx = self.get_context()
        state = ctx.decode_state() if ctx else None

        if state:
            # If we have a state here, we are in DSL land, and want to show the
            # current execution line.
            current_scope = state.scopes and state.scopes[-1]
            if current_scope:
                _, current_expr = current_scope.sorted_expressions()
                if current_expr and current_expr.dsl_sloc:
                    sloc = current_expr.dsl_sloc
                    cmds += ["wincmd l"]
                    if self.current_dsl_filename != sloc.filename:
                        cmds += ["edit {}".format(sloc.filename)]
                        self.current_dsl_filename = sloc.filename

                    cmds += [
                        str(sloc.line_no), "execute \"normal! z.\"", "wincmd h"
                    ]

            from langkit.gdb.commands import StatePrinter
            pr = StatePrinter(ctx)
            state_str = pr.render().splitlines()
            if state_str:
                nvim.windows[1].buffer[:] = state_str

        # Go to next window, meant to show langkit DSL source

        cmds += ["wincmd h"]
        return cmds


plugin = GdbPlugin()
