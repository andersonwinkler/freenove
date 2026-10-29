#!/usr/bin/env python3
'''Report Raspberry Pi 5 + Freenove Tower Cooler power estimates.

Pi 5 exposes per-rail currents via the PMIC, but GPIO 5V loads (WS2812 LEDs,
fan) are not metered directly — those are estimated from config and PWM duty.
'''

import json
import os
import re
import subprocess
import sys
import time

_APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(_APP_DIR, 'app_config.json')
FAN_HWMON_BASE = '/sys/devices/platform/cooling_fan/hwmon'
LED_COUNT = 6
# Typical WS2812B: ~20 mA per channel => ~60 mA full white @ 5V
LED_MA_FULL_WHITE = 60
# Typical small 5V cooler fan full-speed draw
FAN_A_FULL = 0.20
OLED_A_33 = 0.022
PMIC_EFFICIENCY = 0.85

# gradual/rainbow average roughly ~40% of full-white current
LED_MODE_DUTY = {
    0: 0.40,  # rainbow
    1: 0.40,  # gradual
    2: 0.25,  # breathing (avg)
    3: 0.20,  # blink
    4: 0.17,  # rotate (1 of 6 lit)
    5: 0.40,  # following (~4 of 6-ish pattern; treat as mid)
    6: 0.33,  # static single color (~1 channel)
    7: 0.30,  # code cycle
    8: 0.00,  # off
}


def run(cmd):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ''


def read_pmic():
    out = run(['vcgencmd', 'pmic_read_adc'])
    currents, volts = {}, {}
    for line in out.splitlines():
        m = re.match(r'\s*(\S+)\s+(current|volt)\((\d+)\)=([0-9.]+)([AV])', line)
        if not m:
            continue
        name, kind, _, val, _unit = m.groups()
        val = float(val)
        if kind == 'current':
            currents[name.replace('_A', '')] = val
        else:
            volts[name.replace('_V', '')] = val
    return currents, volts


def pmic_breakdown(currents, volts):
    pairs = [
        'VDD_CORE', '3V3_SYS', '1V8_SYS', '0V8_SW', '1V1_SYS',
        'DDR_VDD2', 'DDR_VDDQ', 'HDMI', '3V7_WL_SW', '3V3_DAC',
        '3V3_ADC', '0V8_AON']
    rows = []
    total = 0.0
    for name in pairs:
        if name in currents and name in volts:
            i, v = currents[name], volts[name]
            p = i * v
            rows.append((name, i, v, p))
            total += p
    rows.sort(key=lambda r: -r[3])
    return rows, total


def read_fan_pwm():
    try:
        for name in os.listdir(FAN_HWMON_BASE):
            if not name.startswith('hwmon'):
                continue
            path = os.path.join(FAN_HWMON_BASE, name, 'pwm1')
            with open(path) as f:
                return max(0, min(255, int(f.read().strip())))
    except (OSError, ValueError):
        pass
    return None


def read_fan_rpm():
    try:
        for name in os.listdir(FAN_HWMON_BASE):
            if not name.startswith('hwmon'):
                continue
            path = os.path.join(FAN_HWMON_BASE, name, 'fan1_input')
            if os.path.exists(path):
                with open(path) as f:
                    return int(f.read().strip())
    except (OSError, ValueError):
        pass
    return None


def read_cpu_temp():
    try:
        with open('/sys/class/thermal/thermal_zone0/temp') as f:
            return int(f.read().strip()) / 1000.0
    except OSError:
        return None


def decode_throttled(val):
    flags = {
        0: 'Under-voltage now',
        1: 'Arm frequency capped now',
        2: 'Currently throttled',
        3: 'Soft temp limit now',
        16: 'Under-voltage has occurred',
        17: 'Arm frequency capped has occurred',
        18: 'Throttling has occurred',
        19: 'Soft temp limit has occurred'}
    return [name for bit, name in flags.items() if val & (1 << bit)]


def load_config():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def estimate_accessories(cfg, fan_pwm):
    led = cfg.get('LED', {})
    fan = cfg.get('Fan', {})
    oled = cfg.get('OLED', {})

    mode = int(led.get('mode', 8))
    brightness = int(led.get('brightness', 255)) / 255.0
    color = (
        int(led.get('red_value', 0)),
        int(led.get('green_value', 0)),
        int(led.get('blue_value', 0)))
    mode_frac = LED_MODE_DUTY.get(mode, 0.35)

    # Static mode: scale by lit channels / 3
    if mode == 6:
        channels = sum(1 for c in color if c > 0)
        channel_frac = channels / 3.0 if channels else 0.0
        # mix brightness into channel levels
        level = sum(color) / (255.0 * 3.0)
        led_frac = max(channel_frac * brightness * 0.9, level * brightness)
    else:
        led_frac = mode_frac * brightness

    led_a = LED_COUNT * (LED_MA_FULL_WHITE / 1000.0) * led_frac
    led_w = led_a * 5.0

    if fan_pwm is None:
        fan_pwm = 0
    fan_a = FAN_A_FULL * (fan_pwm / 255.0)
    fan_w = fan_a * 5.0

    oled_on = any(
        screen.get('is_run_on_oled', False)
        for screen in oled.values()
        if isinstance(screen, dict))
    oled_a = OLED_A_33 if oled_on else 0.0
    oled_w = oled_a * 3.3

    return {
        'led': {
            'mode': mode,
            'brightness': int(led.get('brightness', 255)),
            'color': color,
            'amps': led_a,
            'watts': led_w,
            'worst_w': LED_COUNT * (LED_MA_FULL_WHITE / 1000.0) * 5.0},
        'fan': {
            'mode': int(fan.get('mode', -1)),
            'pwm': fan_pwm,
            'amps': fan_a,
            'watts': fan_w,
            'worst_w': FAN_A_FULL * 5.0},
        'oled': {
            'on': oled_on,
            'amps': oled_a,
            'watts': oled_w,
            'worst_w': OLED_A_33 * 3.3},
        'total_w': led_w + fan_w + oled_w,
        'worst_w': (
            LED_COUNT * (LED_MA_FULL_WHITE / 1000.0) * 5.0
            + FAN_A_FULL * 5.0
            + OLED_A_33 * 3.3)}


