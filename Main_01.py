import tkinter as tk
import tkinter.font #on Win10 IDLE it seems that it's needed
from tkinter import ttk
from idlelib.tooltip import Hovertip
from Controller import Controller
from Sensor import Sensor
from QueueMessage import QueueMessage
from Graph import Graph
from GraphManager import GraphManager
import logging
import serial
import serial.tools.list_ports
from threading import Thread, Event
import queue
import random
import time
import datetime as dt
import pymysql
from PIL import Image
from PIL import ImageTk


#suppress irrelevant logging
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("Graph manager").setLevel(logging.WARNING)
logging.getLogger("Sensor 1").setLevel(logging.WARNING)
logging.getLogger("Sensor 2").setLevel(logging.WARNING)
logging.getLogger("Sensor 3").setLevel(logging.WARNING)
logging.getLogger("Sensor 4").setLevel(logging.WARNING)
logging.getLogger("Sensor 5").setLevel(logging.WARNING)
logging.getLogger("Sensor 6").setLevel(logging.WARNING)
logging.getLogger("Sensor 7").setLevel(logging.WARNING)

class App:
    def __init__(self, root):
        self.logger = logging.getLogger("Main")
        self.logger.info("Started main program.")
        self.root = root
        titleText = "Datalogger"
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self._resizeJob = None
        self.root.bind("<Configure>", self.onResize)

        self._databaseName = "DataloggerDB2"
        self._sensorsTableName = "sensors"        
        self._sensorsTableColumns = ["_id", "id", "name", "type", "quantity", "unit", "serialnumber"]
        self._actuatorsTableName = "actuators"
        self._actuatorsTableColumns = []
        
        self._defaultFont = tk.font.nametofont('TkTextFont').actual()
