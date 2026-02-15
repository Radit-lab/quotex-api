import logging
import requests
import json
from time import sleep
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

# =======================================================
#   CONFIG — ADD YOUR BOT TOKEN HERE
# =======================================================
API_TOKEN = "8067374720:AAEKRztKZqOya0nX-wx_otGsaa2L8PJfoMY"
BOT_URL = f"https://api.telegram.org/bot{API_TOKEN}"

logging.basicConfig(level=logging.INFO)


# =======================================================
#   FUNCTION — PROCESS SIGNALS IN SIO.TOOLS
# =======================================================

def get_sio_result(signals: str):

    # Selenium Wire config (allows request capturing)
    options = {
        'disable_encoding': True
    }

    driver = webdriver.Chrome(seleniumwire_options=options)

    driver.get("https://sio.tools/checklist-signal")
    sleep(3)

    # ---------------------------------------------------------
    # 1. SELECT BROKER = QUOTEX
    # ---------------------------------------------------------
    try:
        select = Select(driver.find_element(By.TAG_NAME, "select"))
        select.select_by_visible_text("Quotex")
    except Exception as e:
        print("Dropdown error:", e)

    sleep(1)

    # ---------------------------------------------------------
    # 2. FILL TEXTAREA WITH SIGNALS (name='signals')
    # ---------------------------------------------------------
    textarea = driver.find_element(By.NAME, "signals")
    textarea.send_keys(signals)

    sleep(1)

    # ---------------------------------------------------------
    # 3. CLICK SUBMIT BUTTON
    # ---------------------------------------------------------
    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_btn.click()

    sleep(6)

    # ---------------------------------------------------------
    # 4. CAPTURE THE API REQUEST (HIDDEN SIO ID)
    # ---------------------------------------------------------
    sio_id = None

    for req in driver.requests:
        if "quotex/check/" in req.url:
            sio_id = req.url.split("quotex/check/")[1]
            break

    driver.quit()

    # Error if ID not found
    if not sio_id:
        return None

    # ---------------------------------------------------------
    # 5. FETCH THE JSON DATA FROM API
    # ---------------------------------------------------------
    api_url = f"https://sio.tools/quotex/check/{sio_id}"
    response = requests.get(api_url)
    return response.json()



def send_message(chat_id, text):
    """Send message via Telegram API"""
    url = f"{BOT_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    requests.post(url, data=data)

def get_updates(offset=0):
    """Get updates from Telegram"""
    url = f"{BOT_URL}/getUpdates"
    params = {"offset": offset, "timeout": 30}
    response = requests.get(url, params=params)
    return response.json()

def handle_signals(chat_id, signals):
    """Process signals and send result"""
    send_message(chat_id, "⏳ <b>Checking your signals on SIO Tools...</b>\nPlease wait 5–10 seconds.")
    
    result = get_sio_result(signals)
    
    if result is None:
        send_message(chat_id, "❌ Failed to fetch SIO result.\nTry again.")
        return
    
    send_message(chat_id, f"✅ <b>SIO RESULT:</b>\n\n<code>{json.dumps(result, indent=2)}</code>")

# =======================================================
#   START BOT
# =======================================================

if __name__ == "__main__":
    print("Bot started...")
    offset = 0
    
    while True:
        try:
            updates = get_updates(offset)
            
            if updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    
                    if "message" in update:
                        message = update["message"]
                        chat_id = message["chat"]["id"]
                        text = message.get("text", "")
                        
                        if text.strip():
                            handle_signals(chat_id, text.strip())
                            
        except Exception as e:
            print(f"Error: {e}")
            sleep(5)
