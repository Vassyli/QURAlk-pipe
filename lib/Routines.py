import colorama
from collections import OrderedDict

from .routines.BaseRoutine import BaseRoutine
from .routines.ModRoutine import ModRoutine

def get_routine(key):
    if key in routines:
        return routines[key]
    else:
        raise RoutineNotFoundError("Routine does not exist")


def list_routines():
    for key in routines:
        yield key


class RoutineNotFoundError(Exception):
    pass

class HelpRoutine(BaseRoutine):
    MESSAGE_USAGE = "Usage:\t{} <routine> [options]"
    MESSAGE_COMMAND_LIST = "Routines available:"
    MESSAGE_CLI_HELP = "Shows this help page. Use help <routine> to get more help."

    def run(self):
        if len(self.arguments) == 0:
            # Generic usage
            print(self.MESSAGE_USAGE.format(self.appName))
            print()
            print(self.MESSAGE_COMMAND_LIST)

            for routine in list_routines():
                print(" • {}\t\t{}".format(routine, get_routine(routine).get_cli_help()))
        else:
            # More specific help
            if self.arguments[0] in list_routines():
                print(get_routine(self.arguments[0]).get_more_cli_help())
            else:
                print("The routine you requested is unknown to me.")

    def get_cli_help(self):
        return self.MESSAGE_CLI_HELP

    def get_more_cli_help(self):
        return """Are you really that desperate?
If you need real help, ask someone else.
If you just want to now how the help works...

{}Congratulations, you just used it!{}""".format(colorama.Fore.GREEN, colorama.Fore.RESET)


# Register routines here
routines = {
    "help": HelpRoutine(),
    "mod": ModRoutine(),
}

routines = OrderedDict(sorted(routines.items(), key=lambda t: t[0]))