def fmt_w(w):
    return f'{w:5.2f} W'


def fmt_ma(a):
    return f'{a * 1000:6.0f} mA'


def main():
    samples = 5
    if len(sys.argv) > 1:
        try:
            samples = max(1, int(sys.argv[1]))
        except ValueError:
            print(f'Usage: {sys.argv[0]} [samples]', file=sys.stderr)
            sys.exit(2)

    model = run(['cat', '/proc/device-tree/model']).replace('\x00', '') or 'Raspberry Pi'
    throttled_raw = run(['vcgencmd', 'get_throttled'])
    throttled_val = 0
    m = re.search(r'0x([0-9a-fA-F]+)', throttled_raw)
    if m:
        throttled_val = int(m.group(1), 16)
    flags = decode_throttled(throttled_val)

    pmic_totals = []
    last_rows, last_c, last_v = [], {}, {}
    for i in range(samples):
        last_c, last_v = read_pmic()
        last_rows, total = pmic_breakdown(last_c, last_v)
        pmic_totals.append(total)
        if i + 1 < samples:
            time.sleep(0.35)
    pmic_avg = sum(pmic_totals) / len(pmic_totals)

    fan_pwm = read_fan_pwm()
    fan_rpm = read_fan_rpm()
    cpu_temp = read_cpu_temp()
    cfg = load_config()
    acc = estimate_accessories(cfg, fan_pwm if fan_pwm is not None else 0)

    # Input estimate: PMIC output / efficiency + 5V accessories (fan+LEDs).
    # OLED is on 3.3V so already partly in 3V3_SYS; still show separately.
    wall_w = (pmic_avg / PMIC_EFFICIENCY) + acc['led']['watts'] + acc['fan']['watts']
    ext5v = last_v.get('EXT5V')

    print(f'{model}')
    print('=' * 56)
    if cpu_temp is not None:
        print(f'CPU temp:     {cpu_temp:.1f} C')
    print(f'Throttled:    {throttled_raw or "n/a"}')
    if flags:
        for f in flags:
            print(f'  ! {f}')
    else:
        print('  No undervoltage or throttling (now or since boot)')
    if ext5v is not None:
        print(f'EXT5V:        {ext5v:.3f} V')
    print()

    print(f'Pi PMIC rails (avg of {samples} samples)')
    print('-' * 56)
    for name, i, v, p in last_rows:
        if p < 0.005:
            continue
        print(f'  {name:12s}  {i:6.3f} A @ {v:5.3f} V = {fmt_w(p)}')
    print(f'  {"TOTAL":12s}                    {fmt_w(pmic_avg)}')
    print()

    print('Tower cooler accessories (estimated)')
    print('-' * 56)
    led = acc['led']
    print(
        f'  LEDs  x{LED_COUNT}   mode={led["mode"]}  bright={led["brightness"]}  '
        f'RGB{led["color"]}')
    print(
        f'             {fmt_ma(led["amps"])} @ 5 V   = {fmt_w(led["watts"])}'
        f'   (worst {fmt_w(led["worst_w"]).strip()})')

    fan = acc['fan']
    rpm_s = f', {fan_rpm} RPM' if fan_rpm is not None else ''
    pwm_s = fan['pwm'] if fan['pwm'] is not None else '?'
    print(f'  Fan         mode={fan["mode"]}  PWM={pwm_s}/255{rpm_s}')
    print(
        f'             {fmt_ma(fan["amps"])} @ 5 V   = {fmt_w(fan["watts"])}'
        f'   (worst {fmt_w(fan["worst_w"]).strip()})')

    oled = acc['oled']
    state = 'on' if oled['on'] else 'off'
    print(f'  OLED        {state}')
    print(
        f'             {fmt_ma(oled["amps"])} @ 3.3 V = {fmt_w(oled["watts"])}'
        f'   (worst {fmt_w(oled["worst_w"]).strip()})')
    print(
        f'  {"SUBTOTAL":12s}                    {fmt_w(acc["total_w"])}'
        f'   (worst {fmt_w(acc["worst_w"]).strip()})')
    print()

    print('Approx. input draw')
    print('-' * 56)
    if ext5v is not None and ext5v > 0:
        print(f'  Now:  {fmt_w(wall_w)}  (~{wall_w / ext5v * 1000:.0f} mA @ {ext5v:.2f} V EXT5V)')
    else:
        print(f'  Now:  {fmt_w(wall_w)}')
    print()
    print('Notes:')
    print('  - Accessory figures are estimates (5 V GPIO path is not metered).')
    print('  - OLED 3.3 V draw is partly included in 3V3_SYS already.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
