/******** Created for 2019 ECU ATMAE Robotics Competition ********/

//Configuration for RX'd Serial Character Array//
#define charSize 64
char serialRXArray[charSize] = { 0 }; //Initialize a char array of size charSize

boolean serialEchoFlag = true; //Set this flag to echo data back to Serial Host. True negatively impacts runtime!!
boolean serialReceived = false; //Do not adjust, flag used in processing logic
boolean serialParsed = false;

// GLOBAL VARIABLES RX'd OVER SERIAL LINK, See serialParse() //
int driveMode = 0;
int ltDrive = 0;
int rtDrive = 0;

//Pin mappings for updateOutputs()//
#define driveLPWM 10
#define driveRPWM 11
#define driveLin1 A0
#define driveLin2 A1
#define driveRin3 A2
#define driveRin4 A3
boolean driveStallReady = false;
int driveLastKnownState = 0;

//Initialize watchdog timer in case we lose serial comms (shuts off motors, locks steppers)
long currentTime = 0;
long watchdogTimeout = 0;
long watchdogThreshold = 500; //Time in millis to wait for serial comms before shutting down motors

//Pin mappings for getLimits()
#define elevatorLimit0 5
#define elevatorLimit1 6
#define elevatorLimit2 7
#define gripLimit 8
#define sideshiftLimit 9

//Global variables for getLimits()
int elevatorLimitStatus0 = 0;
int elevatorLimitStatus1 = 0;
int elevatorLimitStatus2 = 0;
int gripLimitStatus = 0;
int sideshiftLimitStatus = 0;

void setup() {
  //Set up serial line
  Serial.begin(9600);

  //Set up getLimits() as PULLUP so we don't have to use external resistor network
  pinMode(elevatorLimit0, INPUT_PULLUP);
  pinMode(elevatorLimit1, INPUT_PULLUP);
  pinMode(elevatorLimit2, INPUT_PULLUP);
  pinMode(gripLimit, INPUT_PULLUP);
  pinMode(sideshiftLimit, INPUT_PULLUP);

  // Set up drive outputs and map to values defined above
  pinMode(driveLPWM, OUTPUT);
  pinMode(driveRPWM, OUTPUT);
  pinMode(driveLin1, OUTPUT);
  pinMode(driveLin2, OUTPUT);
  pinMode(driveRin3, OUTPUT);
  pinMode(driveRin4, OUTPUT);
  // Tell drive outputs to go LOW to prevent erroneous movement on startup
  digitalWrite(driveLin1, LOW);
  digitalWrite(driveLin2, LOW);
  digitalWrite(driveRin3, LOW);
  digitalWrite(driveRin4, LOW);
  analogWrite(driveLPWM, LOW);
  analogWrite(driveRPWM, LOW);
}

void loop() {
  currentTime = millis();
  serialRead();
  serialParse();
  serialEcho();
  getLimits();
  driveModeOutput();
  motorPWM();
  watchdogUpdate();
}

void getLimits() {
  if (digitalRead(elevatorLimit0) == 0) {
    elevatorLimitStatus0 = 0;
  }
  else {
    elevatorLimitStatus0 = 1;
  }
  if (digitalRead(elevatorLimit1) == 0) {
    elevatorLimitStatus1 = 0;
  }
  else {
    elevatorLimitStatus1 = 1;
  }
  if (digitalRead(elevatorLimit2) == 0) {
    elevatorLimitStatus2 = 0;
  }
  else {
    elevatorLimitStatus2 = 1;
  }
  if (digitalRead(gripLimit) == 0) {
    gripLimitStatus = 0;
  }
  else {
    gripLimitStatus = 1;
  }
  if (digitalRead(sideshiftLimit) == 0) {
    sideshiftLimitStatus = 0;
  }
  else {
    sideshiftLimitStatus = 1;
  }
}

//Pull data in over serial link, RX data until startMarker and endMarker are received, denoting a full message
void serialRead() { //Based on code from: https://forum.arduino.cc/index.php?topic=288234.0
  static boolean serialRXInProg = false;
  static byte rxCharIndex = 0; //Initialize a byte with value zero as a pointer to the place in array to move data
  char startMarker = '<'; //All messages must begin with this. If not, it will not be read
  char endMarker = '>'; //End messages with this so the char array gets properly terminated
  char rc; //Used to hold one char from the Serial buffer until it is loaded into the array
  while (Serial.available() && serialReceived == false) { //serialReceived is initialized before first run!
    rc = Serial.read(); //Load next char in line to char rc
    //Serial.print(rc);
    if (serialRXInProg == true) {
      if (rc != endMarker) { //if the received char is NOT the endMarker
        serialRXArray[rxCharIndex] = rc; //Set serialRXArray @ location rxCharIndex to the char in rc
        rxCharIndex++; //Increment rxCharIndex in preparation for the next char 
      }
      else {
        serialRXArray[rxCharIndex] = '\0'; //Our last RX'd char was endMarker. Terminate char array
        serialRXInProg = false; //Done RX'ing. Set bool to false
        rxCharIndex = 0; //Reset rxCharIndex (Technically not necessary due to declaration at beginning of this routine)
        serialReceived = true; //We have a full char array. Prep for Logic() and Reply()
        watchdogTimeout = currentTime + watchdogThreshold; //We've just received a new data packet. Update watchdogTimeout with a new value.
      }
    }
    
    if (rc == startMarker) { //This needs to go at the end so a startMarker doesn't waste space in serialRXArray
      serialRXInProg = true;
    }
    
  }
}