##        print(f"self._defaultFont: {self._defaultFont}")
        self._defaultFontFamily = self._defaultFont["family"]
        self._defaultFontSize = self._defaultFont["size"]
        self._defaultFontWeight = self._defaultFont["weight"]
        print(self._defaultFontFamily, self._defaultFontSize, self._defaultFontWeight)
        fontFamily2 = "Segoe UI"

        self._datetimeStrFormatHumanReadable = "%Y.%m.%d. %H:%M:%S"
        self._datetimeStrFormat = "%y%m%d%H%M%S"
        
        self.root.title(titleText)
        tk.Label(self.root, text=titleText, font=(self._defaultFontFamily, 12, "bold")).grid(row=0, column=0, sticky="W")

        statusFrame = tk.Frame(self.root)
        statusFrame.grid(row=1, column=0, sticky="W")
        tk.Label(statusFrame, text="Status:").grid(row=0, column=0, sticky="W")
        self.statusTextVariable = tk.StringVar()
        self.statusTextVariable.set("Status info appears here.")
        tk.Label(statusFrame, textvariable=self.statusTextVariable).grid(row=0, column=1, sticky="W")

        #set up variables
        self._databaseInfo = {"host" : "localhost", "user" : "root", "password" : "", "database" : "DataloggerDB2"}
        self._databaseConnection = None
        self._sqlPlaceholder = '%s' #'%s' for mysql, '?' for sqlite

        self._loopTimeout = 0.01 #seconds
        self._scanControllerTimeout = 5 #seconds
        self._deviceInitTimeout = 2 #seconds

        self._sensorsInfoList = []
        self._datatableList = []
        
        self._controllers = []
        self._sensorGUIinfo = {} #structure: {sensorid : {"value" : value, "inuse" : inuse}}
        self._commands = {}
        self._baudrates = [9600, 19200, 38400, 57600, 115200]
        self._baudrateVariable = tk.IntVar(value=self._baudrates[0])

        self._stopEvent = Event()
        self._queue = queue.Queue()
        self._measurementThread = None
        self._simulationThread = None
        
        self._lastMeasurementDatetime = dt.datetime(1970, 1, 1, 0, 0, 0)
        self._measurementDeltaTime = None

        self._measurementResults = {} #structure: {sensorid : [(), ()], ...}
        self._measurementResultsToPlot = {"global" : 24} #structure: {"global" : 24, sensorid : number, ...}
        self._measurementResultsToPlotUseGlobal = tk.IntVar(value=1)
        self._measurementDatetimes = {}
        self._graphs = {} #sensorid : graph

        self._renameControllerWindow = None
        self._editSensorWindow = None

        self._iconSizeX, self._iconSizeY = 20, 20
        self._images = {}
        self._images["edit_gear_icon"] = ImageTk.PhotoImage(Image.open("gear_icon.png").resize((self._iconSizeX, self._iconSizeY)))

        #create tabs
        self.tabControl = ttk.Notebook(self.root)
        self.tabControl.grid(row=2, column=0, sticky="NSEW")
        self._databaseTab = ttk.Frame(self.tabControl)
        self._settingsTab = ttk.Frame(self.tabControl)
        self._monitorTab = ttk.Frame(self.tabControl)
        self._imagesTab = ttk.Frame(self.tabControl)
        self._sensorsTab = ttk.Frame(self.tabControl)
        self.tabControl.add(self._databaseTab, text="Database")
        self.tabControl.add(self._settingsTab, text="Settings")
        self.tabControl.add(self._monitorTab, text="Monitor")
        self.tabControl.add(self._imagesTab, text="Images")
        self.tabControl.add(self._sensorsTab, text="Sensors")

        #set up individual tabs
        #settings
        #---------------
        tk.Button(self._settingsTab, text="Scan controller units", command=self.scanControllerUnits).grid(row=0, column=0)
        self.measurementLoopButton = tk.Button(self._settingsTab, text="Start measurement", command=self.handleMeasurementLoop)
        self.measurementLoopButton.grid(row=0, column=1)
        self.simulationLoopButton = tk.Button(self._settingsTab, text="Start simulation", command=self.handleSimulationLoop)
        self.simulationLoopButton.grid(row=0, column=2)
        #---------------
        self._measurementLoopSettingsFrame = tk.Frame(self._settingsTab)
        self._measurementLoopSettingsFrame.grid(row=1, column=0, columnspan=3, sticky="W")
        #
        tk.Label(self._measurementLoopSettingsFrame, text="Delta time").grid(row=0, column=0)
        _deltaTimeFrame = tk.Frame(self._measurementLoopSettingsFrame)
        _deltaTimeFrame.grid(row=0, column=1)
        self._deltaTimeSecondsVariable = tk.IntVar(value=10)
        self._deltaTimeMinutesVariable = tk.IntVar(value=0)
        self._deltaTimeHoursVariable = tk.IntVar(value=0)
        tk.Label(_deltaTimeFrame, text="h").grid(row=0, column=0)
        tk.Label(_deltaTimeFrame, text=":").grid(row=0, column=1)
        tk.Label(_deltaTimeFrame, text="m").grid(row=0, column=2)
        tk.Label(_deltaTimeFrame, text=":").grid(row=0, column=3)
        tk.Label(_deltaTimeFrame, text="s").grid(row=0, column=4)
        tk.Entry(_deltaTimeFrame, textvariable=self._deltaTimeHoursVariable, width=4).grid(row=1, column=0)
        tk.Entry(_deltaTimeFrame, textvariable=self._deltaTimeMinutesVariable, width=4).grid(row=1, column=2)
        tk.Entry(_deltaTimeFrame, textvariable=self._deltaTimeSecondsVariable, width=4).grid(row=1, column=4)
        #
        tk.Label(self._measurementLoopSettingsFrame, text="Number of values\nto plot").grid(row=1, column=0)
        self._numberOfValuesToPlotGlobalVariable = tk.IntVar(value=self._measurementResultsToPlot["global"])
        _numberOfValuesToPlotFrame = tk.Frame(self._measurementLoopSettingsFrame)
        _numberOfValuesToPlotFrame.grid(row=1, column=1)
        tk.Entry(_numberOfValuesToPlotFrame, textvariable=self._numberOfValuesToPlotGlobalVariable, width=6).grid(row=0, column=0)
        tk.Checkbutton(_numberOfValuesToPlotFrame, text="Use global", variable=self._measurementResultsToPlotUseGlobal, command=self.numberOfValuesToPlotCheckbuttonClicked).grid(row=0, column=1)
        #
        tk.Label(self._measurementLoopSettingsFrame, text="Baud rate").grid(row=2, column=0)
        #---------------
        self.controllersFrame = tk.Frame(self._settingsTab)
        self.controllersFrame.grid(row=2, column=0, columnspan=3, sticky="W")

        #database
        tk.Button(self._databaseTab, text="Connect to database", command=self.connectoToDatabase).grid(row=0, column=0)
        frame1 = tk.Frame(self._databaseTab)
        frame1.grid(row=0, column=1)
        tk.Label(frame1, text=self._databaseName).grid(row=0, column=0)
        self._databaseConnectionStateCanvas = tk.Canvas(frame1, width=10, height=10, bg="red")
        self._databaseConnectionStateCanvas.grid(row=0, column=1)
        Hovertip(self._databaseConnectionStateCanvas, "Red: not connected.\nGreen: connected.")
        
        tk.Label(self._databaseTab, text="Select datatable").grid(row=1, column=0)
        self._selectDatatableVariable = tk.StringVar()
        self._selectDatatableList = ["Create new"]
        self._datatableOptionMenuToUse = tk.OptionMenu(self._databaseTab, self._selectDatatableVariable, *self._selectDatatableList, command=self.selectDatatableEvent)
        self._datatableOptionMenuToUse.grid(row=1, column=1)

        #monitor
        self._graphManager = GraphManager(self._monitorTab, n=1, m=1, mode="normal") #n=1 and m=1 are the default (minimum) values

        #sensors
        label = tk.Label(self._sensorsTab, text="Sensor info")
        label.grid(row=0, column=0)
        Hovertip(label, "Connect to database to show sensors info here.")
        self._sensorsInfoFrame = tk.Frame(self._sensorsTab)
        self._sensorsInfoFrame.grid(row=1, column=0)
        self._actuatorsInfoFrame = tk.Frame(self._sensorsTab)
        self._actuatorsInfoFrame.grid(row=2, column=0)
        
        #start periodic check of the queue
        self.root.after(100, self.processQueue)

    def selectDatatableEvent(self, event):
        if self._databaseConnection == None:
            text = "Selecting or creating datatable is not possible. No database connection."
            tk.messagebox.showinfo("Info", text)
            self.logger.info(text)
            return False
        selectedElement = self._selectDatatableVariable.get()
