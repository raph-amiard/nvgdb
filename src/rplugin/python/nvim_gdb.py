import neovim


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
