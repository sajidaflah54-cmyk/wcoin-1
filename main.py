import time as t
import requests as r
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

# API endpoint
API_URL = "https://starfish-app-fknmx.ondigitalocean.app/wapi/api/external-api/verify-task"

# Settings
TASK_ID = 528
BATCH_SIZE = 50          # number of requests per batch
BATCHES_AT_ONCE = 5      # number of batches run in parallel
WAIT_BETWEEN_ROUNDS = 10 # seconds
BALANCE_LIMIT = 100000000 # stop at 100M (example)

# User-Agent rotation (add more if needed)
AGENTS = [
    "Mozilla/5.0 (Linux; Android 13; Pixel 6a) AppleWebKit/537.36 Chrome/139.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-G981B) AppleWebKit/537.36 Chrome/118.0.5993.70 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    "Mozilla/5.0 (Linux; Android 11; Redmi Note 9 Pro) AppleWebKit/537.36 Chrome/105.0.5195.79 Mobile Safari/537.36"
]

# Get init data
x_init_data = input("📥 Please enter your x-init-data:\n> ").strip()

# Simulated balance function (replace with actual check if possible)
def get_balance():
    return 1000  # placeholder

def send_request():
    ts = int(t.time())
    payload = {
        "taskId": TASK_ID,
        "taskContents": {
            "viewedTimes": 1,
            "lastViewed": ts
        }
    }
    headers = {
        "Content-Type": "application/json",
        "accept": "*/*",
        "origin": "https://app.w-coin.io",
        "referer": "https://app.w-coin.io/",
        "user-agent": random.choice(AGENTS),
        "x-init-data": x_init_data,
        "x-request-timestamp": str(ts)
    }

    for attempt in range(3):  # retry up to 3 times
        try:
            res = r.post(API_URL, headers=headers, json=payload, timeout=5)
            if res.status_code == 200:
                print(f"[{ts}] ✅ Success: {res.text}")
                return True
            else:
                print(f"[{ts}] ❌ Error {res.status_code}: {res.text}")
        except Exception as ex:
            print(f"[{ts}] ⚠️ Request error: {ex}")
        t.sleep(1)  # wait before retry
    return False

def run_batch(batch_num):
    print(f"  >> Starting batch {batch_num}")
    results = []
    with ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
        futures = [executor.submit(send_request) for _ in range(BATCH_SIZE)]
        for future in as_completed(futures):
            results.append(future.result())
            # Random short delay to avoid burst detection
            t.sleep(random.uniform(0.05, 0.3))
    print(f"  >> Finished batch {batch_num}")
    return results

# Main loop
round_num = 1
while True:
    balance = get_balance()
    if balance >= BALANCE_LIMIT:
        print(f"💰 Balance limit reached ({balance} >= {BALANCE_LIMIT}), stopping.")
        break

    print(f"\n=== Round {round_num}: {BATCHES_AT_ONCE} batches of {BATCH_SIZE} requests ===")
    start_time = t.time()

    with ThreadPoolExecutor(max_workers=BATCHES_AT_ONCE) as executor:
        futures = [executor.submit(run_batch, i+1) for i in range(BATCHES_AT_ONCE)]
        for _ in as_completed(futures):
            pass

    print(f"=== Round {round_num} completed in {t.time()-start_time:.2f} seconds ===")
    print(f"⏳ Waiting {WAIT_BETWEEN_ROUNDS} seconds before next round...\n")
    t.sleep(WAIT_BETWEEN_ROUNDS)
    round_num += 1