import os
import sys
import hashlib
import time
import logging
import cv2
import filetype
import pyexifinfo
import csv
import sys
import mariadb
import subprocess
from tqdm import tqdm
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, \
    QFileDialog, QLabel, QProgressBar, QInputDialog, QLineEdit
from PyQt5.QtCore import QThread, pyqtSignal

logging.basicConfig()
logging.disable(logging.WARNING)
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

def photoLibGUI():
    app = QApplication(sys.argv)
    window = photoLibWindow()
    app.exec()
    app.quit()
    return
    
class photoLibWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Photo Library')
        self.media = mediaFileUtils(QFileDialog.getExistingDirectory(self, 'Open file'))    
        self.initDB()
        self.initUI()
        return

    def initUI(self):
        self.setGeometry(300, 300, 300, 100)
        self.layout = QVBoxLayout()
        self.display = self.dispWidget(self.media)
        self.progress = self.progWidget(self.media)
        self.layout.addWidget(self.display)
        self.layout.addWidget(self.progress)
        self.layout.addStretch()
        self.setLayout(self.layout)
        self.show()
        self.runAnalysis()
        return
    
    def initDB(self):
        password, ok = QInputDialog.getText(self, 'mySQL password', 'Enter password:', QLineEdit.Password)
        self.dbConnect = mariadb.connect(host="localhost", user="phillip", password=password, database='media')
        self.dbConnect.autocommit = True
        self.dbCursor = self.dbConnect.cursor()
        return
        
    def runAnalysis(self):
        self.getDataThread = self.getData(self.media, self.dbCursor)
        self.getDataThread.start()
        self.getDataThread.progressUpdate.connect(self.onUpdate)
        return
        
    def onUpdate(self,val):        
        self.progress.setValue(val)
        return
        
    def closeEvent(self, event):
        self.getDataThread.quit()
        self.getDataThread.requestInterruption()
        self.dbConnect.close()
        return
                   
    class getData(QThread):      
        progressUpdate = pyqtSignal(int)
        
        def __init__(self, media, cursor):
            super().__init__()
            self.media = media
            self.cursor = cursor
            return
            
        def run(self):
            fileIter = iter(self.media.files)
            filesProcessed = 0
            while(not self.isInterruptionRequested()):
                file = next(fileIter)
                date, md5hash, mime, errors = self.media.getFileData(file)
                self.insertDB(md5hash, file, mime, date, errors)
                filesProcessed = filesProcessed + 1
                self.progressUpdate.emit(filesProcessed)
            return
        
        def insertDB(self, md5, file, mime, date, errors):
            try:
                result = self.cursor.execute("INSERT INTO main (md5hash,fileLocation,mime,bestDate,errors) VALUES (?, ?, ?, ?, ?)", (md5, file, mime, date, errors))
            except mariadb.Error as e:
                error = f"{e}"
                if error.find('Duplicate') != -1:
                    try:
                        result = self.cursor.execute("INSERT INTO scratch (md5hash,fileLocation,mime,bestDate,errors) VALUES (?, ?, ?, ?, ?)", (md5, file, mime, date, errors))
                        print('***************Duplicate******************')
                    except mariadb.Error as e:
                        error = f"{e}"
                        if error.find('Duplicate') != -1:
                            print('*******Already in scratch!!!************')
                        else:
                            print('*******Neither table worked***********')
                            print(error)
                else:
                    print('**************mysql error!!!**************')
                    print(error)
            return
                 
    class dispWidget(QLabel):
        def __init__(self, media):
            super().__init__()
            self.setText('Photos folder: '+media.topFolder+'\n'+'Number of files: ' \
                         +str(media.numFiles))
            self.setWordWrap(True)   
            return

    class progWidget(QProgressBar):
        def __init__(self, media):
            super().__init__()
            self.setRange(0,media.numFiles)
            self.setValue(0)
            self.setFormat('%p% %v/%m')
            return

