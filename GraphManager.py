import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from math import sqrt, ceil
import logging

#suppress irrelevant logging
logging.getLogger("matplotlib").setLevel(logging.WARNING)

class GraphManager:
    def __init__(self, master, n=1, m=1, mode="debug"):
        self.logger = logging.getLogger("Graph manager")
        self.logger.info("Created graph manager.")
        self._mode = mode #debug or normal
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
        self._figure = Figure(figsize=(8, 6), layout="constrained") #a main figure to manage subplots
        self._plotVisibilityVariables = {} #structure: {_id : variable}
##        self._axes = {} #self._data???
        self._checkbuttonFrame = tk.Frame(self._master)
        self._checkbuttonFrame.grid(row=0, column=0)

        self._data = {} #structure: {_id : {"axis" : axis, "plot" : plot, "plotStyle" : plotStyle, "data" : data, "annotation" : annotation, "title" : title, "color" : color, "limits" : {"auto" : True, "xmin" : xmin, ...}}}

        self._canvas = FigureCanvasTkAgg(self._figure, master=self._master)
        self._canvas.get_tk_widget().grid(row=0, column=1, sticky="NSEW")

        self._entryWidth = 8
        
        self.update()
        self._master.grid_rowconfigure(0, weight=1)
        self._master.grid_columnconfigure(1, weight=1)
        self._resizeJob = None
        self._master.bind("<Configure>", self.onResize)

        if self._mode == "debug":
            testFrame = tk.Frame(self._master)
            testFrame.grid(row=1, column=0, columnspan=2)
            tk.Button(testFrame, text="Add graph", command=self.addGraph).grid(row=0, column=0)
            self._plotId = tk.IntVar(value=1)
            tk.Button(testFrame, text="Plot to graph", command=self.plot).grid(row=0, column=1)
            tk.Entry(testFrame, textvariable=self._plotId).grid(row=0, column=2)
            tk.Button(testFrame, text="Save figure", command=self.saveFigure).grid(row=0, column=3)

        self._plotSettingsWindow = None

        self._figure.canvas.mpl_connect("button_press_event", self.onClick) #open plotSettingsWindow
        self._figure.canvas.mpl_connect("motion_notify_event", self.onMotion)

    def updatePlotAnnotation(self):
        pass
    
    def onMotion(self, event):
        for _id, data in self._data.items():
            plotStyle = data["plotStyle"]
            if plotStyle != "scatter":
                continue
            
            axis = data["axis"]
            plot = data["plot"]
            annotation = data["annotation"]
            x, y = event.xdata, event.ydata
##            print(f"x, y: {x}, {y}")
            if event.inaxes == axis:
##                print(f"axis: {axis}")
##                print(f"_id: {_id}")
                if plot == None:
                    continue
                contains, details = plot.contains(event)
