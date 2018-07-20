import pandas
import pickle
import json
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
        df = get_df(jsonPath)
        plainText = df["plainText"]
        df = df.drop(columns=["minus", "totalRows", "rowNumber", "plainText"])
        label_predictions = self.classifier.predict(df)

        articles = []
        sums = []
        vats = []
        vatSums = []
        for i in range(0,len(label_predictions)):
            label = label_predictions[i]
            if label == 1:
                articles.append(plainText[i])
            if label == 2:
                sums.append(plainText[i])
            if label == 3:
                vats.append(plainText[i])
            if label == 4:
                vatSums.append(plainText[i])
        result = {"articles":articles, "sums":sums, "vats":vats, "vatSums":vatSums}
        return result


def main():
    classifierPath = "../assets/müllerClassifier.pkl"
    analyser = DataAnalyser(classifierPath)

    jsonPath = "../assets/tx_2_2-40.webp.json"
    result = analyser.analyse(jsonPath)

    print("articles:")
    pprint(result["articles"])
    print()
    print("sums:")
    pprint(result["sums"])
    print()
    print("vats:")
    pprint(result["vats"])
    print()
    print("vatSums:")
    pprint(result["vatSums"])
    print()

if __name__ == "__main__":
    main()