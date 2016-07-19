import csv
import datetime
import os

from lib.configuration.StatConfiguration import StatConfiguration
from lib.configuration.ModConfiguration import ModConfiguration
from lib.GeneModCount import GeneModCount2 as GeneModCount
from lib.StatMagician import StatMagician

from .BaseRoutine import BaseRoutine


class StatRoutine(BaseRoutine):
    settings = None
    dataList = []
    dataFileList = []

    FDR = 0.05
    OddsRatioThreshold = 1.5
    TAIL = 45
    outputFile = None

    def get_cli_help(self):
        return "Runs statistical tests over the data created with mod and saves only significant gene positions"

    def get_more_cli_help(self):
        return """Runs statistical tests over the data created with the mod procedure and only
saves gene positions with significant changes between treated and control sample."""

    def run(self):
        self.load_settings()
        self.load_data()
        self.run_statistics()

    def load_settings(self):
        filesearchpath = ModConfiguration("~/QURAlkData/mod_config.ini").get("OutputDirectory")
        self.settings = StatConfiguration("~/QURAlkData/stat_config.ini", filesearchpath)

        self.FDR = self.settings.get("FDR")
        self.OddsRatioThreshold = self.settings.get("OddsRatioThreshold")
        self.outputFile = os.path.join(*[
            filesearchpath,
            "output_stats_{}.csv".format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.txt"))
        ])

    def load_data(self):
        print("Loading data files")

        for i in range(0, len(self.settings.get("files"))):
            # Treated: even
            self.dataList.append(self.readSingleDataFile(self.settings.get("files")[i][0]))
            self.dataFileList.append(self.settings.get("files")[i][0])
            # Control: uneven
            self.dataList.append(self.readSingleDataFile(self.settings.get("files")[i][1]))
            self.dataFileList.append(self.settings.get("files")[i][1])

        print("Loading has been completed")

    def run_statistics(self):
        magic = StatMagician(self.dataList, self.settings.get("FDR"), self.settings.get("OddsRatioThreshold"))
        statistics = magic.run()

        self.writeData(statistics)

    def readSingleDataFile(self, filename):
        print(" - Load: %s" % os.path.basename(filename))

        data = {}
        lastDataIndex = None

        with open(filename, "r") as fh:
            for line in fh:
                # Skip non-description lines
                if not line.startswith(">"):
                    continue

                gene = GeneModCount.restore_from_storage(*line.split()[1:11])
                gene.countArray = [int(x) for x in next(fh).split()]
                gene_index = gene.name + "_" + str(gene.Start) + "_" + str(gene.End)

                #data[gene.name] = gene
                data[gene_index] = gene

        print("    (found %i genes)" % len(data))

        return data

    def writeData(self, output):
        print(self.outputFile)

        with open(self.outputFile, "w") as fh:
            writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
            fileheader = []

            for i in range(0, len(self.dataFileList)):
                fileheader.append(os.path.basename(self.dataFileList[i]))
                fileheader.append(os.path.basename(self.dataFileList[i]) + "_SUM")

            header = [
                 "geneName",
                 "chrom",
                 "strand",
                 "type",
                 "start",
                 "end",
                 "length",
                 "pos_o_gene",
                 "chisq",
                 "p_origin",
                 "p_adjusted",
                 "odds_ratio",
                 "OR_lower",
                 "OR_upper"
             ] + fileheader

            # Write header line
            writer.writerow(header)

            for gene in output:
                #print("For gene...", gene.name)
                for i in range(0, max(output[gene].length - self.TAIL, 0)):
                    p_adjusted = output[gene].testArray[i][2]
                    OR = output[gene].testArray[i][3]

                    if p_adjusted != "NA" and p_adjusted <= self.FDR and OR > self.OddsRatioThreshold:
                        # reformat chi, p_origin, p_adjusted, OR, OR_L and OR_U
                        values = output[gene].testArray[i]

                        chi = '{:.3f}'.format(values[0])
                        p_origin = '{:.4g}'.format(values[1])
                        p_adjusted = '{:.4g}'.format(values[2])
                        OR = '{:.3f}'.format(values[3])
                        OR_l = '{:.3f}'.format(values[4])
                        OR_u = '{:.3f}'.format(values[5])

                        row = output[gene].description[:7] + [i + 1] + [chi, p_origin, p_adjusted, OR, OR_l, OR_u] + \
                              output[gene].testArray[i][6:]
                        writer.writerow(row)
                    """else:
                        print(
                            output[gene].name,
                            "Pos",
                            i + 1,
                            p_adjusted,
                            "NA" if p_adjusted == "NA" else p_adjusted <= self.FDR,
                            "NA" if p_adjusted == "NA" else int(p_adjusted) > self.OddsRatioThreshold
                        )"""
