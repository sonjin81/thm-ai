from playwright.sync_api import sync_playwright

def save_auth():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        page = context.new_page()
        page.goto("https://tryhackme.com/login")

        print("👉 ブラウザでログインしてください（reCAPTCHA含む）")

        input("ログイン完了したらEnter押してください")

        context.storage_state(path="auth.json")

        print("✅ 保存完了: auth.json")

        browser.close()

if __name__ == "__main__":
    save_auth()
