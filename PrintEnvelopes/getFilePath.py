import tkinter
from tkinter import filedialog

# Create a file exporere window to select file then returns filepath for that file
def getFilePath():
    root = tkinter.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    filePath = filedialog.askopenfilename()
    return filePath