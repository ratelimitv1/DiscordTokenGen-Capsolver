import time
import requests
import os
from colorama import init, Fore, Style
import json
import random
from enum import Enum
from typing import Optional, Dict, List
import multiprocessing
import sys
from pystyle import Center
from datetime import datetime
import keyboard
import nodriver as uc
import re
import base64
from notifypy import Notify
import urllib3
import asyncio
import string
import warnings
import signal
import atexit
import ctypes
try:
    import pygetwindow as gw
    import pyautogui
except ImportError:
    gw = None
    pyautogui = None


warnings.filterwarnings("ignore")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Browser extension (auto captcha solver) ──────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
extension_path = os.path.join(BASE_DIR, "NewFol")

# ── NopeCHA extension ─────────────────────────────────────────────────────────
import zipfile
NOPECHA_ZIP = os.path.join(BASE_DIR, "nopecha_extension.zip")
NOPECHA_DIR = os.path.join(BASE_DIR, "nopecha")
NOPECHA_API_KEY = "I-CX6GPNBR6YVA"

# Extract NopeCHA extension if not already extracted
if os.path.isfile(NOPECHA_ZIP) and not os.path.isdir(NOPECHA_DIR):
    with zipfile.ZipFile(NOPECHA_ZIP, 'r') as zf:
        zf.extractall(NOPECHA_DIR)

# Resolve the actual extension folder path
if os.path.isdir(NOPECHA_DIR):
    # Look for the subfolder that contains manifest.json
    _nopecha_found = None
    for _item in os.listdir(NOPECHA_DIR):
        _candidate = os.path.join(NOPECHA_DIR, _item)
        if os.path.isdir(_candidate) and os.path.isfile(os.path.join(_candidate, "manifest.json")):
            _nopecha_found = _candidate
            break
    if _nopecha_found:
        nopecha_ext_path = _nopecha_found
    elif os.path.isfile(os.path.join(NOPECHA_DIR, "manifest.json")):
        nopecha_ext_path = NOPECHA_DIR
    else:
        nopecha_ext_path = None
else:
    nopecha_ext_path = None

import logging
logging.getLogger("asyncio").setLevel(logging.CRITICAL)
logging.getLogger("nodriver").setLevel(logging.CRITICAL)
logging.getLogger("uc").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)

# ══════════════════════════════════════════════════════════════════
#  UNUSED EMAILS MANAGER  (ported from cap.py)
# ══════════════════════════════════════════════════════════════════

UNUSED_EMAILS_FILE = 'unused_emails.txt'

# Globals used by the CTRL+C / atexit handler
_current_email_data = None   # set to email_data dict while an account is being created
_email_saved_flag   = False  # prevents double-saving on exit

class UnusedEmailsManager:
    """Stores/retrieves failed email accounts in unused_emails.txt for reuse."""

    @staticmethod
    def save_unused_email(email_data: dict) -> bool:
        try:
            line = json.dumps(email_data)
            with open(UNUSED_EMAILS_FILE, 'a', encoding='utf-8') as f:
                f.write(line + '\n')
            return True
        except Exception as e:
            return False

    @staticmethod
    def get_unused_email() -> Optional[dict]:
        try:
            if not os.path.exists(UNUSED_EMAILS_FILE):
                return None
            with open(UNUSED_EMAILS_FILE, 'r', encoding='utf-8') as f:
                lines = [l.strip() for l in f if l.strip()]
            if not lines:
                return None
            first_line = lines[0]
            remaining  = lines[1:]
            with open(UNUSED_EMAILS_FILE, 'w', encoding='utf-8') as f:
                f.write('\n'.join(remaining) + ('\n' if remaining else ''))
            return json.loads(first_line)
        except Exception:
            return None

    @staticmethod
    def count_unused_emails() -> int:
        try:
            if not os.path.exists(UNUSED_EMAILS_FILE):
                return 0
            with open(UNUSED_EMAILS_FILE, 'r', encoding='utf-8') as f:
                return sum(1 for l in f if l.strip())
        except Exception:
            return 0


def _handle_exit(signum=None, frame=None):
    """Save the in-progress email on CTRL+C / SIGTERM so it isn't wasted."""
    global _current_email_data, _email_saved_flag
    if _email_saved_flag:
        return
    if _current_email_data:
        try:
            UnusedEmailsManager.save_unused_email(_current_email_data)
            _email_saved_flag = True
        except Exception:
            pass
    if signum is not None:
        sys.exit(0)

signal.signal(signal.SIGINT,  _handle_exit)
signal.signal(signal.SIGTERM, _handle_exit)
atexit.register(_handle_exit)

# ══════════════════════════════════════════════════════════════════
#  YOUR TOOL (unchanged below)
# ══════════════════════════════════════════════════════════════════

class FilteredStdout:
    def __init__(self, original):
        self.original = original
        self._blocked = [
            "successfully removed temp profile",
            "temp profile",
        ]

    def write(self, text):
        lower = text.lower()
        if any(phrase in lower for phrase in self._blocked):
            return
        self.original.write(text)

    def flush(self):
        self.original.flush()

    def __getattr__(self, attr):
        return getattr(self.original, attr)

sys.stdout = FilteredStdout(sys.stdout)

class SuppressWarnings:
    def __init__(self):
        self.original_stderr = sys.stderr
        self.devnull = open(os.devnull, 'w')
    
    def __enter__(self):
        sys.stderr = self.devnull
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stderr = self.original_stderr
        self.devnull.close()

warnings_suppressor = SuppressWarnings()
warnings_suppressor.__enter__()

nighty = "\033[38;2;200;65;246m"
blume = "\033[38;5;208m"
paste = "\x1b[0;92;49m"
maow = "\x1b[0;94;49m"

class Timer:
    def __format__(self, _):
        return datetime.now().strftime("%H:%M:%S")
timer = Timer()

init(autoreset=True)

with open('config.json', 'r') as f:
    config = json.load(f)

os.makedirs("output", exist_ok=True)

# ── Token output file ──────────────────────────────────────────────────────
TOKENS_FILE = os.path.join(BASE_DIR, "tokens.txt")

