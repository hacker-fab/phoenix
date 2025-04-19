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

# Python setup
```
pip install -r requirements.txt
```

# Micropython setup

Install micropython
```
https://github.com/micropython/micropython/tree/master/ports/unix#readme
```

Install `typing`
```
micropython -m mip install github:josverl/micropython-stubs/mip/typing.mpy
```

Install `udataclasses`
```bash
cd ~/.micropython/lib
# extract src/udataclasses
git clone https://github.com/dhrosa/udataclasses.git tmp
mv tmp/src/udataclasses .
rm -rf tmp
```
