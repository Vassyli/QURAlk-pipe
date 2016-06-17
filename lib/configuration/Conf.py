import os


def expandFilename(filename):
    return os.path.expanduser(os.path.expandvars(filename))


class Reader:
    filename = None
    config = {}

    def __init__(self, filename):
        self.filename = expandFilename(filename)

        if not os.path.exists(self.filename):
            raise Exception("The configuration file «" + self.filename + "» does not exist.")

        self.parse()

    def get(self, key):
        if key in self.config:
            return self.config[key]
        else:
            raise Exception("key not found")

    def parse(self):
        with open(self.filename, "r") as fh:
            for line in fh:
                line = line.strip()

                # Skip emtpy lines or lines starting with comment tag
                if line[0] == "#" or len(line) < 2:
                    continue

                key, val = [x.strip() for x in line.split("=")]
                self.config[key] = val


class Writer:
    filename = None
    config = {}

    def __init__(self, filename):
        self.filename = expandFilename(filename)

    def set(self, key, val):
        self.config[key] = val

    def write(self):
        # Create directories if needed
        dirname = os.path.dirname(self.filename)
        if not os.path.exists(dirname):
            try:
                os.makedirs(dirname)
            except OSError as exc:
                # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        # Write to file
        with open(self.filename, "w") as fh:
            for key in self.config:
                fh.write(key + " = " + str(self.config[key]) + "\n")