##                print(contains, details)
                if contains:
                    x, y = plot.get_offsets()[details["ind"][0]]
                    text = f"x, y: {round(x, 2)}, {round(y, 2)}"
                    annotation.set_text(text)
                    annotation.xy = (x, y)
                    annotation.get_bbox_patch().set_alpha(0.4)
                    annotation.set_visible(True)
                else:
                    if annotation.get_visible():
                        annotation.set_visible(False)
            else:
                pass
        self._figure.canvas.draw_idle()

    def onClick(self, event):
        if self._plotSettingsWindow is not None:
            return
        self._plotLimitVariables = {"autoX" : tk.IntVar(name="autoX"),
                                    "autoY" : tk.IntVar(name="autoY"),
                                    "xmin" : tk.DoubleVar(name="xmin"),
                                    "xmax" : tk.DoubleVar(name="xmax"),
                                    "ymin" : tk.DoubleVar(name="ymin"),
                                    "ymax" : tk.DoubleVar(name="ymax"),}
        axEvent = event.inaxes
        for _id, data in self._data.items():
            if axEvent == data["axis"]:
                ax = data["axis"]
                title = data["title"]
                color = data["color"]
                limits = data["limits"]
                for key, value in limits.items():
                    self._plotLimitVariables[key].set(value)
                print(f"event in graph {title}")
                self._plotSettingsWindow = tk.Toplevel() #add some window close method, when you don't click apply
                self._plotSettingsWindow.protocol("WM_DELETE_WINDOW", self.closePlotSettings)
                self._plotSettingsWindow.title("Plot settings")
                self._plotSettingsWindow.bind_all("<Button-1>", lambda event: event.widget.focus_set())
                self._plotSettingsWindow.bind_all("<FocusOut>", self.focusOut)
                tk.Label(self._plotSettingsWindow, text=title).grid(row=0, column=0)
                limitsFrame = tk.Frame(self._plotSettingsWindow)
                limitsFrame.grid(row=1, column=0)
                tk.Label(limitsFrame, text="X min:").grid(row=0, column=0)
                tk.Entry(limitsFrame, textvariable=self._plotLimitVariables["xmin"], width=self._entryWidth).grid(row=0, column=1)
                tk.Label(limitsFrame, text="X max:").grid(row=0, column=2)
                tk.Entry(limitsFrame, textvariable=self._plotLimitVariables["xmax"], width=self._entryWidth).grid(row=0, column=3)
                tk.Checkbutton(limitsFrame, text="Auto X", variable=self._plotLimitVariables["autoX"]).grid(row=0, column=4)
                tk.Label(limitsFrame, text="Y min:").grid(row=1, column=0)
                tk.Entry(limitsFrame, textvariable=self._plotLimitVariables["ymin"], width=self._entryWidth).grid(row=1, column=1)
                tk.Label(limitsFrame, text="Y max:").grid(row=1, column=2)
                tk.Entry(limitsFrame, textvariable=self._plotLimitVariables["ymax"], width=self._entryWidth).grid(row=1, column=3)
                tk.Checkbutton(limitsFrame, text="Auto Y", variable=self._plotLimitVariables["autoY"]).grid(row=1, column=4)
                #
                tk.Label(limitsFrame, text="Color").grid(row=3, column=0, columnspan=2)
##                print(f"color: {color}")
                colors = ["blue", "red", "green", "orange", "purple", "brown", "black", "grey", "yellow"]
                self._plotColorVariable = tk.StringVar()
                color = color if color in colors else None
                self._plotColorVariable.set(color) #set a default value
                tk.OptionMenu(limitsFrame, self._plotColorVariable, *colors).grid(row=3, column=2, columnspan=2)
                #
                tk.Label(limitsFrame, text="Plot style").grid(row=4, column=0, columnspan=2)
                plotStyles = ["scatter", "line"]
                self._plotStyleVariable = tk.StringVar()
                plotStyle = plotStyles[0] if plotStyles else None
                self._plotStyleVariable.set(plotStyle) #set a default value
                tk.OptionMenu(limitsFrame, self._plotStyleVariable, *plotStyles).grid(row=4, column=2, columnspan=2)
                #
                self.apply_button = tk.Button(limitsFrame, text="Apply settings", command=lambda _id=_id: self.applyPlotSettings(_id))
                self.apply_button.grid(row=5, column=0, columnspan=5)
            else:
                pass

    def closePlotSettings(self):
        #changes are not applied
        self._plotSettingsWindow.destroy() #must be destroyed first, then set to None 
        self._plotSettingsWindow = None

    def applyPlotSettings(self, _id):
##        print(f"_id: {_id}")
        data = self._data[_id]
        axis = data["axis"]
        newColor = self._plotColorVariable.get()
##        print(f"newColor: {newColor}")
        self._data[_id]["color"] = newColor
        newPlotStyle = self._plotStyleVariable.get()
        self._data[_id]["plotStyle"] = newPlotStyle
        limits = data["limits"]
        limits["autoX"] = self._plotLimitVariables["autoX"].get()
        limits["autoY"] = self._plotLimitVariables["autoY"].get()
        if limits["autoX"] == 0:
            limits["xmin"] = self._plotLimitVariables["xmin"].get()
            limits["xmax"] = self._plotLimitVariables["xmax"].get()
        if limits["autoY"] == 0:
            limits["ymin"] = self._plotLimitVariables["ymin"].get()
            limits["ymax"] = self._plotLimitVariables["ymax"].get()
        self._data[_id]["limits"] = limits
        self.update()
        self._plotSettingsWindow.destroy() #must be destroyed first, then set to None 
        self._plotSettingsWindow = None

    def focusOut(self, event):
        widget = event.widget
        try:
            variableName = widget["textvariable"]
            variable = self._plotLimitVariables[variableName]
        except:
