import os

def main():
    imageDirectory = "/media/media/photo library/2020/06"

    files = list()
    numFiles = 0
    
    for (path, folders, filesLocal) in os.walk(imageDirectory):
        for f in filesLocal:
            fullFileName = path+'/'+f
            files.append(fullFileName)
            
    numFiles = len(files)

if __name__ == "__main__":
    main()