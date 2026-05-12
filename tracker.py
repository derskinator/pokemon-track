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

TARGET_PRODUCTS = {
    "Prismatic Evolutions ETB":      "94166941",
    "Journey Together Booster Box":  "94603823",
    "Journey Together ETB":          "94603822",
    "Scarlet & Violet 151 ETB":      "88867374",
    "Ascended Heroes ETB":           "95082118",
    "Ascended Heroes Bundle":        "95120834",
    "Pokemon Perfect Order Booster": "1011040115",
    "SV 151 Booster Pack":           "1001304528",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
seen = {}

def ts():
    return datetime.now().strftime("%H:%M:%S")

def send_alert(product, status, url):
    try:
        requests.post(DISCORD_WEBHOOK, json={
            "content": (
                f"🌐 **Target.com restock!**\n"
                f"📦 {product}\n"
                f"📊 {status}\n"
                f"🔗 https://www.target.com/p/-/A-{url}\n"
                f"⏰ {ts()}"
            )
        }, timeout=5)
        print(f"  Alert sent!", flush=True)
    except Exception as e:
        print(f"  Discord error: {e}", flush=True)

def check_online(tcin):
    url = (
        f"https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1"
        f"?key=9f36aeafbe60771e321a7cc95a78140772ab3e96"
        f"&tcin={tcin}"
        f"&store_id=1267"
        f"&zip=92101&state=CA&latitude=32.71&longitude=-117.15"
        f"&scheduled_delivery_store_id=1267"
        f"&pricing_store_id=1267"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()
        avail = (
            data.get("data", {})
                .get("product", {})
                .get("fulfillment", {})
                .get("shipping_options", {})
                .get("availability_status", "")
        )
        print(f"  {tcin}: {avail}", flush=True)
        if avail in ("IN_STOCK", "LIMITED_STOCK", "INSTOCK"):
            return avail
    except Exception as e:
        print(f"  Error {tcin}: {e}", flush=True)
    return None

print(f"Online tracker ready - {len(TARGET_PRODUCTS)} products", flush=True)
print(f"Scanning target.com every {CHECK_INTERVAL}s", flush=True)

while True:
    try:
        print(f"[{ts()}] Scanning...", flush=True)
        for product, tcin in TARGET_PRODUCTS.items():
            status = check_online(tcin)
            prev = seen.get(tcin)
            if status and not prev:
                print(f"  ONLINE: {product} — {status}", flush=True)
                send_alert(product, status, tcin)
            seen[tcin] = status
            time.sleep(1)
        print(f"[{ts()}] Done. Waiting {CHECK_INTERVAL}s...", flush=True)
        time.sleep(CHECK_INTERVAL)
    except Exception as e:
        print(f"Loop error: {e}", flush=True)
        time.sleep(10)
