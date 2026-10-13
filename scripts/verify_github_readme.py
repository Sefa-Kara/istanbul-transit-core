"""
Visual inspection script for GitHub README.
Scrolls down to README and captures full viewport screenshot.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path

ARTIFACT_DIR = Path("/Users/sefa/.gemini/antigravity/brain/c93cf407-d4e4-4da2-b4d3-16b71cf9641f")
SCREENSHOT_PATH = ARTIFACT_DIR / "github_readme_view.png"

def capture_github():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        
        print("Navigating to GitHub repo...")
        page.goto("https://github.com/Sefa-Kara/istanbul-transit-core", wait_until="load", timeout=30000)
        page.wait_for_timeout(2500)
        
        # Scroll to README
        page.evaluate("window.scrollTo(0, 650);")
        page.wait_for_timeout(1000)
        
        page.screenshot(path=str(SCREENSHOT_PATH))
        print(f"Viewport screenshot saved to: {SCREENSHOT_PATH}")
        
        body_text = page.inner_text("body")
        has_yaml = "title\nIstanbul Transit Core" in body_text or "title\tIstanbul Transit Core" in body_text
        print("Has YAML table in body:", has_yaml)
        
        browser.close()
        return not has_yaml

if __name__ == "__main__":
    clean = capture_github()
    print("GitHub Verification Result:", "CLEAN" if clean else "FAIL")
