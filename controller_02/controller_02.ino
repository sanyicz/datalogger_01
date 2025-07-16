#include <Wire.h>
#include "Adafruit_HTU21DF.h"

//define sensors
Adafruit_HTU21DF htu_1 = Adafruit_HTU21DF();

//controller and sensor IDs
int controllerID = 2;
int sensorIDs[] = {6, 7}; //
int sensorCount = 2;

void setup() {
  Serial.begin(9600); //9600, 115200
  if (!htu_1.begin()) {
    Serial.println("Couldn't find sensor!");
    while (1);
  }
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    // Initial handshake: send controller ID
    if (input == "GETID") {
      Serial.println(controllerID);
    }
    // Request for sensor IDs
    else if (input == "GETIDS") {
      for (int i = 0; i < sensorCount; i++) {
        Serial.print(sensorIDs[i]);
        if (i < sensorCount - 1) Serial.print(",");
      }
      Serial.println();
    }
    // Measurement request
    else {
      int req = input.toInt();
      if (req == 0) {
        // Measure all
        float t4 = htu_1.readTemperature();
        float rh4 = htu_1.readHumidity();
        Serial.print(t4); Serial.print(",");
        Serial.println(rh4);

      }
      else if (req == 6) {
        Serial.println(htu_1.readTemperature());
      }
      else if (req == 7) {
        Serial.println(htu_1.readHumidity());
      }
    }
  }
}