import asyncio
import aiohttp
import time
import random
import json

API_URL = "https://starfish-app-fknmx.ondigitalocean.app/wapi/api/external-api/verify-task"

TASK_ID = 528
TIMEOUT = 8
REQUESTS_PER_BATCH = 400   # requests per batch
PAUSE_AFTER_BATCH = 6      # pause between batches
MAX_RETRIES = 50           # each request retries up to 50 times
CONCURRENCY_LIMIT = 200    # prevent overload

# Collect multiple x-init-data values (accounts)
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
    retries = 0
    while retries < MAX_RETRIES:
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
                    elif r.status in (429, 500, 502, 503):  # Server busy or rate limit
                        wait_time = min(2 ** retries, 10)
                        print(f"[{task_id}] ⚠️ Retry {retries+1} ({r.status}) | Waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"[{task_id}] ❌ {x_init[:10]}.. | {r.status} | {text[:80]}")
                        return False
            except asyncio.TimeoutError:
                print(f"[{task_id}] ⏱️ Timeout ({x_init[:10]}) - retrying...")
            except aiohttp.ClientError as e:
                print(f"[{task_id}] 🌐 Conn error ({x_init[:10]}) - {e}")

            retries += 1
            await asyncio.sleep(random.uniform(0.1, 0.3))  # jitter between retries

    print(f"[{task_id}] ❌ Dropped after {MAX_RETRIES} retries ({x_init[:10]})")
    return False


async def run_batch(session, batch_num):
    print(f"\n🚀 Starting batch {batch_num} ({REQUESTS_PER_BATCH} requests)...")
    per_account = max(1, REQUESTS_PER_BATCH // len(X_INIT_DATA_LIST))
    tasks = []
    for x_init in X_INIT_DATA_LIST:
        for _ in range(per_account):
            tasks.append(asyncio.create_task(send_task(session, TASK_ID, x_init)))

    results = await asyncio.gather(*tasks)
    successes = sum(1 for r in results if r)

    # Save successes to file
    with open("results.json", "a") as f:
        json.dump({"batch": batch_num, "successes": successes}, f)
        f.write("\n")

    print(f"✅ Batch {batch_num} complete: {successes}/{len(tasks)} succeeded")
    print(f"⏸️ Pausing for {PAUSE_AFTER_BATCH}s...\n")
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