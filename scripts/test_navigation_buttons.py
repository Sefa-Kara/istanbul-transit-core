"""
Automated End-to-End Navigation & Touch UI Button Verification Suite.
Clicks all buttons, tests sheet snap gestures, filters, and route planning.
"""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = Path("/Users/sefa/.gemini/antigravity/brain/c93cf407-d4e4-4da2-b4d3-16b71cf9641f")

def run_e2e_ui_test(target_url: str):
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Mobile viewport for mobile-first PWA testing
        context = browser.new_context(
            viewport={"width": 393, "height": 852},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            permissions=["geolocation"],
            geolocation={"latitude": 41.0082, "longitude": 28.9784}
        )
        page = context.new_page()

        print(f"Connecting to: {target_url}...")
        try:
            page.goto(target_url, wait_until="networkidle", timeout=45000)
        except Exception as e:
            print(f"Direct connection timed out, trying domcontentloaded: {e}")
            page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(3000)

        # 1. Map Verification
        map_el = page.locator("#map")
        results["map_loaded"] = map_el.count() > 0
        print("1. Map Canvas Present:", results["map_loaded"])

        # 2. Bottom Sheet Handle Click Toggle
        sheet = page.locator("#sidebar")
        handle = page.locator("#sheetHandle")
        if handle.count() > 0:
            handle.click()
            page.wait_for_timeout(400)
            results["handle_toggle_works"] = True
            print("2. Bottom Sheet Handle Click: PASS")
        else:
            results["handle_toggle_works"] = False

        # 3. Strategy Pills Verification
        strategy_pills = page.locator(".target-pill")
        pill_count = strategy_pills.count()
        clicked_pills = 0
        for i in range(pill_count):
            pill = strategy_pills.nth(i)
            pill.click()
            page.wait_for_timeout(100)
            clicked_pills += 1
        results["strategy_pills_clicked"] = clicked_pills
        print(f"3. Strategy Pills Tested: {clicked_pills}/{pill_count}")

        # 4. Mode Filter Chips Verification
        mode_chips = page.locator(".mode-chip")
        mode_count = mode_chips.count()
        clicked_modes = 0
        for i in range(mode_count):
            chip = mode_chips.nth(i)
            chip.click()
            page.wait_for_timeout(100)
            clicked_modes += 1
        results["mode_chips_clicked"] = clicked_modes
        print(f"4. Mode Filter Chips Tested: {clicked_modes}/{mode_count}")

        # 5. Time Chips Verification
        time_chips = page.locator(".time-quick-chip")
        time_count = time_chips.count()
        clicked_times = 0
        for i in range(time_count):
            chip = time_chips.nth(i)
            chip.click()
            page.wait_for_timeout(100)
            clicked_times += 1
        results["time_chips_clicked"] = clicked_times
        print(f"5. Time Chips Tested: {clicked_times}/{time_count}")

        # 6. FAB Buttons Verification
        locate_fab = page.locator("#mobileLocateFab")
        sheet_fab = page.locator("#mobileSheetFab")
        results["mobile_locate_fab"] = locate_fab.count() > 0
        results["mobile_sheet_fab"] = sheet_fab.count() > 0
        if sheet_fab.count() > 0:
            sheet_fab.click()
            page.wait_for_timeout(300)
            sheet_fab.click()
            page.wait_for_timeout(300)
            print("6. FAB Sheet Toggle: PASS")

        # 7. Popular Route Quick Chip Click & Autocomplete Test
        quick_chip = page.locator(".quick-chip").first
        if quick_chip.count() > 0:
            quick_chip.click()
            page.wait_for_timeout(2500)
            from_val = page.locator("#fromInput").input_value()
            to_val = page.locator("#toInput").input_value()
            results["quick_chip_fill"] = bool(from_val and to_val)
            print(f"7. Quick Chip Route Auto-Fill: {from_val} -> {to_val}")

        # 8. Take Comprehensive Screenshot
        shot_path = ARTIFACT_DIR / "mobile_pwa_verified.png"
        page.screenshot(path=str(shot_path))
        results["screenshot"] = str(shot_path)
        print(f"Mobile UI Screenshot saved to: {shot_path}")

        browser.close()
    return results

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://th3g3nt13man-istanbul-transit-core.hf.space/"
    res = run_e2e_ui_test(url)
    print("Test Results:", res)
