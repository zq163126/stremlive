import os
import json
import time
import requests
from playwright.sync_api import sync_playwright

def send_telegram_notification(message, image_path=None):
    """发送消息和截图至 Telegram"""
    token = os.getenv("TG_BOT_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")
    
    if not token or not chat_id:
        print("⚠️ 未配置 TG_BOT_TOKEN 或 TG_CHAT_ID，跳过 Telegram 推送")
        return

    try:
        if image_path and os.path.exists(image_path):
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            with open(image_path, "rb") as photos:
                payload = {"chat_id": chat_id, "caption": message}
                files = {"photo": photos}
                response = requests.post(url, data=payload, files=files, timeout=15)
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {"chat_id": chat_id, "text": message}
            response = requests.post(url, data=payload, timeout=15)
            
        if response.status_code == 200:
            print("✅ 异常通知已成功发送至 Telegram")
        else:
            print(f"❌ Telegram 推送失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 发送 Telegram 消息异常: {e}")

def wake_with_browser():
    cookies_json = os.getenv("USER_COOKIES_JSON")
    if not cookies_json:
        print("❌ 错误：未找到 USER_COOKIES_JSON")
        return

    try:
        users = json.loads(cookies_json)
    except Exception as e:
        print(f"❌ JSON 解析失败: {e}")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        for user_name, info in users.items():
            print(f"\n{'='*20} 正在执行: {user_name} {'='*20}")
            target_url = info.get("url")
            raw_cookie_str = info.get("cookie")
            
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # 注入 Cookies
            formatted_cookies = []
            for item in raw_cookie_str.split(';'):
                if '=' in item:
                    name, value = item.strip().split('=', 1)
                    formatted_cookies.append({"name": name, "value": value, "url": target_url})
            context.add_cookies(formatted_cookies)

            page = context.new_page()
            screenshot_path = f"result_{user_name}.png"
            
            try:
                print(f"正在打开页面...")
                page.goto(target_url, wait_until="networkidle", timeout=60000)
                time.sleep(12) # 给 iframe 充足的渲染时间

                # --- 维度 1：外层验证 ---
                if page.locator('button[data-testid="manage-app-button"]').is_visible():
                    print("✅ 登录验证成功：发现 'Manage app' 按钮。")

                # --- 维度 2：进入 iframe ---
                frame = page.frame_locator('iframe[title="streamlitApp"]')
                
                # 2.1 处理休眠唤醒
                wakeup_btn = frame.locator('button[data-testid="wakeup-button-owner"]')
                if wakeup_btn.count() > 0 and wakeup_btn.first.is_visible():
                    print("💤 发现 App 正在休眠，点击唤醒...")
                    wakeup_btn.first.click()
                    time.sleep(30) 
                
                # 2.3 验证内部状态 (解决多元素冲突)
                # 我们使用 .first 只取第一个匹配项，或者检查 count 是否大于 0
                stop_locator = frame.locator('button[data-testid="stBaseButton-header"]')
                text_stop_locator = frame.locator('text=Stop')

                if stop_locator.count() > 0 or text_stop_locator.count() > 0:
                    print(f"✨ 最终确认：已成功进入 App 内部，发现 {stop_locator.count()} 个头部组件。")
                else:
                    msg = f"🔎 [streamlit] 未直接抓取到 Stop 按钮，请检查截图。\n用户: {user_name}\n目标地址: {target_url}\n疑似 Cookie 已失效。"
                    print(msg)
                    # 发生异常时先截取并保存当前画面
                    page.screenshot(path=screenshot_path)
                    # 发送通知与图片至 Telegram
                    send_telegram_notification(msg, screenshot_path)

            except Exception as e:
                print(f"⚠️ 过程提醒: {e}")
            finally:
                # 无论是否报错，强制截图
                try:
                    # page.screenshot(path=f"result_{user_name}.png")
                    print(f"📸 截图已保存为 result_{user_name}.png")
                except:
                    pass
                context.close()
        
        browser.close()

if __name__ == "__main__":
    wake_with_browser()
