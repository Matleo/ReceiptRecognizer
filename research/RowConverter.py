import json

class RowConverter:
        def __init__(self, threshhold):
            self.threshhold = threshhold# pixels that y0 can differ to classify it as same row

        def convert(self, path):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                rows = []

                boxes = data["regions"]
                for box in boxes:
                    for line in box["lines"]:
                        bounding = line["boundingBox"].split(",")
                        x0 = int(bounding[0])
                        y0 = int(bounding[1])
                        width = int(bounding[2])
                        height = int(bounding[3])

                        exists = False

                        # search in rows if the row alrdy exists -> need to append.
                        for row in rows:
                            rowY0 = row["coordinates"][1]
                            if abs(y0 - rowY0) <= self.threshhold:
                                self.__mergeRow(row, line)
                                exists = True
                                break
                        # else insert this row
                        if not exists:
                            coordinates = [x0, y0, x0 + width, y0 + height]
                            appendCount = 0  # Count how many times a section got added to the line
                            sectionMargin = 0  # Count the width of the white spaces between the appended sections
                            words = ""
                            for word in line["words"]:
                                words += word["text"] + " "
                            newRow = {"coordinates": coordinates, "plainText": words, "appendCount": appendCount,
                                      "sectionMargin": sectionMargin, "words": line["words"]}
                            rows.append(newRow)
                return rows

        def __mergeRow(self, row, newRow):
            row["appendCount"] += 1
            bounding = newRow["boundingBox"].split(",")
            x0 = int(bounding[0])
            y0 = int(bounding[1])
            width = int(bounding[2])
            height = int(bounding[3])

            # merge text:
            # append new words (unordered)
            for word in newRow["words"]:
                row["words"].append(word)
            # sort words by x0
            wordToX0 = {}
            for word in row["words"]:
                wordToX0[word["text"]] = int(word["boundingBox"].split(",")[0])  # dict of word->x0
            sortedWordToX0 = sorted(wordToX0.items(), key=lambda x: x[1])  # list of tupels word->x0, ordered by x0
            sortedText = ""
            for tup in sortedWordToX0:
                sortedText += tup[0] + " "
            row["plainText"] = sortedText

            # add width distance between sections to sectionMargin
            if (x0 > row["coordinates"][0]):  # if new line is on the right side
                margin = x0 - row["coordinates"][2]  # new x0 - old x1
            else:
                margin = row["coordinates"][0] - (x0 + width)  # old x0 - (new x0+new width)
            row["sectionMargin"] += margin

            # extend coordinates:
            row["coordinates"][0] = min(row["coordinates"][0], x0)  # take the far most left
            row["coordinates"][1] = min(row["coordinates"][1], y0)  # is almost same anyways
            # add the appropriate width to right
            if (x0 > row["coordinates"][0]):  # if current line is on the right side
                right = x0 + width
            else:  # if current line is on left side. right side is the edge of found row
                right = row["coordinates"][2]
            row["coordinates"][2] = right  # max(x0)+that.width
            row["coordinates"][3] = max(row["coordinates"][3], y0 + height)  # should be close to each other TODO: what if not



if(__name__=="__main__"):
    from PIL import Image, ImageDraw
    from random import randint

    #print image with boxes
    name="clean-200-jpg"
    path = "../data/"+name

    converter = RowConverter(3)
    rows = converter.convert(path + ".json")

    im = Image.open(path+".jpg")
    draw = ImageDraw.Draw(im)
    for row in rows:
        print(row)
        coordinates = row["coordinates"]
        rndColor = (randint(0, 255), randint(0, 255), randint(0, 255))
        draw.rectangle(coordinates, outline=rndColor)
    im.show()