//Data received, put it into the proper global variables
void serialParse() {
  if (serialReceived == true && serialParsed == false) {
     char * strtokIndex; // used by strtok() as an index (pointer)
     strtokIndex = strtok(serialRXArray,","); //Look for the first comma, set pointer there
     driveMode = strtol(strtokIndex, NULL, 16);
     strtokIndex = strtok(NULL, ","); //Look for third comma, set pointer there
     ltDrive = strtol(strtokIndex, NULL, 16);
     strtokIndex = strtok(NULL, ","); //Look for fourth comma, set pointer there
     rtDrive = strtol(strtokIndex, NULL, 16);
     serialParsed = true; //Data has been parsed. Set bool flag
  }
}

void serialEcho() {
  if (serialEchoFlag == true && serialParsed == true && serialReceived == true) {
    Serial.print(elevatorLimitStatus0);
    Serial.print(F(","));
    Serial.print(elevatorLimitStatus1);
    Serial.print(F(","));
    Serial.print(elevatorLimitStatus2);
    Serial.print(F(","));
    Serial.print(gripLimitStatus);
    Serial.print(F(","));
    Serial.print(sideshiftLimitStatus);
    Serial.print(F(","));
    Serial.print(ltDrive);
    Serial.print(F(","));
    Serial.print(rtDrive);
    Serial.println();
    for (int i=0; i<charSize; i++) {
      serialRXArray[i] = '\0';
    }
    serialRXArray[0] = '\0'; //Nullify all data in char array by setting NULL to placeholder 0 This is redundant.
    serialReceived = false; //Reset this so we can RX more data
    serialParsed = false; //We've echoed, set boolean to false so we can analyze data again
  }
  if (serialEchoFlag == false && serialParsed == true && serialReceived == true) {
    serialRXArray[0] = '\0'; //Nullify all data in char array by setting NULL to placeholder 0 This is redundant.
    serialReceived = false; //Reset this so we can RX more data
    serialParsed = false; //We've echoed, set boolean to false so we can analyze data again
  }
}

void driveModeOutput() {
  // No drive motor movement
  if (driveMode == 0) {
    setDriveStop();
  }
  // Drive motor FORWARD
  if (driveMode == 1) {
    setDriveForward();
  }
  // Drive moter REVERSE
  if (driveMode == 2) {
    setDriveReverse();
  }
  // ZERO TURN CLOCKWISE
  if (driveMode == 3) {
    setDriveZturnCW();
  }
  // ZERO TURN COUNTER CLOCKWISE
  if (driveMode == 4) {
    setDriveZturnCCW();
  }
}

void setDriveStop() {
  digitalWrite(driveLin1, LOW);
  digitalWrite(driveLin2, LOW);
  digitalWrite(driveRin3, LOW);
  digitalWrite(driveRin4, LOW);
}

void setDriveForward() {
  digitalWrite(driveLin1, LOW);
  digitalWrite(driveLin2, HIGH);
  digitalWrite(driveRin3, HIGH);
  digitalWrite(driveRin4, LOW);
}

void setDriveReverse() {
  digitalWrite(driveLin1, HIGH);
  digitalWrite(driveLin2, LOW);
  digitalWrite(driveRin3, LOW);
  digitalWrite(driveRin4, HIGH);
}

void setDriveZturnCW() {
  digitalWrite(driveLin1, HIGH);
  digitalWrite(driveLin2, LOW);
  digitalWrite(driveRin3, HIGH);
  digitalWrite(driveRin4, LOW);
}

void setDriveZturnCCW() {
  digitalWrite(driveLin1, LOW);
  digitalWrite(driveLin2, HIGH);
  digitalWrite(driveRin3, LOW);
  digitalWrite(driveRin4, HIGH);
}

void motorPWM() {
  // Write PWM value to motors from value RX'd over serial
  if (driveMode == 0 || driveMode == 1 || driveMode == 2) {
    analogWrite(driveLPWM, ltDrive);
    analogWrite(driveRPWM, rtDrive);
    if (driveMode != 0 && ((ltDrive > 120) || (rtDrive > 120))) {
      driveStallReady = true;
      driveLastKnownState = driveMode;
    }
  }
  // If driveMode is ZERO TURN, set drive speed to MAX
  if (driveMode == 3 || driveMode == 4) {
    analogWrite(driveLPWM, 120);
    analogWrite(driveRPWM, 120);
    driveStallReady = false;
    driveLastKnownState = 0;
  }
  motorStallPulse();
}

void motorStallPulse() {
  if (driveStallReady == true && driveMode == 0) {
    if (driveLastKnownState == 1) {
      setDriveReverse();
      delayMicroseconds(50);
      analogWrite(driveLPWM, 255);
      analogWrite(driveRPWM, 180);
      delay(100);
      analogWrite(driveLPWM, 0);
      analogWrite(driveRPWM, 0);
      setDriveStop();
      driveStallReady = false;
    }
    if (driveLastKnownState == 2) {
      setDriveForward();
      delayMicroseconds(50);
      analogWrite(driveLPWM, 255);
      analogWrite(driveRPWM, 180);
      delay(100);
      analogWrite(driveLPWM, 0);
      analogWrite(driveRPWM, 0);
      setDriveStop();
      driveStallReady = false;
    }
  }
}

void watchdogUpdate() {
  if (currentTime > watchdogTimeout) {
    analogWrite(driveLPWM, 0);
    analogWrite(driveRPWM, 0);
  }
}
