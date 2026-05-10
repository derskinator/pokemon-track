import requests, time, os
from datetime import datetime

DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]
BESTBUY_API_KEY = os.environ["BESTBUY_API_KEY"]
TARGET_INTERVAL = 120
BESTBUY_INTERVAL = 90

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

BESTBUY_PRODUCTS = {
    "Prismatic Evolutions ETB":     "6570202",
    "Journey Together Booster Box": "6614837",
    "Journey Together ETB":         "6614838",
    "Scarlet & Violet 151 ETB":     "6543940",
}

SD_ZIP = "92101"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
seen = {}

def ts():
    return datetime.now().strftime("%H:%M:%S")

def send_alert(retailer, product, location, qty):
    icon = "🔴" if retailer == "Target" else "🔵"
    msg = {
        "content": (
            f"{icon} **{retailer}** — {product}\n"
            f"📍 {location} — **{qty} units**\n"
            f"⏰ {ts()}"
        )
    }
    try:
        requests.post(DISCORD_WEBHOOK, json=msg, timeout=5)
    except Exception as e:
        print(f"Discord error: {e}")

def check_target(tcin, store_id):
    url = (
        "https://api.target.com/fulfillment_aggregator/v1/fiats"
        f"?key=9f36aeafbe60771e321a7cc95a78140772ab3e96"
        f"&tcins={tcin}&store_id={store_id}"
        f"&zip={SD_ZIP}&state=CA&latitude=32.71&longitude=-117.15"
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

def check_bestbuy(sku):
    url = (
        f"https://api.bestbuy.com/v1/stores(area({SD_ZIP},25))"
        f"+products(sku={sku})/availability"
        f"?apiKey={BESTBUY_API_KEY}"
        f"&show=sku,stores.name,stores.availability&format=json"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        stores = r.json().get("stores", [])
        return [
            {"name": s["name"], "text": s["availability"].get("inStoreAvailabilityText", "In stock")}
            for s in stores
            if s.get("availability", {}).get("inStoreAvailability")
        ]
    except Exception as e:
        print(f"Best Buy error: {e}")
    return []

def scan_target():
    print(f"[{ts()}] Scanning Target...")
    for product, tcin in TARGET_PRODUCTS.items():
        for store_name, store_id in SD_TARGET_STORES.items():
            key = f"target_{tcin}_{store_id}"
            qty = check_target(tcin, store_id)
            prev = seen.get(key, 0)
            if qty > 0 and prev == 0:
                print(f"  FOUND @ Target {store_name}: {product} ({qty})")
                send_alert("Target", product, f"Target {store_name}", qty)
            seen[key] = qty
            time.sleep(2)

def scan_bestbuy():
    print(f"[{ts()}] Scanning Best Buy...")
    for product, sku in BESTBUY_PRODUCTS.items():
        key = f"bb_{sku}"
        stores = check_bestbuy(sku)
        prev_names = {s["name"] for s in seen.get(key, [])}
        for s in stores:
            if s["name"] not in prev_names:
                print(f"  FOUND @ {s['name']}: {product}")
                send_alert("Best Buy", product, s["name"], s["text"])
        seen[key] = stores
        time.sleep(1)

def main():
    print("Pokemon TCG tracker started — Target + Best Buy")
    print(f"Monitoring {len(TARGET_PRODUCTS)} products across {len(SD_TARGET_STORES)} Target stores")
    target_last = 0
    bb_last = 0
    while True:
        now = time.time()
        if now - target_last >= TARGET_INTERVAL:
            scan_target()
            target_last = time.time()
        if now - bb_last >= BESTBUY_INTERVAL:
            scan_bestbuy()
            bb_last = time.time()
        time.sleep(5)

if __name__ == "__main__":
    main()
