union {
  struct {
    int data;
  } param;
  byte packet[2];
} dataRecv;

union {
  struct {
    int data;
  } param;
  byte packet[2];
} data;

#define hijau 3
#define merah 4
#define putih 5
uint8_t data_remove[5] = {0x04, 0xFF, 0x0F, 0x65, 0x5D};
int ID = 0;
int NEWID = 0;
int dataID;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  pinMode(hijau, OUTPUT);
  pinMode(merah, OUTPUT);
  Serial1.begin(57600);
  pinMode(2, INPUT_PULLUP);
}

void loop() {
  // put your main code here, to run repeatedly:
  if (!digitalRead(2)) {
    sendData();
  }

  while (Serial1.available()) {
    dataID = Serial1.read();
    switch (dataID) {
      case 151: NEWID = 1;
        break;
      case 165: NEWID = 2;
        break;
      case 180: NEWID = 3;
        break;
      case 192: NEWID = 4;
        break;
      case 209: NEWID = 5;
        break;
      case 227: NEWID = 6;
        break;
    }
  }

  if (ID != NEWID) {
    ID = NEWID;
    data.param.data = ID;
    Serial.write(data.packet, sizeof(data.packet));
  }

  if (Serial.available()) {
    Serial.readBytes(dataRecv.packet, sizeof(dataRecv.packet));
    switch (dataRecv.param.data) {
      case 1:
        analogWrite(hijau, 150);
        delay(3000);
        analogWrite(hijau, 0);
        break;
      case 2:
        analogWrite(merah, 150);
        delay(3000);
        analogWrite(merah, 0);
        break;
      default:
        analogWrite(hijau, 0);
        analogWrite(merah, 0);
    }
  }
}

void sendData() {
  for (int i = 0; i <= 5; i++) {
    Serial1.write(data_remove[i]);
  }
  delay(200);
}
