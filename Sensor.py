import time
import serial
import logging

class Sensor:
    def __init__(self, ID, name="NotSet", _type="NotSet", quantity="NotSet", unit="NotSet", serialnumber="NotSet"):
        self.logger = logging.getLogger(f"Sensor {ID}")
        self.logger.info(f"Created sensor with id {ID} and name {name}.")
        if isinstance(ID, int):
            self._id = ID
        else:
            pass #handle this
        self._name = name
        self._type = _type
        self._quantity = quantity
        self._unit = unit
        self._serialnumber = serialnumber

    def getID(self):
        return self._id

    def setID(self, ID):
        if isinstance(ID, int):
            self.logger.debug(f"Setting id of sensor with id {self._id} to {ID}.")
            self._id = ID
        else:
            pass

    def getName(self):
        return self._name

    def setName(self, name):
        self.logger.debug(f"Setting name of sensor with id {self._id} to {name}.")
        self._name = name

    def getType(self):
        return self._type

    def setType(self, _type):
        self.logger.debug(f"Setting type of sensor with id {self._id} to {_type}.")
        self._type = _type

    def getQuantity(self):
        return self._quantity

    def setQuantity(self, quantity):
        self.logger.debug(f"Setting quantity of sensor with id {self._id} to {quantity}.")
        self._quantity = quantity

    def getUnit(self):
        return self._unit

    def setUnit(self, unit):
        self.logger.debug(f"Setting unit of sensor with id {self._id} to {unit}.")
        self._unit = unit

    def getSerialNumber(self):
        return self._serialnumber

    def setSerialNumber(self, serialnumber):
        self.logger.debug(f"Setting serial number of sensor with {self._id} to {serialnumber}.")
        self._serialnumber = serialnumber

    def measure(self, serialConnection, command, maxRetries=3):
        attempt = 0
        serialConnectionLost = False
        while attempt < maxRetries:
            self.logger.debug(f"Measuring, {attempt}/{maxRetries}.")
            attempt += 1
            try:
                if serialConnection.is_open:
                    serialConnection.write((command + '\n').encode(encoding="utf-8", errors="strict"))
                    response = serialConnection.readline().decode().strip() #decode("utf-8", "ignore")
                    self.logger.debug(f"Response: {response}.")
                else:
                    self.logger.debug(f"Serial connection is not open.")
            except serialConnection.SerialException as e:
                self.logger.debug(f"Serial exception during write/read: {e}.")
                serialConnectionLost = True
                break
            except Exception as e:
                self.logger.debug(f"Unexpected error: {e}.")
                time.sleep(0.5)
        try:
            result = float(response)
        except:
            result = float('NaN')
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
    
    sensor1 = Sensor(1)
    print(sensor1.getID())
    sensor1.setID(2)
    print(sensor1.getID())
    sensor1.setName("temp1")
    print(sensor1.getName())
    sensor1.setQuantity("temperature")
    print(sensor1.getQuantity())
    sensor1.setUnit("C")
    print(sensor1.getUnit())
    sensor1.setSerialNumber("T0001V0")
    print(sensor1.getSerialNumber())
    ser = serial.Serial()
    sensor1.measure(ser, "GETID")
