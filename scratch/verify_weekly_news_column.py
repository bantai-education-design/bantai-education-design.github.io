import http.server
import socketserver
import threading
import time
import sys
import os
from playwright.sync_api import sync_playwright

PORT = 8090
DIRECTORY = "."

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

httpd = socketserver.TCPServer(("", PORT), Handler)
server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
server_thread.start()
time.sleep(1)

out_dir = os.path.join(os.getcwd(), "scratch")
os.makedirs(out_dir, exist_ok=True)

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        
        # 1. Homepage verification
        page.goto(f"http://localhost:{PORT}/")
        page.wait_for_selector("#home-columns-grid .column-card")
        time.sleep(1)
        hp_path = os.path.join(out_dir, "weekly_news_homepage.png")
        page.screenshot(path=hp_path)
        print(f"Homepage screenshot saved to {hp_path}", flush=True)
        
        # 2. Columns list page verification
        page.goto(f"http://localhost:{PORT}/columns/")
        page.wait_for_selector("#columns-grid .column-card")
        time.sleep(1)
        cl_path = os.path.join(out_dir, "weekly_news_columns_list.png")
        page.screenshot(path=cl_path)
        print(f"Columns list screenshot saved to {cl_path}", flush=True)
        
        # Open Vol 6 modal directly via JS
        page.evaluate("openColumnModal('column-weekly-education-news-20260917')")
        page.wait_for_selector("#column-modal.is-open")
        time.sleep(1)
        
        # Top of modal screenshot
        modal_dialog = page.locator(".column-modal-dialog")
        mt_path = os.path.join(out_dir, "weekly_news_modal_top.png")
        modal_dialog.screenshot(path=mt_path)
        print(f"Modal top screenshot saved to {mt_path}", flush=True)
        
        # Scroll modal dialog down to reveal inline images
        modal_dialog.evaluate("el => el.scrollTop = 1200")
        time.sleep(1)
        mi_path = os.path.join(out_dir, "weekly_news_modal_inline_images.png")
        modal_dialog.screenshot(path=mi_path)
        print(f"Modal inline images screenshot saved to {mi_path}", flush=True)
        
        browser.close()
finally:
    httpd.shutdown()

print("Weekly education news column Playwright verifications passed!", flush=True)
sys.exit(0)
