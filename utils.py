import tkinter
from tkinter import filedialog

# Create a file exporere window to select file then returns filepath for that file
def get_file_path():
    root = tkinter.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    filePath = filedialog.askopenfilename()
    return filePath