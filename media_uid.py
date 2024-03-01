import pyexifinfo

file = r'/media/media/photo library/2020/04/20200404_003335.mp4'
file = r'/media/media/photo library/2020/04/20200403_195556.jpg'
tags = pyexifinfo.get_json(file)