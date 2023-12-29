const int lockPin = 7; // Replace with the actual pin connected to the lock relay

void setup() {
  Serial.begin(9600);
  pinMode(lockPin, OUTPUT);
}

void loop() {
  if (Serial.available() > 0) {
    char signal = Serial.read();
    if (signal == '1') {
      unlockDoor();
    }
  }
}

void unlockDoor() {
  digitalWrite(lockPin, HIGH); // Assuming HIGH activates the lock mechanism
  delay(5000); // Keep the door unlocked for 5 seconds (adjust as needed)
  digitalWrite(lockPin, LOW); // Lock the door
}
