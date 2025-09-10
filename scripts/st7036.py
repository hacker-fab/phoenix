from machine import I2C, Pin
import time

# ---- Pins & I2C ----
LCD_RESET = 14           # reset pin (active-low). Set to None if not wired.
I2C_ADDR  = 0x3C         # 60 decimal for many ST7036 boards
I2C_BUS   = 0            # I2C(0) on many MCUs; adjust if needed
SCL_PIN   = 13
SDA_PIN   = 12
I2C_FREQ  = 250_000

# ---- Control bytes ----
CMD = 0x00               # Co=0, RS=0  (following bytes = commands)
DAT = 0x40               # Co=0, RS=1  (following bytes = data)

# ---- Basic commands ----
SET_DDRAM = 0x80         # OR with address (0x00..)
CLEAR     = 0x01
ENTRY_INC = 0x06         # increment, no shift
DISP_ON   = 0x0C         # display on, cursor off, blink off

# ---- Create I2C ----
i2c = I2C(I2C_BUS, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)

# ---- Low-level I2C writers ----
def wr_cmd(byte_val):
    # Send one command byte
    i2c.writeto(I2C_ADDR, bytes([CMD, byte_val]))

def wr_cmd_seq(seq):
    # Send several commands, one-by-one (simple & reliable on MicroPython)
    for b in seq:
        wr_cmd(b)

def wr_data(buf):
    # Write a bytes/bytearray of character data
    if not isinstance(buf, (bytes, bytearray)):
        buf = bytes(buf)
    i2c.writeto(I2C_ADDR, bytes([DAT]) + buf)

# ---- Convenience helpers ----
def set_cursor(col, row):
    # ST7036 2-line DDRAM: line0 base 0x00, line1 base 0x40
    base = 0x00 if row == 0 else 0x40
    wr_cmd(SET_DDRAM | (base + col))

def clear():
    wr_cmd(CLEAR)
    time.sleep_ms(2)

def print_text(s):
    wr_data(s.encode('ascii', 'replace'))

# ---- Reset & init ----
def hw_reset():
    if LCD_RESET is None:
        return
    rst = Pin(LCD_RESET, Pin.OUT)
    rst.value(0)
    time.sleep_ms(5)
    rst.value(1)
    time.sleep_ms(50)

def init_st7036():
    # Enter extended instruction set to configure bias/contrast/booster/follower
    # The exact values may need small tweaks per module; these are solid defaults.
    wr_cmd_seq([
        0x39,   # Function set: 8-bit, 2-line, IS=1 (extended)
        0x14,   # Bias 1/5 (try 0x1C for 1/4 if your module needs it)
        0x78,   # Contrast low nibble (0..15) << 4 ; here 0x7 (mid)
        0x5E,   # ICON off, Booster on, Contrast high bits (try 0x5C..0x5F)
        0x6A,   # Follower on, amplifier gain (try 0x68..0x6F)
    ])
    time.sleep_ms(200)  # allow VLCD to settle
    wr_cmd_seq([
        0x38,   # Function set: 8-bit, 2-line, IS=0 (normal instruction set)
        DISP_ON,
        CLEAR,
        ENTRY_INC,
    ])
    time.sleep_ms(2)

# ---- Demo ----
def demo():
    print("I2C scan:", i2c.scan())
    hw_reset()
    init_st7036()

    set_cursor(0, 0)
    print_text("HELLO")
    set_cursor(0, 1)
    print_text("ST7036 I2C")

demo()
