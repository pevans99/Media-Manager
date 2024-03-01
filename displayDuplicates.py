import sys
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import os

class ImageWidget(QWidget):
    def __init__(self, imagePath, parent=None):
        super(ImageWidget, self).__init__(parent)
        self.imagePath = imagePath
        self.selected = False

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.label = QLabel(self)
        pixmap = QPixmap(imagePath)
        self.label.setPixmap(pixmap)
        layout.addWidget(self.label)

    def mousePressEvent(self, event):
        self.selected = not self.selected
        if self.selected:
            self.label.setStyleSheet("border: 2px solid red")
        else:
            self.label.setStyleSheet("")
        QWidget.mousePressEvent(self, event)

class ImageGrid(QWidget):
    def __init__(self, imagePaths, parent=None):
        super(ImageGrid, self).__init__(parent)
        self.imagePaths = imagePaths
        self.imageWidgets = []

        layout = QGridLayout()
        self.setLayout(layout)

        for i, imagePath in enumerate(imagePaths):
            imageWidget = ImageWidget(imagePath)
            self.imageWidgets.append(imageWidget)
            layout.addWidget(imageWidget, i // 5, i % 5)

    def closeEvent(self, event):
        selectedImages = [w.imagePath for w in self.imageWidgets if w.selected]
        print("Selected images:", selectedImages)
        QWidget.closeEvent(self, event)

def main():
    imageDirectory = "/media/media/photo library/2020/06"

    topFolder = imageDirectory
    files = list()
    numFiles = 0
    
    for (path, folders, filesLocal) in os.walk(topFolder):
        for f in filesLocal:
            fullFileName = path+'/'+f
            files.append(fullFileName)
            
    numFiles = len(files)


    app = QApplication(sys.argv)

    window = ImageGrid(files[0:2])
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
