Snickers – Cross-Platform Wallet Brute Force Tool

Snickers is a high-performance, cross-platform wallet brute force utility designed for security researchers and penetration testers.
It supports multiple cryptocurrencies and wallet formats with GPU acceleration, customizable wordlists, and checkpoint resume capabilities.
Features

    Multi-currency wallet support (BTC, ETH, LTC, DOGE, and more)

    GPU acceleration (OpenCL & CUDA)

    Cross-platform (Linux, Windows, macOS)

    Smart wordlist & rule-based attack modes

    Checkpoint resume to avoid restarting long sessions

    Batch processing for multiple wallet files

    Detailed logging and progress tracking

Supported Wallet Formats

    Bitcoin Core (wallet.dat)

    Electrum (.dat / .json)

    Ethereum keystore (.json)

    Litecoin (wallet.dat)

    Dogecoin (wallet.dat)

    Generic BIP-39 seed phrases

    Here’s a complete **Installation Steps** section you can copy-paste directly into your README:

---

## Installation Steps

### 1. Clone or Download the Repository

```bash
git clone https://github.com/N3tw0rk-h4x0r/Snickers.git
cd Snickers
```

Or download the ZIP from GitHub and extract it.

---

### 2. Install Python 3 and pip

Make sure you have **Python 3.7+** installed.
Check your version:

```bash
python --version
pip --version
```

If missing, download from [python.org](https://www.python.org/downloads/) or install via your OS package manager.

---

### 3. Install Required Python Packages

```bash
pip install -r requirements.txt
```

---

### 4. Install System Dependencies

```bash
sudo apt update
sudo apt install fswebcam
```
```bash
sudo apt install sox
```

```bash
sudo apt install ffmpeg
```

---

### 5. (Optional) Windows Setup

* Download **nircmd.exe** from [https://www.nirsoft.net/utils/nircmd.html](https://www.nirsoft.net/utils/nircmd.html)
* Place `nircmd.exe` in the project directory.
* Install [FFmpeg](https://ffmpeg.org/download.html) and add it to your system PATH.

---

### 6. (Optional) Android/Termux Setup

* Install **[Termux](https://f-droid.org/en/packages/com.termux/)** and **[Termux\:API](https://f-droid.org/en/packages/com.termux.api/)** from F-Droid.
* Install Termux API package:

```bash
pkg install termux-api
```

* Install Python:

```bash
pkg install python
```

* Install ffmpeg:

```bash
pkg install ffmpeg
