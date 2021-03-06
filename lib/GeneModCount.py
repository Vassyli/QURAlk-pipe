import numpy as np

class GeneModCount2:
    name = None
    chrms = None
    strain = None
    featureType = None

    Start = 0
    End = 0
    length = 1

    def __init__(self, gene_name, chromosome, strain, feature_type, pos_start, pos_end):
        self.name = gene_name
        self.chrms = chromosome
        self.strain = strain
        self.featureType = feature_type

        self.Start = int(pos_start)
        self.End = int(pos_end)
        self.length = self.End - self.Start + 1

        #self.countArray = np.zeros(self.length, np.int32)
        self.countArray = [0 for i in range(self.length)]
        self.testArray = ["NA" for i in range(0, self.length)]

        self.prepare_description()

    def restore_from_storage(gene_name, chromosome, strain, feature_type, pos_start, pos_end, length, count, count_per_nt):
        gene = GeneModCount2(gene_name, chromosome, strain, feature_type, pos_start, pos_end)
        gene.length = int(length)
        gene.count = int(count)
        gene.countPerNt = float(count_per_nt)

        return gene

    def calculate_statistics(self):
        self.count = sum(self.countArray)
        self.countPerNt = self.count / self.length

    def prepare_description(self):
        self.calculate_statistics()
        self.description = [
            self.name,
            self.chrms,
            self.strain,
            self.featureType,
            self.Start,
            self.End,
            self.length,
            self.count,
            self.countPerNt
        ]

    def getDescription(self):
        self.calculate_statistics()
        self.prepare_description()
        return self.description


class GeneModCount():
    def __init__(self, name, chrms, strain, featureType, posStart, posEnd):
        self.name = name
        self.chrms = chrms
        self.strain = strain
        self.featureType = featureType
        self.Start = int(posStart)
        self.End = int(posEnd)
        self.length = self.End - self.Start + 1
        self.countArray = [0 for i in range(self.length)]
        self.count = "NA"
        self.countPerNt = "NA"
        self.testArray = ['NA' for i in range(self.length)]
        self.stat()
        self.getDescription()

    def stat(self):
        self.count = sum(self.countArray)
        self.countPerNt = float(self.count) / self.length

    def getDescription(self):
        self.stat()
        self.description = [self.name, self.chrms, self.strain, self.featureType, self.Start, self.End, self.length,
                            self.count, self.countPerNt]
        return (self.description)

    def copyGene(self, newName):
        newGene = geneModCount(newName, self.chrms, self.strain, self.featureType, self.Start, self.End)
        newGene.length = self.length
        newGene.countArray = copy.deepcopy(self.countArray)
        newGene.count = self.count
        newGene.countPerNt = self.countPerNt
        newGene.testArray = copy.deepcopy(self.testArray)
        return newGene

    def mergeGenes(self, other, newName):
        newGene = self.copyGene(newName)
        for i in range(min(newGene.length, other.length)):
            newGene.countArray[i] = int(self.countArray[i]) + int(other.countArray[i])
            newGene.count = int(self.count) + int(other.count)
        return newGene