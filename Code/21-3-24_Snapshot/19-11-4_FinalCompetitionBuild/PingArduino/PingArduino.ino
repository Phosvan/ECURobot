#include <Wire.h>
#define i2cReadyPin 13

void setup() {
  // put your setup code here, to run once:
  pinMode(i2cReadyPin, INPUT);
  while(i2cReadyPin != 1) {
    
  }
  Wire.begin(1);
}

void loop() {

}
