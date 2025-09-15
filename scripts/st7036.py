# st7036_force.py — brute force init to make text appear
from machine import I2C, Pin
import time

# ---- Pins & I2C ----
SCL_PIN, SDA_PIN = 13, 12
I2C_BUS = 0
I2C_FREQ = 250_000
RST_PIN = 14          # set to None if not wired

# ---- I2C address ----
ADDRS = [0x3C, 0x3D, 0x3E, 0x3F]

# ---- Control bytes ----
CMD = 0x00     # Co=0, RS=0 (commands)
DAT = 0x40     # Co=0, RS=1 (data)

# ---- Commands ----
CLEAR      = 0x01
ENTRY_INC  = 0x06
DISP_ON    = 0x0C        # display on, cursor off, blink off
DISP_CURBL = 0x0F        # display on, cursor on, blink on (diagnostic)
SET_DDRAM  = 0x80        # OR with addr
RETURN_HOME= 0x02

# ---- I2C ----
i2c = I2C(I2C_BUS, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
I2C_ADDR = None

def wr_cmd(b):
    i2c.writeto(I2C_ADDR, bytes([CMD, b]))

def wr_cmd_seq(seq):
    for x in seq:
        wr_cmd(x)

def wr_data(buf):
    if not isinstance(buf, (bytes, bytearray)):
        buf = bytes(buf)
    i2c.writeto(I2C_ADDR, bytes([DAT]) + buf)

def set_cursor(col, row, two_lines=True):
    if two_lines:
        base = 0x00 if row == 0 else 0x40
    else:
        # If it’s really a 1-line mapping, keep everything on 0..0x27
        base = 0x00
    wr_cmd(SET_DDRAM | ((base + col) & 0x7F))

def clear():
    wr_cmd(CLEAR)
    time.sleep_ms(2)

def print_text(s):
    wr_data(s.encode('ascii', 'replace'))

def hw_reset():
    if RST_PIN is None:
        return
    rst = Pin(RST_PIN, Pin.OUT)
    rst.value(0); time.sleep_ms(5)
    rst.value(1); time.sleep_ms(50)

def find_addr():
    found = i2c.scan()
    for a in ADDRS:
        if a in found:
            return a
    # fallback probe
    for a in ADDRS:
        try:
            i2c.writeto(a, bytes([CMD, 0x38]))
            return a
        except OSError:
            pass
    return None

def write_test_pattern(two_lines=True):
    # Big obvious patterns to maximize visibility
    line0 = "0123456789ABCDEF"
    line1 = "st7036 I2C hello!"
    set_cursor(0, 0, two_lines)
    print_text(line0)
    set_cursor(0, 1 if two_lines else 0, two_lines)
    print_text(line1)

def try_combo(two_lines, bias_1_5, low_nib, hi_bits, follower, booster_on):
    # Enter extended instruction set
    wr_cmd(0x30 | (0x08 if two_lines else 0x00))  # ensure 8-bit first (IS=0)
    wr_cmd(0x39 if two_lines else 0x31)           # IS=1 (extended), set N accordingly

    # Bias
    wr_cmd(0x14 if bias_1_5 else 0x1C)

    # Contrast low nibble (as 0x70..0x7F)
    wr_cmd(0x70 | (low_nib & 0x0F))

    # Power/icon/contrast high bits: bit2=Booster
    # Base 0x50, add hi bits (0..3), optionally set booster bit (0x08)
    pib = 0x50 | (hi_bits & 0x03)
    if booster_on:
        pib |= 0x08
    wr_cmd(pib)

    # Follower control/gain
    wr_cmd(follower)  # 0x68..0x6F typical

    time.sleep_ms(200)  # allow VLCD to settle

    # Back to normal instruction set, turn on display with cursor+blink, clear, entry
    wr_cmd(0x30 | (0x08 if two_lines else 0x00))  # IS=0, proper line count
    wr_cmd(DISP_CURBL)
    clear()
    wr_cmd(ENTRY_INC)

    # Write test text
    write_test_pattern(two_lines)

def main():
    print("scan:", [hex(x) for x in i2c.scan()])
    hw_reset()
    global I2C_ADDR
    I2C_ADDR = find_addr()
    if I2C_ADDR is None:
        raise RuntimeError("ST7036 not found")
    print("Using addr:", hex(I2C_ADDR))

    # Parameter spaces
    two_line_options = [True, False]       # try 2-line and 1-line
    bias_options     = [True, False]       # 1/5, 1/4
    low_nibs         = list(range(0, 16))  # 0..15 => 0x70..0x7F
    hi_bits_opts     = [0, 1, 2, 3]        # contrast high bits
    followers        = [0x68, 0x69, 0x6A, 0x6B, 0x6C, 0x6D, 0x6E, 0x6F]
    boosters         = [True, False]       # booster on/off

    # Try quick, common combos first
    quick = [
        (True,  True, 7, 2, 0x6A, True),
        (True,  False,7, 2, 0x6A, True),
        (True,  True, 9, 3, 0x6C, True),
        (True,  True, 7, 2, 0x6A, False),
    ]
    for params in quick:
        try:
            two_lines,bias,lo,hi,foll,boost = params
            try_combo(two_lines, bias, lo, hi, foll, boost)
            print("QUICK HIT:", params)
            time.sleep_ms(600)
        except OSError:
            pass

    # Full sweep (comment out if the quick pass already works)
    for two_lines in two_line_options:
        for bias in bias_options:
            for boost in boosters:
                for hi in hi_bits_opts:
                    for foll in followers:
                        for lo in low_nibs:
                            try:
                                try_combo(two_lines, bias, lo, hi, foll, boost)
                                print("TRY:", dict(two_lines=two_lines,bias_1_5=bias,
                                                   low_nib=lo, hi_bits=hi,
                                                   follower=hex(foll), booster_on=boost))
                                # Give your eyes a chance—wait a bit
                                time.sleep_ms(50)
                            except OSError:
                                # I2C hiccup; keep going
                                pass

main()