##        print(f"Selected element: {selectedElement}")
        if selectedElement == "Create new":
            self._createDatatableWindow = tk.Toplevel()
            self._createDatatableWindow.protocol("WM_DELETE_WINDOW", self.closeCreateDatatableWindow)
            self._createDatatableWindow.title("Create datatable")
            tk.Label(self._createDatatableWindow, text="Create datatable").grid(row=0, column=0)
            frame2 = tk.Frame(self._createDatatableWindow)
            frame2.grid(row=0, column=1)
            self._newDatatableVariable = tk.StringVar()
            self._datatableNameEntry = tk.Entry(frame2, width=30, textvariable=self._newDatatableVariable)
            self._datatableNameEntry.grid(row=0, column=0)
            self._autoNameDatatableVariable = tk.IntVar()
            autoNameDatatableCheckbutton = tk.Checkbutton(frame2, text="Auto name", variable=self._autoNameDatatableVariable, command=self.autoNameDatatableCheckbuttonClicked)
            autoNameDatatableCheckbutton.grid(row=0, column=1)
            Hovertip(autoNameDatatableCheckbutton, "Enable to generate a name for the datatable.")
            tk.Button(self._createDatatableWindow, text="Create new datatable", command=self.createDatatable).grid(row=1, column=0, columnspan=2)
    
    def closeCreateDatatableWindow(self):
        self._createDatatableWindow.destroy()

    def createDatatable(self):
        newDatatable = self._newDatatableVariable.get()
        if newDatatable != "":
            if self.saveNewDatatable(newDatatable):
                self._selectDatatableList.append(newDatatable)
##                print(self._selectDatatableList)
                queueMessage = QueueMessage("getDatatables", self._selectDatatableList) #modify QueueMessage to handle objects, not just text
                self._queue.put(queueMessage)
            else:
                pass
            self._createDatatableWindow.destroy()
        else:
            self.log("guiStateInfo", f"New datatable name {newDatatable} is not valid.")
            pass

    def saveNewDatatable(self, newDatatable):
        if self._databaseConnection == None:
            self.logger.info("Saving is not possible. No database connection.")
            return False
        sqlQuery = f"CREATE TABLE {newDatatable} LIKE measurements"
        print(f"sqlQuery: {sqlQuery}")
        cursor = self._databaseConnection.cursor()
        cursor.execute(sqlQuery)
        self._databaseConnection.commit()
        return True

    def autoNameDatatableCheckbuttonClicked(self):
        if self._autoNameDatatableVariable.get():
            self._datatableNameEntry["state"] = "disabled"
            newDatatableName = "measurements_" + dt.datetime.now().strftime(self._datetimeStrFormat)
            self._newDatatableVariable.set(newDatatableName)
        else:
            self._datatableNameEntry["state"] = "normal"

    def numberOfValuesToPlotCheckbuttonClicked(self):
        if self._measurementResultsToPlotUseGlobal.get():
            print(f"Values to plot: {self._numberOfValuesToPlotGlobalVariable.get()}")
        else:
            pass

    def onResize(self, event):
        if self._resizeJob:
            self.root.after_cancel(self._resizeJob)
        self._resizeJob = self.root.after(200, self.resize)

    def resize(self):
##        self._canvas.draw()
        self._resizeJob = None

    def connectoToDatabase(self):
        text = "Connecting to database..."
        self.logger.info(text)
        queueMessage = QueueMessage("guiStateInfo", text)
        self._queue.put(queueMessage)
        self._databaseConnection = None
        self._databaseConnectionStateCanvas.config(bg="red")
        host, user, password, database = self._databaseInfo["host"], self._databaseInfo["user"], self._databaseInfo["password"], self._databaseInfo["database"]
        try:
            self._databaseConnection = pymysql.connect(host=host, user=user, password=password, database=database)
            self._databaseConnectionStateCanvas.config(bg="green")
            text = "Successfully connected to database."
        except Exception as e:
            text = f"Error during connection: {e}."
        self.logger.info(text)
        queueMessage = QueueMessage("guiStateInfo", text)
        self._queue.put(queueMessage)
        self.getDatatables()
        self.getSensorsInfo()
        self.getActuatorsInfo()

    def log(self, _type, _text):
        self.logger.info(_text)
        queueMessage = QueueMessage(_type, _text)
        self._queue.put(queueMessage)

    def getDatatables(self):
        #handles the query, then sends message to the GUI to handle the rest
        if self._databaseConnection == None:
            self.log("guiStateInfo", "Getting datatables is not possible. No database connection.")
            return
        self.log("guiStateInfo", "Getting datatables from database...")
        sqlQuery = "SELECT table_name FROM information_schema.tables WHERE table_schema = " + self._sqlPlaceholder
        parameters = (self._databaseName, )
        cursor = self._databaseConnection.cursor()
        cursor.execute(sqlQuery, parameters)
        self._datatableList = [element[0] for element in cursor.fetchall()]
