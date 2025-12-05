from smartcard.System import readers
from smartcard.Exceptions import NoCardException
import pyautogui
import time
import re
import tkinter as tk
from tkinter import messagebox
import pyperclip

# ✅ UID Validation Pattern (7 HEX bytes)
UID_PATTERN = r"^([0-9A-F]{2}:){6}[0-9A-F]{2}$"

def show_popup(title, msg):
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(title, msg)
    root.destroy()

r = readers()

if len(r) == 0:
    print("❌ No NFC Reader Found")
    exit()

reader = r[0]
print("✅ Using reader:", reader)

last_uid = None

while True:
    try:
        connection = reader.createConnection()
        connection.connect()

        get_uid = [0xFF, 0xCA, 0x00, 0x00, 0x00]
        data, sw1, sw2 = connection.transmit(get_uid)

        # ✅ If UID was NOT returned correctly → ignore silently
        if sw1 != 0x90:
            time.sleep(0.5)
            continue

        uid = ":".join([format(x, '02X') for x in data])
        print("📖 UID Read:", uid)

        # ✅ STOP duplicate UID
        if uid == last_uid:
            time.sleep(0)
            show_popup(
                    "NFC Duplicate",
                    "❌ UID READ successfully\nBUT NOT WRITTEN in software!"
                )

        last_uid = uid

        # ✅ VALIDATE UID FORMAT
        if re.fullmatch(UID_PATTERN, uid):
            try:
                time.sleep(0.3)
                pyperclip.copy(uid)
                pyautogui.hotkey("ctrl", "v")
                pyautogui.press("enter")
                print("✅ VALID UID SENT:", uid)

            except Exception:
                show_popup(
                    "NFC Write Error",
                    "❌ UID READ successfully\nBUT NOT WRITTEN in software!"
                )

        else:
            show_popup(
                "Invalid UID",
                f"❌ Invalid UID Format Detected:\n{uid}"
            )

        time.sleep(2)

    except NoCardException:
        last_uid = None
        time.sleep(0.3)
