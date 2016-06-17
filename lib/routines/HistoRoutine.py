
import datetime
import matplotlib
matplotlib.use('cairo')

import matplotlib.pyplot as plt
import os
import math

from lib.configuration.ModConfiguration import ModConfiguration
from lib.configuration.StatConfiguration import StatConfiguration
from .StatRoutine import StatRoutine


class DataList:
    datalist = []

    def __init__(self, datalist):
        self.datalist = datalist

    def __contains__(self, item):
        for l in self.datalist:
            if item not in l:
                return False

        return True

    def __getitem__(self, geneName):
        return self.datalist[0][geneName]

    def common(self):
        for gene in self.datalist[0]:
            if gene in self:
                yield gene

    def treatedCountAverage(self, gene, i):
        counts = 0
        for t in range(0, len(self.datalist), 2):
            counts = counts + int(self.datalist[t][gene].countArray[i])
        return int(round(counts, 0) / (len(self.datalist) / 2))

    def controlCountAverage(self, gene, i):
        counts = 0
        for c in range(1, len(self.datalist), 2):
            counts = counts + int(self.datalist[c][gene].countArray[i])
        return int(round(counts, 0) / (len(self.datalist) / 2))


class HistoRoutine(StatRoutine):
    settings = None
    fileSearchPath = None
    geneFilter = None

    def get_cli_help(self):
        return "Creates histogram for every single gene"

    def get_more_cli_help(self):
        return """Creates a histogram of all genes derives by mod.
Genes can be filtered by passing an additional option.

To filter for genes starting with RDN, use:

$ quralk-pipe histo ^RDN

To filter for genes ending with 25S, use:

$ quralk-pipe histo 25S$

Additionally, free fit strings (without using ^ or $) as well as
exact strings (starting with ^ and ending with $) can be used as well."""

    def run(self):
        self.load_settings()
        self.load_data()
        self.run_histograms()

    def load_settings(self):
        filesearchpath = ModConfiguration("~/QURAlkData/mod_config.ini").get("OutputDirectory")
        self.settings = StatConfiguration("~/QURAlkData/stat_config.ini", filesearchpath)
        self.fileSearchPath = filesearchpath
        if len(self.arguments) > 0:
            self.geneFilter = self.arguments[0]
        else:
            self.geneFilter = ""

    def run_histograms(self):
        self.draw_histogram()

    def draw_histogram(self):
        datalist = DataList(self.dataList)

        if len(self.geneFilter) == 0:
            filterF = lambda name: True
        elif self.geneFilter.startswith("^") and self.geneFilter.endswith("$"):
            filterF = lambda name, f=self.geneFilter: name == f
        elif self.geneFilter.startswith("^"):
            filterF = lambda name, f=self.geneFilter: name.startswith(f[1:])
        elif self.geneFilter.endswith("$"):
            filterF = lambda name, f=self.geneFilter: name.endswith(f[:-1])
        else:
            filterF = lambda name, f=self.geneFilter: str.find(name, f) != -1

        # Get all genes common in all files
        for geneName in datalist.common():
            if not filterF(geneName):
                continue
            if len(self.geneFilter) > 0:
                print("Found", self.geneFilter, "in", geneName)

            # Make histogram for all of them!
            gene = datalist[geneName]

            treatedCountAverage = []
            controlCountAverage = []
            differenceCountAverage = []

            for pos in range(gene.length):
                treatedCountAverage.append(datalist.treatedCountAverage(geneName, pos))
                controlCountAverage.append(datalist.controlCountAverage(geneName, pos))
                differenceCountAverage.append(treatedCountAverage[pos] - controlCountAverage[pos])

            f, (ax1, ax2, ax3) = plt.subplots(3, sharex=True, sharey=True)
            width = 1.0
            pos = range(gene.Start, gene.Start + gene.length)

            ax1.bar(pos, treatedCountAverage, width)
            ax1.set_xlim(gene.Start, gene.Start + gene.length)
            ax1.set_xlabel("Position")
            ax1.set_ylabel("counts")
            ax1.set_ylim(min(0, min(differenceCountAverage)),
                         max(max(max(treatedCountAverage), max(controlCountAverage)), 100))
            ax1.set_title("Gene %s on chromosome %s" % (gene.name, gene.chrms))

            ax2.bar(pos, controlCountAverage, width)
            ax3.bar(pos, differenceCountAverage, width)

            f.subplots_adjust(hspace=0)
            plt.setp([a.get_xticklabels() for a in f.axes[:-1]], visible=False)

            filename = "histogram_%s.png" % (geneName)
            filename = os.path.join(*[self.fileSearchPath, filename])

            print(filename)
            plt.savefig(filename)