##        self._datatableList.insert(0, "Create new")
        print(self._datatableList)
        queueMessage = QueueMessage("getDatatables", self._datatableList) #modify QueueMessage to handle objects, not just text
        self._queue.put(queueMessage)

    def getSensorsInfo(self):
        #sensors
        #handles the query, then sends message to the GUI to handle the rest
        if self._databaseConnection == None:
            self.log("guiStateInfo", "Getting info of sensors is not possible. No database connection.")
            return
        self.log("guiStateInfo", "Getting info of sensors from database...")
        self._sensorsInfoList = []
        sqlQuery = f"SELECT * FROM {self._sensorsTableName}"
        cursor = self._databaseConnection.cursor()
        cursor.execute(sqlQuery)
        self._sensorsInfoList = [element for element in cursor.fetchall()]
        print(self._sensorsInfoList)
        queueMessage = QueueMessage("getSensorsInfo", self._sensorsInfoList) #modify QueueMessage to handle objects, not just text
        self._queue.put(queueMessage)

    def getActuatorsInfo(self):
        #pumps, motors, etc.
        #handles the query, then sends message to the GUI to handle the rest
        if self._databaseConnection == None:
            self.log("guiStateInfo", "Getting info of actuators is not possible. No database connection.")
            return
        self.log("guiStateInfo", "Getting info of sensors from database...")
        self._actuatorsInfoList = []
        sqlQuery = f"SELECT * FROM {self._actuatorsTableName}"
        cursor = self._databaseConnection.cursor()
        cursor.execute(sqlQuery)
        self._actuatorsInfoList = [element for element in cursor.fetchall()]
        print(self._actuatorsInfoList)
        queueMessage = QueueMessage("getActuatorsInfo", self._actuatorsInfoList) #modify QueueMessage to handle objects, not just text
        self._queue.put(queueMessage)

    def updateActuatorsInfoFrame(self):
        print("self.updateActuatorsInfoFrame() called.")
        if self._actuatorsInfoList:
            for child in self._actuatorsInfoFrame.winfo_children():
                child.destroy()
        else:
            pass

    def updateSensorsInfoFrame(self):
        print("self.updateSensorsInfoFrame() called.")
        if self._sensorsInfoList:
            for child in self._sensorsInfoFrame.winfo_children():
                child.destroy()
            _r = 0
            font = (self._defaultFontFamily, 9, "bold")
            tk.Label(self._sensorsInfoFrame, text="ID", font=font).grid(row=_r, column=0)
            tk.Label(self._sensorsInfoFrame, text="Name", font=font).grid(row=_r, column=1)
            tk.Label(self._sensorsInfoFrame, text="Type", font=font).grid(row=_r, column=2)
            tk.Label(self._sensorsInfoFrame, text="Quantity", font=font).grid(row=_r, column=3)
            tk.Label(self._sensorsInfoFrame, text="Unit", font=font).grid(row=_r, column=4)
            tk.Label(self._sensorsInfoFrame, text="Serial number", font=font).grid(row=_r, column=5)
            tk.Label(self._sensorsInfoFrame, text="Edit", font=font).grid(row=_r, column=6)
            _r += 1
            for sensorInfo in self._sensorsInfoList:
                #sensor infos
                sensorID = sensorInfo[0]
                sensorName = sensorInfo[1]
                sensorType = sensorInfo[2]
                sensorQuantity = sensorInfo[3]
                sensorUnit = sensorInfo[4]
                sensorSerialnumber = sensorInfo[5]
                #labels and editing
                tk.Label(self._sensorsInfoFrame, text=str(sensorID)).grid(row=_r, column=0)
                tk.Label(self._sensorsInfoFrame, text=str(sensorName)).grid(row=_r, column=1)
                tk.Label(self._sensorsInfoFrame, text=str(sensorType)).grid(row=_r, column=2)
                tk.Label(self._sensorsInfoFrame, text=str(sensorQuantity)).grid(row=_r, column=3)
                tk.Label(self._sensorsInfoFrame, text=str(sensorUnit)).grid(row=_r, column=4)
                tk.Label(self._sensorsInfoFrame, text=str(sensorSerialnumber)).grid(row=_r, column=5)
                tk.Button(self._sensorsInfoFrame, height=20, width=20, image=self._images["edit_gear_icon"], command=lambda sensorID=sensorID: self.editSensor(sensorID)).grid(row=_r, column=6)
                _r += 1
        else:
            pass

    def measureSensor(self, controllerID, sensorID):
        if not self._controllers:
            return
        text = f"Measuring sensor with id {sensorID} in controller {controllerID}."
        self.log("guiStateInfo", text)
        controller = self._controllers[cID]
        command = str(sensorID)# + '\n' #where to add the line ending? Sensor.measure() adds it
        result = controller.measure(command)
        print(result)

    def editSensor(self, sensorID):
        if self._editSensorWindow is not None:
            return
        text = f"Editing sensor with id {sensorID}."
        print(text)
        self._editSensorWindow = tk.Toplevel()
        self._editSensorWindow.protocol("WM_DELETE_WINDOW", self.closeEditSensorWindow)
        self._editSensorWindow.title("Edit sensor")
        font = (self._defaultFontFamily, 9, "bold")
        #labels
        tk.Label(self._editSensorWindow, text="ID", font=font).grid(row=0, column=0)
        tk.Label(self._editSensorWindow, text="Name", font=font).grid(row=1, column=0)
        tk.Label(self._editSensorWindow, text="Type", font=font).grid(row=2, column=0)
        tk.Label(self._editSensorWindow, text="Quantity", font=font).grid(row=3, column=0)
        tk.Label(self._editSensorWindow, text="Unit", font=font).grid(row=4, column=0)
        tk.Label(self._editSensorWindow, text="Serial number", font=font).grid(row=5, column=0)
        #entries and variables
        tk.Entry(self._editSensorWindow, state="disabled").grid(row=0, column=1)
        tk.Entry(self._editSensorWindow).grid(row=1, column=1)
        tk.Entry(self._editSensorWindow).grid(row=2, column=1)
        tk.Entry(self._editSensorWindow).grid(row=3, column=1)
        tk.Entry(self._editSensorWindow).grid(row=4, column=1)
        tk.Entry(self._editSensorWindow).grid(row=5, column=1)
        tk.Button(self._editSensorWindow, text="Reset changes", command=None).grid(row=6, column=0, columnspan=2)        
        tk.Button(self._editSensorWindow, text="Apply changes", command=lambda _id=sensorID: self.applySensorInfo(_id)).grid(row=7, column=0, columnspan=2)
        #close on apply
        #self.closeEditSensorWindow()

    def applySensorInfo(self, _id):
        #save into sensors table
        sqlQuery = "UPDATE"
        pass

    def closeEditSensorWindow(self):
        if self._editSensorWindow:
            self._editSensorWindow.destroy()
            self._editSensorWindow = None
    
    def scanControllerUnits(self):
        if self._measurementThread is not None:
            if self._measurementThread.is_alive:
                text = "Measurement is already running."
                self.logger.info(text)
                tk.messagebox.showinfo("Info", text)
                return
        if self._simulationThread is not None:
            if self._simulationThread.is_alive():
                text = "Simulation is already running."
                self.logger.info(text)
                tk.messagebox.showinfo("Info", text)
                return
        self.logger.info("Scanning controller units...")
        self._controllers = []
        #list all serial ports
        ports = serial.tools.list_ports.comports()
        self.logger.info(f"Found ports: {[p.device for p in ports]}")
        for port_info in ports:
            port = port_info.device
