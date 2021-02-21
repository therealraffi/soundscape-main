const byte numChars = 32;
char receivedChars[numChars];
char tempChars[numChars];

int p0 = 0;
int p1 = 0;
int p2 = 0;
int p3 = 0;
int p4 = 0;
int p5 = 0;

boolean newData = false;

void setup() {
  Serial.begin(115200);
  pinMode(3, OUTPUT); 
  pinMode(5, OUTPUT);  
  pinMode(6, OUTPUT); 
  pinMode(9, OUTPUT);  
  pinMode(10, OUTPUT); 
  pinMode(11, OUTPUT);  
}

void loop() {
  recvWithStartEndMarkers();
  if (newData == true) {
    strcpy(tempChars, receivedChars);
    parseData();
    showParsedData();
    analogWrite(3, p0 * 2.55);
    analogWrite(5, p1 * 2.55);
    analogWrite(6, p2 * 2.55);
    analogWrite(9, p3 * 2.55);
    analogWrite(10, p4 * 2.55);
    analogWrite(11, p5 * 2.55);
    newData = false;
  }
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
  p0 = atoi(strtokIndx);

  strtokIndx = strtok(NULL, ",");
  p1 = atoi(strtokIndx);

  strtokIndx = strtok(NULL, ",");
  p2 = atof(strtokIndx);

  strtokIndx = strtok(NULL, ",");
  p3 = atof(strtokIndx);

  strtokIndx = strtok(NULL, ",");
  p4 = atof(strtokIndx);

  strtokIndx = strtok(NULL, ",");
  p5 = atof(strtokIndx);
}

void showParsedData() {
  Serial.println(p0);
  Serial.println(p1);
  Serial.println(p2);
  Serial.println(p3);
  Serial.println(p4);
  Serial.println(p5);
  Serial.println();
}
