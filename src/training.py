import os
import pandas as pd
import random
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
import numpy as np
from src.utility import plot_confusion_matrix
import matplotlib.pyplot as plt
import pickle


def readDFs(folder):
    dfs = []
    for file in os.listdir(folder):
        if file.endswith(".jpg"):
            name = file.split(".jpg")[0]
            df = pd.read_pickle(folder+"/"+name+"_df.pkl")
            dfs.append(df)
    return dfs

def splitTrainTest(test_amount, folder):
    random.seed(1234)

    # split list into test and train lists
    dfs = readDFs(folder)
    test_threshhold = int(test_amount * (len(dfs) - 1))
    random.shuffle(dfs)
    test_df_list = dfs[:test_threshhold]
    train_df_list = dfs[test_threshhold:]

    # unfold list into one df (for training and testing each)
    test_df = test_df_list[0]
    for i in range(1, len(test_df_list)):
        df = test_df_list[i]
        test_df = test_df.append(df, ignore_index=True)

    train_df = train_df_list[0]
    for i in range(1, len(train_df_list)):
        df = train_df_list[i]
        train_df = train_df.append(df, ignore_index=True)
    return train_df,test_df

def train(df,printImportance=False):
    labels = df["rowClass"]
    features = df.loc[:,df.columns != "rowClass"]
    forest = RandomForestClassifier(random_state=1234, class_weight="balanced_subsample")
    forest.fit(features,labels)

    if printImportance:
        # Print the feature ranking
        feature_importance = forest.feature_importances_
        indices = np.argsort(feature_importance)[::-1]
        feature_names = features.columns.values
        print("------------------------------------------------------------")
        print("\tFeature ranking:")
        for f in range(features.shape[1]):
            print("%d.feature: %s (%f)" % (f + 1, feature_names[int(indices[f])], feature_importance[indices[f]]))
        print("------------------------------------------------------------")

    return forest

def test(df, forest, plainText, jsonPath, printWrongClassifications=False, plotConfustionMatrix=False):
    labels = df["rowClass"]
    features = df.loc[:, df.columns != "rowClass"]
    label_predictions = forest.predict(features)

    #model evaluation
    accuracy = accuracy_score(labels, label_predictions)
    print("Accuracy: "+str(accuracy))
    class_names = ["Irrelevant", "Article", "Sum", "Vat", "Vat-Sum"]
    print("------------------------------------------------------------")

    #find wrong classifications
    if printWrongClassifications:
        print("Wrong Classifications:")
        for i in range(0, len(labels)):
            if labels[i] != label_predictions[i]:
                print()
                print("plainText:\t"+plainText[i])
                print("jsonPath:\t"+jsonPath[i])
                print("label:\t"+str(labels[i]))
                print("prediction:\t"+str(label_predictions[i]))
        print("------------------------------------------------------------")

    if plotConfustionMatrix:
        cnf_matrix = confusion_matrix(labels, label_predictions)
        plt.figure()
        plot_confusion_matrix(cnf_matrix, classes=class_names, normalize=False,
                              title='Confusion matrix, without normalization')
        plt.show()


def train_test(folder, test_amount, dropFeatures, printImportance, printWrongClassifications, plotConfustionMatrix):
    print("(1|5): Splitting Test/Train")
    train_df, test_df = splitTrainTest(test_amount, folder)

    print("(2|5): Dropping some Features")
    test_plainText = test_df["plainText"]
    test_jsonPath = test_df["jsonPath"]
    dropFeatures.append("plainText")
    dropFeatures.append("jsonPath")
    # drop some features:
    train_df = train_df.drop(columns=dropFeatures)
    test_df = test_df.drop(columns=dropFeatures)

    print("(3|5): Training the forest")
    forest = train(train_df, printImportance)

    print("(4|5): Evaluating model against test set")
    test(test_df, forest, test_plainText, test_jsonPath, printWrongClassifications, plotConfustionMatrix)
    print("(5|5): Done!")

def train_full(folder, dropFeatures):
    dfs = readDFs(folder)
    #unfold
    full_df = dfs[0]
    for i in range(1, len(dfs)):
        df = dfs[i]
        full_df = full_df.append(df, ignore_index=True)
    dropFeatures.append("plainText")
    dropFeatures.append("jsonPath")
    full_df = full_df.drop(columns=dropFeatures)

    classifier = train(full_df)
    return classifier



def main(folder):
    printImportance = True
    printWrongClassifications = True
    plotConfustionMatrix = True
    test_amount = 0.2

    #, "maxWhiteSpaceX0Matches", "maxWhiteSpaceLengthMatches", "significantWhitespaces"
    dropFeatures = []

    train_test(folder, test_amount, dropFeatures,
               printImportance, printWrongClassifications, plotConfustionMatrix)

    classifier = train_full(folder, dropFeatures)
    with open(folder+"/../müllerClassifier.pkl", "wb") as outfile:
        pickle.dump(classifier, outfile)

if __name__ == "__main__":
    folder = "../assets/müllerData"
    main(folder)