##            self.logger.debug(f"Widget {widget} is not an Entry. Return.")
            pass
            return
        #sanity check here: if the value is not a float/double, it can't be accepted
        try:
            value = variable.get()
        except:
            pass

    def addGraph(self, _id=None, _title=None):
        _row = len(self._data.keys())
##        print(f"_row, _id in addGraph(): {_row}, {_id}")
        t = len(self._data.keys()) #total number of graphs before adding the new one
        self._n = round(sqrt(t+1))
        self._m = ceil((t+1) / self._n)
        variable = tk.IntVar(value=True)
        if _title == None:
            _title = f"Graph {t+1}" if _id == None else f"Graph {_id}"
        checkbutton = tk.Checkbutton(self._checkbuttonFrame, text=_title, variable=variable, command=self.update)
        checkbutton.grid(row=_row, column=0)
        self._m = min(self._m, t + 1)
        self._n = (t + 1 + self._m - 1) // self._m
        axis = self._figure.add_subplot(self._n, self._m, t + 1)
        annotation = axis.annotate("", xy=(0,0), xytext=(20,20),textcoords="offset points",
                                   bbox=dict(boxstyle="round", fc="w"),
                                   arrowprops=dict(arrowstyle="->"))
        annotation.set_visible(False)
        _id = _id if _id != None else t + 1
##        self._axes[_id] = axis
        self._plotVisibilityVariables[_id] = variable
        limits = {}
        limits["autoX"] = 1 #True, but the checkbutton variable is IntVar
        limits["autoY"] = 1 #True, but the checkbutton variable is IntVar
        limits["xmin"], limits["xmax"] = axis.get_xlim()
        limits["ymin"], limits["ymax"] = axis.get_ylim()
        self._data[_id] = {"axis" : axis, "data" : None, "plot" : None, "plotStyle": "scatter", "annotation" : annotation, "title" : _title, "color" : "blue", "limits" : limits}
