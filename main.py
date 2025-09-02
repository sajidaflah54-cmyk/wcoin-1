import asyncio
import aiohttp
import time
import random
import json

API_URL = "https://starfish-app-fknmx.ondigitalocean.app/wapi/api/external-api/verify-task"
TASK_ID = 528
TIMEOUT = 10   # higher tolerance for slow net

REQUESTS_PER_BATCH = 100000
SUB_CHUNK_SIZE = 200            # will adjust dynamically
CHUNK_PAUSE = 4
PAUSE_AFTER_BATCH = 20
MAX_RETRIES = 6
CONCURRENCY_LIMIT = 100         # base concurrency

# Input x-init-data
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
                    if r.status == 200:
                        return True
                    elif r.status in (429, 500, 502, 503, 520):
                        wait_time = min(2 ** attempt + random.uniform(0, 2), 20)
                        await asyncio.sleep(wait_time)
                    else:
                        return False
            except Exception:
                await asyncio.sleep(random.uniform(0.5, 2.0))
    return False

async def run_batch(session, batch_num):
    global SUB_CHUNK_SIZE, CHUNK_PAUSE

    print(f"\n🚀 Starting batch {batch_num} ({REQUESTS_PER_BATCH} requests)...")
    per_account = max(1, REQUESTS_PER_BATCH // len(X_INIT_DATA_LIST))
    total_sent = 0
    total_success = 0
    total_fail = 0

    while total_sent < REQUESTS_PER_BATCH:
        tasks = []
        for x_init in X_INIT_DATA_LIST:
            for _ in range(min(SUB_CHUNK_SIZE // len(X_INIT_DATA_LIST), per_account)):
                tasks.append(asyncio.create_task(send_task(session, TASK_ID, x_init)))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        success = sum(1 for r in results if r is True)
        fail = len(results) - success
        total_success += success
        total_fail += fail
        total_sent += len(results)

        print(f"⚡ Sent {total_sent}/{REQUESTS_PER_BATCH} | ✅ {total_success} | ❌ {total_fail}")

        # 🔄 Adaptive logic
        error_rate = (fail / len(results)) if results else 0
        if error_rate > 0.4:  # too many fails
            SUB_CHUNK_SIZE = max(100, SUB_CHUNK_SIZE - 50)
            CHUNK_PAUSE = min(10, CHUNK_PAUSE + 1)
            print(f"🐌 High errors → slowing down | Chunk={SUB_CHUNK_SIZE}, Pause={CHUNK_PAUSE}s")
        elif error_rate < 0.1 and SUB_CHUNK_SIZE < 500:
            SUB_CHUNK_SIZE += 50
            CHUNK_PAUSE = max(2, CHUNK_PAUSE - 1)
            print(f"⚡ Stable → speeding up | Chunk={SUB_CHUNK_SIZE}, Pause={CHUNK_PAUSE}s")

        await asyncio.sleep(CHUNK_PAUSE + random.uniform(1, 2))

    print(f"✅ Batch {batch_num} finished. Success: {total_success}/{REQUESTS_PER_BATCH}")
    print(f"⏸️ Pausing for {PAUSE_AFTER_BATCH}s...\n")
    await asyncio.sleep(PAUSE_AFTER_BATCH)

async def main():
    connector = aiohttp.TCPConnector(limit=0, ttl_dns_cache=300, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        batch_num = 1
        while True:
            await run_batch(session, batch_num)
            batch_num += 1

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n📝 Stopped by user.")