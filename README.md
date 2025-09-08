# phoenix

Phoenix is a tube furnace used for thermal oxidation and annealing.

It uses PID control to follow custom temperature profiles and works on both MicroPython on the ESP32 and a simulated Python desktop environment.

<table>
  <tr>
    <td>
      <img src="https://github.com/user-attachments/assets/3d76382d-c257-4131-b17b-15bba04e13a1" width="350"><br>
      <sub>Fig 1. Tube furnace in action</sub>
    </td>
    <td>
      <img src="https://github.com/user-attachments/assets/71b93478-83d2-484c-b73c-5136b2d3e025" width="350"><br>
      <sub>Fig 2. Simulated PID following a heat profile</sub>
    </td>
    <td>
      <img src="https://github.com/user-attachments/assets/b7655219-a86a-4da7-9037-93fa70059ff8" width="350"><br>
      <sub>Fig 3. Controlling ramp rate to prevent thermal shock</sub>
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

# Flash code
```
esptool erase-flash
esptool --baud 460800 write-flash 0 images/ESP32_GENERIC_S3-SPIRAM_OCT-20250809-v1.26.0.bin

mpremote
mpremote connect /dev/ttyUSB0 fs cp main.py :
```