##        print(self._data)
        self.update()

    def plot(self, _id=None, data=None):
        if _id == None:
            _id = self._plotId.get()

        if data == None:
            import numpy as np #is it okay here, like this?
            x = np.linspace(0, 10, 100)
            y = np.sin(x)
        else:
            x, y = data[0], data[1]

        if _id in self._data.keys():
            data = self._data[_id]
            axis = data["axis"]
            title = data["title"]
            color = data["color"]
            color = "blue" if color == None else color
            plotStyle = data["plotStyle"]
            limits = data["limits"]
            axis.clear()
            axis.title.set_text(title)
            if plotStyle == "scatter":
                plot = axis.scatter(x, y, color=color)
            elif plotStyle == "line":
                plot = axis.plot(x, y, color=color, marker='o')
            else:
                pass
            annotation = axis.annotate("", xy=(0,0), xytext=(20,20),textcoords="offset points",
                                       bbox=dict(boxstyle="round", fc="w"),
                                       arrowprops=dict(arrowstyle="->"))
            annotation.set_visible(False)
            self._data[_id]["data"] = [x, y]
            self._data[_id]["plot"] = plot
            self._data[_id]["annotation"] = annotation
            autoX, autoY = limits["autoX"], limits["autoY"]
            if autoX == 0 and autoY == 0:
                axis.set_xlim(limits["xmin"], limits["xmax"])
                axis.set_ylim(limits["ymin"], limits["ymax"])
            elif autoX == 1 and autoY == 0:
                limits["xmin"], limits["xmax"] = axis.get_xlim()
                axis.set_ylim(limits["ymin"], limits["ymax"])
            elif autoX == 0 and autoY == 1:
                axis.set_xlim(limits["xmin"], limits["xmax"])
                limits["ymin"], limits["ymax"] = axis.get_ylim()
            else:
                limits["xmin"], limits["xmax"] = axis.get_xlim()
                limits["ymin"], limits["ymax"] = axis.get_ylim()
            self._data[_id]["limits"] = limits
            self._canvas.draw()
        else:
            print(f"The graph with id = {_id} doesn't exist.")

    def setTickParams(self, _id=None, ax=None, labelrotation=90):
        axis = self._data[_id]["axis"]
        axis.tick_params(axis=ax, labelrotation=labelrotation)

    def update(self):
        #clear figure and reset axes list
        self._figure.clf()
        #determine which graphs are visible
        visibleIndices = [_id for _id, variable in self._plotVisibilityVariables.items() if variable.get()]
        visibleN = len(visibleIndices)
        if visibleN == 0:
            self._canvas.draw()
            return
        #calculate new grid size
        m = min(self._m, visibleN)
        n = (visibleN + m - 1) // m
        #add subplots for visible graphs
        _i = 1
        for _id in visibleIndices:
            axis = self._figure.add_subplot(n, m, _i)
            annotation = axis.annotate("", xy=(0,0), xytext=(20,20),textcoords="offset points",
                                       bbox=dict(boxstyle="round", fc="w"),
                                       arrowprops=dict(arrowstyle="->"))
            annotation.set_visible(False)
            _i += 1
            data = self._data[_id]["data"]
            title = self._data[_id]["title"]
            color = self._data[_id]["color"]
            limits = self._data[_id]["limits"]
            plotStyle = self._data[_id]["plotStyle"]
            self._data[_id] = {"axis" : axis, "data" : data, "plot" : None, "plotStyle" : plotStyle, "annotation" : annotation, "title" : title, "color" : color, "limits" : limits}
            axis.title.set_text(title)
            if data != None:
                x = data[0]
                y = data[1]
                if plotStyle == "scatter":
                    plot = axis.scatter(x, y, color=color)
                elif plotStyle == "line":
                    plot = axis.plot(x, y, color=color, marker='o')
                else:
                    pass
                self._data[_id]["plot"] = plot
                if limits: #fix this
                    autoX, autoY = limits["autoX"], limits["autoY"]
                    #print(f"auto limits X, Y {autoX}, {autoY}")
                    if autoX == 0 and autoY == 0:
                        axis.set_xlim(limits["xmin"], limits["xmax"])
                        axis.set_ylim(limits["ymin"], limits["ymax"])
                    elif autoX == 1 and autoY == 0:
                        limits["xmin"], limits["xmax"] = axis.get_xlim()
                        axis.set_ylim(limits["ymin"], limits["ymax"])
                    elif autoX == 0 and autoY == 1:
                        axis.set_xlim(limits["xmin"], limits["xmax"])
                        limits["ymin"], limits["ymax"] = axis.get_ylim()
                    else:
                        limits["xmin"], limits["xmax"] = axis.get_xlim()
                        limits["ymin"], limits["ymax"] = axis.get_ylim()
        self._canvas.draw()

    def clearFigure(self):
        #clear figure and reset axes list
        self._figure.clf()
        self._data = {}
        self._plotVisibilityVariables = {}
        self._canvas.draw()

    def clear(self):
        for child in self._checkbuttonFrame.winfo_children():
            child.destroy()
        self.clearFigure()

    def saveFigure(self, _id=None):
        if _id == None:
            _id = self._plotId.get()
        if _id not in list(self._data.keys()):
            print(f"Invalid id: {_id}")
            return
        print(f"Saving id {_id}")
        axis = self._data[_id]["axis"]
        title = self._data[_id]["title"]
        filename = f"Sensor_id_{_id} - {title}.png"
        extent = axis.get_window_extent().transformed(self._figure.dpi_scale_trans.inverted())
        extent = extent.expanded(1.2, 1.2) #pad the saved area by 20% in the x-direction and 20% in the y-direction
        self._figure.savefig(filename, bbox_inches=extent)

    def onResize(self, event):
        if self._resizeJob:
            self._master.after_cancel(self._resizeJob)
        self._resizeJob = self._master.after(200, self.resize)

    def resize(self):
        self._canvas.draw()
        self._resizeJob = None

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
    root.title("Dynamic Graph Grid Manager")
    app = GraphManager(root, n=1, m=1)
    root.mainloop()
