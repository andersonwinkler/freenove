Refactored driver for Freenove tower cooler (FNK0113B). This repo is self-contained for the tower cooler.

## Setup

```bash
python3 setup.py
```

That installs under `/opt/freenove/tower-cooler`:

```text
/opt/freenove/tower-cooler/
├── uninstall.sh
├── lib/libfreenove_ws2812_lib.so
└── app/                             # UI, tasks, assets
```

Desktop launchers are created under `~/Desktop` and
`~/.local/share/applications`, pointing at the `/opt` install.
Official APT packages (build tools, `libpio-dev`, `python3-luma.oled`, …)
stay in their normal system locations.

### Uninstall

From the repo or the installed copy:

```bash
./uninstall.sh
# or after install:
/opt/freenove/tower-cooler/uninstall.sh
```

Removes services, desktop shortcuts, and `/opt/freenove/tower-cooler`.
APT packages and the repo checkout are left alone.

### Power estimate

After install, approximate Pi 5 + tower-cooler draw (PMIC rails + LED/fan/OLED
estimates) with:

```bash
python3 /opt/freenove/tower-cooler/app/tower-cooler-power.py
# optional: average more PMIC samples
python3 /opt/freenove/tower-cooler/app/tower-cooler-power.py 10
```

### Copyright

All the files in this repository are released under [Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License](http://creativecommons.org/licenses/by-nc-sa/3.0/).

![markdown](https://i.creativecommons.org/l/by-nc-sa/3.0/88x31.png)

This means you can use them on your own derived works, in part or completely. But NOT for the purpose of commercial use.
You can find a copy of the license in this repository.

Freenove brand and logo are copyright of Freenove Creative Technology Co., Ltd. Can't be used without formal permission. For information, see: [http://www.freenove.com].