##            baudrate = self._baudrateVariable.get()
            for baudrate in self._baudrates:
                self.logger.info(f"Trying port {port} with baudrate {baudrate}...")
                serialConnection = None
                try:
                    serialConnection = serial.Serial(port, baudrate=baudrate, timeout=1, write_timeout=self._scanControllerTimeout)
                except (serial.SerialException, ValueError) as e:
                    self.logger.info(f"Error on port {port}: {e}")
                if serialConnection == None:
                    continue
                time.sleep(self._deviceInitTimeout) #wait for device to initialize
                command = "GETID" + '\n'
                serialConnection.write(command.encode(encoding="utf-8", errors="strict"))
                controller_id_raw = serialConnection.readline().decode().strip() #decode("utf-8", "ignore")
                self.logger.info(f"Raw response on serial port {port} with baudrate {baudrate}: controller_id_raw = {controller_id_raw}.")
                if controller_id_raw == "":
                    continue
                controller_id_raw = int(controller_id_raw)
                if isinstance(controller_id_raw, int):
                    controller = Controller(controller_id_raw)
                    controller.setPort(port)
                    controller.setBaudrate(baudrate)
                    self._controllers.append(controller)
                    command = "GETIDS" + '\n'
                    serialConnection.write(command.encode(encoding="utf-8", errors="strict"))
                    sensor_ids_raw = serialConnection.readline().decode().strip() #decode("utf-8", "ignore")
                    sensor_ids = sensor_ids_raw.split(",")
                    #print(f"sensor_ids: {sensor_ids}")
                    self.logger.info(f"Creating sensors for controller with id {controller.getID()}...")
                    for sensor_id in sensor_ids:
                        sensor_id = int(sensor_id)
                        sensor = Sensor(sensor_id)
                        #get all the necessary sensor info from the database, based on the sensor_id
                        sensorInfo = ()
                        for element in self._sensorsInfoList:
                            if element[0] == sensor_id:
                                sensorInfo = element
                                break
                        #print(f"sensorInfo: {sensorInfo}")
                        if sensorInfo:
                            self.logger.info(f"Setting info for sensor with id {sensor_id}.")
                            sensor.setName(sensorInfo[1])
                            sensor.setType(sensorInfo[2])
                            sensor.setQuantity(sensorInfo[3])
                            sensor.setUnit(sensorInfo[4])
                            sensor.setSerialNumber(sensorInfo[5])
                        else:
                            #sensor info not found based on it's id
                            self.logger.info(f"No info for sensor with id {sensor_id}")
                            pass
                        controller.addSensors(sensor)
                    break
                else:
                    pass
        if len(ports) == 0:
            text = "No serial ports detected."
            self.logger.info(text)
            tk.messagebox.showinfo("Info", text)
        else:
            text = "Creating graphs and sensor interface."
            self.logger.info(text)
            self.createGraphs()
            self.updateControllersFrame()

    def createGraphs(self):
        self._graphManager.clearFigure()
        if self._controllers:
            for controller in self._controllers:
                for sensor in controller.getSensors():
                    _id = sensor.getID()
                    _name = sensor.getName()
                    self._measurementResults[_id] = []
                    self._measurementDatetimes[_id] = []
                    self._graphManager.addGraph(_id=_id, _title=_name)

    def handleMeasurementLoop(self):
        self.logger.info("Handling measurement loop.")
        if not self._controllers:
            text = "There are no controller units."
            self.logger.info(text)
            tk.messagebox.showinfo("Info", text)
            return
