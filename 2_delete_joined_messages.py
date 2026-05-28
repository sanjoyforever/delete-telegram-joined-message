"""
Script 2: Connect to the already-running Chrome (port 9222) and delete all
Telegram service messages matching the pattern "{Name} joined Telegram".

Flow per message:
    1. Left-click  the message  (selects / highlights it)
    2. Right-click the message  (opens context menu)
    3. Click "Delete" in the context menu
    4. Confirm in the modal dialog

Prerequisites:
    pip install selenium

Usage:
    1. Run 1_launch_chrome.py and log into Telegram Web.
    2. Open the group/chat whose join messages you want to delete.
    3. Run this script.
"""

import time
import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    ElementNotInteractableException,
)

# ── Configuration ─────────────────────────────────────────────────────────────
DEBUGGER_ADDRESS = "127.0.0.1:9222"

# Seconds to wait between individual deletes (be gentle with Telegram)
DELAY_BETWEEN_DELETES = 1.2

# Maximum scroll-up rounds when searching for older messages
MAX_SCROLL_ROUNDS = 100

# The text fragment present in every "joined" service message
JOINED_TEXT = "joined Telegram"
# ─────────────────────────────────────────────────────────────────────────────


def connect_to_chrome() -> webdriver.Chrome:
    opts = Options()
    opts.add_experimental_option("debuggerAddress", DEBUGGER_ADDRESS)
    try:
        driver = webdriver.Chrome(options=opts)
    except Exception as exc:
        print(f"ERROR: Could not connect to Chrome at {DEBUGGER_ADDRESS}.")
        print("Make sure 1_launch_chrome.py is running and Telegram Web is open.")
        print(f"Detail: {exc}")
        sys.exit(1)
    print(f"Connected to Chrome at {DEBUGGER_ADDRESS}")
    return driver


def dismiss_overlay(driver):
    """Press Escape to close any open menu, modal, or selection mode."""
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    except Exception:
        pass
    time.sleep(0.3)


def find_joined_messages(driver):
    """
    Find all currently-visible rows with class 'chatlist-chat' whose inner text
    contains 'joined Telegram' (case-insensitive).

    XPath translate() is used for case-insensitive matching because XPath 1.0
    has no lower-case() function natively in browsers.
    """
    UPPER = "JOINED TELEGRAM"
    LOWER = "joined telegram"

    # Case-insensitive match using translate():
    # translate(., 'JOINED TELEGRAM', 'joined telegram') lowercases those chars,
    # then we check contains(result, 'joined telegram').
    xpath = (
        "//*[contains(@class,'chatlist-chat')]"
        f"[contains("
        f"translate(.,'{UPPER}','{LOWER}'),"
        f"'{LOWER}'"
        f")]"
    )
    elements = driver.find_elements(By.XPATH, xpath)
    if elements:
        return elements

    # Fallback: any element whose inner text contains the joined text
    xpath_fallback = (
        f"//*[contains("
        f"translate(.,'{UPPER}','{LOWER}'),"
        f"'{LOWER}'"
        f")]"
        f"[contains(@class,'service') or contains(@class,'Service') or "
        f"contains(@class,'system') or contains(@class,'System')]"
    )
    return driver.find_elements(By.XPATH, xpath_fallback)


def js_click_class(driver, class_name: str, index: int) -> bool:
    """Click document.getElementsByClassName(class_name)[index]. Returns True on success."""
    result = driver.execute_script(
        """
        var els = document.getElementsByClassName(arguments[0]);
        if (els.length > arguments[1]) {
            els[arguments[1]].click();
            return true;
        }
        return false;
        """,
        class_name,
        index,
    )
    return bool(result)


