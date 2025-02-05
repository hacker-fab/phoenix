Tube Furnace used at the Waterloo Hacker Fab

# Installation

1. Install Arduino libraries
```
arduino-cli core install arduino:avr
arduino-cli lib update-index
arduino-cli lib install "Adafruit MAX31856 Library"
arduino-cli lib install "LiquidCrystal I2C"
arduino-cli lib install "RunningAverage"
```

2. Build
```
arduino-cli compile \
    --fqbn arduino:avr:uno \
    --libraries TubeFurnace/libraries \
    TubeFurnace
```
