import os, re, time
from playwright.sync_api import sync_playwright

class THMManager:
    def __init__(self, state_path="auth.json"):
        self.state_path = state_path
        self.img_dir = "writeups/images"
        os.makedirs(self.img_dir, exist_ok=True)

    def prepare_room(self, room_name):
        room_name = re.sub(r'[\r\n\t\x00-\x1f]', '', room_name.strip())
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(storage_state=self.state_path)
            page = context.new_page()
            
            print(f"[*] Accessing Room: {room_name}...")
            try:
                page.goto(f"https://tryhackme.com/room/{room_name}", wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(7000) # 展開を待つ
            except Exception as e:
                print(f"[!] Page load warning: {e}")

            # 1. ルーム構造の取得
            tasks_elements = page.query_selector_all(".room-task")
            room_structure = []
            for i, task in enumerate(tasks_elements):
                title_elem = task.query_selector(".task-title")
                title = title_elem.inner_text().strip() if title_elem else f"Task {i+1}"
                q_elems = task.query_selector_all(".task-question-output")
                questions = [q.inner_text().strip() for q in q_elems]
                room_structure.append({"task_no": i+1, "title": title, "questions": questions})

            # 2. マシン起動処理 (Zerologon Task4対応版)
            # ページ内のすべての「Start Machine」ボタンを検索
            start_buttons = page.get_by_role("button", name=re.compile(r"Start Machine|Start Lab", re.I))
            
            count = start_buttons.count()
            if count > 0:
                print(f"[*] Found {count} start button(s). Attempting to trigger...")
                for i in range(count):
                    btn = start_buttons.nth(i)
                    if btn.is_visible():
                        btn.scroll_into_view_if_needed()
                        btn.click(force=True)
                        print(f"[+] Clicked Start Button {i+1}")
                        page.wait_for_timeout(5000)
            else:
                # すでに起動しているか確認
                html = page.content()
                if re.search(r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", html):
                    print("[!] Machine seems already running.")
                else:
                    print("[?] No start button found. Check if the machine is dynamic.")

            # 3. IP取得 (自動リロード)
            ip = None
            print("[*] Waiting for Target IP...")
            for _ in range(30):
                page.reload(wait_until="domcontentloaded")
                page.wait_for_timeout(7000)
                html = page.content()
                m = re.search(r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", html)
                if m:
                    ip = m.group(0)
                    page.screenshot(path=f"{self.img_dir}/dashboard.png")
                    print(f"[+] Target IP Found: {ip}")
                    break
                time.sleep(5)
            
            browser.close()
            return ip, room_structure
