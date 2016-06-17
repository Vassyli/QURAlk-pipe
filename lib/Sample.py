import csv
import os
import subprocess

SAMTOOLS_SORT_MEMORY = "500M"


class Sample():
    sampleName = None
    settings = None

    def __init__(self, sampleName, settings):
        self.sampleName = sampleName
        self.settings = settings

    def run(self):
        jobs = [
            ["cutadapters", self.runCutAdapters, "[Error] Failed to run cutadapt for %s"],
            ["bowtieAlign", self.runBowtieAlign, "[Error] Failed ro run bowtie for %s"],
            ["fivePrimeFix", self.runFivePrimeFix, "[Error] Failed to run fivePrimeFix for %s"],
            ["samToBam", self.runSamToBam, "[Error] Failed to run samtools for %s"],
            ["sortBam", self.runSortBam, "[Error] Failed to run samtools for %s"],
            ["intersect", self.runIntersect, "[Error] Failed to run BEDTools for %s"],
            ["modcount", self.runModCount, "[Error] Failed to run modCount for %s"]
        ]

        for job in jobs:
            try:
                job[1]()
            except Exception as e:
                print(e)
                print(job[2] % (self.sampleName,))
                return

        print("Completed sample %s" % (self.sampleName,))

    def getFileName(self, suffix=None, extension=".fastq", ref=False):
        if suffix is None:
            return os.path.join(*[self.settings.get("InputDirectory"), self.sampleName + extension])
        else:
            if ref == False:
                filename = "%s_%s%s" % (
                    suffix,
                    self.sampleName,
                    extension
                )

                return os.path.join(*[self.settings.get("OutputDirectory"), filename])
                # return os.path.join(*[self.settings.get("OutputDirectory"), suffix + "_" + self.sampleName + extension])
            else:
                filename = "%s-%s_%s%s" % (
                    suffix,
                    self.settings.get("ReferenceGenomFile"),
                    self.sampleName,
                    extension
                )

                return os.path.join(*[self.settings.get("OutputDirectory"), filename])
                # return os.path.join(*[self.settings.get("OutputDirectory"), suffix + "-" + + "_" + self.sampleName + extension])

    def pack(self, targetFile):
        subprocess.check_output("gzip -f " + targetFile, shell=True)

    def runCutAdapters(self):
        """ Cuts the adapters from the sequence """

        # Cut 3' adapter
        cli = "cutadapt -m 25 -a %s %s > %s 2> %s"

        sequence3 = self.settings.get("SequenceAdapter3")
        toCut3 = {
            "in": self.getFileName(None, ".fastq.gz"),
            "out": self.getFileName("Trimmed", ".fastq"),
            "log": self.getFileName("Trimmed", ".log")
        }

        subprocess.check_output(cli % (sequence3, toCut3["in"], toCut3["out"], toCut3["log"]), shell=True)

        # Cut 5' adapter and separate modstop from adapter stop
        cli = "cutadapt -g %s --untrimmed-output %s %s > %s 2> %s"

        sequence5 = self.settings.get("SequenceAdapter5")
        toCut5 = {
            "in": toCut3["out"],
            "outMod": self.getFileName("ModStop", ".fastq"),
            "outAdapt": self.getFileName("AdaptStop", ".fastq"),
            "log": self.getFileName("ModAdaptStop", ".log")
        }

        subprocess.check_output(cli % (sequence5, toCut5["outMod"], toCut5["in"], toCut5["outAdapt"], toCut5["log"]),
                                shell=True)

        # Now let's pack these fastq files that we don't need anymore
        self.pack(toCut3["out"])
        self.pack(toCut5["outAdapt"])

    def runBowtieAlign(self):
        cli = "bowtie --best --chunkmbs 500 -p %d -t -S %s %s %s 2> %s"

        bowtie = {
            "threads": self.settings.get("MaxBowtieThreads"),
            "ref": os.path.join(*[self.settings.get("ReferenceGenomPath"), self.settings.get("ReferenceGenomFile")]),
            "in": self.getFileName("ModStop", ".fastq"),
            "out": self.getFileName("Aligned", ".sam", True),
            "log": self.getFileName("Aligned", ".log", True),
        }

        subprocess.check_output(cli % (bowtie["threads"], bowtie["ref"], bowtie["in"], bowtie["out"], bowtie["log"]),
                                shell=True)
        self.pack(bowtie["in"])

    def runFivePrimeFix(self):
        sets = {
            "in": self.getFileName("Aligned", ".sam", True),
            "out": self.getFileName("5pFixed", ".sam", True),
            "mismatch": self.getFileName("5pMisMatch", ".sam", True),
        }

        self.wrapFix(sets["in"], sets["out"], sets["mismatch"])

        # Delete not needed file
        subprocess.check_output("rm -f %s" % sets["in"], shell=True)

    def runSamToBam(self):
        cli = "samtools view -bS %s > %s 2> %s"

        sets = {
            "in": self.getFileName("5pFixed", ".sam", True),
            "out": self.getFileName("5pFixed", ".bam", True),
            "log": self.getFileName("5pFixed", ".log", True),
        }

        subprocess.check_output(cli % (sets["in"], sets["out"], sets["log"]), shell=True)

        # Delete not needed file
        subprocess.check_output("rm -f %s" % sets["in"], shell=True)

    def runSortBam(self):
        cli = "samtools sort -m " + SAMTOOLS_SORT_MEMORY + " %s %s 2> %s"

        sets = {
            "in": self.getFileName("5pFixed", ".bam", True),
            "out": self.getFileName("Sorted", "", True),
            "log": self.getFileName("Sorted", ".log", True),
        }

        subprocess.check_output(cli % (sets["in"], sets["out"], sets["log"]), shell=True)

        # Delete not needed file
        subprocess.check_output("rm -f %s" % sets["in"], shell=True)

    def runIntersect(self):
        intersectFile = self.settings.get("GeneAnnotationFile")

        cli = "intersectBed -s -wo -split -bed -abam %s -b %s %s > %s 2> %s"

        if intersectFile.endswith(".gff"):
            cli2 = """| awk 'BEGIN { OFS = "\t";} {split($21,a,";"); sub(/ID=/,"",a[1]); print $1, $2, $3, $4, $6, $15, $16, $17, a[1]}' """
        elif intersectFile.endswith(".bed"):
            cli2 = """| awk 'BEGIN { OFS = "\t";} {print $1, $2, $3, $4, $6, "NA", $14, $15, $16}' """
        else:
            raise Exception("Cannot read intersection file, unknown format!")

        sets = {
            "in": self.getFileName("Sorted", ".bam", True),
            "sect": intersectFile,
            "out": self.getFileName("Intersect", ".tab", True),
            "log": self.getFileName("Intersect", ".log", True),
        }

        subprocess.check_output(cli % (sets["in"], sets["sect"], cli2, sets["out"], sets["log"]), shell=True)

    def runModCount(self):
        # count ModStops on each position
        # inputfile = outputpath+"Intersect_"+ref+'_'+sampleName+'.tab'
        # outputfile = outputpath+"CountMod_"+ref+'_'+sampleName+".tab"
        inputfile = self.getFileName("Intersect", ".tab", True)
        outputfile = self.getFileName("CountMod", ".tab", True)

        intersectFile = self.settings.get("GeneAnnotationFile")
        if intersectFile.endswith(".gff"):
            intersectRefType = "gff"
        elif intersectFile.endswith(".bed"):
            intersectRefType = "bed"
        else:
            raise Exception("Can't determine gen annotation file format of %s" % intersectFile)

        fh = open(inputfile, 'r')
        genes = dict()

        """.tab file format:
        0       1       2       3       4       5       6       7       8
        chr     rStart  rEnd    rName   +/-     type    geneS   geneEnd geneName
        """

        line = fh.readline()
        while (line):
            line = line.split()
            gene = line[8]
            if (int(line[1]) > int(line[6]) and int(line[2]) < int(line[7])):  # if mod-stop is inside gene
                if gene not in genes:
                    genes[gene] = geneModCount(line[8], line[0], *line[4:8])
                if line[4] == '+':
                    if intersectRefType == 'gff':
                        genes[gene].countArray[int(line[1]) - int(line[6])] += 1
                    elif intersectRefType == 'bed':
                        genes[gene].countArray[int(line[1]) - int(line[6]) - 1] += 1
                elif line[4] == '-':
                    genes[gene].countArray[int(line[7]) - int(line[2]) - 1] += 1

            line = fh.readline()
        # print genes[gene]
        fh.close()

        for gene in genes:
            genes[gene].count = sum(genes[gene].countArray)
            genes[gene].countPerNt = float(genes[gene].count) / genes[gene].length
            genes[gene].getDescription()

        fh = open(outputfile, 'w')
        mywriter = csv.writer(fh, delimiter=' ')
        for gene in genes:
            # if genes[gene].countPerNt > 1:
            mywriter.writerow([">"] + genes[gene].description)
            mywriter.writerow(genes[gene].countArray)
        fh.close()

    def wrapFix(self, inputfile, outputfile, mismatchfile):
        """ Taken from mod-seeker, need to rewrite """
        # if inputfile.endswith(".bam"):
        #    inputfile = self.bamToSam(inputfile)

        fhIn = open(inputfile, "r")
        fhOut = open(outputfile, "w")
        fhOut.close()
        fhOut = open(outputfile, "a")
        fhMis = open(mismatchfile, "w")
        fhMis.close()
        fhMis = open(mismatchfile, "a")

        i = 0
        mis = 0
        writerOut = csv.writer(fhOut, delimiter="\t")
        writerMis = csv.writer(fhMis, delimiter="\t")
        # read lines, loop through file
        line = fhIn.readline()

        while line:
            lineOrigin = line
            lineStr, misCount = self.fix(line)
            if line:
                fhOut.write(lineStr)
            if misCount:
                fhMis.write(lineOrigin)
                mis += 1
            line = fhIn.readline()
            i += 1

        fhIn.close()
        fhOut.close()
        fhMis.close()

    def fix(self, line):
        # sam file format example:
        # HISEQ:108:H7N5WADXX:1:1107:18207:18800  0       gi|207113128|ref|NR_002819.2|   553     255     51M     *       0       0       AAAATTTCCGTGCGGGCCGTGGGGGGCTGGCGGCAACTGGGGGGCCGCAGA     BBBFFFFFFFFFFIIIIIIIIIIIIFFFFFFFFFFFFFFFFFFFFFFFFFF   XA:i:0  MD:Z:51 NM:i:0
        # QNAME FLAG RNAME POS(leftmost) MAPQ CIGAR RNEXT PNEXT TLEN SEQ QUAL
        misCount = 0
        lineStr = line
        line = line.split()
        if len(line) >= 13:
            m = line[12].split(':')
            # if(line[1]=='0' or line[1]=='16') and len(m[2]) > 2: #mismatch detected
            # if (line[1]=='0' or line[1]=='16'):
            # if m[1] != 'Z':

            if line[1] == '0':  # postive strand, remove 5' end

                while m[2].startswith('0'):  # have a mismatch
                    m[2] = m[2][2:]  # strip first two character
                    misCount += 1  # mismatch count +1
                if misCount != 0:
                    line[3] = str(int(line[3]) + misCount)  # move 5'start to 3' direction
                    line[5] = str(int(line[5].rstrip('M')) - misCount) + 'M'  # change seq length
                    line[9] = line[9][misCount:]
                    line[10] = line[10][misCount:]
                    line[12] = 'MD:Z:' + str(len(line[9]))
                lineStr = '\t'.join(line)
                lineStr = lineStr + '\n'
            elif line[1] == '16':  # negtive strand, remove 3' end
                while (m[2][-1] == '0' and m[2][-2] in "ATCG"):  # have a mismatch
                    m[2] = m[2][:-2]  # strip last two character
                    misCount += 1  # mismatch count +1
                if misCount != 0:
                    line[5] = str(int(line[5].rstrip('M')) - misCount) + 'M'  # change seq length
                    line[9] = line[9][:-misCount]
                    line[10] = line[10][:-misCount]
                    line[12] = 'MD:Z:' + str(len(line[9]))
                lineStr = '\t'.join(line)
                lineStr = lineStr + '\n'
        return (lineStr, misCount)


class geneModCount(object):
    def __init__(self, name, chrms, strain, featureType, posStart, posEnd):
        self.name = name
        self.chrms = chrms
        self.strain = strain
        self.featureType = featureType
        self.Start = int(posStart)
        self.End = int(posEnd)
        self.length = self.End - self.Start + 1
        self.count = "NA"
        self.countPerNt = "NA"
        self.countArray = [0 for i in range(self.length)]
        self.description = [self.name, self.chrms, self.strain, self.featureType, self.Start, self.End, self.length,
                            self.count, self.countPerNt]

    def getDescription(self):
        self.description = [self.name, self.chrms, self.strain, self.featureType, self.Start, self.End, self.length,
                            self.count, self.countPerNt]
