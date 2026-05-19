# KANISHK — Discord Account Generator

Automated Discord account creation tool with email verification, captcha auto-solving, and token extraction.

---

## Features

- **Dual Email Provider Support**
  - **Hotmail007** — Purchases Outlook/Hotmail accounts via API, verifies using Microsoft Graph API inbox access
  - **Custom Domain (boostcord.shop)** — Creates mailboxes on your own domain via Mailcow API, verifies via IMAP

- **NopeCHA Captcha Solver**
  - Auto-extracts and loads the NopeCHA browser extension
  - Solves hCaptcha, reCAPTCHA, FunCaptcha, Turnstile automatically
  - API key pre-configured in the extension

- **Browser Automation**
  - Uses Brave browser via `nodriver` (undetected Chrome driver)
  - Fills registration form (email, username, display name, password, DOB)
  - Handles year dropdown scrolling via JavaScript wheel events
  - Clicks TOS checkbox and submits form

- **Email Verification**
  - Hotmail007: Fetches verification link via Microsoft Graph API (refresh token → access token → inbox)
  - Custom Domain: Connects via IMAP SSL to `mail.boostcord.shop`, polls inbox for Discord verification email
  - Follows `click.discord.com` redirect links to extract final verify URL

- **Token Extraction**
  - Logs into Discord API with created credentials to retrieve auth token
  - Verifies token is email-verified via `/users/@me` endpoint
  - Saves tokens to `tokens.txt` in format: `email:password:token`

- **Proxy Support**
  - Load proxies from `proxies.txt` or `config.json`
  - Supports HTTP, HTTPS, SOCKS4, SOCKS5
  - Applied to both browser and API requests

- **Ratelimit Handling**
  - Pre-checks Discord registration ratelimit before each account
  - Countdown timer showing wait progress
  - Configurable delay when ratelimit check is disabled

- **Unused Email Recovery**
  - On CTRL+C or crash, saves in-progress email to `unused_emails.txt`
  - Reuses saved emails on next run (no wasted purchases)

- **Phone Number Attachment** (optional)
  - Navigates to Discord settings after verification
  - Enters phone number and prompts for OTP

- **Multiprocessing**
  - Parallel account creation (configurable instance count)
  - Each instance runs in its own process with isolated browser

- **Desktop Notifications**
  - Optional system notifications for key events (mail generated, captcha solving, ratelimit)

---

## Requirements

- Python 3.10+
- Brave Browser installed
- Windows OS

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## File Structure

```
WORKER/
├── main.py                 # Main script
├── config.json             # Configuration file
├── requirements.txt        # Python dependencies
├── proxies.txt             # Proxy list (one per line)
├── tokens.txt              # Output: generated tokens
├── unused_emails.txt       # Recovered emails for reuse
├── nopecha_extension.zip   # NopeCHA extension (auto-extracted)
├── nopecha/                # Extracted NopeCHA extension folder
├── NewFol/                 # Legacy captcha extension (unused)
└── output/                 # Output directory
```

---

## Configuration (config.json)

```json
{
  "check_ratelimit": true,
  "notify": false,
  "notification_icon": "data/pack.ico",
  "browser": "brave",
  "hotmail007_key": "YOUR_HOTMAIL007_API_KEY",
  "discord_account_password": "YourPassword123",
  "number_attacher": false,
  "delay_when_no_ratelimit": 5,
  "use_proxy": false,
  "proxy_file": "proxies.txt",
  "proxies": []
}
```

| Key | Description |
|-----|-------------|
| `check_ratelimit` | Pre-check Discord ratelimit before each account |
| `notify` | Enable desktop notifications |
| `browser` | Browser to use: `brave`, `chrome`, `firefox`, `microsoft` |
| `hotmail007_key` | API key for Hotmail007 email provider |
| `discord_account_password` | Password used for Discord accounts |
| `number_attacher` | Prompt for phone number to attach to accounts |
| `delay_when_no_ratelimit` | Seconds to wait between accounts when ratelimit check is off |
| `use_proxy` | Enable proxy rotation |
| `proxy_file` | Path to proxy list file |
| `proxies` | Inline proxy list (overrides file) |

---

## Usage

```bash
cd WORKER
python main.py
```

### Flow

1. Select email provider (Hotmail007 or Custom Domain)
2. Enter number of accounts to create
3. Tool launches Brave, navigates to Discord register
4. Creates mailbox, fills form, submits
5. NopeCHA auto-solves captcha
6. Waits for registration to complete
7. Fetches verification email (Graph API or IMAP)
8. Opens verify link in browser
9. Extracts token via login API
10. Saves `email:password:token` to `tokens.txt`
11. Repeats for next account

---

## Proxy Format

Supports these formats in `proxies.txt`:

```
ip:port
user:pass@ip:port
http://ip:port
socks5://user:pass@ip:port
```

---

## Output

Tokens are saved to `tokens.txt`:

```
karen.davis813@boostcord.shop:xK9#mPw2$qLz:MTIzNDU2Nzg5.abc123.xyz789
```

Format: `email:password:discord_token`

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Brave not found | Install Brave or change `browser` in config.json |
| NopeCHA not solving | Check API key credits at nopecha.com |
| "Must be 13 years old" | Year selection failed — restart and try again |
| Custom mail creation failed | Check boostcord API key / domain quota |
| IMAP connection refused | Ensure mailbox was created successfully first |
| Token not retrieved | Account may be locked/flagged — check with proxy |

---

## Credits

Developer: **@kanishkismean**
