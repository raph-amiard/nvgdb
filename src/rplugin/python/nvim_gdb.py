import neovim
from os import path as P

sources_path = P.join(
    P.dirname(P.dirname(P.dirname(P.realpath(__file__))))
)


@neovim.plugin
class GdbPlugin(object):

    def __init__(self, vim):
        self.vim = vim

    @neovim.command('StartGdb', range='', nargs='*', sync=True)
    def command_handler(self, args, range):
        gdb_args = [
            "gdb", "-ex", "\"python import nvgdb_module; nvgdb_module.main()\""
        ] + args
        self.vim.call("termopen", " ".join(gdb_args))
        self.vim.command("echo \"{}\"".format(sources_path))
        self.vim.command("set rtp+={}".format(sources_path))
