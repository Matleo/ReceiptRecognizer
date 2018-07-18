import json
from PIL import Image, ImageDraw
from pprint import pprint
from random import randint

def printTxt(data):
    boxes = data["regions"]
    for box in boxes:
        lines = box["lines"]
        for line in lines:
            words = line["words"]
            for word in words:
                print(word["text"], end=" ")
            print()


#draws boxes for text recognized by OCR. Select selects which level of abstraction (elements, sections)
def showImage(path, data, select):
    im = Image.open(path)
    draw = ImageDraw.Draw(im)
    if(select=="elements"):
        for box in data["regions"]:
            for lines in box["lines"]:
                pprint(lines)
                bounding = lines["boundingBox"].split(",")

                x0 = bounding[0]
                y0 = bounding[1]
                width = bounding[2]
                heigth = bounding[3]
                coordinates = [int(x0), int(y0), int(x0) + int(width), int(y0) + int(heigth)]

                rndColor = (randint(0, 255), randint(0, 255), randint(0, 255))
                draw.rectangle(coordinates, outline=rndColor)
                print()
    elif (select=="sections"):
        pprint(data["regions"])
        for box in data["regions"]:
            bounding = box["boundingBox"].split(",")

            x0 = bounding[0]
            y0 = bounding[1]
            width = bounding[2]
            heigth = bounding[3]
            coordinates = [int(x0), int(y0), int(x0) + int(width), int(y0) + int(heigth)]

            rndColor = (randint(0, 255), randint(0, 255), randint(0, 255))
            draw.rectangle(coordinates, outline=rndColor)
            print()
    elif(select=="rows"):
        im = showImageRows(data,im)

    im.show()

def showImageRows(data, im):
    rows = []
    threshhold = 3 #pixels that y0 can differ to classify it as same row

    boxes = data["regions"]
    for box in boxes:
        for line in box["lines"]:
            bounding = line["boundingBox"].split(",")

            x0 = int(bounding[0])
            y0 = int(bounding[1])
            width = int(bounding[2])
            heigth = int(bounding[3])
            exists = False;

            #search in rows if the row alrdy exists -> need to append.
            for row in rows:
                rowY0 = row["coordinates"][1]
                if(abs(y0 - rowY0) <= threshhold):
                    #add text
                    for word in line["words"]:
                        if(x0>row["coordinates"][0]):#if new is on right side
                            row["words"] += word["text"] + " "
                        else:
                            row["words"] = word["text"] +" " + row["words"]


                    #extend coordinates:
                    row["coordinates"][0] = min(row["coordinates"][0],x0)#take the far most left
                    row["coordinates"][1] = min(row["coordinates"][1],y0)#is almost same anyways

                    left = min(row["coordinates"][0],x0)
                    right0 = max(row["coordinates"][0],x0)
                    #add the appropriate width to right
                    if(right0 == x0): #if current line is on the right side
                        right = x0 + width
                    else: # if current line is on left side. right side is the edge of found row
                        right = row["coordinates"][2]
                    row["coordinates"][2] = right #max(x0)+that.width

                    row["coordinates"][3] = max(row["coordinates"][3], y0 + heigth) #should be close to each other TODO: what if not

                    exists = True
            #else insert this row
            if not exists:
                coordinates = [x0, y0, x0 + width, y0 + heigth]
                words = ""
                for word in line["words"]:
                    words += word["text"]+" "
                newRow = {"coordinates":coordinates, "words":words}
                rows.append(newRow)

    #now draw rows:
    draw = ImageDraw.Draw(im)
    for row in rows:
        print(row)
        coordinates = row["coordinates"]
        rndColor = (randint(0, 255), randint(0, 255), randint(0, 255))
        draw.rectangle(coordinates, outline=rndColor)
    return im



path = "../data/clean-200-jpg"
with open(path+".json", encoding="utf-8") as f:
    data = json.load(f)
    showImage(path+".jpg", data, select="elements")