class mediaFileUtils:
    metaTags = ['EXIF:CreateDate', 'EXIF:DateTimeOriginal', 'EXIF:ModifyDate', \
                'QuickTime:CreateDate', 'QuickTime:MediaCreateDate', \
                'QuickTime:MediaModifyDate', 'QuickTime:TrackModifyDate', \
                'File:FileModifyDate']
    
    def __init__(self, name, lst = False):
        '''mediaFileUtils(directory)
        Create photo library object with all files in "directory", including subfolders.
        
        "directory" is stored in "topFolder" and each file including in all subfolders is
        listed with it's full name in a flat list "files" and the number of files is
        stored in "numFiles".
        '''
        if lst:
            self.files = name
            self.numFiles = len(self.files)
            self.topFolder = '/home/jenny/Apps/Python'
            
        else:
            self.topFolder = name
            self.files = list()
            self.numFiles = 0
    
            for (path, folders, files) in os.walk(self.topFolder):
                for f in files:
                    fullFileName = path+'/'+f
                    self.files.append(fullFileName)
            
            self.numFiles = len(self.files)
        
        return
    
    def saveCSV(self):
        filesProcessed = 0
        fileOpener = open(self.topFolder+'/photoLib.csv', 'w', newline='')
        csvWriter = csv.writer(fileOpener)
        for file in tqdm(self.files):
            date, md5hash, mime, errors = self.getFileData(file)
            csvWriter.writerow([file, date, md5hash, mime, errors])
            filesProcessed = filesProcessed + 1
            
        fileOpener.close()
        return
    
    def saveDB(self, password):
        self.dbConnect = mariadb.connect(host="localhost", user="phillip", password=password, database='media')
        self.dbConnect.autocommit = True
        self.dbCursor = self.dbConnect.cursor()
        for file in tqdm(self.files):
            date, md5hash, mime, errors = self.getFileData(file)
            self.insertDB(md5hash, file, mime, date, errors)
        
        self.dbConnect.close()
        
    def insertDB(self, md5, file, mime, date, errors):
        try:
            result = self.dbCursor.execute("INSERT INTO main (md5hash,fileLocation,mime,bestDate,errors) VALUES (?, ?, ?, ?, ?)", (md5, file, mime, date, errors))
        except mariadb.Error as e:
            error = f"{e}"
            if error.find('Duplicate') != -1:
                try:
                    result = self.dbCursor.execute("INSERT INTO scratch (md5hash,fileLocation,mime,bestDate,errors) VALUES (?, ?, ?, ?, ?)", (md5, file, mime, date, errors))
                    print('***************Duplicate******************')
                except mariadb.Error as e:
                    error = f"{e}"
                    if error.find('Duplicate') != -1:
                        print('*******Already in scratch!!!************')
                    else:
                        print('*******Neither table worked***********')
                        print(error)
            else:
                print('**************mysql error!!!**************')
                print(error)
        return
    
    def open(self,index):
        subprocess.Popen(['/usr/bin/xdg-open',self.files[index]])
        
    def getFileData(self, file):
        '''dateTaken, md5hash, mime, errors = MediaFileUtils.getFileData(file)
        
        Find the best estimate of the date taken, preferred order is stored in "metaTags".
        Deterime file type, compute md5hash, and return any errors
        '''
        tags = pyexifinfo.get_json(file) # get meta data from pyexifinofo plugin
        errors = '' #initialize errors
        # look for a date tag in the order liste in metaTags
        for checkTag in self.metaTags:
            try:
                if checkTag in tags[0]:
                    bestDate = str(tags[0][checkTag])                       
                    # fix date formatting
                    if len(bestDate)>19:
                        bestDate = bestDate[:-(len(bestDate)-19)]
                        dateTaken = time.strptime(bestDate, '%Y:%m:%d %H:%M:%S')
                        dateTaken = time.strftime('%Y-%m-%d %H:%M:%S', dateTaken)
                    else:
                        dateTaken = time.strptime(bestDate, '%Y:%m:%d %H:%M:%S')
                        dateTaken = time.strftime('%Y-%m-%d %H:%M:%S', dateTaken)
                    
                    break
            except Exception as e:
                # catch errors
                dateTaken = ''
                errors = errors+str(e)
        
        # get file type
        fileTypeChecker = mimetypes.guess_type(file)[0]
        if fileTypeChecker is None:
            mime = 'none'
        else:
            mime = fileTypeChecker
        
        try:
            # open with cv2 if video and compute hash
            if mime.startswith('video'):
                ret, frame = cv2.VideoCapture(file).read()
                if ret:
                    md5hash = hashlib.md5(frame.tobytes())
                    md5hash = md5hash.digest()
                else:
                    filePointer = open(file, 'rb')
                    md5hash = hashlib.md5(filePointer.read())
                    md5hash = md5hash.digest()
                    filePointer.close()
                    errors = errors+'*video hash computed from total file'
            # open with PIL if not video and compute hash
            elif mime.startswith('image') == 0:
                try:
                    md5hash = hashlib.md5(ImageFile.Image.open(file).tobytes())
                    md5hash = md5hash.digest()
                except Exception as e:
                    filePointer = open(file, 'rb')
                    md5hash = hashlib.md5(filePointer.read())
                    md5hash = md5hash.digest()
                    filePointer.close()
                    errors = errors+'*image hash from total file*'+str(e)
            else:
                filePointer = open(file, 'rb')
                md5hash = hashlib.md5(filePointer.read())
                md5hash = md5hash.digest()
                filePointer.close()
                errors = errors+'*hash from total file*'   
                        
        except Exception as e:
            filePointer = open(file, 'rb')
            md5hash = hashlib.md5(filePointer.read())
            md5hash = md5hash.digest()
            filePointer.close()
            errors = errors+'*hash computed from total file*'+str(e)
            
        return dateTaken, md5hash, mime, errors