import os

from . import Conf


class ModConfiguration():
    config = {
        "ReferenceGenomPath": None,
        "ReferenceGenomFile": None,
        "GeneAnnotationFile": None,
        "SequenceAdapter5": None,
        "SequenceAdapter3": None,
        "OutputDirectory": None,
        "InputDirectory": None,
        "MaxPythonThreads": None,
        "MaxBowtieThreads": None,
    }

    def __init__(self, confFile):
        self.readOrCreateAndRead(confFile)

    def get(self, key):
        if key in self.config:
            if self.config[key] is None:
                raise Exception("Known key " + key + " has no value set. Please specify in your mod setting file")
            return self.config[key]
        else:
            raise Exception("Unknown key " + key + " asked in ModConfiguration.get")

    def readOrCreateAndRead(self, confFile):
        # Try to read the file, or create an example and read that
        try:
            reader = Conf.Reader(confFile)
        except Exception:
            self.writeDefaultConfig(confFile)
            try:
                reader = Conf.Reader(confFile)
            except Exception:
                raise Exception("Creation of default file not possible.")

        self.config["ReferenceGenomPath"] = Conf.expandFilename(reader.get("ReferenceGenomPath"))
        if not os.path.exists(self.config["ReferenceGenomPath"]):
            raise Exception("ReferenceGenomPath does not exist")
        if not os.path.isdir(self.config["ReferenceGenomPath"]):
            raise Exception("ReferenceGenomPath is not a valid path")

        self.config["ReferenceGenomFile"] = reader.get("ReferenceGenomFile")

        self.config["GeneAnnotationFile"] = Conf.expandFilename(reader.get("GeneAnnotationFile"))
        if not os.path.exists(self.config["GeneAnnotationFile"]):
            raise Exception("GeneAnnotationFile does not exist")

        self.config["SequenceAdapter5"] = reader.get("SequenceAdapter5")
        self.config["SequenceAdapter3"] = reader.get("SequenceAdapter3")

        self.config["OutputDirectory"] = Conf.expandFilename(reader.get("OutputDirectory"))
        if not os.path.exists(self.config["OutputDirectory"]):
            os.makedirs(self.config["OutputDirectory"])

        self.config["InputDirectory"] = Conf.expandFilename(reader.get("InputDirectory"))
        if not os.path.exists(self.config["InputDirectory"]):
            raise Exception("InputDirectory does not exist")

        self.config["MaxPythonThreads"] = int(reader.get("MaxPythonThreads"))
        self.config["MaxBowtieThreads"] = int(reader.get("MaxBowtieThreads"))

    def writeDefaultConfig(self, confFile):
        writer = Conf.Writer(confFile)

        writer.set("ReferenceGenomPath", "~/QURAlkData/GenRef")
        writer.set("ReferenceGenomFile", "s_cer")
        writer.set("GeneAnnotationFile", "~/QURAlkData/GenAnnot/annotation")
        writer.set("SequenceAdapter5", "^ATCGTAGGCACCTGAAA")
        writer.set("SequenceAdapter3", "CTGTAGGCACCATCAAT")
        writer.set("OutputDirectory", "~/QURAlkData/Output")
        writer.set("InputDirectory", "~/QURAlkData/Input")
        writer.set("MaxPythonThreads", 4)
        writer.set("MaxBowtieThreads", 2)

        writer.write()

        print("Written example file to %s" % confFile)