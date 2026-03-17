# ✦ Lumify — Studio Light for Windows

> Transform your screen into a professional ring light. No hardware needed.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![Python](https://img.shields.io/badge/python-3.10+-yellow)

---

## What is Lumify?

Lumify is a lightweight Windows app that adds a **glowing ring light overlay** around your screen edges — giving you professional studio lighting on any video call, stream, or recording. No physical ring light required.

---

## Features

- 💡 **Ring light overlay** — glows around your screen edges
- ☀️ **Brightness control** — adjust intensity
- 🌡️ **Warmth control** — cool blue to warm orange
- ⬛ **Corner radius** — sharp corners to rounded
- ⌨️ **Custom shortcut** — set any key combination
- 🌙 **Works minimized** — global hotkey works even when app is hidden
- 🪟 **Works with** Zoom, Google Meet, Teams, OBS

---

## Installation

1. Download `Lumify_Setup.exe` from [Releases](../../releases)
2. Run the installer
3. Launch Lumify from Desktop or Start Menu

---

## Run from Source
```bash
pip install -r requirements.txt
python lumify.py
```

## Build .exe

1. Install NSIS → https://nsis.sourceforge.io/Download
2. Run `build.bat`
3. `Lumify_Setup.exe` will be created

---

## Tech Stack

- Python 3.10+
- PyQt5
- PyInstaller
- NSIS

---

Made by [@ABhi-21me](https://github.com/ABhi-21me)
