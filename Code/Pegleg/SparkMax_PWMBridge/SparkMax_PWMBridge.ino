/**** Created for the 2020 ECU ATMAE Robotics Competition ****/

/******** CONSIDERATIONS ********/
/*
 * This sketch exists solely because the SparkMAX requires
 * a specific PWM frequency to work (50Hz to 200Hz, as found in the data sheet).
 * Direction is given by leftDirPin and rightDirPin (true for forward, false for reverse).
 * Because the Arduino is able to parse the analog input pins extremely fast,
 * it does not have a means to properly interpret incoming PWM signals in hardware.
 * This code takes a rolling average (effectively the I in a PID loop) to simulate
 * an R-C circuit to obtain an effective voltage for a given PWM input signal.
 * 
 * Changing any variables, execution order, or array sizes will have an impact on
 * the speed of this code and the corresponding PWM output frequency that is sent
 * to the SparkMax. Pick your edits carefully!
 * 
 * As measured by an oscilloscope, the current output PWM frequency is ~169Hz. Nice.
 */

#define averagePWMSize 100 // declare the size of our averaging routine
int averageLPWMArray[averagePWMSize] = { 0 }; // init to zero
int averageRPWMArray[averagePWMSize] = { 0 }; // init to zero
int arrayPWMIndex = 0;

bool leftDir = 0;
bool rightDir = 0;
int leftSpeed = 0;
int rightSpeed = 0;

#define leftDrivePWMInput A0
#define rightDrivePWMInput A1
#define leftDirPin A2
#define rightDirPin A3
#define leftPWMOutput 4
#define rightPWMOutput 5

#define zeroDeadZone 10 // variable

#define sparkMaxPulseRange 2500 // in micros, found on sparkMAX site
#define fullReverseMicros 1000
#define minReverseMicros 1475
#define neutralMicros 1500
#define minForwardMicros 1525
#define fullForwardMicros 2000

void setup() {
    Serial.begin(9600);
    pinMode(leftDrivePWMInput, INPUT); //used for L-drive
    pinMode(rightDrivePWMInput, INPUT); //used for R-drive
    pinMode(leftDirPin, INPUT); //used for L-drive dir
    pinMode(rightDirPin, INPUT); //used for R-drive dir
    pinMode(leftPWMOutput, OUTPUT);
    pinMode(rightPWMOutput, OUTPUT);
}

void loop() {
    //erial.print(F("In: "));
    //Serial.print(analogRead(A0));
    //Serial.print(F(","));
    //Serial.println(analogRead(A1));
    writeToArray();
    getMotorDir();
    writeToSparkMax();
}

void writeToArray() {
    averageLPWMArray[arrayPWMIndex] = analogRead(A0);
    averageRPWMArray[arrayPWMIndex] = analogRead(A1);
    arrayPWMIndex++;
    if  (arrayPWMIndex > averagePWMSize) {
     arrayPWMIndex = 0;
    }
}

void getMotorDir() {
    leftDir = digitalRead(leftDirPin);
    rightDir = digitalRead(rightDirPin);
}

int averageLPWM() {
    long addend = 0;
    for (int i = 0; i < averagePWMSize; ++i) {
        addend += averageLPWMArray[i];
    }
    addend /= averagePWMSize;
    int result = addend;
    return result;
}

int averageRPWM() {
    long addend = 0;
    for (int i = 0; i < averagePWMSize; ++i) {
        addend += averageRPWMArray[i];
    }
    addend /= averagePWMSize;
    int result = addend;
    return result;
}

void writeToSparkMax() {
    int leftSpeed = averageLPWM();
    int rightSpeed = averageRPWM();
    if (leftSpeed < zeroDeadZone) {
        /* Mapping of micros is not necessary here,
         *  but we're using it so we ensure a
         *  consistent execution time.
         */
        delayMicroseconds(54); // to maintain even timing, as measured by the scope
        digitalWrite(leftPWMOutput, HIGH);
        delayMicroseconds(neutralMicros);
        digitalWrite(leftPWMOutput, LOW);
        delayMicroseconds(sparkMaxPulseRange - neutralMicros);
    }
    else {
        int mappedLMicros;
        if (leftDir) {
            mappedLMicros = map(leftSpeed, 0, 1023, minForwardMicros, fullForwardMicros);
        }
        else {
            mappedLMicros = map (leftSpeed, 0, 1023, minReverseMicros, fullReverseMicros);
        }
        digitalWrite(leftPWMOutput, HIGH);
        delayMicroseconds(mappedLMicros);
        digitalWrite(leftPWMOutput, LOW);
        delayMicroseconds(sparkMaxPulseRange - mappedLMicros);
    }

    if (rightSpeed < zeroDeadZone) {
        delayMicroseconds(54); // to maintain even timing, as measured by the scope
        digitalWrite(rightPWMOutput, HIGH);
        delayMicroseconds(neutralMicros);
        digitalWrite(rightPWMOutput, LOW);
        delayMicroseconds(sparkMaxPulseRange - neutralMicros);
    }
    else {
        int mappedRMicros;
        if (rightDir) {
            mappedRMicros = map(rightSpeed, 0, 1023, minForwardMicros, fullForwardMicros);
        }
        else {
            mappedRMicros = map(rightSpeed, 0, 1023, minReverseMicros, fullReverseMicros);
        }
        digitalWrite(rightPWMOutput, HIGH);
        delayMicroseconds(mappedRMicros);
        digitalWrite(rightPWMOutput, LOW);
        delayMicroseconds(sparkMaxPulseRange - mappedRMicros);
    }
}
