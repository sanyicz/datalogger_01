import tkinter as tk
import logging
from PIL import Image
from PIL import ImageTk
import string

#suppress irrelevant logging
logging.getLogger("PIL").setLevel(logging.WARNING)

class SpreadsheetManager:
    def __init__(self, master, n=1, m=1):
        self.logger = logging.getLogger("Spreadsheet manager")
        self.logger.info("Created spreadsheet manager.")
        self._master = master
        if isinstance(n, int) and isinstance(m, int):
            if n > 0 and m > 0:
                self._n, self._m = n, m
            else:
                print("Parameter error.")
                return
        else:
            print("Parameter error.")
            return

        #set up variables
        self._iconSizeX, self._iconSizeY = 16, 16
        self._images = {}
        self._images["addColumn_plus_icon"] = ImageTk.PhotoImage(Image.open("plus_icon.png").resize((self._iconSizeX, self._iconSizeY)))

        self._mouseButton1Pressed = False
        self._mouseButton2Pressed = False

        self._entryWidth = 8
        
        self._header = []
        self._table = []

##        self._headerFrame = tk.Frame(self._master)
##        self._headerFrame.grid(row=0, column=0)
        self._tableFrame = tk.Frame(self._master)
        self._tableFrame.grid(row=0, column=0)

        _row = 0
        for j in range(self._m):
            columnName = string.ascii_letters[j]
            textvariable = tk.StringVar(value=columnName)
            entry = tk.Entry(self._tableFrame, textvariable=textvariable, width=self._entryWidth)
            entry.grid(row=_row, column=j)
            self._header.append(textvariable)
        self._addColumnButton = tk.Button(self._tableFrame, image=self._images["addColumn_plus_icon"])
        self._addColumnButton.grid(row=_row, column=len(self._header))
        _row += 1
        for i in range(self._n):
            self._table.append([])
            for j in range(self._m):
                textvariable = tk.StringVar()
                entry = tk.Entry(self._tableFrame, textvariable=textvariable, width=self._entryWidth)
                entry.grid(row=_row+i, column=j)
                self._table[i].append(textvariable)
            _row += 1
        print(self._table)
        self._master.bind("<ButtonPress-1>", self.handleMousePress1)
        self._master.bind("<ButtonRelease-1>", self.handleMouseRelease1)
        self._master.bind("<B1-Motion>", self.handleMouseMove)

    def addColumn(self, position=-1, columnName=None):
        if position == -1:
            position = self._m
        if columnName == None:
            columnName = str(self._m)

    def addRow(self, position=-1):
        pass

    def handleMousePress1(self, event, entry=None, i=None, j=None):
        widget = event.widget.winfo_containing(event.x_root, event.y_root)
        if isinstance(widget, tk.Entry):
            self._mouseButton1Pressed = True

    def handleMouseRelease1(self, event, entry=None, i=None, j=None):
        self._mouseButton1Pressed = False

    def handleMouseMove(self, event, entry=None, i=None, j=None):
        if self._mouseButton1Pressed:
            widget = event.widget.winfo_containing(event.x_root, event.y_root)
            if isinstance(widget, tk.Entry):
                widget.config(bg='blue')

        


if __name__ == "__main__":
    # Configure logging once, in your main program
    logging.basicConfig(
        level=logging.DEBUG,  # Or INFO in production
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        handlers=[
            logging.FileHandler("log.log"),
            logging.StreamHandler()
        ]
    )

    root = tk.Tk()
    root.title("Spreadsheet Manager Test")
    app = SpreadsheetManager(root, n=2, m=3)
    root.mainloop()
