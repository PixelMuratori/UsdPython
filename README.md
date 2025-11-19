# Usd – Custom Pixar USD Python Build

**Full Pixar USD build with Python, UsdImaging, Hydra, and plugins**
Maintained by **PixelMuratori**

---

## Overview

This repository provides a **prebuilt Python package of Pixar USD** with the features our team needs, including:

- **UsdImaging & Hydra** support
- **Qt viewer integration** (embedded in Qt windows)
- Precompiled binaries for **Windows** (Python ≥ 3.9)
- Included **plugins, scripts, and resources**

> ⚠️ This package is intended to **save build time** for our team and ensure all team members use the **same USD build**. It is **not the official usd-core** package, and it contains custom modifications.

---

## Installation

Install directly from GitHub (public repo):

```bash
pip install git+https://github.com/PixelMuratori/Usd.git
```

## Requirements

* Python 3.9 or higher

* Dependencies automatically included:
    * jinja2
    * PyOpenGL

## 📜 License

Based on Pixar USD (Apache 2.0)<br>
LICENSE and NOTICE files are included in this package.<br>
You may use, modify, and redistribute this package according to the Apache 2.0 terms.