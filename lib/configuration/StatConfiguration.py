import os

from . import Conf


class StatConfiguration():
    config = {
        "FDR": None,
        "OddsRatioThreshold": None,
        "NumberOfReplicates": None,
        "files": None,
    }

    def __init__(self, confFile, fileSearchPath):
        self.readOrCreateAndRead(confFile, fileSearchPath)

    def get(self, key):
        if key in self.config:
            return self.config[key]
        else:
            raise Exception("Unknown key " + key + " asked in StatConfiguration.get")

    def readOrCreateAndRead(self, confFile, fileSearchPath):
        # Try to read the file, or create an example and read that
        try:
            reader = Conf.Reader(confFile)
        except Exception:
            self.writeDefaultConfig(confFile)
            try:
                reader = Conf.Reader(confFile)
            except Exception:
                raise Exception("Creation of default file not possible.")

        # Read options
        self.config["FDR"] = float(reader.get("FDR"))
        self.config["OddsRatioThreshold"] = float(reader.get("OddsRatioThreshold"))
        self.config["NumberOfReplicates"] = int(reader.get("NumberOfReplicates"))

        # Read files
        treatedFiles = [x.strip() for x in reader.get("treatedFiles").split(",")]
        controlFiles = [x.strip() for x in reader.get("controlFiles").split(",")]

        if len(treatedFiles) != len(controlFiles):
            raise Exception("The number of treated Files must be the same as the number of control files")
        if len(treatedFiles) != self.config["NumberOfReplicates"]:
            raise Exception("The number of files given must be the same as stated on NumberOfReplicates")

        treatedFilesFull = []
        controlFilesFull = []

        # Check files
        for fileItem in treatedFiles:
            fullFile = Conf.expandFilename(os.path.join(*[fileSearchPath, fileItem + ".tab"]))
            if not os.path.exists(fullFile):
                raise Exception(fullFile + " does not exist")
            treatedFilesFull.append(fullFile)

        for fileItem in controlFiles:
            fullFile = Conf.expandFilename(os.path.join(*[fileSearchPath, fileItem + ".tab"]))
            if not os.path.exists(fullFile):
                raise Exception(fullFile + " does not exist")
            controlFilesFull.append(fullFile)

        # Store files
        self.config["files"] = []
        for i in range(0, len(treatedFiles)):
            self.config["files"].append((treatedFilesFull[i], controlFilesFull[i]))

    def writeDefaultConfig(self, confFile):
        writer = Conf.Writer(confFile)

        writer.set("FDR", 0.05)
        writer.set("OddsRatioThreshold", 1.5)
        writer.set("NumberOfReplicates", 2)
        writer.set("treatedFiles", "file1a, file2a")
        writer.set("controlFiles", "file1b, file2b")

        writer.write()

        print("Created stat configuration file at %s" % confFile)