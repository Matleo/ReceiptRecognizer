import sys
import os
from PyQt5.QtWidgets import QApplication, QDesktopWidget, QMainWindow, QAction, qApp, QMenu, QLabel, QScrollArea, QFileDialog
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QPen, QColor, QBrush, QTransform
from PyQt5.QtCore import Qt
from src.preprocessing import get_df
from random import randint
from PIL import Image
import shutil

class LabelWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.folder = str(QFileDialog.getExistingDirectory(self, "Select Directory","../assets"))
        self.imgNames = self.searchImgNames(self.folder)#the names of jpg files
        self.imgCount = -1 #keep track on which file we are
        self.nextImg()

        self.minMouseY = None
        self.maxMouseY = 0

        self.initUI()

    def initUI(self):

        self.statusBar().showMessage('Ready')

        self.initMenu()

        self.setWindowTitle('Labeler')
        self.setWindowIcon(QIcon('../assets/img/label.png'))
        self.resize(self.pixmap.width()+20, QDesktopWidget().availableGeometry().height()-30)

        self.center()

        self.show()

    def center(self):
        frame = self.frameGeometry()
        desktopCenter = QDesktopWidget().availableGeometry().center()
        frame.moveCenter(desktopCenter)
        diff = QDesktopWidget().availableGeometry().height() - self.frameSize().height()
        frame.moveTop(-diff/8) #Hack to make fit to top side
        self.move(frame.topLeft())

    def initMenu(self):
        saveAct = QAction(QIcon('../assets/img/save.png'), 'Save', self)
        saveAct.setShortcut('Ctrl+S')
        saveAct.setStatusTip('Save Classes and also opens next image')
        saveAct.triggered.connect(self.saveClasses)
        self.toolbar = self.addToolBar('Save')
        self.toolbar.addAction(saveAct)

        refreshAct = QAction(QIcon('../assets/img/refresh.jpg'), 'Refresh', self)
        refreshAct.setShortcut('Ctrl+R')
        refreshAct.setStatusTip('Refresh picture')
        refreshAct.triggered.connect(self.refreshPic)
        self.toolbar = self.addToolBar('Refresh')
        self.toolbar.addAction(refreshAct)

        rotateAct = QAction(QIcon('../assets/img/rotate.png'), 'Rotate', self)
        rotateAct.setShortcut('Ctrl+T')
        rotateAct.setStatusTip('Rotate picture 180°')
        rotateAct.triggered.connect(self.rotatePic)
        self.toolbar = self.addToolBar('Rotate')
        self.toolbar.addAction(rotateAct)

        removeAct = QAction(QIcon('../assets/img/remove.png'), 'Remove', self)
        removeAct.setShortcut('Ctrl+D')
        removeAct.setStatusTip('Moves image to garbage folder')
        removeAct.triggered.connect(self.removeImg)
        self.toolbar = self.addToolBar('Remove')
        self.toolbar.addAction(removeAct)

        exitAct = QAction(QIcon('../assets/img/exit.png'), 'Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(qApp.quit)
        self.toolbar = self.addToolBar('Exit')
        self.toolbar.addAction(exitAct)


    def contextMenuEvent(self, event):
        cmenu = QMenu(self)

        vat = cmenu.addAction("vat")
        vatSum = cmenu.addAction("vatSum")
        ignore = cmenu.addAction("ignore")
        action = cmenu.exec_(self.mapToGlobal(event.pos()))

        if action == vat:
            self.selectRow(event, "vat")
        elif action == vatSum:
            self.selectRow(event, "vatSum")
        elif action == ignore:
            self.selectRow(event, "ignore")

    def setImageWidget(self):
        #draw rectangles on img
        painterInstance = QPainter(self.pixmap)
        i = 0
        while i < len(self.df.values):
            row = self.df.loc[i]
            rndColor1 = randint(0, 255)
            rndColor2 = randint(0, 255)
            rndColor3 = randint(0, 255)
            pen = QPen(QColor(rndColor1,rndColor2,rndColor3))
            painterInstance.setPen(pen)
            painterInstance.drawRect(row["x0"], row["y0"], row["width"], row["height"])
            i += 1

        self.paint(0) #shows the modified pixelmap


    def mousePressEvent(self, event):
        if(event.button() == Qt.LeftButton):
            self.selectRow(event, "article")

    def mouseDoubleClickEvent(self, event):
        self.selectRow(event, "articleSum")

    # recognize if row was clicked and modify df
    def selectRow(self, event, classSelected):
        picX0 = 0
        picY0 = self.centralWidget().pos().y()  # toolbar is on top of pic
        scrolled_y0 = self.centralWidget().verticalScrollBar().value()
        x_clicked = event.x() - picX0
        y_clicked = scrolled_y0 + event.y() - picY0

        i = 0
        while i < len(self.df.values):
            row = self.df.loc[i]
            x_drinne = row["x0"] <= x_clicked <= (row["x0"] + row["width"])
            y_drinne = row["y0"] <= y_clicked <= (row["y0"] + row["height"])
            if x_drinne & y_drinne:# found row that was clicked on
                painterInstance = QPainter(self.pixmap)
                pen = QPen(QColor("black"))
                painterInstance.setPen(pen)
                if classSelected == "article":
                    col = QColor("red")
                    self.df.at[i,"rowClass"] = 1
                elif classSelected == "articleSum":
                    col = QColor("blue")
                    self.df.at[i, "rowClass"] = 2
                elif classSelected == "vat":
                    col = QColor("green")
                    self.df.at[i, "rowClass"] = 3
                elif classSelected == "vatSum":
                    col = QColor("yellow")
                    self.df.at[i, "rowClass"] = 4
                elif classSelected == "ignore":
                    col = QColor("black")
                    self.df.at[i, "rowClass"] = -1
                painterInstance.fillRect(row["x0"], row["y0"], row["width"], row["height"],
                                         QBrush(col, 5))
                self.paint(scrolled_y0)  # shows the modified pixelmap
                break
            i += 1

    #save over which rows the mouse got dragged
    def mouseMoveEvent(self, event):
        picY0 = self.centralWidget().pos().y()  # toolbar is on top of pic
        scrolled_y0 = self.centralWidget().verticalScrollBar().value()
        y_clicked = scrolled_y0 + event.y() - picY0

        if self.minMouseY is None:
            self.minMouseY = y_clicked
        if y_clicked > self.maxMouseY:
            self.maxMouseY = y_clicked
    def mouseReleaseEvent(self, event):
        if not self.minMouseY is None:
            painterInstance = QPainter(self.pixmap)
            pen = QPen(QColor("black"))
            painterInstance.setPen(pen)
            i = 0
            while i < len(self.df.values):
                row = self.df.loc[i]
                y_drinne = self.minMouseY <= row["y0"] <= self.maxMouseY
                if y_drinne:
                    self.df.at[i,"rowClass"] = 1
                    painterInstance.fillRect(row["x0"], row["y0"], row["width"], row["height"], QBrush(QColor("red"),5))
                i += 1

            self.paint(self.centralWidget().verticalScrollBar().value())  # shows the modified pixelmap
            self.minMouseY = None
            self.maxMouseY = 0

    #after showing the modified pixelmap, scroll down for "scrolled_y0"
    def paint(self, scrolled_y0):
        label = QLabel(self)
        label.setPixmap(self.pixmap)
        scrollarea = QScrollArea()
        scrollarea.setWidget(label)
        scrollarea.verticalScrollBar().setValue(scrolled_y0)
        self.setCentralWidget(scrollarea)

    def refreshPic(self):
        self.df["rowClass"] = 0
        self.pixmap = QPixmap(self.path)
        self.setImageWidget()

    def saveClasses(self):
        name = self.imgNames[self.imgCount]
        picklePath = self.folder + "/" + name + "_label.pkl"
        label_df = self.df[["plainText","rowClass"]]
        label_df.to_pickle(picklePath) #save labeled df

        #print(self.df.to_string())
        print(self.df.to_string())
        print("pickled to: "+picklePath)
        print("-----------------------------------------------")
        if self.imgCount+1 < len(self.imgNames):
            self.nextImg()
        else:
            print("Done labeling all available images!")
            qApp.exit()

    def nextImg(self):
        self.imgCount += 1
        name = self.imgNames[self.imgCount]
        self.path = self.folder + "/" + name + ".jpg"
        print("opening next image at: " + self.path)

        jsonPath = self.folder + "/" + name + ".jpg.json"
        self.df = get_df(jsonPath)
        self.df["rowClass"] = 0  # set all classes to 0

        self.pixmap = QPixmap(self.path)
        self.setImageWidget()

    def searchImgNames(self, folder):
        names = []
        for file in os.listdir(folder):
            if file.endswith(".jpg"):
                name = file.split(".jpg")[0]
                picklePath = self.folder + "/" + name + "_label.pkl"
                if not os.path.isfile(picklePath):
                    names.append(name)
        return names

    def removeImg(self):
        print("removing picture: " +self.path)
        jsonPath = self.folder + "/" + self.imgNames[self.imgCount] + ".jpg.json"
        pic_path_dest = self.folder+"/garbage/"+self.imgNames[self.imgCount]+".jpg"
        json_path_dest = self.folder+"/garbage/"+self.imgNames[self.imgCount]+ ".jpg.json"

        shutil.move(self.path, pic_path_dest)
        shutil.move(jsonPath, json_path_dest)

        if self.imgCount+1 < len(self.imgNames):
            self.nextImg()
        else:
            print("Done labeling all available images!")
            qApp.exit()

    def rotatePic(self):
        im = Image.open(self.path)
        im.rotate(180).save(self.path)
        self.pixmap = QPixmap(self.path)
        self.setImageWidget()


if __name__=="__main__":
    args = []
    app = QApplication(args)
    window = LabelWindow()

    sys.exit(app.exec_())
    #15, 106 was upside down
    #2, 6, 11, 64, 68, 69, 98, 113, 211, 302 sind upside down
    #21, 102 raus geschmissen
