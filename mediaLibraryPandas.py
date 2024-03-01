"""
Pandas dataframe
Columns

File name: name of the file (without extension)
File extension: file extension
Directory: directory of the file
Best date: estimate of when the photo/video was taken, priority is:

dateTags = ['EXIF:CreateDate', 'EXIF:DateTimeOriginal', 'EXIF:ModifyDate', \
                'QuickTime:CreateDate', 'QuickTime:TrackCreateDate', 'QuickTime:MediaCreateDate', \
                'QuickTime:MediaModifyDate', 'QuickTime:ModifyDate', 'QuickTime:TrackModifyDate', \
                'File:FileModifyDate']

ID-device: unique identifier stored in EXIF:ImageUniqueID
ID-Hash: unique identifier created through hash
Media type: video or photo
Compression: from EXIF:Compression or QuickTime:CompressorID



"""