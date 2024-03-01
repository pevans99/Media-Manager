
import mimetypes
import os
import sys
import hashlib
import time
import logging
import cv2
import pyexifinfo
from csv import writer, reader
import sys
from tqdm import tqdm
from PyQt5.QtWidgets import QApplication, QFileDialog

logging.basicConfig()
logging.disable(logging.WARNING)
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

class mediaFileUtils:
    metaTags = ['EXIF:CreateDate', 'EXIF:DateTimeOriginal', 'EXIF:ModifyDate', \
                'QuickTime:CreateDate', 'QuickTime:MediaCreateDate', \
                'QuickTime:MediaModifyDate', 'QuickTime:TrackModifyDate', \
                'File:FileModifyDate']
    
    def __init__(self, directory = [], files = [], csv = []):
        '''mediaFileUtils(directory)
        Create photo library object with all files in "directory", including subfolders.
        
        "directory" is stored in "topFolder" and each file including in all subfolders is
        listed with it's full name in a flat list "files" and the number of files is
        stored in "numFiles".
        '''
        if files and not directory and not csv:
            app = QApplication([])
            app.setStyle('Fusion')
            self.files = files
            self.numFiles = len(self.files)
            self.topFolder = QFileDialog.getExistingDirectory(None, 'Select Folder', '', QFileDialog.ShowDirsOnly)
            
        elif directory and not files and not csv:
            self.topFolder = directory
            self.files = list()
            self.numFiles = 0
    
            for (path, folders, files) in os.walk(self.topFolder):
                for f in files:
                    fullFileName = path+'/'+f
                    self.files.append(fullFileName)
            
            self.numFiles = len(self.files)
            
        elif csv and not directory and not files:
            self.dataFile = csv
            self.data = []
            # open file in read mode
            csv_reader = reader(open(self.dataFile, 'r'))
            for mediaEntry in csv_reader:
                self.data.append([mediaEntry[0], time.strptime(mediaEntry[1],'%Y-%m-%d %H:%M:%S'),
                                  eval(mediaEntry[2]),mediaEntry[3],mediaEntry[4]])
                        
        else:
            print('I don\'t know what to do')
        
    
    def saveCSV(self):
        filesProcessed = 0
        fileOpener = open(self.topFolder+'/photoLib.csv', 'w', newline='')
        csvWriter = writer(fileOpener)
        for file in tqdm(self.files):
            date, md5hash, mime, errors = self.getFileData(file)
            csvWriter.writerow([file, date, md5hash, mime, errors])
            filesProcessed = filesProcessed + 1
            
        fileOpener.close()
        return
        
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
                        errors = errors+'date shift'
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
            mime = fileTypeChecker.split('/')[0]
        
        try:
            # open with cv2 if video and compute hash
            if mime == 'video':
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
            elif mime == 'image':
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
    

#f = '/media/media/photo library'
#m = mediaFileUtils(directory = f)
        
c = '/media/media/photo library/photoLib.csv'
m = mediaFileUtils(csv = c)
