import re
import pandas as pd
import json
from pprint import pprint
import os

pd.set_option('expand_frame_repr', False)

#1)Read rows
def readRows(jsonPath):
    rows = []
    with open(jsonPath, encoding="utf-8") as f:
        data = json.load(f)
        for line in data:
            row = {}
            row["plainText"] = ""
            row["words"] = []
            for word in line:
                row["plainText"] += word["Text"]+" "
                boundingBox = word["BoundingBox"].split(",")
                word_x0 = abs(int(boundingBox[0]))
                word_width = abs(int(boundingBox[2]))
                word_y0 = abs(int(boundingBox[1]))
                word_height = abs(int(boundingBox[3]))
                wordBoundingBox = [word_x0,word_y0,word_width,word_height]
                row["words"].append({"boundingBox":wordBoundingBox, "text":word["Text"]})

            x0s = []
            y0s = []
            #heights =[]
            x1s = []
            y1s = []
            for word in row["words"]:
                x0s.append(word["boundingBox"][0])
                y0s.append(word["boundingBox"][1])
                #heights.append(word["boundingBox"][3])
                x1s.append(word["boundingBox"][0]+word["boundingBox"][2])
                y1s.append(word["boundingBox"][1]+word["boundingBox"][3])
            x0 = min(x0s)
            y0 = min(y0s)
            maxX1 = max(x1s)
            width = maxX1 - x0
            #height = max(heights)
            maxY1 = max(y1s)
            height = maxY1 - y0
            row["boundingBox"] = [x0,y0,width,height]
            row["jsonPath"] = jsonPath

            rows.append(row)
    return rows


#2)RowToFeatures
def convertRowsToFeatureVectors(rows):
    #significantWhiteSpace = 3 * avg width of first n found single character boundingBox
    significantWhiteSpaceWidth = 3 * findSWSW(rows, 5)

    featureVectors=[]
    for i in range(0,len(rows)):
        row = rows[i]
        newFeatureVector = {}
        newFeatureVector["plainText"] = row["plainText"]

        boundingBox = row["boundingBox"]
        newFeatureVector["x0"] = boundingBox[0]
        newFeatureVector["y0"] = boundingBox[1]
        newFeatureVector["width"] = boundingBox[2]
        newFeatureVector["height"] = boundingBox[3]

        newFeatureVector["wordCount"] = len(row["words"])

        newFeatureVector["numbers"] = sum(c.isdigit() for c in row["plainText"])
        newFeatureVector["UpperCaseLetters"] = sum(c.isalpha() & c.isupper() for c in row["plainText"])
        newFeatureVector["LowerCaseLetters"] = sum(c.isalpha() & c.islower() for c in row["plainText"])
        spaces = sum(c.isspace() for c in row["plainText"]) #dont add to features, since it is redundant to wordCount
        newFeatureVector["dots"] = sum((c == ",") | (c == ".") for c in row["plainText"])
        newFeatureVector["colons"] = sum((c == ":") | (c == ";") for c in row["plainText"])
        newFeatureVector["otherDigits"] = len(row["plainText"]) \
                                     - newFeatureVector["numbers"] - newFeatureVector["UpperCaseLetters"] \
                                     - newFeatureVector["LowerCaseLetters"] - spaces - newFeatureVector["dots"] \
                                     - newFeatureVector["colons"]
        newFeatureVector["floats"] = countFloats(row["plainText"])

        newFeatureVector["eurExists"] = euroExists(row["plainText"])
        newFeatureVector["sumExists"] = sumExists(row["plainText"])

        newFeatureVector["firstCharDigit"] = firstCharDigit(row["plainText"])
        newFeatureVector["firstCharAB"] = firstCharAB(row["plainText"])
        newFeatureVector["lastCharAB"] = lastCharAB(row["plainText"])
        newFeatureVector["lastCharDigit"] = lastCharDigit(row["plainText"])

        #add quotient whitespace/width
        whitespaces = calculateWhitespace(row)
        newFeatureVector["totalWhitespace"] = 0
        newFeatureVector["significantWhitespaces"] = 0
        newFeatureVector["biggestWhitespaceLength"] = 0
        newFeatureVector["biggestWhitespaceX0"] = 0
        for whitespace in whitespaces:
            newFeatureVector["totalWhitespace"] += whitespace["length"]
            #look for max
            if whitespace["length"] > newFeatureVector["biggestWhitespaceLength"]:
                newFeatureVector["biggestWhitespaceLength"] = whitespace["length"]
                newFeatureVector["biggestWhitespaceX0"] = whitespace["x0"]
            #check if significant
            if whitespace["length"] > significantWhiteSpaceWidth:
                newFeatureVector["significantWhitespaces"] += 1
        newFeatureVector["whitespaceQuot"] = newFeatureVector["totalWhitespace"] / newFeatureVector["width"]

        rowNumber = i+1
        totalRows = len(rows)
        newFeatureVector["relativeRowPosition"] = rowNumber / totalRows

        newFeatureVector["jsonPath"] = row["jsonPath"]

        featureVectors.append(newFeatureVector)
    return featureVectors

