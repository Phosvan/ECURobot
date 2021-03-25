/******** Created for 2019 ECU ATMAE Robotics Competition ********/


//Configuration for RX'd Serial Character Array//
#define charSize 64
char serialRXArray[charSize] = { 0 }; //Initialize a char array of size charSize

boolean serialEchoFlag = true; //Set this flag to echo data back to Serial Host. True negatively impacts runtime!!
boolean serialReceived = false; //Do not adjust, flag used in processing logic
boolean serialParsed = false;
long messageRXCount = 0; //NOTE: CAN BE REMOVED!!!

// GLOBAL VARIABLES RX'd OVER SERIAL LINK, See serialParse() //
int id = 0; //NOTE: CAN BE REMOVED!!!
int driveMode = 0;	//NOTE: DEPRECATED AS DRIVE MOTORS MOVED TO SENSOR ARDUINO
int ltDrive = 0;  	//NOTE: DEPRECATED AS DRIVE MOTORS MOVED TO SENSOR ARDUINO
int rtDrive = 0;  	//NOTE: DEPRECATED AS DRIVE MOTORS MOVED TO SENSOR ARDUINO
long elevatorStepperCntrl = 0;
long gripStepperCntrl = 0;
long sideshiftStepperCntrl = 0;

//Initialize watchdog timer in case we lose serial comms (shuts off motors, locks steppers)
long currentTime = 0;
long watchdogTimeout = 0;
long watchdogThreshold = 500; //Time in millis to wait for serial comms before shutting down motors

//Pin mappings for updateOutputs()//
#define driveLPWM 10
#define driveRPWM 11
#define driveLin1 A0
#define driveLin2 A1
#define driveRin3 A2
#define driveRin4 A3

//Initialize stepper motors
#include <Stepper.h>
const int stepsPerRevolution = 200;
Stepper elevatorStepper(stepsPerRevolution, A4, A5, 12, 13); // Set elevatorStepper to 200SPR on pins 2, 3, 4, 5
Stepper gripStepper(stepsPerRevolution, 6, 7, 8, 9); // Set gripStepper to 200SPR on pins 6, 7, 8, 9
Stepper sideshiftStepper(stepsPerRevolution, 2, 3, 4, 5); // Set graspStepper to SPR on pins A4, A5, 12, 13

void setup() {
  // Set up serial line
  Serial.begin(9600);
  Serial.print("Waiting for connection...");

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

  //Set up stepper values
  elevatorStepper.setSpeed(150); // set speed to 150rpm. Found to be best speed/reliability balance.
  gripStepper.setSpeed(130); // set speed to 150rpm
  sideshiftStepper.setSpeed(150); // set speed to 150rpm
}

//Main program loop

void loop() {
  //Get current time for use in watchdog timer
  currentTime = millis();
  //Read our serial line, if it is ready to read
  serialRead();
  //Parse data, if data has been read
  serialParse();
  //Dependent on boolean value set above, print RX'd data back to host
  serialEcho();
  //Using parsed data, update drive motor direction
  driveModeOutput();
  //Drive motor direction has been set, now set speed
  motorPWM();
  //Drive stepper outputs with parsed data
  elevatorStepperOutput();
  gripStepperOutput();
  sideshiftStepperOutput();
  //Update watchdog timer
  watchdogUpdate();
}

//Pull data in over serial link, RX data until startMarkern and endMarker are received, denoting a full message
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
        messageRXCount++; //Increment counter for debugging purposes
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
     //id = strtol(strtokIndex, NULL, 16); //Move all data between placeholder 0 and 1st comma into ID, NULL data after moved
     //strtokIndex = strtok(NULL, ","); //Look for second comma, set pointer there
     driveMode = strtol(strtokIndex, NULL, 16);
     strtokIndex = strtok(NULL, ","); //Look for third comma, set pointer there
     ltDrive = strtol(strtokIndex, NULL, 16);
     strtokIndex = strtok(NULL, ","); //Look for fourth comma, set pointer there
     rtDrive = strtol(strtokIndex, NULL, 16);
     strtokIndex = strtok(NULL, ","); //Look for fifth comma, set pointer there
     elevatorStepperCntrl = strtol(strtokIndex, NULL, 16);
     strtokIndex = strtok(NULL, ","); //Look for sixth comma, set pointer there
     gripStepperCntrl = strtol(strtokIndex, NULL, 16);
     strtokIndex = strtok(NULL, ","); //Look for seventh commma, set pointer there
     sideshiftStepperCntrl = strtol(strtokIndex, NULL, 16);
     strtokIndex = strtok(NULL, ",");
     //serialRXArray[0] = '\0'; //We've parsed all info. Null at placeholder 0 to prep for new info.
     serialParsed = true; //Data has been parsed. Set bool flag
  }
}

