import pandas
import pickle
import json
import sys
import re
from preprocessing import get_df
from pprint import pprint

class DataAnalyser():
    def __init__(self,classifierPath):
        self.classifier = self.initClassifier(classifierPath)

    def initClassifier(self, classifierPath):
        with open(classifierPath, "rb") as infile:
            classifier = pickle.load(infile)
            return classifier

    def analyse(self,jsonPath):
        rows = self.findRows(jsonPath)
        result = self.analyseRows(rows)
        return result

    def findRows(self,jsonPath):
        df = get_df(jsonPath)
        plainText = df["plainText"]
        dropFeatures = ["plainText", "jsonPath"]
        dropFeatures.extend(
            ["biggestWhitespaceX0", "dots", "lastCharAB", "x0", "eurExists", "distanceBot", "firstCharDigit",
             "firstCharAB",
             "otherDigits", "colons", "relativeRowPosition", "y0", "belegExists", "distanceTop",
             "maxWhiteSpaceX0Matches",
             "lastCharAWBW", "maxWhiteSpaceLengthMatches"])
        df = df.drop(columns=dropFeatures)
        label_predictions = self.classifier.predict(df)

        articles = []
        sums = []
        vats = []
        vatSums = []
        for i in range(0, len(label_predictions)):
            label = label_predictions[i]
            if label == 1:
                articles.append(plainText[i])
            if label == 2:
                sums.append(plainText[i])
            if label == 3:
                vats.append(plainText[i])
            if label == 4:
                vatSums.append(plainText[i])
        rows = {"articles": articles, "sums": sums, "vats": vats, "vatSums": vatSums}
        return rows

    def analyseRows(self,rows):
        #articles:
        articles = self.analyse_Articles(rows["articles"])
        sum = self.analyse_Sums(rows["sums"])
        vats = self.analyse_Vats(rows["vats"])
        if len(rows["vatSums"]) >0:
            vatSum = self.analyse_vatsums(rows["vatSums"])
        else:
            vatSum = []

        result = {"articles": articles, "sum": sum, "vats": vats, "vatSum": vatSum}
        return result

    def analyse_Articles(self,articleTexts):
        articles = []
        for articleText in articleTexts:
            floatStrings = self.findFloatStrings(articleText)
            # find price and description
            if len(floatStrings) == 0:
                description = articleText
                price = "unknown"
            elif len(floatStrings) == 1:
                price = self.convertFloat(floatStrings[0]) # convert to float
                description = articleText.replace(floatStrings[0], "")  # delete price from description
            elif len(floatStrings) == 2:
                price = self.convertFloat(floatStrings[1])
                # remove last two floats from description
                description = self.removeFloats(articleText, floatStrings[-2:])
            else: #min 3 floats
                price = self.convertFloat(floatStrings[-1])
                # remove last three from description
                description = self.removeFloats(articleText, floatStrings[-3:])

            # find vat class
            found = False
            if description[-2].lower() in ["a","2","8"]:
                vat = "A"
                description = description[:-2]
                found = True
            elif description[-2].lower() in ["b","5","0"]:
                vat = "B"
                description = description[:-2]
                found = True
            # if ends with aw or ap
            if (description[-3].lower() in ["a","2","8"]) & (description[-2].lower() in ["w", "p"]):
                vat = "A"
                description = description[:-3]
                found = True
            elif (description[-3].lower() in ["b","5","0"]) & (description[-2].lower() in ["w", "p"]):
                vat = "B"
                description = description[:-3]
                found = True
            if not found:
                vat = "---unknown---"
            article = {"description": description, "price": price, "vat": vat}
            articles.append(article)
        return articles

    def analyse_Sums(self,sumTexts):
        if len(sumTexts) > 1:
            print("------------------------------------")
            print("Allert: more then 1 sum row detected")
            print("------------------------------------")
        sum = self.findFloatStrings(sumTexts[0])
        if len(sum) > 0:
            sum = self.convertFloat(sum[0])
        else:
            #assume comma wasnt recognized
            regex = "\d+"
            float_matches = re.findall(regex, sumTexts[0])
            if len(float_matches) != 2:
                print("------------------------------------")
                print("Alert: No comma and not two numbers were found in sum row")
                print(sumTexts[0])
                print("------------------------------------")
                sum = "unknown"
            else:
                sum = float_matches[0]+"."+float_matches[1]
                sum = self.convertFloat(sum)

        return sum

    def analyse_Vats(self, vatTexts):
        vats = []
        for vatText in vatTexts:
            #find all float values in string:
            floatStrings = self.findFloatStrings(vatText)
            floats = []
            for floatString in floatStrings:
                f = self.convertFloat(floatString)
                floats.append(f)
            #find vat class (a|b)
            vatClass = vatText[0].upper()

            if len(floats) < 3:
                vat = {"netto": "unknown", "brutto": "unknown", "class": vatClass}
                print("------------------------------------")
                print("Alert: Less then 3 floats in vat row found")
                print(vatText)
                print("------------------------------------")
            else:
                if len(floats) > 4:
                    print("------------------------------------")
                    print("Alert: More then 4 floats in vat row found")
                    print(vatText)
                    print("------------------------------------")

                if len(floats) == 4:#then remove the 7,00 / 19,00
                    if (7.00 in floats) & (19.00 in floats):
                        print("------------------------------------")
                        print("Alert: found 4 floats in vat. It contains 7.00 aswell as 14.00")
                        print(vatText)
                        print("------------------------------------")
                        floats = floats[1:] # remove first float, assuming this is mehrwertsteuersatz
                        taxRate = floats[1]
                    elif 7.00 in floats:
                        floats.remove(7.00)
                        taxRate = 7.00
                    elif 19.00 in floats:
                        floats.remove(19.00)
                        taxRate = 19.00
                elif len(floats) == 3:#edeka
                    percentage = re.findall(" \d{1,2} %", vatText)[0]
                    taxRate = float(percentage.replace("%","").replace(" ",""))

                # if there are negative values:
                negVals = False
                if any(f < 0 for f in floats):
                    negVals = True
                    for i in range(len(floats)):
                        floats[i] = -1 * floats[i]

                mwst = min(floats)
                brutto = max(floats)
                if mwst == 0.0:
                    print("------------------------------------")
                    print("Alert: mwst is 0")
                    print(vatText)
                    print("------------------------------------")
                    netto = brutto
                else:
                    netto = [f for f in floats if f not in [mwst,brutto]][0] #get the value that is not mwst or brutto
                if not round(brutto - mwst,2) == netto:
                    print("------------------------------------")
                    print("Alert: Brutto - MwSt != Netto")
                    print(vatText)
                    print("------------------------------------")

                #turn neg values back into neg values
                if negVals:
                    for i in range(len(floats)):
                        floats[i] = -1 * floats[i]

                vat = {"netto": netto, "brutto": brutto, "class": vatClass, "taxRate":taxRate}
            vats.append(vat)
        return vats

    def analyse_vatsums(self, vatsumTexts):
        if len(vatsumTexts) > 1:
            print("------------------------------------")
            print("Alert: more than 1 vat sum found")
            print("------------------------------------")
        floats = self.findFloatStrings(vatsumTexts[0])
        for i in range(len(floats)):
            floats[i] = self.convertFloat(floats[i])

        if len(floats) != 3:
            vatSum = {"netto":"unknown", "brutto":"unknown"}
        else:
            mwst = min(floats)
            brutto = max(floats)
            netto = [f for f in floats if f not in [mwst, brutto]][0]  # get the value that is not mwst or brutto
            vatSum = {"netto": netto, "brutto": brutto}
        return vatSum

    def findFloatStrings(self, text):
        float_regex = "(\d+ \. \d{1,2})|(\d+ , \d{1,2})"
        pos_matches = re.finditer(float_regex, text)
        positions = [(m.start(0)) for m in pos_matches]

        float_matches = re.findall(float_regex, text)
        float_values = []
        for tuple in float_matches:
            value = [f for f in tuple if not f == ""][0]
            float_values.append(value)

        myFloats = []
        for i in range(len(float_values)):
            pos = positions[i]
            val = float_values[i]
            if text[pos-2] == "-":
                val = "- " + val
            myFloat = val
            myFloats.append(myFloat)
        return myFloats

    def convertFloat(self, floatString):
        fl = floatString.replace(" ","")
        fl = fl.replace(",",".")
        fl = float(fl)
        return fl

    def removeFloats(self,articleText, floatStrings):
        description = articleText
        i = 0
        iterateThrough = False
        while i < len(floatStrings):
            floatString = floatStrings[i]
            # if this is negative float it might have gotten its abs value removed before
            if (i > 0) & ("-" in floatString) & (not iterateThrough):
                description = articleText
                i = -1  # start loop from beginning
                iterateThrough = True # dont check if in description again
            description = description.replace(floatString, "")
            i += 1
        return description

def main(jsonPath):
    classifierPath = "../classifier.pkl"
    analyser = DataAnalyser(classifierPath)
    result = analyser.analyse(jsonPath)
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        jsonPath = sys.argv[1]
    else:
        jsonPath = "../assets/edekaData/tx_515_2-40.webp.json"
    result = main(jsonPath)

    print("articles:")
    pprint(result["articles"])
    print()
    print("sum:")
    pprint(result["sum"])
    print()
    print("vats:")
    pprint(result["vats"])
    print()
    print("vatSum:")
    pprint(result["vatSum"])
    print()