def wait_for_class(driver, class_name: str, min_count: int = 1, timeout: float = 5.0) -> bool:
    """Wait until at least min_count elements with class_name exist. Returns True if found."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        count = driver.execute_script(
            "return document.getElementsByClassName(arguments[0]).length;", class_name
        )
        if count >= min_count:
            return True
        time.sleep(0.2)
    return False


def select_then_delete(driver, element) -> bool:
    """
    Full delete flow using exact JS selectors provided by the user:

    1. Left-click the chatlist-chat row  → opens the chat
    2. JS: getElementsByClassName("btn-icon rp btn-menu-toggle")[2].click()
           → opens the 3-dot menu inside the chat header
    3. JS: getElementsByClassName("btn-menu-item rp-overflow danger")[0].click()
           → clicks the red "Delete" menu item
    4. JS: getElementsByClassName("checkbox-field-input")[9].click()
           → ticks "Also delete for everyone" checkbox in the confirm popup
    5. JS: getElementsByClassName("popup-button btn danger rp")[0].click()
           → confirms deletion
    6. JS: getElementsByClassName("btn-icon sidebar-back-button is-visible")[0].click()
           → goes back to the main chat list
    """
    try:
        # ── Step 1: click the row to open the chat ────────────────────────
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", element
        )
        time.sleep(0.4)
        element.click()
        time.sleep(1.2)   # wait for chat to fully open

        # ── Step 2: open the 3-dot menu (index 2 = chat header menu btn) ──
        if not wait_for_class(driver, "btn-icon rp btn-menu-toggle", min_count=3):
            print("    [WARN] 3-dot menu button not found")
            dismiss_overlay(driver)
            return False
        js_click_class(driver, "btn-icon rp btn-menu-toggle", 2)
        time.sleep(0.6)

        # ── Step 3: click the red Delete item in the dropdown ─────────────
        if not wait_for_class(driver, "btn-menu-item rp-overflow danger", min_count=1):
            print("    [WARN] Delete menu item not found")
            dismiss_overlay(driver)
            return False
        js_click_class(driver, "btn-menu-item rp-overflow danger", 0)
        time.sleep(0.6)

        # ── Step 4: tick the "delete for everyone" checkbox ───────────────
        if not wait_for_class(driver, "checkbox-field-input", min_count=10):
            print("    [WARN] Checkbox not found (expected index 9)")
            dismiss_overlay(driver)
            return False
        js_click_class(driver, "checkbox-field-input", 9)
        time.sleep(0.4)

        # ── Step 5: confirm deletion ──────────────────────────────────────
        if not wait_for_class(driver, "popup-button btn danger rp", min_count=1):
            print("    [WARN] Confirm delete button not found")
            dismiss_overlay(driver)
            return False
        js_click_class(driver, "popup-button btn danger rp", 0)
        time.sleep(0.8)

        # ── Step 6: go back to chat list ──────────────────────────────────
        if not wait_for_class(driver, "btn-icon sidebar-back-button is-visible", min_count=1):
            print("    [WARN] Back button not found, trying browser back...")
            driver.execute_script("window.history.back();")
        else:
            js_click_class(driver, "btn-icon sidebar-back-button is-visible", 0)
        time.sleep(1.0)   # wait for chat list to reload

        return True

    except (
        TimeoutException,
        NoSuchElementException,
        StaleElementReferenceException,
        ElementNotInteractableException,
    ) as exc:
        print(f"    [WARN] {exc.__class__.__name__}: {exc}")
        dismiss_overlay(driver)
        return False


def get_scroll_container(driver):
    """
    Return the scrollable container that holds the chatlist-chat rows.
    Tries to find the direct parent/ancestor of chatlist-chat items first,
    then falls back to generic scrollable containers.
    """
    # Try: ancestor of a chatlist-chat row that is itself scrollable
    candidates = driver.find_elements(
        By.XPATH,
        "//*[contains(@class,'chatlist-chat')]/ancestor::*[@class][1]",
    )
    if candidates:
        # Walk up until we find one with overflow scroll/auto
        for el in candidates:
            overflow = driver.execute_script(
                "var s = window.getComputedStyle(arguments[0]);"
                "return s.overflowY;",
                el,
            )
            if overflow in ("scroll", "auto"):
                return el

    # Fallback: pick the tallest scrollable element on the page
    all_scrollable = driver.find_elements(
        By.XPATH,
        "//*["
        "contains(@class,'scrollable') or contains(@class,'Scrollable') or "
        "contains(@class,'bubbles') or contains(@class,'Bubbles') or "
        "contains(@class,'messages-container') or contains(@class,'chatlist')"
        "]",
    )
    if all_scrollable:
        all_scrollable.sort(
            key=lambda el: driver.execute_script("return arguments[0].scrollHeight;", el),
            reverse=True,
        )
        return all_scrollable[0]
    return None


def scroll_up(driver, container):
    """
    Scroll the container upward to reveal older messages.
    Telegram loads ~10 items per scroll, so we scroll a moderate amount
    and then wait for the new items to appear in the DOM.
    """
    before_count = len(driver.find_elements(By.XPATH, "//*[contains(@class,'chatlist-chat')]"))

    if container:
        driver.execute_script("arguments[0].scrollTop -= 2000;", container)
    else:
        driver.execute_script("window.scrollBy(0, -2000);")

    # Wait up to 3 s for new items to load (Telegram lazy-loads ~10 at a time)
    deadline = time.time() + 3.0
    while time.time() < deadline:
        after_count = len(driver.find_elements(By.XPATH, "//*[contains(@class,'chatlist-chat')]"))
        if after_count != before_count:
            break
        time.sleep(0.3)
    else:
        time.sleep(1.0)  # nothing loaded, short pause before next round


def main():
    driver = connect_to_chrome()
    driver.switch_to.window(driver.current_window_handle)

    total_deleted = 0
    container = get_scroll_container(driver)
    consecutive_empty = 0

    print(f"\nScanning for '{JOINED_TEXT}' messages...")
    print("Make sure the target chat/group is open in Telegram Web.\n")

    for scroll_round in range(1, MAX_SCROLL_ROUNDS + 1):
        messages = find_joined_messages(driver)

        if not messages:
            consecutive_empty += 1
            print(
                f"[Round {scroll_round:3d}] No joined messages visible "
                f"(empty streak: {consecutive_empty}). Scrolling up..."
            )
            if consecutive_empty >= 5:
                print("5 consecutive empty rounds — reached the top. Done.")
                break
            scroll_up(driver, container)
            continue

        consecutive_empty = 0
        print(f"[Round {scroll_round:3d}] Found {len(messages)} joined message(s).")

        deleted_this_round = 0
        for msg in list(messages):   # snapshot; DOM changes after each delete
            try:
                text = msg.text.strip()
            except StaleElementReferenceException:
                continue

            if JOINED_TEXT not in text:
                continue

            print(f"  → \"{text}\"")
            if select_then_delete(driver, msg):
                total_deleted += 1
                deleted_this_round += 1
                print(f"     Deleted ✓  (total: {total_deleted})")
                time.sleep(DELAY_BETWEEN_DELETES)
            else:
                print(f"     Skipped ✗")

        if deleted_this_round == 0:
            scroll_up(driver, container)

    print(f"\n{'─' * 50}")
    print(f"Finished.  Total messages deleted: {total_deleted}")


if __name__ == "__main__":
    main()
