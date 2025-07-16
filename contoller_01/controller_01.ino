#include <DHT.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// Define sensor pins and types
#define DHTPIN_1 4
#define DHTTYPE_1 DHT22
#define DHTPIN_2 5
#define DHTTYPE_2 DHT22
#define ONE_WIRE_BUS 8

DHT dht_1(DHTPIN_1, DHTTYPE_1);
DHT dht_2(DHTPIN_2, DHTTYPE_2);
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature ds18b20(&oneWire);

// Controller and sensor IDs
int controllerID = 1;
int sensorIDs[] = {1, 2, 3, 4, 5}; //DHT22_1 and DHT22_2 (T and RH respectively), and DS18B20
int sensorCount = 5;

void setup() {
  Serial.begin(9600);
  dht_1.begin();
  dht_2.begin();
  ds18b20.begin();
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
        float t1 = dht_1.readTemperature();
        float rh1 = dht_1.readHumidity();
        float t2 = dht_2.readTemperature();
        float rh2 = dht_2.readHumidity();
        ds18b20.requestTemperatures();
        float t4 = ds18b20.getTempCByIndex(0);
        Serial.print(t1); Serial.print(",");
        Serial.print(rh1); Serial.print(",");
        Serial.print(t2); Serial.print(",");
        Serial.print(rh2); Serial.print(",");
        Serial.println(t4);
      }
      else if (req == 1) {
        Serial.println(dht_1.readTemperature());
      }
      else if (req == 2) {
        Serial.println(dht_1.readHumidity());
      }
      else if (req == 3) {
        Serial.println(dht_2.readTemperature());
      }
      else if (req == 4) {
        Serial.println(dht_2.readHumidity());
      }
      else if (req == 5) {
        ds18b20.requestTemperatures();
        Serial.println(ds18b20.getTempCByIndex(0));
      }
    }
  }
}