//After data has been parsed, print RX'd data values to host
void serialEcho() {
  if (serialEchoFlag == true && serialParsed == true && serialReceived == true) {
    Serial.print(sideshiftStepperCntrl);
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
    digitalWrite(driveLin1, LOW);
    digitalWrite(driveLin2, LOW);
    digitalWrite(driveRin3, LOW);
    digitalWrite(driveRin4, LOW);
  }
  // Drive motor FORWARD
  if (driveMode == 1) {
    digitalWrite(driveLin1, LOW);
    digitalWrite(driveLin2, HIGH);
    digitalWrite(driveRin3, HIGH);
    digitalWrite(driveRin4, LOW);
  }
  // Drive moter REVERSE
  if (driveMode == 2) {
    digitalWrite(driveLin1, HIGH);
    digitalWrite(driveLin2, LOW);
    digitalWrite(driveRin3, LOW);
    digitalWrite(driveRin4, HIGH);
  }
  // ZERO TURN CLOCKWISE
  if (driveMode == 3) {
    digitalWrite(driveLin1, HIGH);
    digitalWrite(driveLin2, LOW);
    digitalWrite(driveRin3, HIGH);
    digitalWrite(driveRin4, LOW);
  }
  // ZERO TURN COUNTER CLOCKWISE
  if (driveMode == 4) {
    digitalWrite(driveLin1, LOW);
    digitalWrite(driveLin2, HIGH);
    digitalWrite(driveRin3, LOW);
    digitalWrite(driveRin4, HIGH);
  }
}

void motorPWM() {
  // Write PWM value to motors from value RX'd over serial
  analogWrite(driveLPWM, ltDrive);
  analogWrite(driveRPWM, rtDrive);
  // If driveMode is ZERO TURN, set drive speed to MAX
  if (driveMode == 3 || driveMode == 4) {
    analogWrite(driveLPWM, 170);
    analogWrite(driveRPWM, 170);
  }
}

void elevatorStepperOutput() {
  // If Cntrl is 0, HOLD
  if (elevatorStepperCntrl == 0) {
    //NEED TO CODE HOLD FUNCTION, MAYBE
  }
  else if (elevatorStepperCntrl == 1) {
    elevatorStepper.setSpeed(180);
    elevatorStepper.step(50);
    elevatorStepperCntrl = 0;
  }
  else if (elevatorStepperCntrl == 2) {
    elevatorStepper.setSpeed(130);
    elevatorStepper.step(-50);
    elevatorStepperCntrl = 0;
  }
}

void gripStepperOutput() {
  if (gripStepperCntrl == 0) {
    
  }
  else if (gripStepperCntrl == 1) {
    gripStepper.step(25);
    gripStepperCntrl = 0;
  }
  else if (gripStepperCntrl == 2) {
    gripStepper.step(-25);
    gripStepperCntrl = 0;
  }

}

void sideshiftStepperOutput() {
  // No, a 3 and 4 here doesn't make sense,
  // but the code doesn't work otherwise,
  // so here it will stay
  if (sideshiftStepperCntrl == 3) {
    sideshiftStepper.step(50);
    sideshiftStepperCntrl = 0; 
  }
  else if (sideshiftStepperCntrl == 4) {
    sideshiftStepper.step(-50);
    sideshiftStepperCntrl = 0;
  }
  else {
    
  }
}

void watchdogUpdate() {
  if (currentTime > watchdogTimeout) {
    analogWrite(driveLPWM, 0);
    analogWrite(driveRPWM, 0);
    elevatorStepperCntrl = 0;
    gripStepperCntrl = 0;
    sideshiftStepperCntrl = 0;
  }
}
