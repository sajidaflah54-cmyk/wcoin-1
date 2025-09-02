import asyncio
import aiohttp
import time
import random
import json

API_URL = "https://starfish-app-fknmx.ondigitalocean.app/wapi/api/external-api/verify-task"
TASK_ID = 528
TIMEOUT = 8
REQUESTS_PER_BATCH = 300        # Safer than 400
PAUSE_AFTER_BATCH = 8           # Slightly longer pause
MAX_RETRIES = 7
CONCURRENCY_LIMIT = 100         # Start lower to avoid instant blocking

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
    """
    Sends a verification task with retries, backoff, and error handling.
    """
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
                        try:
                            js = json.loads(text)
                            print(f"[{task_id}] ✅ {x_init[:10]}.. | {js}")
                        except json.JSONDecodeError:
                            print(f"[{task_id}] ⚠️ Non-JSON (possible Cloudflare) | Retrying...")
                            await asyncio.sleep(random.uniform(1, 3))
                            continue
                        return True

                    elif r.status in (429, 500, 502, 503, 520):
                        wait_time = min(2 ** attempt + random.uniform(0, 2), 15)
                        print(f"[{task_id}] ⚠️ Retry {attempt+1} ({r.status}) | Wait {wait_time:.1f}s")
                        await asyncio.sleep(wait_time)
                    
                    else:
                        print(f"[{task_id}] ❌ {x_init[:10]}.. | {r.status} | {text[:80]}")
                        return False

            except asyncio.TimeoutError:
                print(f"[{task_id}] ⏱️ Timeout ({x_init[:10]}) - retrying...")
            except aiohttp.ClientOSError as e:
                print(f"[{task_id}] 🌐 Conn reset ({x_init[:10]}) - {e}")
            except aiohttp.ClientError as e:
                print(f"[{task_id}] 🌐 Client error ({x_init[:10]}) - {e}")

            # jitter before retry
            await asyncio.sleep(random.uniform(0.2, 1.0))

    print(f"[{task_id}] ❌ Max retries exceeded ({x_init[:10]})")
    return False

async def run_batch(session, batch_num):
    """
    Runs one batch of requests across all accounts.
    """
    print(f"\n🚀 Starting batch {batch_num} ({REQUESTS_PER_BATCH} requests)...")
    per_account = max(1, REQUESTS_PER_BATCH // len(X_INIT_DATA_LIST))
    tasks = []

    for x_init in X_INIT_DATA_LIST:
        for _ in range(per_account):
            tasks.append(asyncio.create_task(send_task(session, TASK_ID, x_init)))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    success = sum(1 for r in results if r is True)
    print(f"✅ Batch {batch_num} finished. Success: {success}/{len(results)}")
    print(f"⏸️ Pausing for {PAUSE_AFTER_BATCH}s...\n")
    await asyncio.sleep(PAUSE_AFTER_BATCH)

async def main():
    print(f"🚀 Starting continuous verification for Task ID {TASK_ID}...\n")
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