def countFloats(text):
    regex = "(\d+ \. \d{1,2})|(\d+ , \d{1,2})"
    matches = re.findall(regex, text)
    return len(matches)
def euroExists(text):
    val = re.findall("euro|€|eur>", text.lower())
    if len(val) > 0: return True
    else: return False
def sumExists(text):
    val = re.findall("summe|sum|total>", text.lower())
    if len(val) > 0: return True
    else: return False
def firstCharDigit(text):
    if (text[0] == "I") | (text[0].isdigit()): return True
    else: return False
def firstCharAB(text):
    c = text[0].lower()
    if (c == "a") | (c == "b") | (c == "0"): return True
    else: return False
def lastCharAB(text):
    c = text[len(text)-2].lower()
    if (c == "a") | (c == "b") | (c == "0"): return True
    else: return False
def lastCharDigit(text):
    c = text[len(text) - 2]
    if (c == "I") | (c.isdigit()): return True
    else: return False
def calculateWhitespace(row):
    words = row["words"]
    whitespaces = []
    for i in range(0,len(row["words"])-1):
        x1 = words[i]["boundingBox"][0] + words[i]["boundingBox"][2]
        nextX0 = words[i+1]["boundingBox"][0]
        length = nextX0 - x1
        whitespace = {"x0" : x1 , "length" :length} #whitespace x0 = left word x1
        whitespaces.append(whitespace)
    return whitespaces
def findSWSW(rows, findAvgValues):
    widths = []
    #skip first row:
    for i in range(1, len(rows)):
        row = rows[i]
        for word in row["words"]:
            if len(word["text"]) == 1:
                width = word["boundingBox"][2]
                widths.append(int(width))
                if len(widths) == findAvgValues:
                    return sum(widths) / float(len(widths))
    #this code is only reached, if couldnt find n one-char-words in the rows
    if len(widths) == 0:
        return 10
    else:
        return sum(widths) / float(len(widths))