def save_token(email: str, password: str, token: str):
    """Save token to tokens.txt in the same folder."""
    try:
        with open(TOKENS_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{email}:{password}:{token}\n")
        log.success(f"Token saved to tokens.txt")
    except Exception as e:
        log.error(f"Failed to save token: {e}")

# ── Mail provider selection (set in main()) ────────────────────────────────
SELECTED_MAIL_PROVIDER = "hotmail007"  # "hotmail007" or "custom"
SELECTED_CUSTOM_DOMAIN = "boostcord.shop"

# ── Proxy helpers ──────────────────────────────────────────────────
def _load_proxies() -> List[str]:
    """Load proxies from config or proxies.txt file."""
    proxies = config.get("proxies", [])
    if not proxies:
        proxy_file = config.get("proxy_file", "proxies.txt")
        if os.path.isfile(proxy_file):
            with open(proxy_file, "r") as f:
                proxies = [line.strip() for line in f if line.strip()]
    return proxies

def get_proxy() -> Optional[str]:
    """Return a random proxy string from the list, or None if disabled/empty."""
    if not config.get("use_proxy", False):
        return None
    proxies = _load_proxies()
    if not proxies:
        return None
    proxy = random.choice(proxies)
    # Normalise: ensure scheme is present
    if not proxy.startswith(("http://", "https://", "socks5://", "socks4://")):
        proxy = "http://" + proxy
    return proxy

def proxy_dict(proxy: Optional[str]) -> Optional[Dict]:
    """Convert a proxy string to a requests-compatible dict."""
    if not proxy:
        return None
    return {"http": proxy, "https": proxy}

class LogLevel(Enum):
    DEBUG = 1
    INFO = 2
    WARNING = 3
    SUCCESS = 4
    ERROR = 5
    CRITICAL = 6
    SPACE = 7

class Logger:
    # ANSI colors
    GRAY    = "\033[38;5;240m"
    WHITE   = "\033[97m"
    RED     = "\033[38;5;196m"
    GREEN   = "\033[38;5;40m"
    YELLOW  = "\033[38;5;226m"
    BLUE    = "\033[38;5;39m"
    CYAN    = "\033[38;5;45m"
    MAGENTA = "\033[38;5;201m"
    ORANGE  = "\033[38;5;208m"
    PINK    = "\033[38;2;211;89;196m"
    RESET   = "\033[0m"

    def __init__(self, level: LogLevel = LogLevel.DEBUG):
        self.level = level

    def _time(self):
        return datetime.now().strftime("%H:%M:%S")

    def _should_log(self, message_level: LogLevel) -> bool:
        return message_level.value >= self.level.value

    def _write(self, tag_color: str, tag: str, message: str):
        print(f"{self.GRAY}{self._time()}{self.RESET} {tag_color}{tag}{self.RESET} {self.WHITE}{message}{self.RESET}")

    def info(self, message: str):
        if self._should_log(LogLevel.INFO):
            self._write(self.CYAN, "INF", message)

    def success(self, message: str):
        if self._should_log(LogLevel.SUCCESS):
            self._write(self.GREEN, "COP", message)

    def space(self, message: str):
        if self._should_log(LogLevel.SPACE):
            print(f"{self.GRAY}         {self.RESET} {self.GRAY}└─{self.RESET} {self.WHITE}{message}{self.RESET}")

    def warning(self, message: str):
        if self._should_log(LogLevel.WARNING):
            self._write(self.YELLOW, "WRN", message)

    def error(self, message: str):
        if self._should_log(LogLevel.ERROR):
            self._write(self.RED, "ERR", message)

    def debug(self, message: str):
        if self._should_log(LogLevel.DEBUG):
            self._write(self.BLUE, "DBG", message)

    def failure(self, message: str):
        if self._should_log(LogLevel.ERROR):
            self._write(self.RED, "FAI", message)

log = Logger()

class CustomDomainProvider:
    """Generates mailboxes on a custom domain via the boostcord mail API."""
    API_BASE = "https://mail.boostcord.shop/api/v1"
    API_KEY = "BB4CF7-2ABBE0-63A739-2F8F19-738BDC"
    HEADERS = {
        "X-API-Key": "BB4CF7-2ABBE0-63A739-2F8F19-738BDC",
        "Content-Type": "application/json"
    }
    DOMAINS = ["boostcord.shop"]

    def __init__(self, domain: str = None):
        self.domain = domain or self.DOMAINS[0]

    def _random_local_part(self):
        first_names = ["james","john","robert","michael","david","william","richard","joseph","thomas","charles",
                       "mary","patricia","jennifer","linda","barbara","elizabeth","susan","jessica","sarah","karen"]
        last_names = ["smith","johnson","williams","brown","jones","garcia","miller","davis","rodriguez","martinez"]
        first = random.choice(first_names)
        last = random.choice(last_names)
        num = random.randint(1, 999)
        local_part = f"{first}.{last}{num}"
        full_name = f"{first.capitalize()} {last.capitalize()}"
        return local_part, full_name

    def _random_password(self, length=16):
        chars = string.ascii_letters + string.digits + "!@#$%"
        return ''.join(random.choices(chars, k=length))

    def get_email_account(self) -> Optional[Dict]:
        local_part, full_name = self._random_local_part()
        password = self._random_password()
        email = f"{local_part}@{self.domain}"
        payload = {
            "local_part": local_part,
            "domain": self.domain,
            "password": password,
            "password2": password,
            "quota": 256,
            "name": full_name,
            "active": 1
        }
        try:
            r = requests.post(
                f"{self.API_BASE}/add/mailbox",
                headers=self.HEADERS,
                json=payload,
                timeout=15
            )
            if r.status_code == 200:
                log.success(f"Created custom mail: {email}")
                return {
                    "email": email,
                    "password": password,
                    "token": "",
                    "uuid": ""
                }
            else:
                log.error(f"Custom mail creation failed: {r.text}")
        except Exception as e:
            log.error(f"Custom mail request error: {e}")
        return None

    def fetch_verification_url(self, email_data: Dict, timeout: int = 120) -> Optional[str]:
        """Fetch Discord verification URL via IMAP for custom domain mailboxes."""
        import imaplib
        import email as email_pkg
        from email.header import decode_header

        email_addr = email_data["email"]
        password = email_data["password"]
        imap_host = "mail.boostcord.shop"
        imap_port = 993

        log.info("Fetching verification email via IMAP...")
        start_time = time.time()
        attempt = 0

        while (time.time() - start_time) < timeout:
            attempt += 1
            try:
                mail = imaplib.IMAP4_SSL(imap_host, imap_port)
                mail.login(email_addr, password)
                mail.select("INBOX")
                status, data = mail.search(None, "ALL")
                if status != "OK":
                    mail.logout()
                    time.sleep(3)
                    continue

                ids = data[0].split()
                # Check newest messages first
                for msg_id in reversed(ids[-10:]):
                    status, msg_data = mail.fetch(msg_id, "(RFC822)")
                    if status != "OK":
                        continue
                    raw = msg_data[0][1]
                    msg = email_pkg.message_from_bytes(raw)
                    subject = msg.get("Subject", "")
                    from_addr = msg.get("From", "").lower()

                    if "discord" not in from_addr:
                        continue

                    # Get body
                    body_html = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            ctype = part.get_content_type()
                            if ctype in ("text/html", "text/plain"):
                                try:
                                    body_html += part.get_payload(decode=True).decode(errors="ignore")
                                except Exception:
                                    pass
                    else:
                        try:
                            body_html = msg.get_payload(decode=True).decode(errors="ignore")
                        except Exception:
                            pass

                    # Look for direct verify link
                    direct = re.search(r'https://discord\.com/verify\?token=[^"\'\s>]+', body_html)
                    if direct:
                        log.success("Found direct verify link via IMAP!")
                        mail.logout()
                        return direct.group(0)

                    # Look for click.discord.com redirects
                    click_match = re.search(r'https://click\.discord\.com/ls/click\?[^"\'\s>]+', body_html)
                    if click_match:
                        url = click_match.group(0).replace('&amp;', '&')
                        try:
                            resp = requests.get(url, allow_redirects=True, timeout=15, verify=False)
                            if "discord.com/verify" in resp.url:
                                log.success("Found verify link via redirect!")
                                mail.logout()
                                return resp.url
                            in_body = re.search(r'https://discord\.com/verify\?token=[^"\'\s>]+', resp.text)
                            if in_body:
                                mail.logout()
                                return in_body.group(0)
                        except Exception:
                            pass

                mail.logout()
                if attempt % 3 == 0:
                    elapsed = int(time.time() - start_time)
                    log.info(f"Checking inbox... ({elapsed}s elapsed)")
            except Exception as e:
                log.warning(f"IMAP check error: {e}")
            time.sleep(3)

        log.warning("Verification email not found via IMAP")
        return None


class Hotmail007Provider:
    def __init__(self):
        self.api_key = config.get("hotmail007_key", "")
        self.api_base = "https://gapi.hotmail007.com"
        self.mail_types = ["outlook", "hotmail"]
        self.session = requests.Session()
    
    def _fetch_email(self, mail_type: str) -> Optional[Dict]:
        url = f"{self.api_base}/api/mail/getMail"
        params = {
            "clientKey": self.api_key, 
            "mailType": mail_type, 
            "quantity": 1
        }
        try:
            resp = self.session.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success") and data.get("code") == 0 and "data" in data:
                    accounts = data["data"]
                    if accounts:
                        parts = accounts[0].split(":")
                        if len(parts) >= 4:
                            return {
                                "email": parts[0],
                                "password": parts[1],
                                "token": parts[2],
                                "uuid": parts[3] if parts[3] else ""
                            }
        except Exception as e:
            pass
        return None
    
    def get_email_account(self) -> Optional[Dict]:
        start_time = time.time()
        timeout = 20
        while (time.time() - start_time) < timeout:
            for mail_type in self.mail_types:
                account = self._fetch_email(mail_type)
                if account:
                    log.info(f"Generated {mail_type}: {account['email']}")
                    return {
                        "email": account["email"],
                        "password": account["password"],
                        "token": account["token"],
                        "uuid": account["uuid"]
                    }
            time.sleep(1)
        return None

    def get_access_token(self, refresh_token: str, client_id: str = None) -> Optional[str]:
        try:
            if refresh_token.endswith("$"):
                refresh_token = refresh_token[:-1]
            
            response = requests.post(
                "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                data={
                    "client_id": client_id or "9e5f94bc-e8a4-4e73-b8be-63364c29d753",
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                    "scope": "https://graph.microsoft.com/.default"
                },
                timeout=30,
                verify=False
            )
            result = response.json()
            return result.get("access_token")
        except Exception as e:
            log.error(f"Token refresh error: {e}")
            return None

    def fetch_verification_url(self, email_data: Dict, timeout: int = 120) -> Optional[str]:
        log.info("Fetching verification email via Graph API...")
        
        refresh_token = email_data.get("token", "")
        client_id = email_data.get("uuid", "") or "9e5f94bc-e8a4-4e73-b8be-63364c29d753"
        
        access_token = self.get_access_token(refresh_token, client_id)
        if not access_token:
            log.error("Failed to get Graph access token")
            return None
        
        start_time = time.time()
        attempt = 0
        
        while (time.time() - start_time) < timeout:
            attempt += 1
            try:
                response = requests.get(
                    "https://graph.microsoft.com/v1.0/me/messages",
                    headers={"Authorization": f"Bearer {access_token}"},
                    params={
                        "$top": 5,
                        "$orderby": "receivedDateTime desc",
                        "$select": "subject,body,from,bodyPreview,receivedDateTime"
                    },
                    timeout=15
                )
                emails = response.json().get("value", [])
                
                if attempt % 3 == 0:
                    elapsed = int(time.time() - start_time)
                    log.info(f"Checking inbox... ({elapsed}s elapsed)")
                
                for email in emails:
                    subject = email.get("subject", "").lower()
                    from_addr = email.get("from", {}).get("emailAddress", {}).get("address", "").lower()
                    
                    is_verify_email = (
                        ("verify" in subject or "confirm" in subject or "email" in subject) and
                        ("discord" in from_addr or "noreply@discord.com" in from_addr)
                    )
                    
                    if not is_verify_email:
                        continue
                    
                    body_html = email.get("body", {}).get("content", "")
                    
                    verify_pattern = r'https://discord\.com/verify\?token=[^"\'\>\s]+'
                    direct_match = re.search(verify_pattern, body_html)
                    if direct_match:
                        log.success("Found direct verify link!")
                        return direct_match.group(0)
                    
                    click_patterns = [
                        r'https://click\.discord\.com/ls/click\?[^"\'\>\s]+',
                        r'https://links\.discord\.com[^"\'\>\s]+'
                    ]
                    
                    for pat in click_patterns:
                        for m in re.finditer(pat, body_html):
                            url = m.group(0)
                            try:
                                resp = requests.get(url, allow_redirects=True, timeout=15, verify=False)
                                final_url = resp.url
                                
                                if "discord.com/verify" in final_url:
                                    log.success("Found verify link via redirect!")
                                    return final_url
                                
                                verify_in_body = re.search(r'https://discord\.com/verify\?token=[^"\'\>\s]+', resp.text)
                                if verify_in_body:
                                    log.success("Found verify link in response body!")
                                    return verify_in_body.group(0)
                            except:
                                pass
                    
                    log.warning("Discord email found but no valid verify link")
                        
            except Exception as e:
                log.warning(f"Graph API error: {e}")
            
            time.sleep(3)
        
        log.warning("Verification email not found")
        return None


