import requests, json, time, os
from bs4 import BeautifulSoup
from exchanges import EXCHANGES, KEYWORDS, TARGET_EXCHANGE

BOT_TOKEN = os.getenv("BOT_TOKEN") or "8559731467:AAHzyC6H3JJw4wTLsXsCI2YiyM5A49Jm_fU"
CHAT_ID = os.getenv("CHAT_ID") or "1987110638"
DB_FILE = "token_db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE) as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def send(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    
def coingecko_link(symbol):
    try:
        r = requests.get(
            f"https://api.coingecko.com/api/v3/search?query={symbol}",
            timeout=10
        ).json()
        if r["coins"]:
            return f"https://www.coingecko.com/en/coins/{r['coins'][0]['id']}"
    except:
        pass
    return "N/A"
    
    def extract_tokens(text):
    tokens = set()
    for word in text.upper().split():
        if word.isalpha() and 2 <= len(word) <= 8:
            tokens.add(word)
    return tokens

def pitch(token, exchange, status, count, cg):
    return f"""Hey, I’m Dominic.
I noticed #{token} is currently trading on {exchange}.

Listing on Biconomy CEX could help you scale faster,
especially with volume and visibility.

Would you be interested in discussing listing opportunities?

CG: {cg}
Status: {status} ({count} exchanges)

"""

def run():
    db = load_db()

    for ex, url in EXCHANGES.items():
        try:
            html = requests.get(url, timeout=10).text
            low = html.lower()

            if not any(k in low for k in KEYWORDS):
                continue

            tokens = extract_tokens(html)

            for t in tokens:
                if t not in db:
                    db[t] = {"ex": [], "biconomy": False}

                if ex not in db[t]["ex"]:
                    db[t]["ex"].append(ex)

                # if already on biconomy → skip
                if TARGET_EXCHANGE in db[t]["ex"]:
                    db[t]["biconomy"] = True
                    continue

                count = len(db[t]["ex"])

                if count == 1:
                    status = "Fresh"
                elif count == 2:
                    status = "Expansion"
                else:
                    status = "Scaling"

                cg = coingecko_link(t)

                msg = "🆕 NEW LISTING SIGNAL\n\n" + pitch(t, ex, status, count,cg)
                send(msg)

        except Exception as e:
            print(ex, e)

    save_db(db)

while True:
    run()
    time.sleep(120)
