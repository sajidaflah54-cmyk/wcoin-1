import asyncio
import aiohttp
import time
import random

API_URL = "https://starfish-app-fknmx.ondigitalocean.app/wapi/api/external-api/verify-task"

TASK_ID = 528
TIMEOUT = 8
REQUESTS_PER_BATCH = 400   # Increased for faster balance gain
PAUSE_AFTER_BATCH = 6      # Shorter pause between batches
MAX_RETRIES = 7
CONCURRENCY_LIMIT = 200    # Prevent overload

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

semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

async def send_task(session, task_id, x_init):
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
                        print(f"[{task_id}] ✅ {x_init[:10]}.. | {text[:80]}")
                        return True
                    elif r.status in (429, 500, 502, 503):  # Rate limit or server error
                        wait_time = min(2 ** attempt, 10)
                        print(f"[{task_id}] ⚠️ Retry {attempt+1} ({r.status}) | Waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"[{task_id}] ❌ {x_init[:10]}.. | {r.status} | {text[:80]}")
                        return False
            except asyncio.TimeoutError:
                print(f"[{task_id}] ⏱️ Timeout ({x_init[:10]}) - retrying...")
            except aiohttp.ClientError as e:
                print(f"[{task_id}] 🌐 Conn error ({x_init[:10]}) - {e}")

            await asyncio.sleep(random.uniform(0.05, 0.2))  # Small jitter
    return False

async def run_batch(session, batch_num):
    print(f"\n🚀 Starting batch {batch_num} ({REQUESTS_PER_BATCH} requests)...")
    per_account = max(1, REQUESTS_PER_BATCH // len(X_INIT_DATA_LIST))
    tasks = []
    for x_init in X_INIT_DATA_LIST:
        for _ in range(per_account):
            tasks.append(asyncio.create_task(send_task(session, TASK_ID, x_init)))
    await asyncio.gather(*tasks)
    print(f"⏸️ Batch {batch_num} complete, pausing for {PAUSE_AFTER_BATCH}s...\n")
    await asyncio.sleep(PAUSE_AFTER_BATCH)

async def main():
    print(f"🚀 Starting continuous verification for Task ID {TASK_ID}...\n")
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=0)) as session:
        batch_num = 1
        while True:
            await run_batch(session, batch_num)
            batch_num += 1

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n📝 Stopped by user.")