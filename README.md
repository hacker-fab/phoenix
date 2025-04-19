# phoenix

Phoenix is a tube furnace used for thermal oxidation and annealing processes.

It uses PID control to follow custom temperature profiles and works on both MicroPython on the ESP32 and a simulated Python desktop environment.

<table>
  <tr>
    <td>
      <img src="https://github.com/user-attachments/assets/3d76382d-c257-4131-b17b-15bba04e13a1" width="300"><br>
      <sub>Fig 1. Tube furnace in action</sub>
    </td>
    <td>
      <img src="https://github.com/user-attachments/assets/71b93478-83d2-484c-b73c-5136b2d3e025" width="300"><br>
      <sub>Fig 2. Simulated PID following a heat profile</sub>
    </td>
    <td>
      <img src="https://github.com/user-attachments/assets/b7655219-a86a-4da7-9037-93fa70059ff8" width="300"><br>
      <sub>Fig 3. Controlled ramp rates</sub>
    </td>
  </tr>
</table>

# Python setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

# Micropython setup

Install micropython
```bash
https://github.com/micropython/micropython/tree/master/ports/unix#readme
```

Install `typing`
```bash
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

# Arduino setup (legacy)

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
