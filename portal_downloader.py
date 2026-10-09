"""
Portal Auto Data Downloader - Playwright Version
Kal ka data, 10 units, automatic download
"""

import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ============= CONFIG =============
USERNAME = "12202006"
PASSWORD = "JCB@2889"
PORTAL_URL = "http://10.0.1.14/portal/index.php"
DOWNLOAD_FOLDER = r"C:\PortalData"

UNITS = [
    ("Krishna",  "17423313"),
    ("SG",       "17423312"),
    ("Indore",   "17423317"),
    ("Jabalpur", "17423318"),
    ("Jaipur",   "17423461"),
    ("Mohali",   "17423460"),
    ("Vapi",     "17423464"),
    ("Vijay",    "17423315"),
    ("Naroda",   "17423314"),
    ("Surat",    "17423463"),
]
# ==================================


def log(msg, level="INFO"):
    colors = {
        "INFO":  "\033[96m",
        "OK":    "\033[92m",
        "WARN":  "\033[93m",
        "ERROR": "\033[91m",
        "UNIT":  "\033[95m",
    }
    reset = "\033[0m"
    color = colors.get(level, "")
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{timestamp}] {msg}{reset}")


def get_yesterday_dates():
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime("%d/%m/%Y")
    return date_str, date_str


def download_units():
    from_date, to_date = get_yesterday_dates()

    Path(DOWNLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
    today_folder = os.path.join(DOWNLOAD_FOLDER, datetime.now().strftime("%Y-%m-%d"))
    Path(today_folder).mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    log("PORTAL AUTO DOWNLOADER - PLAYWRIGHT", "OK")
    log(f"Data Date (Kal) : {from_date}")
    log(f"Save Folder     : {today_folder}")
    log(f"Username        : {USERNAME}")
    log(f"Total Units     : {len(UNITS)}")
    print("=" * 60)
    print()

    with sync_playwright() as p:
        log("[1/6] Chrome browser khol raha hu...")
        browser = p.chromium.launch(
            headless=False,
            slow_mo=200,
            args=["--start-maximized"]
        )

        context = browser.new_context(
            accept_downloads=True,
            viewport={"width": 1366, "height": 768}
        )

        page = context.new_page()

        # STEP 1: Portal kholo
        log(f"[2/6] Portal khol raha hu: {PORTAL_URL}")
        page.goto(PORTAL_URL, timeout=30000)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # STEP 2: Login
        log("[3/6] Login kar raha hu...")
        try:
            page.fill("#j_username", USERNAME)
            time.sleep(0.3)
            page.fill("input[name='j_password']", PASSWORD)
            time.sleep(0.3)
            page.click("input[name='Login']")
            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(3)

            current_url = page.url
            log(f"      Current URL: {current_url}")

            if "Invalid" in current_url:
                log("LOGIN FAIL! Username/Password galat.", "ERROR")
                input("Enter dabao...")
                return

            log("      Login OK", "OK")
        except Exception as e:
            log(f"Login fail: {e}", "ERROR")
            input("Enter dabao...")
            return

        # STEP 3: NMI Dashboard link
        log("[4/6] NMI Dashboard link dhundh raha hu...")
        dashboard_url = None
        try:
            links = page.query_selector_all("a")
            for link in links:
                text = link.inner_text() or ""
                if "NMI Dashboard" in text:
                    dashboard_url = link.get_attribute("href")
                    break

            if not dashboard_url:
                log("NMI Dashboard link nahi mila!", "ERROR")
                input("Enter dabao...")
                return

            if dashboard_url.startswith("../"):
                dashboard_url = "http://10.0.1.14/portal/" + dashboard_url[3:]
            elif dashboard_url.startswith("/"):
                dashboard_url = "http://10.0.1.14" + dashboard_url

            log(f"      Dashboard URL: {dashboard_url}", "OK")
        except Exception as e:
            log(f"Dashboard link error: {e}", "ERROR")
            input("Enter dabao...")
            return

        # STEP 4: Dashboard kholo
        log("[5/6] Dashboard khol raha hu...")
        page.goto(dashboard_url, timeout=30000)
        page.wait_for_load_state("networkidle")
        time.sleep(3)

        if not page.query_selector("#site"):
            log("Dashboard me 'site' dropdown nahi mila!", "WARN")
        else:
            log("      Dashboard ready hai", "OK")

        print()

        # STEP 5: Har unit ka data
        log(f"[6/6] {len(UNITS)} units ka data download kar raha hu...")
        print()

        success_count = 0
        failed_units = []

        for idx, (unit_name, unit_value) in enumerate(UNITS, 1):
            print("-" * 60)
            log(f"[{idx}/{len(UNITS)}] UNIT: {unit_name} ({unit_value})", "UNIT")
            print("-" * 60)

            try:
                page.select_option("#site", value=unit_value)
                time.sleep(1)

                page.evaluate(f"""
                    var fd = document.getElementById('txt_fromdt');
                    if (fd) {{
                        fd.removeAttribute('readonly');
                        fd.value = '{from_date}';
                        fd.dispatchEvent(new Event('change', {{bubbles: true}}));
                        fd.dispatchEvent(new Event('blur', {{bubbles: true}}));
                    }}
                """)
                time.sleep(0.8)

                page.evaluate(f"""
                    var td = document.getElementById('txt_todt');
                    if (td) {{
                        td.removeAttribute('readonly');
                        td.value = '{to_date}';
                        td.dispatchEvent(new Event('change', {{bubbles: true}}));
                        td.dispatchEvent(new Event('blur', {{bubbles: true}}));
                    }}
                """)
                time.sleep(0.8)

                log(f"      Submit...")
                page.click("#Submit")
                page.wait_for_load_state("networkidle", timeout=20000)
                time.sleep(3)

                log(f"      Export...")
                with page.expect_download(timeout=30000) as download_info:
                    page.click("#export")

                download = download_info.value
                suggested_name = download.suggested_filename or f"{unit_name}.xlsb"
                ext = os.path.splitext(suggested_name)[1] or ".xlsb"
                save_name = f"{unit_name}{ext}"
                save_path = os.path.join(today_folder, save_name)

                download.save_as(save_path)
                log(f"      SAVED: {save_name}", "OK")

                success_count += 1

                if idx < len(UNITS):
                    page.goto(dashboard_url, timeout=30000)
                    page.wait_for_load_state("networkidle")
                    time.sleep(2)

            except PlaywrightTimeout:
                log(f"      TIMEOUT - {unit_name} fail", "ERROR")
                failed_units.append(unit_name)
                try:
                    page.goto(dashboard_url, timeout=30000)
                    page.wait_for_load_state("networkidle")
                    time.sleep(2)
                except:
                    pass
                continue

            except Exception as e:
                log(f"      ERROR: {e}", "ERROR")
                failed_units.append(unit_name)
                try:
                    page.goto(dashboard_url, timeout=30000)
                    page.wait_for_load_state("networkidle")
                    time.sleep(2)
                except:
                    pass
                continue

        print()
        print("=" * 60)
        log(f"KAAM PURA HUA!", "OK")
        log(f"Success: {success_count}/{len(UNITS)}", "OK")
        log(f"Files  : {today_folder}", "OK")

        if failed_units:
            log(f"Failed : {', '.join(failed_units)}", "ERROR")

        print("=" * 60)

        log("5 sec me browser band ho raha hai...")
        time.sleep(5)
        browser.close()


if __name__ == "__main__":
    try:
        download_units()
    except KeyboardInterrupt:
        print("\n\nUser ne cancel kiya.")
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

    input("\nBand karne ke liye Enter dabao...")
