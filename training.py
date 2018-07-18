import os
import pandas as pd
import random
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import numpy as np

def readDFs(folder):
    dfs = []
    for file in os.listdir(folder):
        if file.endswith(".jpg"):
            name = file.split(".jpg")[0]
            df = pd.read_pickle(folder+"/"+name+"_df.pkl")
            dfs.append(df)
    return dfs

def splitTrainTest(test_amount):
    random.seed(123456)

    # split list into test and train lists
    dfs = readDFs("./data")
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
    forest = RandomForestClassifier(random_state=1234)
    print("Training Randomforest...",end="")
    forest.fit(features,labels)
    print("done")

    if printImportance:
        # Print the feature ranking
        feature_importance = forest.feature_importances_
        indices = np.argsort(feature_importance)[::-1]
        feature_names = features.columns.values
        print("------------------------------------------------------------")
        print("Feature ranking:")
        for f in range(features.shape[1]):
            print("%d. feature %s (%f)" % (f + 1, feature_names[int(indices[f])], feature_importance[indices[f]]))
        print("------------------------------------------------------------")

    return forest

def test(df, forest, plainText):
    labels = df["rowClass"]
    features = df.loc[:, df.columns != "rowClass"]
    label_predictions = forest.predict(features)

    #model evaluation
    accuracy = accuracy_score(labels, label_predictions)
    print("Accuracy: "+str(accuracy))
    print(classification_report(labels, label_predictions,
                                target_names=["Irrelevant", "Article", "Sum", "Vat", "Vat-Sum"]))
    print("------------------------------------------------------------")

    #find wrong classifications
    print("Wrong Classifications:")
    for i in range(0,len(labels)):
        if labels[i] != label_predictions[i]:
            print()
            print("plainText:\t"+plainText[i])
            print("label:\t"+str(labels[i]))
            print("prediction:\t"+str(label_predictions[i]))
    print("------------------------------------------------------------")



def main():
    test_amount = 0.2
    train_df, test_df = splitTrainTest(test_amount)
    #TODO: replace char values with one-hot-encoded (pd.get_dummies or sklearn.preprocessing.OneHotEncoder)
    train_df = train_df.drop(columns=["firstChar","lastChar"])
    test_df = test_df.drop(columns=["firstChar","lastChar"])

    #drop unnecessary features:
    dropFeatures = ["minus","totalRows","rowNumber"]
    train_df = train_df.drop(columns=dropFeatures)
    test_df = test_df.drop(columns=dropFeatures)

    #drop plainText
    train_df = train_df.drop(columns=["plainText"])
    test_plainText = test_df["plainText"]
    test_df = test_df.drop(columns=["plainText"])

    forest = train(train_df, True)

    test(test_df,forest, test_plainText)


if __name__ == "__main__":
    main()