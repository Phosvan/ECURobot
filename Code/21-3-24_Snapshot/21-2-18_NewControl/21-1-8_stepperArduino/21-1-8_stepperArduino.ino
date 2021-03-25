/******** Created for 2020 ECU ATMAE Robotics Competition ********/

//Initialize watchdog timer in case we lose serial comms (shuts off motors, locks steppers)
long currentTime = 0;
long watchdogTimeout = 0;
long watchdogThreshold = 500; //Time in millis to wait for serial comms before shutting down motors

//Initialiaze stepper variables (values in microseconds between pulses)
int stepSpeed[3] = {30, 30, 30};

//Initialize stepper motor pins
int stepPin[3] = { 3, 5, 7};
int dirPin[3] = { 4, 6, 8};

//Initialize control pins
#define stepCtrl1 A0
#define dirCtrl1 A1
#define stepCtrl2 A2
#define dirCtrl2 A3
#define stepCtrl3 A4
#define dirCtrl3 A5

//Initialize control variables
bool dirState[3] = { false, false, false };
bool stepState[3] = { false, false, false };

//Initialize tracking variables
bool dirPrev[3] = { false, false, false };
bool stepPrev[3] = { false, false, false };

//Initialize vars for keeping track of current rotations
long stepPos[3];

void setup() {
  //Serial.begin(9600);
  //Declare outputs for use by stepper motors
  for (int i = 0; i < 3; i++) {
    pinMode(stepPin[i], OUTPUT);
    pinMode(dirPin[i], OUTPUT);
  }

  //Declare inputs for use by the control pins
  pinMode(stepCtrl1, INPUT);
  pinMode(dirCtrl1, INPUT);
  pinMode(stepCtrl2, INPUT);
  pinMode(dirCtrl2, INPUT);
  pinMode(stepCtrl3, INPUT);
  pinMode(dirCtrl3, INPUT);
}

//Main program loop

void loop() {
  //Get current time for use in watchdog timer
  currentTime = millis();
  //Initialize Control Variables
  controlInitialization();
  //Read control inputs and update control variables
  controlFlagUpdate();
  //Check to see if any of our states changed. If so, delay to give time for motor
  // to spin down
  delayVerification();
  //Spin them things
  motorSpin();
  //Update watchdog timer - NOT PRESENTLY WORKING!!!!
}

void controlInitialization() {
  for (int i = 0; i<3; i++) {
    dirPrev[i] = dirState[i];
    stepPrev[i] = stepState[i];
  }
}

void controlFlagUpdate() {
  //Read stepper controls

  if (analogRead(A0) > 500) stepState[0] = true;
  else stepState[0] = false;

  if (analogRead(A2) > 500) stepState[1] = true;
  else stepState[1] = false;

  if (analogRead(A4) > 500) stepState[2] = true;
  else stepState[2] = false;

  if (analogRead(A1) > 500) dirState[0] = true;
  else dirState[0] = false;

  if (analogRead(A3) > 500) dirState[1] = true;
  else dirState[1] = false;

  if (analogRead(A5) > 500) dirState[2] = true;
  else dirState[2] = false;
  /*
  Serial.print(F("dir State: "));
  for (int i = 0; i < 3; i++) {
    Serial.print(dirState[i]);
    Serial.print(F(","));
  }
  Serial.println();
  Serial.print(F("step State: "));
  for (int i = 0; i < 3; i++) {
    Serial.print(stepState[i]);
    Serial.print(F(","));
  }
  Serial.println();*/
}

void delayVerification() {
  bool wait = false;
  for (int i = 0; i < 3; i++) {
    if ((dirState[i] != dirPrev[i])) {
      wait = true;
    }

    /* IMPORTANT: THE IMPLICATIONS OF THIS METHOD OF DELAY
    MEANS THAT ANY TIME A SINGLE STEPPER NEEDS TO CHANGE SPEED
    OR DIRECTION, ALL STEPPERS WILL WAIT THE ALLOTTED DELAY TIME*/
    if (wait == true) {
      delay(50);
      wait = false;
    }
  }
}

void motorSpin() {
  for (int i = 0; i < 3; i++) {
    if (stepState[i]) {
      digitalWrite(dirPin[i], dirState[i]);
      digitalWrite(stepPin[i], HIGH);
      delayMicroseconds(stepSpeed[i]);
      digitalWrite(stepPin[i], LOW);
      delayMicroseconds(stepSpeed[i]);
    }
    else {
      digitalWrite(stepPin[i], LOW);
    }
  }
}