##        self.updateControllersFrame()
        if self._measurementThread is None or not self._measurementThread.is_alive():
            if self._simulationThread is None or not self._simulationThread.is_alive():
                self._stopEvent.clear()
                self._measurementThread = Thread(target=self.measurementLoop, daemon=True)
                self._measurementThread.start()
                self.measurementLoopButton["text"] = "Stop measurement"
                ######## determine, which name/setting to use
##                self._currentDatatableName = self._newDatatableVariable.get()
##                self._currentDatatableName = self._selectDatatableVariable.get()
                ########
            else:
                text = "Simulation is already running."
                self.logger.info(text)
                tk.messagebox.showinfo("Info", text)
        else:
            self.stopMeasurementLoop()
            self.measurementLoopButton["text"] = "Start measurement"
        
    def measurementLoop(self):
        self.logger.info("Measurement loop started.")
        while not self._stopEvent.is_set():
            self._currentTime = dt.datetime.now()
            self._measurementDeltaTime = dt.timedelta(hours=self._deltaTimeHoursVariable.get(),
                                                      minutes = self._deltaTimeMinutesVariable.get(),
                                                      seconds=self._deltaTimeSecondsVariable.get())
##            print(f"self._measurementDeltaTime: {self._measurementDeltaTime}")
            if self._measurementDeltaTime.total_seconds() == 0: #if the current delta time is 0
                self._deltaTimeSecondsVariable.set(10) #give some more time for the user to set delta time
                continue
                #self._measurementDeltaTime = dt.timedelta(seconds=10) #give some more time for the user to set delta time
            if (self._currentTime - self._lastMeasurementDatetime > self._measurementDeltaTime):
                self._lastMeasurementDatetime = dt.datetime.now()
                _lastMeasurementDatetimeString = self._lastMeasurementDatetime.strftime(self._datetimeStrFormatHumanReadable)
                queueMessage = QueueMessage("newDatetimeMeasurement", _lastMeasurementDatetimeString)
                self._queue.put(queueMessage)
                if self._controllers:
                    for controller in self._controllers:
                        controller_id = controller.getID()
                        self.logger.info(f"Measuring controller with id {controller_id}.")
                        command = str(0)# + '\n' #where to add the line ending? Sensor.measure() adds it
                        result = controller.measure(command) #send 0 to measure all sensors at once
##                        print(f"result: {result}")
                        for sensor_id, value in result.items():
                            #sensor_id: string or int?
                            queueMessage = QueueMessage("newSensorValue", [int(sensor_id), self._lastMeasurementDatetime, value])
                            self._queue.put(queueMessage)
                else:
                    self.logger.info("There are no available controller units.")
            else:
                pass
            time.sleep(self._loopTimeout) #sleep for a bit, parameter is in seconds

    def stopMeasurementLoop(self):
        self._stopEvent.set()
        self._measurementThread = None
        self.measurementLoopButton["text"] = "Start measurement"

    def handleSimulationLoop(self):
        self.logger.info("Handling simulation loop.")
        self._controllers = []
        if self._simulationThread is None or not self._simulationThread.is_alive():
            if self._measurementThread is None or not self._measurementThread.is_alive():
                self.simulationLoopButton["text"] = "Stop simulation"
                controller1 = Controller(1, "SimCon1")
                sensor1 = Sensor(1, name="T1", _type="simulated", quantity="temperature", unit="C")
                sensor2 = Sensor(2, name="RH1", _type="simulated", quantity="relative humidity", unit="%")
                controller1.addSensors([sensor1, sensor2])
                self._controllers.append(controller1)
                self.updateControllersFrame()
                self.createGraphs()
                self._stopEvent.clear()
                self._simulationThread = Thread(target=self.simulationLoop, daemon=True)
                self._simulationThread.start()
            else:
                text = "Measurement is already running."
                self.logger.info(text)
                tk.messagebox.showinfo("Info", text)
        else:
            self.stopSimulationLoop()
            self.simulationLoopButton["text"] = "Start simulation"

    def simulationLoop(self):
        self.logger.info("Simulation loop started.")
        while not self._stopEvent.is_set():
            self._currentTime = dt.datetime.now()
            self._measurementDeltaTime = dt.timedelta(hours=self._deltaTimeHoursVariable.get(),
                                                      minutes = self._deltaTimeMinutesVariable.get(),
                                                      seconds=self._deltaTimeSecondsVariable.get())
