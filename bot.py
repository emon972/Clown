import requests, json, time, os
from bs4 import BeautifulSoup
from exchanges import EXCHANGES, KEYWORDS, TARGET_EXCHANGE

BOT_TOKEN = os.getenv("BOT_TOKEN") or "8559731467:AAHzyC6H3JJw4wTLsXsCI2YiyM5A49Jm_fU"
CHAT_ID = os.getenv("CHAT_ID") or "1987110638"
DB_FILE = "token_db.json"

BICONOMY_URL = "https://www.biconomy.com/exchange-listings"  # Example Biconomy listings page

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def load_sent():
    if not os.path.exists("sent_tokens.txt"):
        return set()
    with open("sent_tokens.txt", "r") as f:
        return set(f.read().splitlines())

def save_sent(token_key):
    with open("sent_tokens.txt", "a") as f:
        f.write(token_key + "\n")

def pitch_message(token, exchange):
    return f"""Hi, I’m Dominic.
I noticed #{token} is currently trading on {exchange}.
Listing on Biconomy CEX could help you scale faster, especially with volume and visibility.
Would you be interested in discussing listing opportunities?
"""

def is_biconomy_listed(token):
    try:
        html = requests.get(BICONOMY_URL, timeout=10).text.lower()
        return token.lower() in html
    except:
        return False

def check_exchanges():
    sent = load_sent()

    for name, url in EXCHANGES.items():
        try:
            html = requests.get(url, timeout=10).text.lower()
            for kw in KEYWORDS:
                if kw in html:
                    # Basic token extraction
                    words = html.split()
                    for w in words:
                        if w.isupper() and 3 <= len(w) <= 8:
                            token = w
                            key = f"{token}_{name}"
                            if key in sent:
                                continue  # Already alerted

                            # Skip if token already on Biconomy
                            if is_biconomy_listed(token):
                                continue

                            # Determine status
                            status = "Recently listed" if "just listed" in html or "live now" in html else "Upcoming listing"

                            # Prepare message
                            msg = f"""🆕 Token Alert

Token: #{token}
Exchange: {name}
Status: {status}
Biconomy: Not listed yet ✅

Pitch:
{pitch_message(token, name)}

Useful Links:
CoinMarketCap: https://coinmarketcap.com/search?q={token}
CoinGecko: https://www.coingecko.com/en/search?query={token}
DEX: https://dexscreener.com/search?q={token}

---
"""
                            send_telegram(msg)
                            save_sent(key)
        except:
            pass

while True:
    check_exchanges()
    time.sleep(300)  # Run every 5 minutes