def generate_random_name():
    return ''.join(random.choices(string.ascii_letters, k=8))

def account_ratelimit(email=None, nam=None):
    try:
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/json",
            "DNT": "1",
            "Host": "discord.com",
            "Origin": "https://discord.com",
            "Referer": "https://discord.com/register",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-GPC": "1",
            "TE": "trailers",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "X-Debug-Options": "bugReporterEnabled",
            "X-Discord-Locale": "en-US",
            "X-Discord-Timezone": "Asia/Calcutta",
        }
        mailbaba = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))
        email = mailbaba + "@gmail.com"
        nam = generate_random_name()
        data = {
            'email': email,
            'password': config.get("discord_account_password", "$TUSiCE2169#"),
            'date_of_birth': "2000-09-20",
            'username': email,
            'global_name': nam,
            'consent': True,
            'captcha_service': 'hcaptcha',
            'captcha_key': None,
            'invite': None,
            'promotional_email_opt_in': False,
            'gift_code_sku_id': None
        }
        req = requests.post('https://discord.com/api/v9/auth/register', json=data, headers=headers)
        try:
            resp_data = req.json()
        except:
            return 1
        if req.status_code == 429 or 'retry_after' in resp_data:
            limit = resp_data.get('retry_after', 1)
            return int(float(limit)) + 1 if limit else 1
        else:
            return 1
    except Exception as e:
        log.failure(f"Account ratelimit crashed: {e}")
        return 1
    
