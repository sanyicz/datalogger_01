import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class Graph(tk.Frame):
    def __init__(self, master=None, title="Graph", **kwargs):
        super().__init__(master, **kwargs)
        self._title = title
        self._figsizeX, self._figsizeY = 4, 3 #inches
        self._dpi = 100
        self._defaultFont = tk.font.nametofont('TkTextFont').actual()
        self._axisLimitVariables = {"xmin" : tk.StringVar(),
                                    "xmax" : tk.StringVar(),
                                    "ymin" : tk.StringVar(),
                                    "ymax" : tk.StringVar(),
                                    }
        self._axisLimitCurrent = {"xmin" : None,
                                  "xmax" : None,
                                  "ymin" : None,
                                  "ymax" : None,
                                  }

        #title label
        titleLabel = tk.Label(self, text=self._title, font=("Arial", 12, "bold"))
        titleLabel.grid(row=0, column=0)

        #matplotlib figure
        self._figure = Figure(figsize=(self._figsizeX, self._figsizeY), dpi=self._dpi)
##        self._figure.tight_layout()
        self._ax = self._figure.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(self._figure, master=self)
        self._canvas.get_tk_widget().grid(row=1, column=0)

        #axis limit controls
        limitsFrame = tk.Frame(self)
        limitsFrame.grid(row=2, column=0)
        tk.Label(limitsFrame, text="X min").grid(row=0, column=0)
        tk.Label(limitsFrame, text="X max").grid(row=0, column=1)
        tk.Label(limitsFrame, text="Y min").grid(row=0, column=2)
        tk.Label(limitsFrame, text="Y max").grid(row=0, column=3)
        tk.Entry(limitsFrame, textvariable=self._axisLimitVariables["xmin"], width=6).grid(row=1, column=0)
        tk.Entry(limitsFrame, textvariable=self._axisLimitVariables["xmax"], width=6).grid(row=1, column=1)
        tk.Entry(limitsFrame, textvariable=self._axisLimitVariables["ymin"], width=6).grid(row=1, column=2)
        tk.Entry(limitsFrame, textvariable=self._axisLimitVariables["ymax"], width=6).grid(row=1, column=3)
        tk.Button(limitsFrame, text="Apply limits", command=self.applyAxisLimits).grid(row=0, column=4)
        tk.Button(limitsFrame, text="Reset limits", command=self.resetAxisLimits).grid(row=0, column=5)
        autoscaleFrame = tk.Frame(limitsFrame)
        autoscaleFrame.grid(row=1, column=4, columnspan=2)
##        tk.Label(autoscaleFrame, text="Autoscale on").grid(row=0, column=0)
        self._autoscaleCheckbuttonVariable = tk.IntVar(value=1)
##        self._autoscaleCheckbuttonVariable.set(1)
        self._scaleY = True
        tk.Checkbutton(autoscaleFrame, text="Autoscale on", variable=self._autoscaleCheckbuttonVariable, command=self.autoscaleCheckbuttonToggle).grid(row=0, column=1)
        
    def setSize(self, x, y):
        self._figsizeX, self._figsizeY = x, y
        self._figure.set_size_inches(self._figsizeX, self._figsizeY, forward=True)
    
    def plot(self, x, y, label="Data"):
        self._ax.clear()
        self._ax.plot(x, y, label=label)
        self._ax.legend()
##        print(self._axisLimitCurrent)
        if self._autoscaleCheckbuttonVariable.get():
            xmin, xmax = self._ax.get_xlim()
            ymin, ymax = self._ax.get_ylim()
            self._axisLimitCurrent["xmin"], self._axisLimitCurrent["xmax"] = xmin, xmax
            self._axisLimitCurrent["ymin"], self._axisLimitCurrent["ymax"] = ymin, ymax
        else:
            xmin, xmax = self._axisLimitCurrent["xmin"], self._axisLimitCurrent["xmax"]
            ymin, ymax = self._axisLimitCurrent["ymin"], self._axisLimitCurrent["ymax"]
##        self._ax.set_xlim(xmin, xmax)
        self._ax.set_ylim(ymin, ymax)
        self._axisLimitVariables["xmin"].set(xmin)
        self._axisLimitVariables["xmax"].set(xmax)
        self._axisLimitVariables["ymin"].set(ymin)
        self._axisLimitVariables["ymax"].set(ymax)
        self._canvas.draw()

    def applyAxisLimits(self):
        newLimitsString = {"xmin" : self._axisLimitVariables["xmin"].get(),
                           "xmax" : self._axisLimitVariables["xmax"].get(),
                           "ymin" : self._axisLimitVariables["ymin"].get(),
                           "ymax" : self._axisLimitVariables["ymax"].get(),
                           }
        self._axisLimitCurrent = {"xmin" : None,
                                  "xmax" : None,
                                  "ymin" : None,
                                  "ymax" : None,
                                  }
        print(self._axisLimitCurrent)
        for limit, value in newLimitsString.items():
            try:
                value = float(value)
            except:
                print(f"{limit} : {value} can't be converted to float.")
                continue
            self._axisLimitCurrent[limit] = value
        print(self._axisLimitCurrent)
        self._ax.set_xlim(self._axisLimitCurrent["xmin"], self._axisLimitCurrent["xmax"])
        self._ax.set_ylim(self._axisLimitCurrent["ymin"], self._axisLimitCurrent["ymax"])
        self._canvas.draw()

    def resetAxisLimits(self):
        self._ax.autoscale()
        self._canvas.draw()

    def autoscaleCheckbuttonToggle(self):
        return
        if self._autoscaleCheckbuttonVariable.get():
            self._ax.autoscale(enable=True, axis="both", tight=None)
        else:
            self._ax.autoscale(enable=False, axis="both", tight=None)

if __name__ == "__main__":
    import numpy as np

    root = tk.Tk()
    root.title("Graph class test")

    graph = Graph(root, title="Demo graph")
    graph.pack()

    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    graph.plot(x, y)

    root.mainloop()
