import requests, json, time, os
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from exchanges import EXCHANGES, KEYWORDS, TARGET_EXCHANGE, TIER1_EXCHANGES

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

# CoinGecko link
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

# CoinMarketCap link
def cmc_link(symbol):
    try:
        r = requests.get(
            f"https://api.coinmarketcap.com/data-api/v3/search?searchQuery={symbol}",
            timeout=10
        ).json()
        if r.get("data", {}).get("coins"):
            slug = r["data"]["coins"][0]["slug"]
            return f"https://coinmarketcap.com/currencies/{slug}/"
    except:
        pass
    return "N/A"

# Fallback link
def get_token_links(symbol):
    cg = coingecko_link(symbol)
    cmc = cmc_link(symbol)
    if cg != "N/A":
        return cg
    elif cmc != "N/A":
        return cmc
    else:
        return None

# Extract tokens
def extract_tokens(text):
    tokens = set()
    for word in text.upper().split():
        if word.isalpha() and 2 <= len(word) <= 8:
            tokens.add(word)
    return tokens

# Date filter (≤30 days)
def is_recent_listing(date_str):
    try:
        # Try multiple formats
        for fmt in ["%Y-%m-%d", "%b %d, %Y", "%d %b %Y"]:
            try:
                listing_date = datetime.strptime(date_str.strip(), fmt)
                return datetime.now() - listing_date <= timedelta(days=30)
            except:
                continue
    except:
        return False
    return False

# Message format
def pitch(token, exchange, status, count, link):
    return f"""🆕 NEW LISTING SIGNAL

Token: #{token}
Exchange: {exchange}
Status: {status} ({count} exchanges)
Link: {link}

Hey, I’m Dominic.
I noticed #{token} just got listed on {exchange}.
Listing on Biconomy CEX could help you scale faster — especially with volume and visibility.
Would you be interested in discussing listing opportunities?
"""

def run():
    db = load_db()

    for ex, url in EXCHANGES.items():
        # Skip Tier-1 exchanges
        if ex.lower() in TIER1_EXCHANGES:
            continue

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

                link = get_token_links(t)
                if not link:
                    continue  # skip if no link found

                # Optional: extract listing date from HTML (example placeholder)
                # soup = BeautifulSoup(html, "html.parser")
                # date_str = soup.find("span", {"class": "listing-date"}).text if soup.find("span", {"class": "listing-date"}) else None
                # if date_str and not is_recent_listing(date_str):
                #     continue

                msg = pitch(t, ex, status, count, link)
                send(msg)

        except Exception as e:
            print(ex, e)

    save_db(db)

while True:
    run()
    time.sleep(120)
