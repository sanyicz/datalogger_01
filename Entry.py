import tkinter as tk

class Entry:
    def __init__(self, master, width=6, value=0):
        self._master = master
        self._frame = tk.Frame(self._master)
        self._width = width
        self._variable = tk.IntVar(value = value)
        self._moduloValue = None
        self._entry = tk.Entry(self._frame, textvariable=self._variable, width=self._width-2)
        self._entry.grid(row=0, column=0, rowspan=2)
        tk.Button(self._frame, text="^", command=self.buttonPlus, width=2, height=1).grid(row=0, column=1)
        tk.Button(self._frame, text="v", command=self.buttonMinus, width=2, height=1).grid(row=1, column=1)
        self._entry.bind('<MouseWheel>', self.entryScroll)

    def grid(self, row, column):
        self._frame.grid(row=row, column=column)

    def entryScroll(self, event):
        pass

    def buttonPlus(self):
        value = self._variable.get()
        if self._moduloValue is not None:
            self._variable.set(((value + 1) % self._moduloValue))
        else:
            self._variable.set(value + 1)

    def buttonMinus(self):
        self._variable.set(self._variable.get() - 1)

    def setModulo(self, value=None):
        self._moduloValue = value

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Entry Test")
    entry = Entry(root, width=10, value=5)
    entry.grid(row=0, column=0)
    entry.setModulo(7)
##    entry.setModulo()
    root.mainloop()
