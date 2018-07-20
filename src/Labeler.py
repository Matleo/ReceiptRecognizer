import sys
import os
from PyQt5.QtWidgets import QApplication, QDesktopWidget, QMainWindow, QAction, qApp, QMenu, QLabel, QScrollArea, QFileDialog
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QPen, QColor, QBrush
from PyQt5.QtCore import Qt
from src.preprocessing import get_df
from random import randint

class LabelWindow(QMainWindow):
    def __init__(self):
        super().__init__()


        self.folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.imgNames = self.searchImgNames(self.folder)#the names of jpg files
        self.imgCount = 0 #keep track on which file we are
        self.path = self.folder+"/"+self.imgNames[0]+".jpg"
        self.pixmap = QPixmap(self.path)

        jsonPath = self.folder + "/" + self.imgNames[0] + "-40.webp.json"
        self.df = get_df(jsonPath)
        self.df["rowClass"] = 0 #set all classes to 0

        self.minMouseY = None
        self.maxMouseY = 0

        self.initUI()

    def initUI(self):
        self.setImageWidget()

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

        refreshAct = QAction(QIcon('../assets/img/refresh.jpg'), 'Refresh', self)
        refreshAct.setShortcut('Ctrl+R')
        refreshAct.setStatusTip('Refresh picture')
        refreshAct.triggered.connect(self.refreshPic)

        exitAct = QAction(QIcon('../assets/img/exit.png'), 'Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(qApp.quit)

        self.toolbar = self.addToolBar('Save')
        self.toolbar.addAction(saveAct)

        self.toolbar = self.addToolBar('Refresh')
        self.toolbar.addAction(refreshAct)

        self.toolbar = self.addToolBar('Exit')
        self.toolbar.addAction(exitAct)

    def contextMenuEvent(self, event):
        cmenu = QMenu(self)

        vat = cmenu.addAction("vat")
        vatSum = cmenu.addAction("vatSum")
        action = cmenu.exec_(self.mapToGlobal(event.pos()))

        if action == vat:
            self.selectRow(event, "vat")
        elif action == vatSum:
            self.selectRow(event, "vatSum")

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
        name = self.imgNames[self.imgCount]+"_label"
        picklePath = self.folder + "/" + name + ".pkl"
        label_df = self.df[["plainText","rowClass"]]
        label_df.to_pickle(picklePath) #save labeled df
        self.imgCount += 1

        #print(self.df.to_string())
        print(self.df.to_string())
        print("pickled to: "+picklePath)
        print("-----------------------------------------------")
        if self.imgCount < len(self.imgNames):
            name = self.imgNames[self.imgCount]
            jsonPath = self.folder + "/" + name + "-40.webp.json"
            self.df = get_df(jsonPath)
            self.df["rowClass"] = 0  # set all classes to 0

            self.path = self.folder + "/" + name + ".jpg"
            self.pixmap = QPixmap(self.path)
            self.setImageWidget()
            print("opened next image at: " + self.path)
        else:
            print("Done labeling all available images!")
            qApp.exit()

    def searchImgNames(selfself, folder):
        names = []
        for file in os.listdir(folder):
            if file.endswith(".jpg"):
                names.append(file.split(".jpg")[0])
        return names



if __name__=="__main__":
    args = []
    app = QApplication(args)
    window = LabelWindow()

    sys.exit(app.exec_())
    #15, 106 was upside down
    #2, 6, 11, 64, 68, 69, 98, 113, 211, 302 sind upside down
    #21, 102 raus geschmissen
