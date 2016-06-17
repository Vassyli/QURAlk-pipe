
from .Routines import HelpRoutine

# Register routines here
routines = {
    "help": HelpRoutine()
}


class App:
    """ Main QURAlk-pipe runtime.

    This class takes and stores command line arguments and
    calls the requested routine.
    """
    routine = None
    arguments = []

    def __init__(self, arguments):
        # Choose subApp and store arguments
        if len(arguments) == 1:
            self.routine = "help"
        elif len(arguments) > 1:
            self.routine = arguments[1]

            if len(arguments) > 2:
                self.arguments = arguments[2:]

    def run(self):
        self.prepare()

        self.close()

    def prepare(self):
        pass

    def close(self):
        pass