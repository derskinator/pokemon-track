import requests, time, os, sys
from datetime import datetime

print("Script starting...", flush=True)

try:
    DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]
    print(f"Webhook loaded: {DISCORD_WEBHOOK[:40]}...", flush=True)
except KeyError:
    print("ERROR: DISCORD_WEBHOOK env variable not set!", flush=True)
    sys.exit(1)

CHECK_INTERVAL = 30

SD_TARGET_STORES = {
    "Mission Valley":    "1267",
    "Chula Vista":       "1335",
    "Kearny Mesa":       "2459",
    "La Mesa":           "2154",
    "Santee":            "2336",
    "Mira Mesa":         "1379",
    "Point Loma":        "2589",
    "North Park":        "3031",
    "South Park":        "3030",
    "Oceanside":         "1346",
    "Escondido":         "1348",
    "El Cajon":          "1356",
    "Poway":             "1350",
    "San Marcos":        "1351",
    "Encinitas":         "1352",
    "Vista":             "1353",
    "Carlsbad":          "1354",
    "Clairemont":        "2460",
}

TARGET_PRODUCTS = {
    "Prismatic Evolutions ETB":       "94166941",
    "Journey Together Booster Box":   "94603823",
    "Journey Together ETB":           "94603822",
    "Scarlet & Violet 151 ETB":       "88867374",
    "Ascended Heroes ETB":            "95082118",
    "Ascended Heroes Bundle":         "95120834",
    "Pokemon Perfect Order Booster":  "1011040115",
    "SV 151 Booster Pack": "1001304528",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
seen = {}

def ts():
    return datetime.now().strftime("%H:%M:%S")

def send_alert(emoji, location, product, qty):
    try:
        r = requests.post(DISCORD_WEBHOOK, json={
            "content": (
                f"{emoji} **Target drop!**\n"
                f"📦 {product}\n"
                f"📍 {location}\n"
                f"🔢 {qty}\n"
                f"⏰ {ts()}"
            )
        }, timeout=5)
        print(f"  Alert sent: {r.status_code}", flush=True)
    except Exception as e:
        print(f"  Discord error: {e}", flush=True)

def check_instore(tcin, store_id):
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
        print(f"  In-store error: {e}", flush=True)
    return 0

def check_online(tcin):
    url = (
        f"https://api.target.com/fulfillment_aggregator/v1/fiats"
        f"?key=9f36aeafbe60771e321a7cc95a78140772ab3e96"
        f"&tcins={tcin}"
        f"&fulfillment_test_mode=grocery_opu_team_member_test"
        f"&nearby=92101&limit=20&requested_quantity=1"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()
        # Check ship-to-home / online availability
        product = data.get("products", [{}])[0]
        online = product.get("online", {})
        availability = online.get("availability_status", "")
        qty = online.get("available_to_promise_quantity", 0)
        if availability in ("IN_STOCK", "LIMITED_STOCK"):
            return int(qty) if qty else 1
    except Exception as e:
        print(f"  Online error: {e}", flush=True)
    return 0

print(f"Tracker ready - {len(TARGET_PRODUCTS)} products", flush=True)
print(f"In-store: {len(SD_TARGET_STORES)} SD stores | Online: target.com", flush=True)
print(f"Scanning every {CHECK_INTERVAL}s", flush=True)

while True:
    try:
        print(f"[{ts()}] Scanning...", flush=True)
        for product, tcin in TARGET_PRODUCTS.items():

            # Check online
            online_key = f"online_{tcin}"
            online_qty = check_online(tcin)
            if online_qty > 0 and seen.get(online_key, 0) == 0:
                print(f"  ONLINE: {product} ({online_qty})", flush=True)
                send_alert("🌐", "Target.com — ships to you", product, f"{online_qty} units available online")
            seen[online_key] = online_qty
            time.sleep(1)

            # Check all SD stores
            for store, store_id in SD_TARGET_STORES.items():
                store_key = f"store_{tcin}_{store_id}"
                qty = check_instore(tcin, store_id)
                if qty > 0 and seen.get(store_key, 0) == 0:
                    print(f"  IN-STORE: {product} @ {store} ({qty})", flush=True)
                    send_alert("🔴", f"Target {store} — go now", product, f"{qty} units in store")
                seen[store_key] = qty
                time.sleep(1)

        print(f"[{ts()}] Scan done. Waiting {CHECK_INTERVAL}s...", flush=True)
        time.sleep(CHECK_INTERVAL)
    except Exception as e:
        print(f"Loop error: {e}", flush=True)
        time.sleep(10)
