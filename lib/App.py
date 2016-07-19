#
import colorama
from datetime import datetime

from .Routines import list_routines, get_routine

MESSAGE_PROGRAM = "Program:\tquralk-pipe (tool chain for mod seq)"
MESSAGE_VERSION = "Version:\t0.2.0-dev"


class App:
    """ Main QURAlk-pipe runtime.

    This class takes and stores command line arguments and
    calls the requested routine.
    """
    routineKey = None
    routine = None
    arguments = []
    appName = None

    def __init__(self, arguments):
        # Initialize for colour support
        colorama.init()

        # Choose subApp and store arguments
        self.appName = arguments[0]

        if len(arguments) == 1:
            self.routineKey = "help"
        elif len(arguments) > 1:
            self.routineKey = arguments[1]

            if len(arguments) > 2:
                self.arguments = arguments[2:]

        print()
        print(MESSAGE_PROGRAM)
        print(MESSAGE_VERSION)
        print()

    def run(self):
        start = datetime.now()

        self.prepare()
        self.run_routine()
        self.close()

        end = datetime.now()
        print("\nTime needes for execution: {}".format(end - start))

    def prepare(self):
        try:
            self.routine = get_routine(self.routineKey)
        except RoutineNotFoundError:
            print("Could not fine routine {}, aborting.".format(self.routineKey))

        self.routine.set_arguments(self.arguments)
        self.routine.set_app_name(self.appName)

    def run_routine(self):
        self.routine.run()

    def close(self):
        pass
