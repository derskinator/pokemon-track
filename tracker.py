import requests, time, os
from datetime import datetime

DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]
CHECK_INTERVAL  = 120

SD_TARGET_STORES = {
    "Mission Valley":  "1267",
    "Chula Vista":     "1335",
    "Kearny Mesa":     "2459",
    "La Mesa":         "2154",
    "Santee":          "2336",
    "Mira Mesa":       "1379",
}

TARGET_PRODUCTS = {
    "Prismatic Evolutions ETB":     "94166941",
    "Journey Together Booster Box": "94603823",
    "Journey Together ETB":         "94603822",
    "Scarlet & Violet 151 ETB":     "88867374",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
seen = {}

def ts():
    return datetime.now().strftime("%H:%M:%S")

def send_alert(product, store, qty):
    try:
        requests.post(DISCORD_WEBHOOK, json={
            "content": (
                f"🔴 **Target** — {product}\n"
                f"📍 {store} — **{qty} units**\n"
                f"⏰ {ts()}"
            )
        }, timeout=5)
    except Exception as e:
        print(f"Discord error: {e}")

def check_stock(tcin, store_id):
    url = (
        "https://api.target.com/fulfillment_aggregator/v1/fiats"
        f"?key=9f36aeafbe60771e321a7cc95a78140772ab3e96"
        f"&tcins={tcin}&store_id={store_id}"
        f"&zip=92101&state=CA&latitude=32.71&longitude=-117.15"
        f"&radius=10&limit=20&include_only_available_stores=false"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        locs = r.json().get("products", [{}])[0].get("locations", [])
        for loc in locs:
            if loc.get("store_id") == store_id:
                return int(loc.get("available_to_promise_quantity", 0))
    except Exception as e:
        print(f"Target error: {e}")
    return 0

def main():
    print(f"Target tracker started — {len(TARGET_PRODUCTS)} products x {len(SD_TARGET_STORES)} stores")
    print(f"Scanning every {CHECK_INTERVAL}s")
    while True:
        print(f"[{ts()}] Scanning...")
        for product, tcin in TARGET_PRODUCTS.items():
            for store, store_id in SD_TARGET_STORES.items():
                key = f"{tcin}_{store_id}"
                qty = check_stock(tcin, store_id)
                if qty > 0 and seen.get(key, 0) == 0:
                    print(f"  FOUND: {product} @ Target {store} ({qty})")
                    send_alert(product, f"Target {store}", qty)
                seen[key] = qty
                time.sleep(2)
        print(f"[{ts()}] Scan done. Waiting {CHECK_INTERVAL}s...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
