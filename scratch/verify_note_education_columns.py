import os
import time
import subprocess
from playwright.sync_api import sync_playwright

def verify():
    brain_dir = r"C:\Users\User\.gemini\antigravity\brain\b6f4fd4e-e888-47c0-8861-e73cd577da74"
    repo_dir = r"C:\Users\User\.gemini\antigravity\scratch\bantai-education-design.github.io"
    
    # Start local http server
    server = subprocess.Popen(["python", "-m", "http.server", "8089"], cwd=repo_dir)
    time.sleep(2)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 1. Homepage
            page.goto("http://localhost:8089/")
            page.wait_for_selector(".column-card")
            page.screenshot(path=os.path.join(brain_dir, "note_education_homepage.png"), full_page=True)
            print("Homepage screenshot captured.")
            
            # 2. Columns List Page
            page.goto("http://localhost:8089/columns/")
            page.wait_for_selector(".column-card")
            page.screenshot(path=os.path.join(brain_dir, "note_education_columns_list.png"), full_page=True)
            print("Columns list screenshot captured.")
            
            # 3. Vol 12 Modal (Extra Reflection)
            vol12_card = page.locator("article[data-id='column-note-education-monthly-extra-reflection-vol12']")
            if vol12_card.count() > 0:
                vol12_card.click()
                page.wait_for_selector("#modalContent img")
                time.sleep(1)
                page.screenshot(path=os.path.join(brain_dir, "note_education_modal_vol12.png"))
                print("Vol 12 modal screenshot captured.")
                page.click("#closeModal")
                time.sleep(0.5)
            
            # 4. Vol 11 Modal (Curation Digest & Comment format)
            vol11_card = page.locator("article[data-id='column-note-education-monthly-curation-vol11']")
            if vol11_card.count() > 0:
                vol11_card.click()
                page.wait_for_selector("#modalContent table")
                time.sleep(1)
                page.screenshot(path=os.path.join(brain_dir, "note_education_modal_vol11.png"))
                print("Vol 11 modal screenshot captured.")
                page.click("#closeModal")
                time.sleep(0.5)

            browser.close()
    finally:
        server.terminate()

if __name__ == "__main__":
    verify()
