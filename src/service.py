import pandas
import pickle
import json
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
        articles = []
        for articleText in rows["articles"]:
            print(articleText)
            float_regex = "(\d+ \. \d{1,2})|(\d+ , \d{1,2})"
            floats = re.findall(float_regex, articleText)
            #find price and description
            if len(floats) == 0:
                description = articleText
                price = "not found"
            elif len(floats) == 1:
                priceTuple = floats[0]
                for p in priceTuple:
                    price = p #finds the one that exists
                    if "- "+price in articleText:
                        price = "- "+price
                description = articleText.replace(price,"")#delete price from description
            else:
                priceTuple = floats[-1] #get last priceTuple
                for p in priceTuple:
                    price = p #finds the one that exists
                    if "- "+price in articleText:
                        price = "- "+price
                #remove last two floats from description
                description = articleText
                for priceTuple in floats[-2:]:
                    for p in priceTuple:
                        if "- " + p in articleText:
                            description = description.replace("- " + p, "")
                        else:
                            description = description.replace(p,"")
            price = price.replace(" ","")#remove spaces


            #find vat class
            found = False
            if description[-2].lower() == "a":
                vat = "a"
                description = description[:-2]
                found = True
            elif description[-2].lower() == "b":
                vat = "b"
                description = description[:-2]
                found = True
            #if ends with aw or ap
            if (description[-3].lower() == "a") & (description[-2].lower() in ["w","p"]):
                vat = "a"
                description = description[:-3]
                found = True
            elif (description[-3].lower() == "b") & (description[-2].lower() in ["w","p"]):
                vat = "b"
                description = description[:-3]
                found = True
            if not found:
                vat = "not found"
            article = {"description":description, "price":price, "vat":vat}
            articles.append(article)
        result = {"articles":articles}
        return result

def main():
    classifierPath = "../assets/classifier.pkl"
    analyser = DataAnalyser(classifierPath)

    jsonPath = "../assets/tx_111_2-40.webp.json"
    result = analyser.analyse(jsonPath)

    print("articles:")
    pprint(result["articles"])
    print()
    '''
    print("sums:")
    pprint(result["sums"])
    print()
    print("vats:")
    pprint(result["vats"])
    print()
    print("vatSums:")
    pprint(result["vatSums"])
    print()
    '''

if __name__ == "__main__":
    main()