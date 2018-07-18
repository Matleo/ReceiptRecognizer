import re
import pandas as pd
import json
from PIL import Image, ImageDraw
from random import randint
from pprint import pprint
import os

pd.set_option('expand_frame_repr', False)

#1)Read rows
def readRows(name, print):
    rows = []
    pathJSON = "./data/"+name+"-40.webp.json"
    with open(pathJSON, encoding="utf-8") as f:
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

            rows.append(row)
    if not print == "none":
        pathIMG = "./data/"+name+".jpg"
        im = Image.open(pathIMG)
        draw = ImageDraw.Draw(im)
        if print == "rows":
            for row in rows:
                boundingBox = row["boundingBox"]
                coordinates = [boundingBox[0],boundingBox[1],boundingBox[0]+boundingBox[2],boundingBox[1]+boundingBox[3]]
                rndColor = (randint(0, 255), randint(0, 255), randint(0, 255))
                draw.rectangle(coordinates, outline=rndColor)
        elif print == "elements":
            for row in rows:
                for word in row["words"]:
                    boundingBox = word["boundingBox"]
                    coordinates = [boundingBox[0],boundingBox[1],boundingBox[0]+boundingBox[2],boundingBox[1]+boundingBox[3]]
                    rndColor = (randint(0, 255), randint(0, 255), randint(0, 255))
                    draw.rectangle(coordinates, outline=rndColor)
        im.show()
    return rows


#2)RowToFeatures
def convertRowsToFeatureVectors(rows):
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
        newFeatureVector["minus"] = sum(c == "-" for c in row["plainText"])
        newFeatureVector["colons"] = sum((c == ":") | (c == ";") for c in row["plainText"])
        newFeatureVector["otherDigits"] = len(row["plainText"]) \
                                     - newFeatureVector["numbers"] - newFeatureVector["UpperCaseLetters"] \
                                     - newFeatureVector["LowerCaseLetters"] - spaces - newFeatureVector["dots"] \
                                     - newFeatureVector["minus"] - newFeatureVector["colons"]
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
        newFeatureVector["biggestWhitespaceLength"] = 0
        newFeatureVector["biggestWhitespaceX0"] = 0
        for whitespace in whitespaces:
            newFeatureVector["totalWhitespace"] += whitespace["length"]
            if whitespace["length"] > newFeatureVector["biggestWhitespaceLength"]:
                newFeatureVector["biggestWhitespaceLength"] = whitespace["length"]
                newFeatureVector["biggestWhitespaceX0"] = whitespace["x0"]
        newFeatureVector["whitespaceQuot"] = newFeatureVector["totalWhitespace"] / newFeatureVector["width"]

        newFeatureVector["rowNumber"] = i+1
        newFeatureVector["totalRows"] = len(rows)
        newFeatureVector["relativeRowPosition"] = newFeatureVector["rowNumber"] / newFeatureVector["totalRows"]




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

#3)makes df from dict and adds features (those that are relative to upper/lower row)
def makeDF(featureVectors):
    df = pd.DataFrame(featureVectors)
    #rearrange columns
    df = df[["plainText","x0","y0","width","height","wordCount",
             "LowerCaseLetters","UpperCaseLetters","numbers","dots","minus","colons","otherDigits",
             "floats","firstCharDigit","firstCharAB","lastCharAB","lastCharDigit",
             "totalWhitespace","whitespaceQuot","biggestWhitespaceLength","biggestWhitespaceX0",
             "sumExists","eurExists","rowNumber","totalRows","relativeRowPosition"]]
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

    return df


def get_df(name , print="none"):
    rows = readRows(name, print)
    featureVectors = convertRowsToFeatureVectors(rows)
    df_nolabel = makeDF(featureVectors)
    return df_nolabel

def append_label(df, name):
    label_df = pd.read_pickle("./data/"+name+"_label.pkl")
    df["rowClass"] = label_df["rowClass"]
    return df


def main(folder):
    names = []
    for file in os.listdir(folder):
        if file.endswith(".jpg"):
            names.append(file.split(".jpg")[0])
    for i in range(0,len(names)):
        name = names[i]
        df = get_df(name, "none")
        df = append_label(df, name)

        picklePath = folder + "/" + name + "_df.pkl"
        df.to_pickle(picklePath)  # save labeled df

        progress = "("+str(i+1)+"|"+str(len(names))+")"
        print(progress+": "+name)


if __name__ =="__main__":
    main("./data")
