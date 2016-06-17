import math
import scipy.stats


class StatMagician:
    dataList = None
    FDR = 0.05
    OddsRatioThreshold = 1.5
    TAIL = 45

    def __init__(self, dataList, FDR, OddsRatioThreshold):
        # Assert that data only comes in pairs
        assert len(dataList) % 2 == 0

        self.dataList = dataList
        self.FDR = FDR
        self.OddsRatioThreshold = OddsRatioThreshold

    def run(self):
        numOfSamples = len(self.dataList)
        reps = len(self.dataList) // 2
        output = {}

        # Run one of the gene lists
        for gene in self.dataList[0]:
            # Check if the gene exists in ALL samples
            if self.checkGeneExistsInAllSamples(gene):
                output[gene] = self.dataList[0][gene]
                output[gene].testArray = ["NA" for i in range(0, output[gene].length)]

                pvalues = []

                for i in range(0, output[gene].length):
                    counts = []
                    array = []

                    for j in range(0, numOfSamples):
                        a = int(self.dataList[j][gene].countArray[i])
                        b = int(self.dataList[j][gene].count)

                        array.append(max(a, 1))
                        array.append(max(b, 1))
                        counts.append(a)
                        counts.append(b)

                    if len(array) == 4:
                        # 4 Samples
                        (chi, p, OR, ORL, ORU) = self.testChisq(array)
                    elif len(array) % 4 == 0:
                        # n*4 samples
                        (chi, p, OR, ORL, ORU) = self.testCMH(array)
                    else:
                        raise Exception("Number of sample files have to be a multiple of 4")

                    output[gene].testArray[i] = list((chi, p, 'NA', OR, ORL, ORU)) + counts  # 'NA' is for p_adjusted
                    pvalues.append(p)

                p_sig = self.BHcontrol(pvalues)  # list pvalues has been sorted in BHcontrol

                if p_sig != "NA":
                    for i in range(0, output[gene].length):
                        if output[gene].testArray[i][1] <= p_sig:
                            j = pvalues.index(output[gene].testArray[i][1]) + 1  # rank
                            output[gene].testArray[i][2] = output[gene].testArray[i][1] * output[gene].length / float(j)
        # Return
        return output

    def checkGeneExistsInAllSamples(self, geneName):
        """ geneName is the index used for every data dict in dataList """
        for sample in self.dataList:
            if geneName not in sample:
                return False
        return True

    def testChisq(self, array):
        """ Calculates the chi value of a 2X2 table with:
          [a c]
          [b d]
        It uses the chi2 contingency test with Yates continuity.

        ToDo: Use numpy here? """
        a, b, c, d = array
        z = 1.959964

        array = [
            [a, c],
            [b, d],
        ]

        chi, p, dof, details = scipy.stats.chi2_contingency(array, True)

        OR = (a * d) / (b * c)
        SE = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)

        ORL = OR * math.exp(-z * SE)
        ORU = OR * math.exp(z * SE)

        return chi, p, OR, ORL, ORU

    def testCMH(self, array):
        """ This function makes a
        Cochran-Mantel-Haenszel Chi-Squared Test for Count Data
        This test method is known in R, but unknown in scipy """

        reps = len(array) // 4
        chit1Sum = 0
        chit2Sum = 0
        ORt1Sum = 0
        ORt2Sum = 0
        SEt1_nSum = 0
        SEt1_dSum = 0
        SEt2_nSum = 0
        SEt2_dSum = 0
        SEt3_nSum = 0

        for i in range(0, reps):
            a = array[4 * i]
            b = array[4 * i + 1]
            c = array[4 * i + 2]
            d = array[4 * i + 3]
            n = float(a + b + c + d)

            chit1 = a - (a + b) * (a + c) / n
            chit2 = (a + b) * (a + c) * (b + d) * (c + d) / (n ** 3 - n ** 2)
            chit1Sum += chit1
            chit2Sum += chit2

            ORt1 = a * d / n
            ORt2 = b * c / n
            ORt1Sum += ORt1
            ORt2Sum += ORt2

            SEt1_n = (a + d) * a * d / n ** 2
            SEt1_d = a * d / n
            SEt2_n = (b + c) * b * c / n ** 2
            SEt2_d = b * c / n
            SEt3_n = ((a + d) * b * c + (b + c) * a * d) / n ** 2
            SEt1_nSum += SEt1_n
            SEt1_dSum += SEt1_d
            SEt2_nSum += SEt2_n
            SEt2_dSum += SEt2_d
            SEt3_nSum += SEt3_n

        chi = (abs(chit1Sum) - 0.5) ** 2 / chit2Sum
        OR = ORt1Sum / ORt2Sum
        var = SEt1_nSum / (2 * SEt1_dSum ** 2) + SEt2_nSum / (2 * SEt2_dSum ** 2) + SEt3_nSum / (
        2 * SEt1_dSum * SEt2_dSum)
        SE = math.sqrt(var)
        z = 1.959964
        ORL = OR * math.exp(SE * (-z))
        ORU = OR * math.exp(SE * z)

        pvalue = self.pchisq(chi)

        return (chi, pvalue, OR, ORL, ORU)

    def pchisq(self, x):
        """ Returns the p-value of a chi-sq test with df=1 """
        return 1 - math.erf(math.sqrt(0.5 * float(x)))

    def BHcontrol(self, pvalues):
        pvalues.sort()
        m = float(len(pvalues))
        p = 0
        i = 0

        while p <= ((i + 1) / m) * self.FDR and i < m:
            p = pvalues[i]
            i += 1

        p_sig = pvalues[max(i - 1, 0)]

        if p_sig <= self.FDR:
            # print "BHcontrol:", p_sig, m, i-1
            return p_sig
        else:
            return 'NA'