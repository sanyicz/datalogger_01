import time
import serial
import logging
from Sensor import Sensor

class Controller:
    def __init__(self, ID, name="NotSet", port="NotSet", baudrate=9600, timeout=1):
        self.logger = logging.getLogger(f"Controller {ID}")
        self.logger.info(f"Created controller with id {ID} and name {name}.")
        self._id = ID
        self._name = name
        self._port = port #port is a device name: depending on operating system. e.g. /dev/ttyUSB0 on GNU/Linux or COM3 on Windows.
        self._baudrate = baudrate
        self._timeout = timeout
        self._serialConnection = None
        self._sensors = []

        self.connect()

    def getID(self):
        return self._id

    def setID(self, ID):
        if isinstance(ID, int):
            self.logger.debug(f"Setting id of controller with id {self._id} to {ID}.")
            self._id = ID
        else:
            pass

    def getName(self):
        return self._name

    def setName(self, name):
        self.logger.debug(f"Setting name of controller with id {self._id} to {name}.")
        self._name = name

    def getPort(self):
        return self._port

    def setPort(self, port):
        self._port = port

    def getBaudrate(self):
        return self._baudrate

    def setBaudrate(self, baudrate):
        if isinstance(baudrate, int):
            self._baudrate = baudrate
        else:
            pass

    def connect(self):
        """Establish serial connection."""
        try:
            self._serialConnection = serial.Serial(self._port, self._baudrate, timeout=self._timeout)
            self.logger.info(f"Connected to port {self._port}")
##            print(f"[Controller {self._id}] Connected to {self._port}")
        except serial.SerialException as e:
            self.logger.error(f"Failed to connect to port {self._port}: {e}")
##            print(f"[Controller {self._id}] Failed to connect: {e}")
            self._serialConnection = None

    def disconnect(self):
        """Close serial connection."""
        if self._serialConnection and self._serialConnection.is_open:
            self._serialConnection.close()
            self.logger.info(f"Connection closed on port {self._port}")
##            print(f"[Controller {self._id}] serial connection closed.")

    def reconnect(self):
        """Attempt to reconnect."""
        self.logger.info("Attempting to reconnect...")
        self.disconnect()
        time.sleep(1)
        self.connect()

    def addSensors(self, sensorarg):
        if isinstance(sensorarg, Sensor):
            self._sensors.append(sensorarg)
            self.logger.info(f"Sensor {sensorarg} added.")
            #self._sensors[sensor.getID()] = sensor
        elif isinstance(sensorarg, list):
            for sensor in sensorarg:
                if isinstance(sensor, Sensor):
                    self._sensors.append(sensor)
                    self.logger.info(f"Sensor {sensor} added.")
                else:
                    self.logger.info(f"The objest {sensor} is not a Sensor.")

    def getSensor(self, _id):
        for sensor in self._sensors:
            if sensor.getID() == _id:
                return sensor

    def getSensors(self):
        return self._sensors

    def measure(self, command):
        #command can be:
        #0 to measure all sensors at once
        #1, 2, ... a specific sensor id
        #the controller's program handles it
##        print(f"Measuring controller with id {self._id}.")
        result = {}
        self.connect()
        if self._serialConnection:
            if command == "0": #measure all sensors at once
                for sensor in self._sensors:
                    sensor_id = sensor.getID()
                    response = sensor.measure(self._serialConnection, str(sensor_id))
                    result[sensor_id] = response
            else:
                sensor = self.getSensor(int(command))
                response = sensor.measure(self._serialConnection, command)
                result[int(command)] = response
##                print(f"result: {result}")
        else:
            pass
        self.disconnect()
        return result
        
        
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
    
    controller1 = Controller(1)
    print(controller1.getID())
    controller1.setID(2)
    print(controller1.getID())
    controller1.setName("cont1")
    print(controller1.getName())
    controller1.disconnect()
    controller1.reconnect()
    