##            print(f"self._measurementDeltaTime: {self._measurementDeltaTime}")
            if self._measurementDeltaTime.total_seconds() == 0: #if the current delta time is 0
                self._deltaTimeSecondsVariable.set(10) #give some more time for the user to set delta time
                continue
                #self._measurementDeltaTime = dt.timedelta(seconds=10) #give some more time for the user to set delta time
            if (self._currentTime - self._lastMeasurementDatetime > self._measurementDeltaTime):
                self._lastMeasurementDatetime = dt.datetime.now()
                _lastMeasurementDatetimeString = self._lastMeasurementDatetime.strftime(self._datetimeStrFormatHumanReadable)
                queueMessage = QueueMessage("newDatetimeMeasurement", _lastMeasurementDatetimeString)
                self._queue.put(queueMessage)
                if self._controllers:
                    for controller in self._controllers:
                        for sensor in controller.getSensors():
                            value = random.randint(0, 100)
                            queueMessage = QueueMessage("newSensorValue", [sensor.getID(), self._lastMeasurementDatetime, value])
                            self._queue.put(queueMessage)
                else:
                    self.logger.info("There are no available controller units.") #should'n happen in simulation mode
            else:
                pass
            time.sleep(self._loopTimeout) #sleep for a bit, parameter is in seconds

    def stopSimulationLoop(self):
        self._stopEvent.set()
        self._simulationThread = None
        self.simulationLoopButton["text"] = "Start simulation"

    def traceVariable(self, variable):
        try:
            value = variable.get()
        except:
##            print("Invalid value.")
            variable.set(0)

    def processQueue(self):
        while not self._queue.empty():
            queueElement = self._queue.get()
            if isinstance(queueElement, QueueMessage):
                _type, _text = queueElement.getType(), queueElement.getText()
##                print(_type, _text)
                if _type == "newSensorValue":
                    _id, _measurementDatetime, _value = _text[0], _text[1], _text[2] 
##                    print(_type, _id, _value)
                    self._sensorGUIinfo[_id]["valueVariable"].set(str(_value))
                    data = [_id, _value]
                    self.saveMeasurementData(data)
                    self._measurementResults[_id].append(_value) #################################
                    self._measurementDatetimes[_id].append(_measurementDatetime) #################################
                    #x = list(range(0, len(y))) #create a list of integers as labels, was used for testing
                    x = self._measurementDatetimes[_id]
                    y = self._measurementResults[_id]
                    ############### double check this solution
                    L, N = len(x), self._numberOfValuesToPlotGlobalVariable.get()
                    x = x[L - N:]
                    y = y[L - N:]
                    ###############
                    self._graphManager.plot(_id=_id, data=(x, y))
                    self._graphManager.setTickParams(_id=_id, ax='x', labelrotation=45)
                elif _type == "guiStateInfo":
                    self.statusTextVariable.set(_text)
                elif _type == "newDatetimeMeasurement":
                    for _id, guiinfo in self._sensorGUIinfo.items():
                        guiinfo["datetimeVariable"].set(_text)
                elif _type == "getDatatables":
                    print(f"_text: {_text}")
                    #update self._datatableOptionMenuToUse
                    if _text[0] != "Create new":
                        self._selectDatatableList = ["Create new", *_text]
                    else:
                        self._selectDatatableList = _text
                    print(f"self._selectDatatableList: {self._selectDatatableList}")
                    self._datatableOptionMenuToUse.destroy()
                    self._datatableOptionMenuToUse = tk.OptionMenu(self._databaseTab, self._selectDatatableVariable, *self._selectDatatableList, command=self.selectDatatableEvent)
                    self._datatableOptionMenuToUse.grid(row=1, column=1)
                elif _type == "getSensorsInfo":
                    print(_text)
                    self.updateSensorsInfoFrame()
                elif _type == "getActuatorsInfo":
                    print(_text)
                    self.updateActuatorsInfoFrame()
                else:
                    pass
            else:
                pass
        self.root.after(100, self.processQueue)

    def renameControllerEvent(self, event, controller):
        if self._renameControllerWindow is not None:
            return
        controllerID = controller.getID()
        print(f"Rename controller with id {controllerID}")
        self._renameControllerWindow = tk.Toplevel()
        self._renameControllerWindow.protocol("WM_DELETE_WINDOW", self.closeRenameController)
        self._renameControllerWindow.title("Rename controller")
        tk.Label(self._renameControllerWindow, text=f"Name of controller {controllerID}:").grid(row=0, column=0)
        currentControllerName = controller.getName()
        self._controllerNameVariable = tk.StringVar()
        self._controllerNameVariable.set(currentControllerName)
        tk.Entry(self._renameControllerWindow, textvariable=self._controllerNameVariable).grid(row=0, column=1)
        tk.Button(self._renameControllerWindow, text="Set controller name", command=lambda controller=controller: self.applyControllerSettings(controller)).grid(row=1, column=0, columnspan=2)
        
    def applyControllerSettings(self, controller):
        newControllerName = self._controllerNameVariable.get()
        controller.setName(newControllerName)
        newLabelText = "Controller " + str(controller.getID()) + " - " + str(controller.getName())
        self._controllerIDandNameLabel["text"] = newLabelText
        self._renameControllerWindow.destroy()

    def closeRenameController(self):
        self._renameControllerWindow.destroy()

    def updateControllersFrame(self, newSensorValues=None):
