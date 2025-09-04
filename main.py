import asyncio
import aiohttp
import time
import random
import sys
import os
import csv
from datetime import datetime

API_URL = "https://starfish-app-fknmx.ondigitalocean.app/wapi/api/external-api/verify-task"
TASK_ID = 528

# --- CONFIG (2x faster) ---
TIMEOUT = 4             # shorter wait before giving up on a request
BASE_REQUESTS = 1000    # double initial batch size
MAX_REQUESTS = 19999     # double max bursts
CONCURRENCY_LIMIT = 600 # double parallel requests
MAX_RETRIES = 6
PAUSE_AFTER_BATCH = 1   # shorter pause between batches

# --- ACCOUNT INPUT ---
X_INIT_DATA_LIST = []
for i in range(10):
    data = input(f"📥 Enter x-init-data for account {i+1}:\n> ").strip()
    if data:
        X_INIT_DATA_LIST.append(data)

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Meizu 18) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; Redmi Note 9 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Mobile Safari/537.36",
]

# --- GLOBAL STATE ---
semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
success_count = 0
fail_count = 0

# --- COLORS ---
RESET = "\033[0m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"

# --- LOGGING SETUP ---
os.makedirs("logs", exist_ok=True)
txt_log_path = os.path.join("logs", "session_log.txt")
csv_log_path = os.path.join("logs", "session_log.csv")

csv_file = open(csv_log_path, "a", newline="", encoding="utf-8")
csv_writer = csv.writer(csv_file)
if os.stat(csv_log_path).st_size == 0:  # write header if file empty
    csv_writer.writerow(["timestamp", "account", "status_code", "result", "response"])

def log_event(account, status, result, response):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    snippet = response[:80].replace("\n", " ")
    line = f"[{timestamp}] {account[:10]}.. | {status} | {result} | {snippet}\n"
    with open(txt_log_path, "a", encoding="utf-8") as f:
        f.write(line)
    csv_writer.writerow([timestamp, account[:10], status, result, snippet])
    csv_file.flush()

async def send_task(session, task_id, x_init):
    global success_count, fail_count
    for attempt in range(MAX_RETRIES):
        async with semaphore:
            t = int(time.time())
            data = {"taskId": task_id, "taskContents": {"viewedTimes": 1, "lastViewed": t}}
            headers = {
                "Content-Type": "application/json",
                "accept": "*/*",
                "origin": "https://app.w-coin.io",
                "referer": "https://app.w-coin.io/",
                "user-agent": random.choice(USER_AGENTS),
                "x-init-data": x_init,
                "x-request-timestamp": str(t)
            }
            try:
                async with session.post(API_URL, headers=headers, json=data, timeout=TIMEOUT) as r:
                    text = await r.text()
                    if r.status == 200:
                        success_count += 1
                        print(f"{GREEN}[OK]{RESET} {x_init[:10]}.. | {text[:60]}")
                        log_event(x_init, r.status, "SUCCESS", text)
                        return True
                    elif r.status in (429, 500, 502, 503):
                        wait_time = min(2 ** attempt, 10)
                        print(f"{YELLOW}[RETRY]{RESET} {x_init[:10]}.. | {r.status} | Waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                    else:
                        fail_count += 1
                        print(f"{RED}[FAIL]{RESET} {x_init[:10]}.. | {r.status} | {text[:60]}")
                        log_event(x_init, r.status, "FAIL", text)
                        return False
            except asyncio.TimeoutError:
                print(f"{YELLOW}[TIMEOUT]{RESET} {x_init[:10]} - retrying...")
            except aiohttp.ClientError as e:
                print(f"{RED}[NET]{RESET} {x_init[:10]} - {e}")
            await asyncio.sleep(random.uniform(0.05, 0.15))
    fail_count += 1
    log_event(x_init, "N/A", "MAX_RETRIES", "No success after retries")
    return False

async def run_batch(session, batch_num, requests_in_batch):
    print(f"\n🚀 Batch {batch_num} | Sending {requests_in_batch} requests...\n")
    per_account = max(1, requests_in_batch // len(X_INIT_DATA_LIST))
    tasks = []
    for x_init in X_INIT_DATA_LIST:
        for _ in range(per_account):
            tasks.append(asyncio.create_task(send_task(session, TASK_ID, x_init)))
    await asyncio.gather(*tasks)
    print(f"\n⏸️ Batch {batch_num} complete | {GREEN}Success: {success_count}{RESET} | {RED}Fails: {fail_count}{RESET}")
    await asyncio.sleep(PAUSE_AFTER_BATCH)

async def main():
    print(f"{CYAN}🚀 Premium Auto-Verification Bot Started for Task {TASK_ID}{RESET}\n")
    requests_in_batch = BASE_REQUESTS
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=0)) as session:
        batch_num = 1
        while True:
            await run_batch(session, batch_num, requests_in_batch)
            if success_count > fail_count * 2 and requests_in_batch < MAX_REQUESTS:
                requests_in_batch += 100
                print(f"{CYAN}⚡ Increasing load -> {requests_in_batch} requests next batch{RESET}")
            elif fail_count > success_count and requests_in_batch > BASE_REQUESTS:
                requests_in_batch -= 100
                print(f"{YELLOW}⚠️ Reducing load -> {requests_in_batch} requests next batch{RESET}")
            batch_num += 1

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n📝 Stopped by user. {GREEN}Success: {success_count}{RESET} | {RED}Fails: {fail_count}{RESET}")
        csv_file.close()
        sys.exit()