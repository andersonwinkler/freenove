# Freenove_Tower_Cooler_for_Raspberry_Pi

> A tower cooler kit suitable for Raspberry Pi 5.

## Introduction
* FNK0113A
Single-fan without 0.96inch OLED
<img src='Picture/FNK0113A.MAIN.jpg' width='70%'/>

* FNK0113B
Dual-fan with 0.96inch OLED
<img src='Picture/FNK0113B.MAIN.jpg' width='70%'/>

## Setup (Raspberry Pi 5)

This repo is self-contained for the tower cooler. LED native sources live
under `native/ws2812/` (vendored from Freenove utils); runtime still uses
the APT `libpio` package.

From the repo root:

```bash
python3 setup.py
```

That installs this product under `/opt/freenove/tower-cooler` (other
Freenove kits can use sibling directories under `/opt/freenove/`):

```text
/opt/freenove/tower-cooler/
├── lib/libfreenove_ws2812_lib.so
└── app/                             # UI, tasks, assets
```

Desktop launchers are created under `~/Desktop` and
`~/.local/share/applications`, pointing at the `/opt` install.
Official APT packages (build tools, `libpio-dev`, `python3-luma.oled`, …)
stay in their normal system locations.

> If you meet any difficulties, please contact our support team for help.

### Support

Freenove provides free and quick customer support. Including but not limited to:

* Quality problems of products
* Using Problems of products
* Questions of learning and creation
* Opinions and suggestions
* Ideas and thoughts

Please send an email to:

[support@freenove.com](mailto:support@freenove.com)

We will reply to you within one working day.

### Purchase

Please visit the following page to purchase our products:

http://store.freenove.com

Business customers please contact us through the following email address:

[sale@freenove.com](mailto:sale@freenove.com)

### Copyright

All the files in this repository are released under [Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License](http://creativecommons.org/licenses/by-nc-sa/3.0/).

![markdown](https://i.creativecommons.org/l/by-nc-sa/3.0/88x31.png)

This means you can use them on your own derived works, in part or completely. But NOT for the purpose of commercial use.
You can find a copy of the license in this repository.

Freenove brand and logo are copyright of Freenove Creative Technology Co., Ltd. Can't be used without formal permission.


### About

Freenove is an open-source electronics platform.

Freenove is committed to helping customer quickly realize the creative idea and product prototypes, making it easy to get started for enthusiasts of programing and electronics and launching innovative open source products.

Our services include:

* Robot kits
* Learning kits for Arduino, Raspberry Pi and micro:bit
* Electronic components and modules, tools
* Product customization service

Our code and circuit are open source. You can obtain the details and the latest information through visiting the following web site:

http://www.freenove.com