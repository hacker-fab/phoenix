#include <LiquidCrystal_I2C.h>

// Pin definitions for rotary encoder
#define CLK 2  // Clock pin
#define DT 3   // Data pin
#define SW 4   // Switch pin

// LCD setup
LiquidCrystal_I2C lcd(0x27, 16, 2);  // I2C address 0x27, 16 column and 2 rows

// Encoder variables
volatile int counter = 0;  // Current "position" of encoder
volatile bool needsUpdate = false;  // Flag to indicate when display should update
volatile unsigned long lastButtonPress = 0;
volatile unsigned long lastEncoderISR = 0;  // For encoder debouncing
int temperature = 1000;    // Starting temperature
String currentDir = "";

void setup() {
  Serial.begin(115200);  // Initialize serial for debugging
  
  // Initialize LCD
  lcd.init();
  lcd.backlight();
  
  // Set up encoder pins
  pinMode(CLK, INPUT);
  pinMode(DT, INPUT);
  pinMode(SW, INPUT_PULLUP);
  
  // Initial pin state
  attachInterrupt(digitalPinToInterrupt(CLK), updateEncoder, CHANGE);
  
  // Initial display
  updateDisplay();
}

void updateEncoder() {
  // Simple debounce in ISR
  unsigned long now = millis();
  if (now - lastEncoderISR < 5) {  // 5ms debounce
    return;
  }
  lastEncoderISR = now;
  
  // Read the current state of CLK
  if (digitalRead(CLK) == HIGH) {
    // If DT state is different from CLK state then
    // encoder is rotating clockwise
    if (digitalRead(DT) == LOW) {
      counter++;
      if (counter > 20) counter = 20;  // Limit for 1200°C
    } else {
      counter--;
      if (counter < -99) counter = -99;  // Limit for 10°C
    }
    needsUpdate = true;  // Set flag to indicate display needs updating
  }
}

void updateDisplay() {
  // Calculate temperature based on counter
  temperature = 1000 + (counter * 10);
  
  // Ensure temperature stays within bounds
  if (temperature > 1200) temperature = 1200;
  if (temperature < 10) temperature = 10;
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Temp: ");
  lcd.print(temperature);
  lcd.print((char)223);  // Degree symbol
  lcd.print("C");
  
  lcd.setCursor(0, 1);
  lcd.print("Count: ");
  lcd.print(counter);
  
  // Debug output
  Serial.print("Counter: ");
  Serial.print(counter);
  Serial.print(" Temp: ");
  Serial.println(temperature);
}

void checkButton() {
  bool buttonState = digitalRead(SW);
  
  if (buttonState == LOW) {
    // Button is pressed
    if (millis() - lastButtonPress > 50) {  // Debounce
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Button Pressed!");
      Serial.println("Button pressed!");
      delay(500);
      updateDisplay();  // Restore normal display
      lastButtonPress = millis();
    }
  }
}

void loop() {
  // Only update display when encoder has changed
  if (needsUpdate) {
    updateDisplay();
    needsUpdate = false;  // Reset the flag
  }
  
  checkButton();  // Check for button presses
  delay(10);      // Small delay to prevent button bounce
}
