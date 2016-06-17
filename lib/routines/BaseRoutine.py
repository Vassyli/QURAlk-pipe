
class BaseRoutine:
    appName = None
    arguments = []

    def set_app_name(self, appName):
        self.appName = appName

    def set_arguments(self, arguments):
        self.arguments = arguments

    def get_cli_help(self):
        raise NotImplementedError("Implement BaseRoutine.get_cli_help() in {}".format(self.__class__))

    def get_more_cli_help(self):
        raise NotImplementedError("Implement BaseRoutine.get_more_cli_help() in {}")

    def run(self):
        raise NotImplementedError("Implement BaseRoutine.run() in {}".format(self.__class__))