#3)makes df from dict and adds features (those that are relative to upper/lower row)
def makeDF(featureVectors):
    df = pd.DataFrame(featureVectors)
    #rearrange columns
    df = df[["plainText", "jsonPath","x0","y0","width","height","wordCount",
             "LowerCaseLetters","UpperCaseLetters","numbers","dots","colons","otherDigits",
             "floats","firstCharDigit","firstCharAB","lastCharAB","lastCharDigit",
             "totalWhitespace","whitespaceQuot","biggestWhitespaceLength","biggestWhitespaceX0",
             "significantWhitespaces","sumExists","eurExists","relativeRowPosition"]]
    #sort by y0 and renew indexes (probably redundant)
    df = df.sort_values(by=['y0']).reset_index(drop=True)

    # add distance to rows on top/bottom
    distancesTop = []
    distancesBot = []
    for index, row in df.iterrows():
        if index == 0:
            distanceTop = 0
            nextY0 = df.iloc[index + 1]["y0"]
            distanceBot = nextY0 - (row["y0"] + row["height"])
        elif index == (len(df.index)-1):
            previousY1 = (df.iloc[index - 1]["y0"] + df.iloc[index - 1]["height"])
            distanceTop = row["y0"] - previousY1
            distanceBot = 0
        else:
            previousY1 = (df.iloc[index - 1]["y0"] + df.iloc[index - 1]["height"])
            distanceTop = row["y0"] - previousY1

            nextY0 = df.iloc[index + 1]["y0"]
            distanceBot = nextY0 - (row["y0"] + row["height"])

        distancesTop.append(distanceTop)
        distancesBot.append(distanceBot)
    df["distanceTop"] = distancesTop
    df["distanceBot"] = distancesBot


    #add maxWhiteSpaceLength/X0 matches top/bot
    maxWhiteSpaceLengthMatches = [] #counts if row on top/bot have same maxWhiteSpaceLength
    maxWhiteSpaceX0Matches = []
    for index, row in df.iterrows():
        length = row["biggestWhitespaceLength"]
        x0 = row["biggestWhitespaceX0"]
        if index == 0:#first row
            nextLength = df.iloc[index + 1]["biggestWhitespaceLength"]
            nextX0 = df.iloc[index + 1]["biggestWhitespaceX0"]
            if abs(nextLength-length) < 5:
                lengthMatches = 1
            else:
                lengthMatches = 0
            if abs(nextX0-x0) < 5:
                x0Matches = 1
            else:
                x0Matches = 0
        elif index == (len(df.index)-1):#last row
            previousLength = df.iloc[index - 1]["biggestWhitespaceLength"]
            previousX0 = df.iloc[index - 1]["biggestWhitespaceX0"]
            if abs(previousLength - length) < 5:
                lengthMatches = 1
            else:
                lengthMatches = 0
            if abs(previousX0 - x0) < 5:
                x0Matches = 1
            else:
                x0Matches = 0
        else:
            previousLength = df.iloc[index - 1]["biggestWhitespaceLength"]
            previousX0 = df.iloc[index - 1]["biggestWhitespaceX0"]
            if abs(previousLength - length) < 5:
                lengthMatches = 1
            else:
                lengthMatches = 0
            if abs(previousX0 - x0) < 5:
                x0Matches = 1
            else:
                x0Matches = 0

            nextLength = df.iloc[index + 1]["biggestWhitespaceLength"]
            nextX0 = df.iloc[index + 1]["biggestWhitespaceX0"]
            if abs(nextLength - length) < 5:
                lengthMatches += 1
            if abs(nextX0 - x0) < 5:
                x0Matches += 1
        maxWhiteSpaceLengthMatches.append(lengthMatches)
        maxWhiteSpaceX0Matches.append(x0Matches)

    df["maxWhiteSpaceLengthMatches"] = maxWhiteSpaceLengthMatches
    df["maxWhiteSpaceX0Matches"] = maxWhiteSpaceX0Matches


    return df


def get_df(jsonPath):
    rows = readRows(jsonPath)
    featureVectors = convertRowsToFeatureVectors(rows)
    df_nolabel = makeDF(featureVectors)
    return df_nolabel

def append_label(df, labelPath):
    label_df = pd.read_pickle(labelPath)
    df["rowClass"] = label_df["rowClass"]
    return df


def main(folder):
    names = []
    for file in os.listdir(folder):
        if file.endswith(".jpg"):
            names.append(file.split(".jpg")[0])
    for i in range(0,len(names)):
        name = names[i]
        jsonPath = folder + "/" + name + "-40.webp.json"
        df = get_df(jsonPath)
        labelPath = folder + "/" + name + "_label.pkl"
        df = append_label(df, labelPath)

        picklePath = folder + "/" + name + "_df.pkl"
        df.to_pickle(picklePath)  # save labeled df

        progress = "("+str(i+1)+"|"+str(len(names))+")"
        print(progress+": "+name)


if __name__ =="__main__":
    main("../assets/müllerData")
