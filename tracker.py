import requests, time, os, sys
from datetime import datetime

print("Script starting...", flush=True)

try:
    DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]
    print(f"Webhook loaded: {DISCORD_WEBHOOK[:40]}...", flush=True)
except KeyError:
    print("ERROR: DISCORD_WEBHOOK env variable not set!", flush=True)
    sys.exit(1)

CHECK_INTERVAL = 120

SD_TARGET_STORES = {
    "Mission Valley": "1267",
    "Chula Vista":    "1335",
    "Kearny Mesa":    "2459",
    "La Mesa":        "2154",
    "Santee":         "2336",
    "Mira Mesa":      "1379",
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
        r = requests.post(DISCORD_WEBHOOK, json={
            "content": f"Target drop! {product} @ {store} - {qty} units"
        }, timeout=5)
        print(f"  Alert sent: {r.status_code}", flush=True)
    except Exception as e:
        print(f"  Discord error: {e}", flush=True)

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
        print(f"  Target error: {e}", flush=True)
    return 0

print(f"Tracker ready - {len(TARGET_PRODUCTS)} products x {len(SD_TARGET_STORES)} stores", flush=True)
print(f"Scanning every {CHECK_INTERVAL}s", flush=True)

while True:
    try:
        print(f"[{ts()}] Scanning...", flush=True)
        for product, tcin in TARGET_PRODUCTS.items():
            for store, store_id in SD_TARGET_STORES.items():
                key = f"{tcin}_{store_id}"
                qty = check_stock(tcin, store_id)
                if qty > 0 and seen.get(key, 0) == 0:
                    print(f"  FOUND: {product} @ {store} ({qty})", flush=True)
                    send_alert(product, f"Target {store}", qty)
                seen[key] = qty
                time.sleep(2)
        print(f"[{ts()}] Done. Waiting {CHECK_INTERVAL}s...", flush=True)
        time.sleep(CHECK_INTERVAL)
    except Exception as e:
        print(f"Loop error: {e}", flush=True)
        time.sleep(10)
