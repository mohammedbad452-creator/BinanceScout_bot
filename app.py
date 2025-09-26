from flask import Flask
from flask_apscheduler import APScheduler
import requests
import os

app = Flask(__name__)
scheduler = APScheduler()

# مجموعة لحفظ أسماء العملات الأساسية المعروفة
BASE_ASSETS = set()

def send_telegram_message(text):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("فشل إرسال رسالة إلى Telegram:", e)

def check_new_listings():
    global BASE_ASSETS
    try:
        # استدعاء واجهة ExchangeInfo للحصول على معلومات التداول الحالية
        res = requests.get("https://api.binance.com/api/v3/exchangeInfo")
        res.raise_for_status()
        data = res.json()
        symbols = data.get("symbols", [])
    except Exception as e:
        print("خطأ في جلب بيانات Binance:", e)
        return

    # استخراج مجموعة أسماء العملات الأساسية (baseAsset) من رموز التداول
    current_assets = {sym["baseAsset"] for sym in symbols}
    # في أول مرة، نحفظ القائمة الحالية فقط دون إرسال تنبيهات
    if not BASE_ASSETS:
        BASE_ASSETS = current_assets
        return

    # إيجاد العملات الجديدة التي لم تكن موجودة سابقًا
    new_coins = current_assets - BASE_ASSETS
    if new_coins:
        BASE_ASSETS = current_assets  # تحديث القائمة المعروفة
        for coin in new_coins:
            message = f"🔔 تم إدراج عملة جديدة على Binance: {coin}"
            send_telegram_message(message)
            print(f"إشعار تم إرساله للرمز الجديد: {coin}")

# جدولة تنفيذ المهمة كل 5 دقائق
@scheduler.task('interval', id='check_new', minutes=5)
def scheduled_task():
    check_new_listings()

# تهيئة المجدول ثم تشغيل التطبيق
scheduler.init_app(app)
scheduler.start()

@app.route('/')
def home():
    return 'البوت يعمل!'
