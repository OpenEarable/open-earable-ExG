#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
#include "OpenEarable.h"
#include "NHB_AD7124.h"
#include "ArduinoBLE.h"

BLEService adcService("0029d054-23d0-4c58-a199-c6bdc16c4975");
// Arduino max MTU is 23 bytes, so 5 32 bit floats == 20 bytes is the maximum number of samples that can be sent in one BLE packet
BLECharacteristic adcCharacteristic("20a4a273-c214-4c18-b433-329f30ef7275", BLERead | BLENotify, 20);

Ad7124 adc(EPIN_SPI_CS, 8000000); // max sample rate: ~12100 SPS (when nothing printed on Serial, ~7080 when writing to Serial with 32 bit float)

float data[5] = {0.0};
int i = 0;


// When OpenEarable firmware is running as well, observed sample rate is not perfectly matched
// samples per second: 614400/(32*x) where x is the value of samplesPerSecondVal
//const uint16_t samplesPerSecondVal = 1; // 1 == 19200 SPS
//const uint16_t samplesPerSecondVal = 60; // 60 == 320 SPS
//const uint16_t samplesPerSecondVal = 160; // 160 == 120 SPS
//const uint16_t samplesPerSecondVal = 38; // 38 == 505 SPS
//const uint16_t samplesPerSecondVal = 19; // 19 == 1010 SPS
const uint16_t samplesPerSecondVal = 75; // 75 == 256 SPS
//const uint16_t samplesPerSecondVal = 384; // 384 == 50 SPS
//const uint16_t samplesPerSecondVal = 320; // 320 == 60 SPS
//const uint16_t samplesPerSecondVal = 2047; // 2047 == 9.38 SPS // max value: 2047

void updateBLE(float reading) {
  data[i] = reading; 
  if (i == 4) {
    adcCharacteristic.writeValue((byte*)&data, sizeof(data));
    memset(data, 0, sizeof(data));
    i = 0;
  }
  else {
    i++;
  }
}

void readExternalADC() {
  float reading = (float) adc.readVolts(0);
  Serial.write((byte*)&reading, 4);
  Serial.write('\n');
  updateBLE(reading);
}

void measureSampleRate() {
  unsigned long startTime = millis();
  unsigned long endTime = startTime + 5000;
  unsigned long sampleCount = 0;

  while (millis() < endTime) {
    readExternalADC();
    sampleCount++;
  }

  double sampleRate = (double)sampleCount / 5.0;
  Serial.print("Achieved sample rate: ");
  Serial.print(sampleRate);
  Serial.println(" samples per second");
}

void setup() {
  Serial.begin(115200);
  open_earable.begin();

  adc.begin();
  adc.reset();
  adc.setAdcControl(AD7124_OpMode_Continuous, AD7124_FullPower, true);

  adc.setup[0].setConfig(AD7124_Ref_Internal, AD7124_Gain_1, true);
  adc.setup[0].setFilter(AD7124_Filter_SINC4, samplesPerSecondVal, AD7124_PostFilter_NoPost, false);
  adc.setChannel(0, 0, AD7124_Input_AIN1, AD7124_Input_AIN0, true);

  BLE.setAdvertisedService(adcService);
  adcService.addCharacteristic(adcCharacteristic);
  BLE.addService(adcService);
  adcCharacteristic.writeValue((byte*)&data, sizeof(data));
  BLE.advertise();
}

void loop() {
  open_earable.update();
  readExternalADC();
}
