import requests, json, time, os
from bs4 import BeautifulSoup
from exchanges import EXCHANGES, KEYWORDS, TARGET_EXCHANGE

BOT_TOKEN = os.getenv("BOT_TOKEN") or "8559731467:AAHzyC6H3JJw4wTLsXsCI2YiyM5A49Jm_fU"
CHAT_ID = os.getenv("CHAT_ID") or "1987110638"
DB_FILE = "token_db.json"

FAKE_KEYWORDS = [
    "INU", "PEPE", "DOGE", "SHIB", "ELON",
    "BABY", "MEME", "TEST", "SCAM", "MOON"
]

REFRESH_TIME = 120  # seconds

# ---------------- DB ----------------
def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE) as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

# ---------------- Telegram send ----------------
def send(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ---------------- Fake token filter ----------------
def is_fake_token(symbol):
    s = symbol.upper()
    if len(s) < 2 or len(s) > 10:
        return True
    if not re.match("^[A-Z]+$", s):
        return True
    for k in FAKE_KEYWORDS:
        if k in s:
            return True
    return False

# ---------------- Extract tokens from text ----------------
def extract_tokens(text):
    tokens = set()
    for w in text.upper().split():
        if w.isalpha() and 2 <= len(w) <= 10:
            tokens.add(w)
    return tokens

# ---------------- Get Telegram from CoinGecko ----------------
def get_tg_from_cg(symbol):
    try:
        r = requests.get(f"https://api.coingecko.com/api/v3/search?query={symbol}", timeout=10).json()
        if not r["coins"]:
            return None
        coin_id = r["coins"][0]["id"]
        details = requests.get(f"https://api.coingecko.com/api/v3/coins/{coin_id}", timeout=10).json()
        tg = details["links"].get("telegram_channel_identifier")
        if tg:
            return f"https://t.me/{tg}"
    except:
        pass
    return None

# ---------------- Get Telegram from CoinMarketCap ----------------
def get_tg_from_cmc(symbol):
    try:
        headers = {"Accepts": "application/json"}
        r = requests.get(f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/info?symbol={symbol}&CMC_PRO_API_KEY=YOUR_CMC_API_KEY", headers=headers, timeout=10).json()
        data = r.get("data", {})
        if symbol in data:
            links = data[symbol].get("urls", {})
            tg_list = links.get("telegram", [])
            if tg_list:
                return tg_list[0]
    except:
        pass
    return None

# ---------------- Clean pitch message ----------------
def pitch(token, exchange, tg_link):
    return f"""Hey, I’m Dominic.

I noticed #{token} is currently trading on {exchange}.

Listing on Biconomy CEX could help you scale faster,
especially with stronger volume and broader visibility.

Would you be interested in discussing listing opportunities?

Telegram: {tg_link}
"""

# ---------------- Main loop ----------------
def run():
    db = load_db()

    for ex, url in EXCHANGES.items():
        try:
            html = requests.get(url, timeout=10).text.lower()
            if not any(k in html for k in KEYWORDS):
                continue

            tokens = extract_tokens(html)

            for t in tokens:

                if is_fake_token(t):
                    continue

                # Skip if already on Biconomy
                if t in db and TARGET_EXCHANGE in db[t].get("ex", []):
                    continue

                tg_link = get_tg_from_cg(t) or get_tg_from_cmc(t)
                if not tg_link:
                    continue  # skip if no TG

                if t not in db:
                    db[t] = {"ex": [], "sent": False}

                if ex not in db[t]["ex"]:
                    db[t]["ex"].append(ex)

                if db[t]["sent"]:
                    continue

                msg = pitch(t, ex, tg_link)
                send(msg)
                db[t]["sent"] = True
                save_db(db)

        except Exception as e:
            print(ex, e)

    save_db(db)

# ---------------- Run forever ----------------
send("✅ Biconomy Listing Hunter Bot Started")
while True:
    run()
    time.sleep(REFRESH_TIME)
