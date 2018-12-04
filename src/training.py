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


def train(df):
    labels = df["rowClass"]
    features = df.loc[:,df.columns != "rowClass"]
    forest = RandomForestClassifier(random_state=1234, class_weight="balanced_subsample")
    forest.fit(features,labels)
    return forest


def test(df, forest, plainText, jsonPath):
    labels = df["rowClass"]
    features = df.loc[:, df.columns != "rowClass"]
    label_predictions = forest.predict(features)

    #model evaluation
    accuracy = accuracy_score(labels, label_predictions)

    #find wrong classifications
    wrongClassifications = []
    for i in range(0, len(labels)):
        if labels[i] != label_predictions[i]:
            wrongClass = {"plainText":plainText[i], "jsonPath":jsonPath[i], "label": labels[i], "prediction": label_predictions[i]}
            wrongClassifications.append(wrongClass)

    cnf_matrix = confusion_matrix(labels, label_predictions)

    return [accuracy, wrongClassifications, cnf_matrix]


def train_full_save(folders, dropFeatures):
    print("Training with full set...")
    dfs = []
    for folder in folders:
        dfs.extend(readDFs(folder))
    #unfold
    full_df = dfs[0]
    for i in range(1, len(dfs)):
        df = dfs[i]
        full_df = full_df.append(df, ignore_index=True)
    dropFeatures.append("plainText")
    dropFeatures.append("jsonPath")
    full_df = full_df.drop(columns=dropFeatures)

    classifier = train(full_df)
    classifierPickle = "../classifier.pkl"
    classifierPickle = os.path.abspath(classifierPickle)
    with open(classifierPickle,"wb") as outfile:
        pickle.dump(classifier, outfile)
    print("Pickled classifier to: "+classifierPickle)

    return classifier


def cross_validate(k, folders, dropFeatures):
    dfs = []
    for folder in folders:
        dfs.extend(readDFs(folder))
    random.seed(1234)
    random.shuffle(dfs)

    n_test = int((1 / k) * (len(dfs)-1))
    start_index = 0
    results = []
    feature_importance_dict = {}
    #k-fold-cv:
    for i in range(0, k):
        print("("+str(i+1)+"|"+str(k)+")")
        left = start_index
        right = start_index+n_test-1
        # take all left overs for test set on last iteration
        if i == k-1:
            right = len(dfs)-1

        test_df_list = dfs[left:right]
        train_df_list = [dfs[i] for i in range(0,len(dfs)) if i not in range(left,right)]#all dfs that are not in [left,right]
        # unfold list into one df (for training and testing each)
        test_df = test_df_list[0]
        for i in range(1, len(test_df_list)):
            df = test_df_list[i]
            test_df = test_df.append(df, ignore_index=True)

        train_df = train_df_list[0]
        for i in range(1, len(train_df_list)):
            df = train_df_list[i]
            train_df = train_df.append(df, ignore_index=True)


        test_plainText = test_df["plainText"]
        test_jsonPath = test_df["jsonPath"]
        # drop some features:
        dropFeatures.append("plainText")
        dropFeatures.append("jsonPath")
        train_df = train_df.drop(columns=dropFeatures)
        test_df = test_df.drop(columns=dropFeatures)

        forest = train(train_df)

        # save feature_importances
        features = test_df.loc[:,test_df.columns != "rowClass"]
        feature_names = features.columns.values
        feature_importance = forest.feature_importances_
        for i in range(features.shape[1]):
            if feature_names[i] in feature_importance_dict:
                feature_importance_dict[feature_names[i]].append(feature_importance[i])
            else:
                feature_importance_dict[feature_names[i]] = [feature_importance[i]]

        result = test(test_df, forest, test_plainText, test_jsonPath)
        results.append(result)

        start_index += n_test

    return results, feature_importance_dict


def analyseResults(results, feature_importance_dict, printImportance, printWrongClassifications, plotConfustionMatrix):
    accuracies = []
    wrongClassifications = []
    confusion_matrices = []
    for result in results:
        accuracies.append(result[0])
        for wrongClass in result[1]:
            wrongClassifications.append(wrongClass)
        confusion_matrices.append(result[2])

    print("Accuracies: " + ''.join(str(round(acc,4))+", " for acc in accuracies))
    avgAccuracy = sum(accuracies) / float(len(accuracies))
    print("AvgAccuracy: " + str(round(avgAccuracy,4)))

    if printImportance:
        feature_importances = {}
        for key,value in feature_importance_dict.items():
            avg = sum(value) / float(len(value))
            feature_importances[key] = avg

        feature_importances_sorted = sorted(feature_importances, key=feature_importances.get, reverse=True) #only names
        print("------------------------------------------------------")
        print("Average Feature importances:")
        for i in range(len(feature_importances_sorted)):
            feature = feature_importances_sorted[i]
            print(str(i) + ". " + feature + " (" + str(round(feature_importances[feature],4)) + ")")

    if printWrongClassifications:
        print("------------------------------------------------------")
        print("Wrong Classifications:")
        for wc in wrongClassifications:
            print(wc)

    if plotConfustionMatrix:
        print("------------------------------------------------------")
        cnf_matrix = confusion_matrices[0]
        for i in range(1,len(confusion_matrices)):
            cnf_matrix = np.add(cnf_matrix, confusion_matrices[i])
        #cnf_matrix = np.divide(cnf_matrix, len(confusion_matrices)).astype(int)
        class_names = ["Irrelevant", "Article", "Sum", "Vat", "Vat-Sum"]
        plt.figure()
        plot_confusion_matrix(cnf_matrix, classes=class_names, normalize=False,
                              title='Total confusion matrix over k-fold-cv')
        plt.show()


def train_test_analyse(folders, options, dropFeatures):
    print("Starting cross validation")
    results, feature_importances = cross_validate(5, folders, dropFeatures)
    print("Done with cross validation")

    analyseResults(results, feature_importances, options[0], options[1], options[2])



if __name__ == "__main__":
    printImportance = True
    printWrongClassifications = True
    plotConfustionMatrix = True
    options = [printImportance, printWrongClassifications, plotConfustionMatrix]

    dropFeatures = []
    #dropFeatures.extend(["LowerCaseLetters", "wordCount", "width"])
    #dropFeatures.extend(["lastCharDigit", "height", "significantWhitespaces", "whitespaceQuot"])
    #dropFeatures.extend(
    #    ["biggestWhitespaceX0", "dots", "lastCharAB", "x0", "eurExists", "distanceBot", "firstCharDigit", "firstCharAB",
    #     "otherDigits", "colons", "relativeRowPosition", "y0", "belegExists", "distanceTop", "maxWhiteSpaceX0Matches",
    #     "lastCharAWBW", "maxWhiteSpaceLengthMatches"])

    müller = "../assets/müllerData"
    edeka = "../assets/edekaData"
    folders = [müller]

    train_test_analyse(folders,options, dropFeatures)
    #classifier = train_full_save(folders, dropFeatures)
