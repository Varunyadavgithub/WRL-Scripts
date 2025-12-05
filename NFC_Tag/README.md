# **NFC Tag Auto-Reader & Auto-Writer Script**

This Python script automatically reads the UID (Unique Identifier) from an NFC tag using a PC/SC-compatible NFC reader.
When a valid UID is detected, it is automatically copied to the clipboard and typed into the active application using keyboard automation.

The script also displays popup alerts for invalid UIDs, duplicate scans, and write failures.

---

## ✨ **Features**

* 📡 Automatically detects a connected NFC reader
* 🔄 Continuously listens for NFC tag placement
* 🆔 Reads the UID using standard APDU command
* ✔ Validates UID format (7-byte hex UID)
* 📋 Copies UID to clipboard
* ⌨ Automatically pastes & submits the UID
* ⚠ Popup alerts for:

  * Invalid UID format
  * Duplicate UID scans
  * Write/Automation errors
* 🛡 Prevents duplicate UID inputs accidentally being re-sent

---

## 📦 **Requirements**

Install the dependencies using:

```bash
pip install -r requirements.txt
```

### `requirements.txt`

```
pyscard
pyautogui
pyperclip
```

**Notes:**

* `tkinter`, `time`, and `re` come with Python and require no installation.
* This script requires **Windows**, since `pyautogui` key simulation and PC/SC smartcard stack are most reliable there.

---

## 🛠 **How It Works**

1. The script identifies available PC/SC NFC readers:

   ```python
   r = readers()
   ```
2. It connects to the first available reader.
3. It sends the APDU command to request the tag UID:

   ```python
   get_uid = [0xFF, 0xCA, 0x00, 0x00, 0x00]
   ```
4. If the UID is valid (matches `XX:XX:XX:XX:XX:XX:XX`), it:

   * Copies it to clipboard
   * Simulates Ctrl+V and Enter to submit it to the active window
5. Duplicate UIDs trigger a popup warning instead of re-typing.
6. Removing the card resets the state.

---

## 📑 **Script Overview**

The UID must match this pattern:

```
XX:XX:XX:XX:XX:XX:XX
```

Where each `XX` is a hexadecimal byte (`00–FF`).

The script has built-in popups for errors and duplicate cards using:

```python
tkinter.messagebox
```

Keyboard automation is performed with:

```python
pyautogui.hotkey("ctrl", "v")
pyautogui.press("enter")
```

---

## ▶️ **Running the Script**

Make sure an NFC reader is plugged in, then run:

```bash
python nfc_reader.py
```

Keep your target application focused—this is where the UID will be auto-pasted.

---

## 🧪 **Tested On**

* **Windows 10/11**
* ACR122U / similar PCSC-compatible NFC readers
* Python 3.8–3.12

---

## ⚠️ **Important Notes**

* Ensure no app blocks simulated keystrokes (some admin apps may).
* Popups may appear **behind fullscreen applications** unless focus is switched.
* Do not touch the keyboard during UID auto-paste unless necessary.