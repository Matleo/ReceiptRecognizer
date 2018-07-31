import matplotlib.pyplot as plt
import numpy as np
import itertools
from preprocessing import readRows
from PIL import Image, ImageDraw
from random import randint
import os
import service

np.set_printoptions(precision=2)


def plot_confusion_matrix(cm, classes,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=plt.cm.Blues):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]


    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')

def plotImgWithBox(jsonPath, imgPath, scope):
    rows = readRows(jsonPath)

    im = Image.open(imgPath)
    draw = ImageDraw.Draw(im)
    if scope == "rows":
        for row in rows:
            boundingBox = row["boundingBox"]
            coordinates = [boundingBox[0], boundingBox[1], boundingBox[0] + boundingBox[2],
                           boundingBox[1] + boundingBox[3]]
            rndColor = (randint(0, 255), randint(0, 255), randint(0, 255))
            draw.rectangle(coordinates, outline=rndColor)
    elif scope == "elements":
        for row in rows:
            for word in row["words"]:
                boundingBox = word["boundingBox"]
                coordinates = [boundingBox[0], boundingBox[1], boundingBox[0] + boundingBox[2],
                               boundingBox[1] + boundingBox[3]]
                rndColor = (randint(0, 255), randint(0, 255), randint(0, 255))
                draw.rectangle(coordinates, outline=rndColor)
    im.show()

def countVatClasses(folder, limit):
    names = []
    for file in os.listdir(folder):
        if file.endswith(".jpg"):
            name = file.split(".jpg")[0]
            number = name.split("_")[1]
            if int(number) <= limit:
                names.append(name)
    countA = 0
    countB = 0
    for name in names:
        print(name)
        jsonPath = folder+"/"+name+"-40.webp.json"
        result = service.main(jsonPath)
        articles = result["articles"]
        for article in articles:
            vat = article["vat"]
            if vat.lower() == "a":
                countA += 1
            if vat.lower() == "b":
                countB += 1
    print("------------------------")
    print("countA: " + str(countA))
    print("countB: " + str(countB))


if __name__ =="__main__":
    '''
    nummer = "244"
    name = "tx_"+nummer+"_2"
    folder = "edekaData"
    jsonPath = "../assets/"+folder+"/"+name+"-40.webp.json"
    imgPath = "../assets/"+folder+"/" + name + ".jpg"
    plotImgWithBox(jsonPath, imgPath, scope="elements")
    '''
    folder = "../assets/edekaData"
    upto_limit = 270
    countVatClasses(folder, upto_limit)