##        print(self._controllers)
        if not self._controllers:
            self.logger.info("There are no available or simulated controller units.")
            return
        else:
            #clear structure holding measurement information for the GUI
            self._sensorGUIinfo = {}
            #clear the controllersFrame
            for child in self.controllersFrame.winfo_children():
                child.destroy()
            #populate the controllersFrame
            r_ = 0
            for controller in self._controllers:
                controllerID = controller.getID()
                conrollerName = controller.getName()
                controllerText = "Controller " + str(controllerID) + " - " + str(conrollerName)
                font = (self._defaultFontFamily, 11, "bold")
                self._controllerIDandNameLabel = tk.Label(self.controllersFrame, text=controllerText, font=font)
                self._controllerIDandNameLabel.grid(row=r_, column=0, columnspan=7, sticky="W")
                self._controllerIDandNameLabel.bind("<Button-1>", lambda e, controller=controller: self.renameControllerEvent(e, controller))
                Hovertip(self._controllerIDandNameLabel, "Click to change controller name.\nChanging it won't affect the info stored in the database.")
                r_ += 1
                font = (self._defaultFontFamily, 9, "bold")
                tk.Label(self.controllersFrame, text="Sensor ID", font=font).grid(row=r_, column=0)
                tk.Label(self.controllersFrame, text="Sensor name", font=font).grid(row=r_, column=1)
                tk.Label(self.controllersFrame, text="Quantity", font=font).grid(row=r_, column=2)
                tk.Label(self.controllersFrame, text="Value", font=font).grid(row=r_, column=3)
                tk.Label(self.controllersFrame, text="Unit", font=font).grid(row=r_, column=4)
                tk.Label(self.controllersFrame, text="In use", font=font).grid(row=r_, column=5)
                label = tk.Label(self.controllersFrame, text="Datetime", font=font)
                label.grid(row=r_, column=6)
                Hovertip(label, "Datetime of the last measurement.")
                tk.Label(self.controllersFrame, text="Measure").grid(row=r_, column=7)
                r_ += 1
                for sensor in controller.getSensors():
                    sensorID = sensor.getID()
                    _sensorDictionary = {} #add variables to this dictionary
                    tk.Label(self.controllersFrame, text=str(sensorID)).grid(row=r_, column=0)
                    tk.Label(self.controllersFrame, text=str(sensor.getName())).grid(row=r_, column=1)
                    tk.Label(self.controllersFrame, text=str(sensor.getQuantity())).grid(row=r_, column=2)
                    valueVariable = tk.StringVar()
                    valueVariable.set("-")
                    tk.Label(self.controllersFrame, textvariable=valueVariable).grid(row=r_, column=3)
                    tk.Label(self.controllersFrame, text=str(sensor.getUnit())).grid(row=r_, column=4)
                    inuseVariable = tk.IntVar()
                    tk.Checkbutton(self.controllersFrame, variable=inuseVariable).grid(row=r_, column=5)
                    datetimeVariable = tk.StringVar()
                    datetimeVariable.set("1970.01.01. 00:00:00")
                    tk.Label(self.controllersFrame, textvariable=datetimeVariable).grid(row=r_, column=6)
                    tk.Button(self.controllersFrame, text="Measure", command=lambda c=controllerID, s=sensorID: self.measureSensor(c, s)).grid(row=r_, column=7)
                    r_ += 1
                    _sensorDictionary["valueVariable"] = valueVariable
                    _sensorDictionary["inuseVariable"] = inuseVariable
                    _sensorDictionary["datetimeVariable"] = datetimeVariable
                    self._sensorGUIinfo[sensorID] = _sensorDictionary

    def saveMeasurementData(self, data):
        if self._databaseConnection == None:
            self.logger.info("Saving is not possible. No database connection.")
            return
        if not isinstance(data, list):
            self.logger.info("Data to be saved is not a list.")
            return
        self.logger.info(f"Saving data: [id, value] = {data}.")
        self._currentDatatableName = self._selectDatatableVariable.get() #"measurements"
##        print(f"self._currentDatatableName: {self._currentDatatableName}")
        if self._currentDatatableName in ["", "Create new"]:
            self.logger.info(f"Saving is not possible. Invalid datatable selected: {self._currentDatatableName}.")
            return
        if self._simulationThread is not None:
            if self._simulationThread.is_alive():
                sqlQuery = f"INSERT INTO {self._currentDatatableName} (sensorid, value) VALUES (" + self._sqlPlaceholder + "," + self._sqlPlaceholder + ")"
                cursor = self._databaseConnection.cursor()
                try:
                    cursor.execute(sqlQuery, data)
                except Exception as e:
                    self.logger.info(f"Saving is not possible. An error occurred: {e}.")
                    return
                self._databaseConnection.commit()
        elif self._measurementThread is not None:
            if self._measurementThread.is_alive():
                sqlQuery = f"INSERT INTO {self._currentDatatableName} (sensorid, value) VALUES (" + self._sqlPlaceholder + "," + self._sqlPlaceholder + ")"
                cursor = self._databaseConnection.cursor()
                try:
                    cursor.execute(sqlQuery, data)
                except Exception as e:
                    self.logger.info(f"Saving is not possible. An error occurred: {e}.")
                    return
                self._databaseConnection.commit()
        else:
            pass

if __name__ == "__main__":
    # Configure logging once, in your main program
    logging.basicConfig(
        level=logging.DEBUG,  # Or INFO in production
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        handlers=[
            logging.FileHandler("log1.log"),
            logging.StreamHandler()
        ]
    )
    
    root = tk.Tk()
    app = App(root)
    root.mainloop()
