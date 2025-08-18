import time, requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==== CONFIG ====
API_URL = "https://starfish-app-fknmx.ondigitalocean.app/wapi/api/external-api/verify-task"
TASK_ID = 528
REQUESTS_PER_BATCH = 100
BATCHES_PER_ROUND = 1
ROUND_DELAY = 5
BALANCE_LIMIT = 100000

# 🟡 Ask user to enter their x-init-data
X_INIT_DATA = input("📥 Please enter your x-init-data:\n> ").strip()

# 🟢 Simulated balance fetch (replace with actual API if needed)
def get_balance():
    return 1000

# 🔁 Send a single request
def send_task():
    t = int(time.time())
    data = {"taskId": TASK_ID, "taskContents": {"viewedTimes": 1, "lastViewed": t}}
    headers = {
        "Content-Type": "application/json",
        "accept": "*/*",
        "origin": "https://app.w-coin.io",
        "referer": "https://app.w-coin.io/",
        "user-agent": "Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
        "x-init-data": X_INIT_DATA,
        "x-request-timestamp": str(t)
    }
    try:
        r = requests.post(API_URL, headers=headers, json=data, timeout=5)
        print(f"[{t}] Status: {r.status_code} | {r.text}")
    except Exception as e:
        print(f"Request error: {e}")

# 🔁 One batch
def run_batch(batch_num):
    print(f"  >> Starting batch {batch_num}")
    with ThreadPoolExecutor(max_workers=REQUESTS_PER_BATCH) as ex:
        futures = [ex.submit(send_task) for _ in range(REQUESTS_PER_BATCH)]
        for _ in as_completed(futures): pass
    print(f"  >> Finished batch {batch_num}")

# 🔁 Main loop
while True:
    bal = get_balance()
    if bal >= BALANCE_LIMIT:
        print(f"Balance limit reached ({bal} >= {BALANCE_LIMIT}), stopping.")
        break

    print(f"\n=== New round: {BATCHES_PER_ROUND} batches of {REQUESTS_PER_BATCH} requests ===")
    start = time.time()

    with ThreadPoolExecutor(max_workers=BATCHES_PER_ROUND) as ex:
        futures = [ex.submit(run_batch, i+1) for i in range(BATCHES_PER_ROUND)]
        for _ in as_completed(futures): pass

    print(f"=== Round completed in {time.time() - start:.2f} seconds ===")
    print(f"Waiting {ROUND_DELAY} seconds before next round...\n")
    time.sleep(ROUND_DELAY)
