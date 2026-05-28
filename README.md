# Telegram Joined-Message Cleanup (Selenium)

Automates cleanup of Telegram messages matching the pattern:

- `<Name> joined Telegram`

This repository contains two scripts:

- `1_launch_chrome.py` launches Chrome with remote debugging on port `9222`.
- `2_delete_joined_messages.py` connects to that browser session and performs deletion.

## Why This Exists

Telegram groups can accumulate many "joined" service messages over time. This project helps moderators/admins clean those entries faster by automating a repetitive UI workflow.

## Features

- Uses your real logged-in Telegram Web session (no unofficial API token handling).
- Works through Chrome remote debugging for stable Selenium attachment.
- Targets only messages whose inner text contains `joined telegram` (case-insensitive).
- Supports lazy-loaded lists (loads roughly 10 rows per scroll).
- Includes safety fallbacks when expected UI elements are not found.

## Project Structure

```text
cleanup-telegram/
|-- 1_launch_chrome.py
|-- 2_delete_joined_messages.py
|-- requirements.txt
|-- .gitignore
|-- LICENSE
`-- README.md
```

## Requirements

- Windows/macOS/Linux
- Python 3.10+
- Google Chrome
- Telegram Web access
- Group/channel permissions sufficient to delete target messages

Install dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start

1. Launch Chrome in debug mode:

```bash
python 1_launch_chrome.py
```

2. In the opened Chrome window:

- Open Telegram Web
- Log in with your phone
- Keep the session open

3. Run the cleanup script:

```bash
python 2_delete_joined_messages.py
```

## Current Automation Flow

For each matching row in the chat list, the script performs this sequence:

1. Click the row (opens the chat).
2. Open menu via class `btn-icon rp btn-menu-toggle` (index 2).
3. Click danger menu item via class `btn-menu-item rp-overflow danger`.
4. Tick checkbox via class `checkbox-field-input` (index 9).
5. Confirm delete via class `popup-button btn danger rp`.
6. Go back using class `btn-icon sidebar-back-button is-visible`.

If Telegram changes class names or index positions, update selectors in `2_delete_joined_messages.py`.

## Configuration

Edit these constants in `2_delete_joined_messages.py`:

- `DEBUGGER_ADDRESS`
- `DELAY_BETWEEN_DELETES`
- `MAX_SCROLL_ROUNDS`
- `JOINED_TEXT`

## Safety and Scope Notes

- Test in a non-critical group first.
- Keep a conservative delete delay to avoid aggressive action bursts.
- This tool relies on Telegram Web UI selectors and can break after UI updates.
- Use at your own risk and ensure your usage complies with Telegram Terms.

## Troubleshooting

### Script exits immediately with no deletions

- Ensure Telegram Web is open in the same Chrome started by `1_launch_chrome.py`.
- Confirm target rows actually contain `joined telegram` text.

### "Could not connect to Chrome at 127.0.0.1:9222"

- Start `1_launch_chrome.py` first.
- Close other Chrome instances if they conflict with the debug profile.

### Element index errors (menu/checkbox)

- Telegram likely changed DOM ordering.
- Inspect current classes and update index values in `2_delete_joined_messages.py`.

## Publishing Checklist

Before making the repository public:

- Verify `.gitignore` excludes `chrome_profile/`.
- Remove any local sensitive artifacts or logs.
- Update the `LICENSE` copyright holder/year if needed.
- Add example screenshots/GIFs (optional, but recommended).

## License

This project is licensed under the MIT License. See `LICENSE`.
