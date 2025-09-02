# main_termux.py
import time as t
import requests as r
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Configuration ---
START_WORKERS = 100
MAX_WORKERS = 500
MIN_WORKERS = 50
BATCHES_PER_ROUND = 3
WAIT_BETWEEN_ROUNDS = 2
BALANCE_LIMIT = 10000000
NUM_REQUESTS_PER_BATCH = 100  # placeholder

# --- Placeholder Functions ---
def get_balance():
    try:
        with open('balance.txt', 'r') as f:
            balance = int(f.read())
    except (FileNotFoundError, ValueError):
        balance = 0

    # Simulate a balance increase
    balance += 1000
    with open('balance.txt', 'w') as f:
        f.write(str(balance))
    return balance

def fetch_x_init_data():
    """
    Placeholder function for fetching x init data from Telegram mini app.
    Replace this with your actual logic.
    """
    try:
        # Example: send a GET request to fetch data
        # response = r.get("YOUR_X_INIT_URL", timeout=10)
        # data = response.json()
        # return data
        t.sleep(0.1)  # simulate network delay
        return {"x_init": "data"}
    except Exception:
        return None

def run_batch(batch_number, num_requests):
    print(f"  - Running batch {batch_number} with {num_requests} requests...")
    successes, failures = 0, 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(single_request) for _ in range(num_requests)]
        for fut in as_completed(futures):
            if fut.result():
                successes += 1
            else:
                failures += 1

    return successes, failures

def single_request():
    """
    Placeholder for a single request using x_init_data.
    Replace with your actual API or Telegram mini app logic.
    """
    x_data = fetch_x_init_data()
    if x_data:
        t.sleep(0.05)  # simulate processing
        return True
    return False

# --- Main Loop ---
current_workers = START_WORKERS

while True:
    balance = get_balance()
    if balance >= BALANCE_LIMIT:
        print(f"Balance limit reached ({balance} >= {BALANCE_LIMIT}), stopping.")
        break

    print(f"\n=== New round: {BATCHES_PER_ROUND} batches of {current_workers} requests ===")
    start = t.time()

    total_success, total_failed = 0, 0
    with ThreadPoolExecutor(max_workers=BATCHES_PER_ROUND) as executor:
        futures = [executor.submit(run_batch, i + 1, current_workers) for i in range(BATCHES_PER_ROUND)]
        for fut in as_completed(futures):
            s, f = fut.result()
            total_success += s
            total_failed += f

    round_time = t.time() - start
    balance_after = get_balance()
    success_rate = total_success / max(1, (total_success + total_failed)) * 100

    print(f"=== Round done in {round_time:.2f}s | Success rate: {success_rate:.1f}% | "
          f"Balance now: {balance_after} ===")

    # --- Auto-tuning Logic ---
    if success_rate > 90 and round_time < 6 and current_workers < MAX_WORKERS:
        current_workers += 50
        print(f"✅ Increasing workers to {current_workers}")
    elif success_rate < 60 or round_time > 15:
        current_workers = max(MIN_WORKERS, current_workers - 50)
        print(f"⚠️ Decreasing workers to {current_workers}")

    print(f"Waiting {WAIT_BETWEEN_ROUNDS} seconds before next round...\n")
    t.sleep(WAIT_BETWEEN_ROUNDS)