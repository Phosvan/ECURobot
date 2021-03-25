
// made for ECU ROBOT
// Hardware arduino nano using default ic2 pins 
// PINS : A4 SDA (data) A5 SCL (clock)
// Hardware is a pololu LSM6DS33 and LIS3MDL carier part number #2738
// NOT A FINAL VERSION. NOT FOR OFFICAL USE.
//3V34$


#include <Wire.h>
#include <LIS3MDL.h>
#include <Wire.h>
#include <LIS3MDL.h>

LIS3MDL mag;
LIS3MDL::vector<int16_t> running_min = {32767, 32767, 32767}, running_max = {-32768, -32768, -32768};

char report1[80];
char report[80];
void setup()
{
  Serial.begin(9600);
  Wire.begin();

  if (!mag.init())
  {
    Serial.println("Failed to detect and initialize mag");
    while (1);
  }

  mag.enableDefault();
}

void loop()
{
  mag.read();

  running_min.x = min(running_min.x, mag.m.x);
  running_min.y = min(running_min.y, mag.m.y);
  running_min.z = min(running_min.z, mag.m.z);

  running_max.x = max(running_max.x, mag.m.x);
  running_max.y = max(running_max.y, mag.m.y);
  running_max.z = max(running_max.z, mag.m.z);

  snprintf(report1, sizeof(report1), "min: {%+5d, %+6d, %+6d}   max: {%+6d, %+6d, %+6d} M: {%4d %4d %4d}",
    running_min.x, running_min.y, running_min.z,
    running_max.x, running_max.y, running_max.z, mag.m.x, mag.m.y, mag.m.z) ;

  delay(.5);  
  
    
  Serial.println(report1);
  delay(100);
}
