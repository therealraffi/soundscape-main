const byte numChars = 128;
char receivedChars[numChars];
char tempChars[numChars];

const int devices = 18;
int amps[devices];
int pins[] = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 18, 19, 22, 23};

boolean newData = false;

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < devices; i++) {
    pinMode(pins[i], OUTPUT);
  }
}

void loop() {
  //Serial.println("Hello World...");
  //delay(1000);
  
  /*for (int i = 0; i < 16; i++) {
    Serial.print(amps[i]);
    Serial.print(" ");
  }
  Serial.println();*/
  
  recvWithStartEndMarkers();
  if (newData == true) {
    strcpy(tempChars, receivedChars);
    parseData();
    showParsedData();
    for (int i = 0; i < devices; i++) {
      analogWrite(pins[i], amps[i] * 2.55);
    }
    newData = false;
  }
  //delay(10);
}

 void recvWithStartEndMarkers() {
  static boolean recvInProgress = false;
  static byte ndx = 0;
  char startMarker = '<';
  char endMarker = '>';
  char rc;

  while (Serial.available() > 0 && newData == false) {
    rc = Serial.read();

    if (recvInProgress == true) {
      if (rc != endMarker) {
        receivedChars[ndx] = rc;
        ndx++;
        if (ndx >= numChars) {
          ndx = numChars - 1;
        }
      } else {
        receivedChars[ndx] = '\0';
        recvInProgress = false;
        ndx = 0;
        newData = true;
      }
    } else if (rc == startMarker) {
      recvInProgress = true;
    }
  }
 }


 void parseData() {
  char * strtokIndx;

  strtokIndx = strtok(tempChars, ",");
  amps[0] = atoi(strtokIndx);
  
  for (int i = 1; i < devices; i++) {
    strtokIndx = strtok(NULL, ",");
    amps[i] = atoi(strtokIndx);
  }
 }

 void showParsedData() {
  for (int i = 0; i < devices; i++) {
    Serial.print(amps[i]);
    Serial.print(" ");
  }
  Serial.println();
 }