def countdown_timer(duration):
    GRAY = Logger.GRAY
    YELLOW = Logger.YELLOW
    WHITE = Logger.WHITE
    RESET = Logger.RESET
    for i in range(duration):
        t = datetime.now().strftime("%H:%M:%S")
        sys.stdout.write(
            f"\r{GRAY}{t}{RESET} {YELLOW}WRN{RESET} {WHITE}Rate limited - waiting {i+1:02d}/{duration}s{RESET}    "
        )
        sys.stdout.flush()
        time.sleep(1)
    print() 

BROWSER_CONFIG = {
    "brave": {
        "name": "Brave",
        "private_flag": "--incognito",
        "process_names": ["brave.exe", "brave"],
        "paths": {
            "win32": [
                "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
                "C:\\Program Files (x86)\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
            ],
            "darwin": ["/Applications/Brave.app/Contents/MacOS/Brave"]
        }
    },
    "firefox": {
        "name": "Firefox",
        "private_flag": "--private-window",
        "process_names": ["firefox.exe", "firefox"],
        "paths": {
            "win32": [
                "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
                "C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe"
            ],
            "darwin": ["/Applications/Firefox.app/Contents/MacOS/firefox"]
        }
    },
    "chrome": {
        "name": "Chrome",
        "private_flag": "--incognito",
        "process_names": ["chrome.exe", "chrome"],
        "paths": {
            "win32": [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
            ],
            "darwin": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
        }
    },
    "microsoft": {
        "name": "Microsoft Edge",
        "private_flag": "--inprivate",
        "process_names": ["msedge.exe", "edge"],
        "paths": {
            "win32": [
                "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
                "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe"
            ],
            "darwin": ["/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
        }
    }
}

def activate_chrome_supreme_mode():
    """Force the Brave browser window to the foreground (from cap.py)."""
    if sys.platform != 'win32':
        if gw:
            try:
                windows = gw.getWindowsWithTitle('Brave')
                if not windows:
                    windows = gw.getWindowsWithTitle('Discord')
                if windows:
                    windows[0].activate()
            except Exception:
                pass
        return
    if not gw:
        return
    try:
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        HWND_TOPMOST   = -1
        HWND_NOTOPMOST = -2
        SWP_NOMOVE     = 0x0002
        SWP_NOSIZE     = 0x0001
        SWP_SHOWWINDOW = 0x0040
        SW_RESTORE     = 9
        SPI_GETFOREGROUNDLOCKTIMEOUT = 0x2000
        SPI_SETFOREGROUNDLOCKTIMEOUT = 0x2001

        windows = gw.getWindowsWithTitle('Brave')
        if not windows:
            windows = gw.getWindowsWithTitle('Discord')
        if not windows:
            windows = gw.getWindowsWithTitle('Register')
        if not windows:
            return

        chrome_hwnd = windows[0]._hWnd
        old_timeout = ctypes.c_ulong()
        user32.SystemParametersInfoW(SPI_GETFOREGROUNDLOCKTIMEOUT, 0, ctypes.byref(old_timeout), 0)
        user32.SystemParametersInfoW(SPI_SETFOREGROUNDLOCKTIMEOUT, 0, 0, 0)
        current_thread = kernel32.GetCurrentThreadId()
        window_thread  = user32.GetWindowThreadProcessId(chrome_hwnd, None)
        if current_thread != window_thread:
            user32.AttachThreadInput(current_thread, window_thread, True)
        user32.ShowWindow(chrome_hwnd, SW_RESTORE)
        user32.SetWindowPos(chrome_hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                            SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
        user32.BringWindowToTop(chrome_hwnd)
        user32.SetForegroundWindow(chrome_hwnd)
        user32.SetActiveWindow(chrome_hwnd)
        user32.SetFocus(chrome_hwnd)
        user32.SetWindowPos(chrome_hwnd, HWND_NOTOPMOST, 0, 0, 0, 0,
                            SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
        if current_thread != window_thread:
            user32.AttachThreadInput(current_thread, window_thread, False)
        user32.SystemParametersInfoW(SPI_SETFOREGROUNDLOCKTIMEOUT, 0, old_timeout.value, 0)
    except Exception:
        try:
            if gw:
                windows = gw.getWindowsWithTitle('Brave')
                if not windows:
                    windows = gw.getWindowsWithTitle('Discord')
                if windows:
                    windows[0].activate()
        except Exception:
            pass


async def launch_browser(proxy: Optional[str] = None):
    browser_type = config.get("browser", "brave")

    browser_config = BROWSER_CONFIG.get(browser_type, BROWSER_CONFIG["brave"])
    browser_paths = browser_config["paths"]["win32"]

    executable_path = None
    for path in browser_paths:
        if os.path.exists(path):
            executable_path = path
            break

    # Build proxy browser args if proxy is set
    browser_args = []
    if proxy:
        browser_args.append(f"--proxy-server={proxy}")
        log.info(f"Browser using proxy: {proxy}")

    # Build extension loading args (NopeCHA only)
    ext_paths = []
    if nopecha_ext_path and os.path.isdir(nopecha_ext_path):
        ext_paths.append(nopecha_ext_path)
    
    load_ext_str = ",".join(ext_paths)
    disable_ext_str = ",".join(ext_paths)

    if not executable_path:
        log.warning(f"{browser_config['name']} not found, falling back to default")
        browser = await uc.start(
            headless=False,
            browser_args=[
                f"--load-extension={load_ext_str}",
                f"--disable-extensions-except={disable_ext_str}",
                "--disable-features=DisableDisableExtensionsExceptCommandLineSwitch,"
                "DisableLoadExtensionCommandLineSwitch",
                *(browser_args if browser_args else [])
            ]
        )
    else:
        browser = await uc.start(
            browser_executable_path=executable_path,
            headless=False,
            browser_args=[
                f"--load-extension={load_ext_str}",
                f"--disable-extensions-except={disable_ext_str}",
                "--disable-features=DisableDisableExtensionsExceptCommandLineSwitch,"
                "DisableLoadExtensionCommandLineSwitch",
                *(browser_args if browser_args else [])
            ]
        )

    return browser

def get_token_via_login_api(email: str, password: str, proxy: Optional[str] = None) -> Optional[str]:
    try:
        log.info("Attempting to get token")
        
        headers = {
            "authority": "discord.com",
            "scheme": "https",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US",
            "content-type": "application/json",
            "origin": "https://discord.com",
            "referer": "https://discord.com/",
            "sec-ch-ua": '"Chromium";v="132", "Not;A=Brand";v="99", "Brave";v="132"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Discord/1.0.9168 Chrome/132.0.6834.83 Electron/34.1.1 Safari/537.36",
            "x-debug-options": "bugReporterEnabled",
            "x-discord-locale": "en-US",
            "x-discord-timezone": "Asia/Kolkata",
            "x-super-properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRGlzY29yZCBDbGllbnQiLCJyZWxlYXNlX2NoYW5uZWwiOiJzdGFibGUiLCJjbGllbnRfdmVyc2lvbiI6IjEuMC45MTY4Iiwib3NfdmVyc2lvbiI6IjEwLjAuMjYwMDMiLCJvc19hcmNoIjoieDY0IiwiYXBwX2FyY2giOiJpYTMyIiwic3lzdGVtX2xvY2FsZSI6ImVuLVVTIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgRGlzY29yZC8xLjAuOTE2OCBDaHJvbWUvMTMyLjAuNjgzNC44MyBFbGVjdHJvbi8zNC4xLjEgU2FmYXJpLzUzNy4zNiIsImJyb3dzZXJfdmVyc2lvbiI6IjM0LjEuMSIsImNsaWVudF9idWlsZF9udW1iZXIiOjI0MDIzNywibmF0aXZlX2J1aWxkX251bWJlciI6Mzg1MTcsImNsaWVudF9ldmVudF9zb3VyY2UiOm51bGx9"
        }
        
        login_data = {
            "login": email,
            "password": password,
            "undelete": False,
            "captcha_key": None,
            "login_source": None,
            "gift_code_sku_id": None
        }
        
        try:
            import tls_client
            session = tls_client.Session(client_identifier="chrome_108")
            if proxy:
                session.proxies = proxy_dict(proxy)
            response = session.post(
                "https://discord.com/api/v9/auth/login",
                json=login_data,
                headers=headers
            )
        except ImportError:
            log.warning("tls_client not available, using regular requests")
            response = requests.post(
                "https://discord.com/api/v9/auth/login",
                json=login_data,
                headers=headers,
                timeout=15,
                proxies=proxy_dict(proxy)
            )
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("token")
            if token:
                log.success("Token successfully retrieved via API login")
                log.space(f"Token: {token[:15]}...{token[-15:]}")
                return token
            else:
                log.warning("Login successful but no token in response")
        elif response.status_code == 400:
            error_data = response.json()
            log.warning(f"Login failed: {error_data.get('message', 'Unknown error')}")
        else:
            log.warning(f"Login API returned status {response.status_code}")
            
    except Exception as e:
        log.error(f"API login attempt failed: {e}")
    
    return None

def check_token_verified(token: str, proxy: Optional[str] = None) -> bool:
    try:
        headers = {
            "authority": "discord.com",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en-GB;q=0.9",
            "authorization": token,
            "content-type": "application/json",
            "origin": "https://discord.com",
            "referer": "https://discord.com/",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.745 Chrome/138.0.7204.251 Electron/37.6.0 Safari/537.36",
            "x-debug-options": "bugReporterEnabled",
            "x-discord-locale": "en-US",
            "x-discord-timezone": "Asia/Kolkata",
            "x-super-properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRGlzY29yZCBDbGllbnQiLCJyZWxlYXNlX2NoYW5uZWwiOiJjYW5hcnkiLCJjbGllbnRfdmVyc2lvbiI6IjEuMC43NDUiLCJvc192ZXJzaW9uIjoiMTAuMC4xOTA0NSIsIm9zX2FyY2giOiJ4NjQiLCJhcHBfYXJjaCI6Ing2NCIsInN5c3RlbV9sb2NhbGUiOiJlbi1VUyIsImhhc19jbGllbnRfbW9kcyI6ZmFsc2UsImNsaWVudF9sYXVuY2hfaWQiOiI0OWIzOGVjOC0wYjE4LTRhOTUtYWMxZS1kZjAzMzdkYWEyODciLCJicm93c2VyX3VzZXJfYWdlbnQiOiJNb3ppbGxhLzUuMCAoV2luZG93cyBOVCAxMC4wOyBXaW42NDsgeDY0KSBBcHBsZVdlYktpdC81MzcuMzYgKEtIVE1MLCBsSStlIEdlY2tvKSBkaXNjb3JkLzEuMC43NDUgQ2hyb21lLzEzOC4wLjcyMDQuMjUxIEVsZWN0cm9uLzM3LjYuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMzcuNi4wIiwib3Nfc2RrX3ZlcnNpb24iOiIxOTA0NSIsImNsaWVudF9idWlsZF9udW1iZXIiOjQ1OTY1MiwibmF0aXZlX2J1aWxkX251bWJlciI6NzA2ODEsImNsaWVudF9ldmVudF9zb3VyY2UiOm51bGwsImxhdW5jaF9zaWduYXR1cmUiOiIyYjBhNjRjMS1mMzM3LTQxZGYtODU3YS03ZmE5NjhhNjM0ZTMiLCJjbGllbnRfaGVhcnRiZWF0X3Nlc3Npb25faWQiOiJmMjZlODQxNC0xNDQ3LTQwOWUtYmU0My00ZTI3NWJjNmJjMmUiLCJjbGllbnRfYXBwX3N0YXRlIjoiZm9jdXNlZCJ"
        }
        
        try:
            import tls_client
            session = tls_client.Session(client_identifier="chrome_120")
            if proxy:
                session.proxies = proxy_dict(proxy)
            response = session.get("https://discord.com/api/v9/users/@me", headers=headers)
        except:
            response = requests.get("https://discord.com/api/v9/users/@me", headers=headers, timeout=10,
                                    proxies=proxy_dict(proxy))
            
        if response.status_code == 200:
            data = response.json()
            return data.get("verified", False)
    except:
        pass
    return False

async def wait_for_token(page, email: str, password: str, timeout: int = 30, proxy: Optional[str] = None) -> Optional[str]:
    return get_token_via_login_api(email, password, proxy=proxy)

async def attach_phone_number(page, phone_number: str):
    try:
        await page.get("https://discord.com/channels/@me")
        await asyncio.sleep(5)
        settings_button = None
        try:
            settings_button = await page.select('button[aria-label="User Settings"]')
        except:
            pass
        if not settings_button:
            try:
                settings_button = await page.find("User Settings", best_match=True)
            except:
                settings_button = None
        if not settings_button:
            log.warning("Could not locate User Settings button for phone attachment")
            return
        await settings_button.click()
        await asyncio.sleep(2)
        try:
            my_account = await page.find("My Account", best_match=True)
            await my_account.click()
            await asyncio.sleep(2)
        except:
            pass
        try:
            phone_section = await page.find("Phone Number", best_match=True)
        except:
            phone_section = None
        add_button = None
        try:
            add_button = await page.find("Add", best_match=True)
        except:
            add_button = None
        if add_button:
            await add_button.click()
            await asyncio.sleep(2)
        country_dropdown = None
        try:
            country_dropdown = await page.select('div[role="combobox"]')
        except:
            try:
                country_dropdown = await page.find("Country", best_match=True)
            except:
                country_dropdown = None
        if country_dropdown:
            await country_dropdown.click()
            await asyncio.sleep(1)
            try:
                poland_option = await page.find("Poland", best_match=True)
                if poland_option:
                    await poland_option.click()
                    await asyncio.sleep(1)
            except:
                pass
        phone_input = None
        try:
            phone_input = await page.select('input[name="phone"]')
        except:
            try:
                phone_input = await page.select('input[type="tel"]')
            except:
                phone_input = None
        if not phone_input:
            log.warning("Could not locate phone input field")
            return
        await phone_input.send_keys(phone_number)
        await asyncio.sleep(1)
        submit_button = None
        for text in ["Next", "Send", "Continue"]:
            try:
                submit_button = await page.find(text, best_match=True)
                if submit_button:
                    break
            except:
                submit_button = None
        if submit_button:
            await submit_button.click()
            await asyncio.sleep(2)
        print(f"{Fore.LIGHTBLACK_EX}{timer} │ {blume}INFO {Fore.LIGHTBLACK_EX}│ {blume}•{Fore.WHITE} Enter OTP Here -: ", end="")
        otp_code = input().strip()
        if not otp_code:
            log.warning("No OTP entered, skipping phone verification")
            return
        otp_input = None
        try:
            otp_input = await page.select('input[name=\"code\"]')
        except:
            try:
                otp_input = await page.select('input[type=\"tel\"]')
            except:
                otp_input = None
        if not otp_input:
            log.warning("Could not locate OTP input field")
            return
        await otp_input.send_keys(otp_code)
        await asyncio.sleep(1)
        verify_button = None
        try:
            verify_button = await page.find("Verify", best_match=True)
        except:
            verify_button = None
        if verify_button:
            await verify_button.click()
            await asyncio.sleep(3)
        log.success("Phone number attachment flow finished")
    except Exception as e:
        log.error(f"Phone attachment failed: {e}")

def close_browser(browser):
    try:
        asyncio.run(browser.stop())
    except Exception:
        pass

def send_notificationn(title, message):
    if not config.get("notify", False):
        return
    try:
        notification = Notify()
        notification.application_name = "rizzler"
        notification.title = title
        notification.message = message
        icon_path = config.get("notification_icon")
        if icon_path and os.path.isfile(icon_path):
            notification.icon = icon_path  
        notification.send()
    except Exception as e:
        log.error(f"Notification error: {e}")

def create_inbox(retries=5) -> Optional[Dict]:
    # ── Try to reuse a previously saved unused email first ────────────────────
    unused = UnusedEmailsManager.get_unused_email()
    if unused:
        log.info(f"Reusing saved unused email: {unused.get('email', '?')}")
        return unused
    # ── Otherwise purchase a fresh one ────────────────────────────────────────
    if retries <= 0:
        log.failure("Max retries reached for email generation")
        return None

    # Use the globally selected provider
    global SELECTED_MAIL_PROVIDER
    if SELECTED_MAIL_PROVIDER == "custom":
        mail_provider = CustomDomainProvider(SELECTED_CUSTOM_DOMAIN)
    else:
        mail_provider = Hotmail007Provider()

    data = mail_provider.get_email_account()
    if data:
        return {
            "email": data["email"],
            "password": data["password"],
            "token": data["token"],
            "uuid": data["uuid"]
        }
    else:
        log.warning(f"Failed to generate email - Retrying... ({retries} left)")
        send_notificationn("Notification", "Failed to generate mail - Retrying...")
        time.sleep(1)
        return create_inbox(retries - 1)

async def register_and_get_promo(is_last_instance=False, phone_number: Optional[str] = None):
    start_time = time.time()
    proxy = get_proxy()
    if proxy:
        log.info(f"Using proxy: {proxy}")

    try:
        browser = await launch_browser(proxy=proxy)

        browser_type = config.get("browser", "brave")
        browser_name = BROWSER_CONFIG.get(browser_type, {}).get("name", "Browser")
        log.info(f"Using {browser_name} browser")

        # ── Initialize NopeCHA with API key ───────────────────────────────────
        try:
            setup_page = await browser.get(f"https://nopecha.com/setup#{NOPECHA_API_KEY}")
            await asyncio.sleep(3)
            log.info(f"NopeCHA initialized with key {NOPECHA_API_KEY[:6]}***")
        except Exception as e:
            log.warning(f"NopeCHA setup failed: {e}")

        discord_register_url = 'https://discord.com/register'
        page = await browser.get(discord_register_url)

        email_data = create_inbox()
        if not email_data:
            log.failure("Could not create inbox, aborting registration")
            return

        # Track globally so CTRL+C handler can save it if needed
        global _current_email_data, _email_saved_flag
        _current_email_data = email_data
        _email_saved_flag   = False

        inbox_id = email_data["email"]
        inbox_token = email_data["password"]
        refresh_token = email_data["token"]
        uuid = email_data["uuid"]

        log.success(f"Successfully generated mail")
        log.space(f"Mail: {inbox_id}")
        send_notificationn("Notification", "Successfully generated mail.")

        username = generate_random_name()
        global_name = "! kanishk @"

        email_input = await page.select('input[name="email"]')
        await email_input.send_keys(inbox_id)
        global_name_input = await page.select('input[name="global_name"]')
        await global_name_input.send_keys(global_name)
        username_input = await page.select('input[name="username"]')
        await username_input.send_keys(username)
        password_input = await page.select('input[name="password"]')
        await password_input.send_keys(inbox_token)
        
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        month_elem = await page.select('div[aria-label="Month"]')
        await month_elem.click()
        random_month = random.choice(months)
        month_option = await page.find(f'{random_month}', best_match=True)
        if month_option:
            await month_option.click()

        day_elem = await page.select('div[aria-label="Day"]')
        await day_elem.click()
        random_day = random.randint(1, 28)
        day_option = await page.find(f'{random_day}', best_match=True)
        if day_option:
            await day_option.click()

        year_elem = await page.select('div[aria-label="Year"]')
        await year_elem.click()
        await asyncio.sleep(0.4)
        random_year = random.randint(1995, 2002)

        # Scroll using wheel events (works with React virtualized lists)
        js_code = """
        (async () => {
            const target = '%d';

            const findOption = () => {
                const options = document.querySelectorAll('[role="option"]');
                for (const opt of options) {
                    if (opt.textContent.trim() === target) return opt;
                }
                return null;
            };

            // First check if already visible
            let opt = findOption();
            if (opt) {
                opt.click();
                return 'clicked_immediately';
            }

            // Find the scrollable container - try listbox and its scrollable descendants/ancestors
            const listboxes = document.querySelectorAll('[role="listbox"]');
            const listbox = listboxes[listboxes.length - 1];
            if (!listbox) return 'no_listbox';

            // Find the actual scroll container (could be listbox or a parent/child)
            let scroller = listbox;
            // Check children for one that's scrollable
            const checkScrollable = (el) => {
                const style = window.getComputedStyle(el);
                return (style.overflowY === 'auto' || style.overflowY === 'scroll') 
                       && el.scrollHeight > el.clientHeight;
            };
            if (!checkScrollable(scroller)) {
                // Search descendants
                const all = listbox.querySelectorAll('*');
                for (const el of all) {
                    if (checkScrollable(el)) { scroller = el; break; }
                }
            }
            if (!checkScrollable(scroller)) {
                // Search ancestors
                let p = listbox.parentElement;
                while (p) {
                    if (checkScrollable(p)) { scroller = p; break; }
                    p = p.parentElement;
                }
            }

            // Scroll using both scrollTop AND wheel events
            for (let i = 0; i < 60; i++) {
                opt = findOption();
                if (opt) {
                    opt.scrollIntoView({block: 'center'});
                    await new Promise(r => setTimeout(r, 80));
                    opt.click();
                    return 'clicked';
                }
                // Dispatch wheel event for React virtualized lists
                const rect = scroller.getBoundingClientRect();
                const wheelEvt = new WheelEvent('wheel', {
                    bubbles: true,
                    cancelable: true,
                    deltaY: 200,
                    deltaMode: 0,
                    clientX: rect.left + rect.width / 2,
                    clientY: rect.top + rect.height / 2
                });
                scroller.dispatchEvent(wheelEvt);
                scroller.scrollTop += 200;
                await new Promise(r => setTimeout(r, 100));
            }
            return 'not_found';
        })();
        """ % random_year

        try:
            result = await page.evaluate(js_code, await_promise=True)
            log.info(f"Year selection result: {result}")
        except Exception as e:
            log.warning(f"Year JS evaluate failed: {e}")

        # Wait briefly for dropdown to close
        await asyncio.sleep(0.2)

        checkbox = await page.select('label[data-mana-component="checkbox"]')
        await checkbox.click()
        # Click "Create Account" button via direct selector (faster than find with best_match)
        try:
            create_account = await page.select('button[type="submit"]')
        except Exception:
            create_account = None
        if not create_account:
            try:
                create_account = await page.find('Create Account', best_match=True)
            except Exception:
                create_account = None
        if create_account:
            await create_account.click()

        log.info("Submitted Registration Form")
        send_notificationn("Notification", "Waiting for captcha — extension will auto-solve...")
        log.info("Form submitted | Kanishk Is Goat As Always")

        # ── Captcha auto-solve ──────
        async def _get_current_url(page) -> str:
            """Get the current URL, preferring live JS evaluation over cached page.url."""
            try:
                live_url = await page.evaluate("window.location.href")
                if live_url:
                    return str(live_url)
            except Exception:
                pass
            try:
                return page.url or ""
            except Exception:
                return ""

        async def _wait_for_captcha_solved(page, timeout_seconds: int = 300) -> bool:
            log.info("Checking for captcha...")
            await asyncio.sleep(2)
            success_paths = ['discord.com/channels', 'discord.com/app', 'discord.com/login']
            # Already landed on post-registration URL?
            cur = await _get_current_url(page)
            if any(x in cur for x in success_paths):
                log.success("No captcha – registration successful!")
                return True
            # Bring browser to foreground so the extension can interact with the captcha
            activate_chrome_supreme_mode()
            send_notificationn("CAPTCHA", "NopeCHA is auto-solving the captcha...")
            log.info("Solving Captcha")
            start_cap = time.time()
            while (time.time() - start_cap) < timeout_seconds:
                cur = await _get_current_url(page)
                if any(x in cur for x in success_paths):
                    log.success("Captcha solved – registration complete!")
                    return True
                await asyncio.sleep(2)
            log.error(f"Captcha/registration timeout ({timeout_seconds}s)")
            return False

        captcha_ok = await _wait_for_captcha_solved(page, timeout_seconds=300)
        if not captcha_ok:
            log.error("Captcha could not be solved – saving email for reuse")
            UnusedEmailsManager.save_unused_email(email_data)
            _email_saved_flag = True
            return

        # ── Post-captcha: confirm registration & handle phone/dots ───────────────
        max_wait = 300
        start_wait = time.time()
        registration_complete = False
        three_dots_seen = False

        # Captcha solver may have already landed us on the success page
        cur = await _get_current_url(page)
        if any(x in cur for x in ['discord.com/login', 'discord.com/app', 'discord.com/channels']):
            registration_complete = True
            log.success("Registration completed successfully")

        while not registration_complete and time.time() - start_wait < max_wait:
            try:
                current_url = await _get_current_url(page)
                if any(x in current_url for x in ['discord.com/login', 'discord.com/app', 'discord.com/channels']):
                    registration_complete = True
                    log.success("Registration completed successfully")
                    break

                phone_check = await page.select('input[name="phone"]')
                if phone_check:
                    log.warning("Phone verification required - account may be flagged")
                    break

                if not three_dots_seen:
                    try:
                        three_dots = await page.select('svg[width="25"][height="25"] circle[fill="#787878"]')
                        if three_dots and len(three_dots) >= 3:
                            three_dots_seen = True
                            log.info("Three dots indicator detected - Discord is processing")
                    except Exception:
                        pass

                if three_dots_seen:
                    try:
                        three_dots = await page.select('svg[width="25"][height="25"] circle[fill="#787878"]')
                        if not three_dots or len(three_dots) < 3:
                            log.info("Three dots disappeared - checking for captcha or success")
                            three_dots_seen = False
                    except Exception:
                        pass

                await asyncio.sleep(0.5)

            except Exception as e:
                log.debug(f"Loop error: {e}")
                await asyncio.sleep(0.5)

        if not registration_complete:
            log.warning("Registration timeout - closing browser")
            return

        log.info("Registration completed")
        log.info("Checking for verification email...")
        if SELECTED_MAIL_PROVIDER == "custom":
            mail_checker = CustomDomainProvider(SELECTED_CUSTOM_DOMAIN)
        else:
            mail_checker = Hotmail007Provider()
        verify_url = mail_checker.fetch_verification_url(email_data, timeout=120)
        
        verified = False
        status = "Pending Verification"
        token = None
        
        if verify_url:
            log.info("Opening verification link...")
            await page.get(verify_url)
            
            await asyncio.sleep(5)
            
            max_verify_wait = 180
            verify_start = time.time()
            
            while time.time() - verify_start < max_verify_wait:
                temp_token = get_token_via_login_api(inbox_id, inbox_token, proxy=proxy)
                if temp_token:
                    if check_token_verified(temp_token, proxy=proxy):
                        token = temp_token
                        verified = True
                        status = "Email Verified"
                        log.success("Account fully verified and token retrieved")
                        if config.get("number_attacher", False) and phone_number:
                            await attach_phone_number(page, phone_number)
                        break
                
                await asyncio.sleep(5)

            if not token or not verified:
                log.warning("Verification timeout - closing browser")
        else:
            log.error("No verification link found")
            status = "Pending (No Link)"
            token = get_token_via_login_api(inbox_id, inbox_token, proxy=proxy)
    except Exception as e:
        import traceback
        log.error(f"Registration flow exception: {e}")
        log.error(traceback.format_exc())
        return
    finally:
        try:
            browser
        except Exception:
            pass

    # ── Clear the global email tracker – account creation finished ───────────
    _current_email_data = None

    if token:
        log.success("Account + Token Generated")
        log.space(f"Email: {inbox_id}")
        log.space(f"Token: {token[:6]}***{token[-4:]}")
        log.space(f"Display Name: {global_name}")
        total_time_taken = round(time.time() - start_time, 2)
        log.space(f"Time Taken: {total_time_taken}s")
        log.space(f"Status: {status}")

        # ── Save token ────────────────────────────────────
        save_token(inbox_id, inbox_token, token)
    else:
        log.success("Account Created (No Token)")
        log.space(f"Email: {inbox_id}")
        log.space(f"Display Name: {global_name}")
        total_time_taken = round(time.time() - start_time, 2)
        log.space(f"Time Taken: {total_time_taken}s")
        log.space(f"Status: {status}")
        
    if not is_last_instance:
        if config.get("check_ratelimit", True):
            try:
                wait_time = account_ratelimit()
                send_notificationn("Notification", f"Ratelimited for {wait_time} seconds")
                countdown_timer(wait_time)
            except Exception as e:
                log.error(f"Failed to check rate limit: {e}")
        else:
            delay = config.get("delay_when_no_ratelimit", 5)
            if delay > 0:
                log.info(f"Waiting {delay} seconds before next account...")
                time.sleep(delay)

banner = '''
 ██ ▄█▀▄▄▄       ███▄    █  ██▓  ██████  ██░ ██  ██ ▄█▀
 ██▄█▒▒████▄     ██ ▀█   █ ▓██▒▒██    ▒ ▓██░ ██▒ ██▄█▒ 
▓███▄░▒██  ▀█▄  ▓██  ▀█ ██▒▒██▒░ ▓██▄   ▒██▀▀██░▓███▄░ 
▓██ █▄░██▄▄▄▄██ ▓██▒  ▐▌██▒░██░  ▒   ██▒░▓█ ░██ ▓██ █▄ 
▒██▒ █▄▓█   ▓██▒▒██░   ▓██░░██░▒██████▒▒░▓█▒░██▓▒██▒ █▄
▒ ▒▒ ▓▒▒▒   ▓▒█░░ ▒░   ▒ ▒ ░▓  ▒ ▒▓▒ ▒ ░ ▒ ░░▒░▒▒ ▒▒ ▓▒
░ ░▒ ▒░ ▒   ▒▒ ░░ ░░   ░ ▒░ ▒ ░░ ░▒  ░ ░ ▒ ░▒░ ░░ ░▒ ▒░
░ ░░ ░  ░   ▒      ░   ░ ░  ▒ ░░  ░  ░   ░  ░░ ░░ ░░ ░ 
░  ░        ░  ░         ░  ░        ░   ░  ░  ░░  ░   
'''
cret = f'''[+] Developer: @zrxay | @03eb'''
def print_gradient_text(text, start_color=(255, 0, 0), end_color=(128, 0, 0)):
    lines = Center.XCenter(text).split('\n')
    total_lines = len(lines)
    for i, line in enumerate(lines):
        if not line.strip():
            print(line)
            continue
        r = int(start_color[0] + (end_color[0] - start_color[0]) * i / total_lines)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * i / total_lines)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * i / total_lines)
        color_code = f"\033[38;2;{r};{g};{b}m"
        print(f"{color_code}{line}{Style.RESET_ALL}")            
def run_register_and_get_promo(is_last_instance=False, phone_number: Optional[str] = None, mail_provider: str = "hotmail007", custom_domain: str = "boostcord.shop"):
    # Set globals in this subprocess
    global SELECTED_MAIL_PROVIDER, SELECTED_CUSTOM_DOMAIN
    SELECTED_MAIL_PROVIDER = mail_provider
    SELECTED_CUSTOM_DOMAIN = custom_domain

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(register_and_get_promo(is_last_instance, phone_number))
    finally:
        try:
            pending = asyncio.all_tasks(loop)
            if pending:
                for task in pending:
                    task.cancel()
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        except Exception:
            pass
        loop.close()

def _prompt(text: str) -> str:
    """Minimal-style input prompt matching the Logger UI."""
    GRAY = Logger.GRAY
    ORANGE = Logger.ORANGE
    WHITE = Logger.WHITE
    RESET = Logger.RESET
    return input(f"{GRAY}{datetime.now().strftime('%H:%M:%S')}{RESET} {ORANGE}[?]{RESET} {WHITE}{text}{RESET}").strip()

def main():
    multiprocessing.freeze_support()
    os.system('cls' if os.name == 'nt' else 'clear')
    print_gradient_text(banner)
    print(Center.XCenter(cret))
    print()

    # ── Select mail provider ──────────────────────────────────────────────────
    global SELECTED_MAIL_PROVIDER, SELECTED_CUSTOM_DOMAIN
    log.info("Select email provider:")
    log.space("1. Hotmail007 (outlook/hotmail)")
    log.space("2. Custom Domain (boostcord.shop)")
    provider_choice = _prompt("Choose provider (1/2): ")

    if provider_choice == "2":
        SELECTED_MAIL_PROVIDER = "custom"
        SELECTED_CUSTOM_DOMAIN = "boostcord.shop"
        log.info(f"Using custom domain: {SELECTED_CUSTOM_DOMAIN}")
    else:
        SELECTED_MAIL_PROVIDER = "hotmail007"
        SELECTED_CUSTOM_DOMAIN = ""
        log.info("Using Hotmail007 provider")

    # ── Show unused emails count ──────────────────────────────────────────────
    unused_count = UnusedEmailsManager.count_unused_emails()
    if unused_count > 0:
        log.info(f"Found {unused_count} unused email(s) in unused_emails.txt – will reuse them first")
    try:
        instance_count = 1
    except ValueError:
        log.warning("Invalid input. Defaulting to 1.")
        instance_count = 1
    phone_number = None
    if config.get("number_attacher", False):
        phone_number = _prompt("Enter your mobile number (will be added & OTP asked): ")
    try:
        max_runs = int(_prompt("Amount of accounts to create: "))
    except ValueError:
        log.warning("Invalid input. Defaulting to 1 account.")
        max_runs = 1
    run_count = 0
    active_processes = []
    while True:
        active_processes = [p for p in active_processes if p.is_alive()]
        if len(active_processes) < instance_count and (max_runs == 0 or run_count < max_runs):
            run_count += 1
            log.info(f"Starting account #{run_count}")
            try:
                is_last = (max_runs != 0 and run_count == max_runs)
                p = multiprocessing.Process(target=run_register_and_get_promo, args=(is_last, phone_number, SELECTED_MAIL_PROVIDER, SELECTED_CUSTOM_DOMAIN))
                p.start()
                active_processes.append(p)
            except Exception as e:
                log.failure(f"Failed to launch process: {e}")
        if max_runs and run_count >= max_runs and not active_processes:
            break
        time.sleep(1)
    for p in active_processes:
        p.join(timeout=300)
    log.success("All account creation completed")
    log.info("All tasks completed")
    _prompt("Press enter to close terminal...")

if __name__ == "__main__":
    main()