const int relayPin = 9;  // PWM output pin for the solid state relay

void setup() {
  pinMode(relayPin, OUTPUT);
}

void loop() {
  // Generate a 50% duty cycle pulse wave using analogWrite.
  // The analogWrite value ranges from 0 (0% duty cycle) to 255 (100% duty cycle)
  analogWrite(relayPin, 128);  // 50% duty cycle (128 out of 255)

  // The PWM hardware continuously outputs the pulse wave,
  // so no additional code is required in the loop.
}