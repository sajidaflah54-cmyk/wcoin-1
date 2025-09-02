import asyncio
import aiohttp
import time
import random

API_URL = "https://starfish-app-fknmx.ondigitalocean.app/wapi/api/external-api/verify-tas>
TASK_ID = 528
TIMEOUT = 10
REQUESTS_PER_BATCH = 300
PAUSE_AFTER_BATCH = 10  # seconds
MAX_RETRIES = 5

# --- 10 X-INIT-DATA input ---
X_INIT_DATA_LIST = []
for i in range(10):
    data = input(f"📥 Enter x-init-data for account {i+1}:\n> ").strip()
    if data:
        X_INIT_DATA_LIST.append(data)

USER_AGENTS = [
    # same list (not removed)
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chr>
    # ...
    "Mozilla/5.0 (Linux; Android 12; Meizu 18) AppleWebKit/537.36 (KHTML, like Gecko) Chr>
]

async def send_task(session, task_id, x_init):
    for attempt in range(MAX_RETRIES):
        t = int(time.time())
        data = {"taskId": task_id, "taskContents": {"viewedTimes": 1, "lastViewed": t}}
        headers = {
            "Content-Type": "application/json",
            "accept": "*/*",
            "origin": "https://app.w-coin.io",
            "referer": "https://app.w-coin.io/",
            "user-agent": random.choice(USER_AGENTS),
            "x-init-data": x_init,  # fixed to this account
            "x-request-timestamp": str(t)
        }

        try:
            async with session.post(API_URL, headers=headers, json=data, timeout=TIMEOUT)>
                text = await r.text()
                if r.status == 200:
                    print(f"[{task_id}] ✅ {x_init[:10]}.. | {text[:80]}")
                    return True
                else:
                    print(f"[{task_id}] ❌ {x_init[:10]}.. | {r.status} | {text[:80]}")
        except asyncio.TimeoutError:
            print(f"[{task_id}] Timeout ({x_init[:10]}) - retrying...")
        except aiohttp.ClientError as e:
            print(f"[{task_id}] Conn error ({x_init[:10]}) - {e}")
        await asyncio.sleep(random.uniform(0.1, 0.5))
    return False

async def run_batch(session, batch_num):
    print(f"\n🚀 Starting batch {batch_num} ({REQUESTS_PER_BATCH} requests)...")
    per_account = max(1, REQUESTS_PER_BATCH // len(X_INIT_DATA_LIST))  # divide requests >
    tasks = []
    for x_init in X_INIT_DATA_LIST:
        for _ in range(per_account):
            tasks.append(asyncio.create_task(send_task(session, TASK_ID, x_init)))
    await asyncio.gather(*tasks)
    print(f"⏸️ Batch {batch_num} complete, pausing for {PAUSE_AFTER_BATCH}s...\n")
    await asyncio.sleep(PAUSE_AFTER_BATCH)

async def main():
    print(f"🚀 Starting continuous verification for Task ID {TASK_ID}...\n")
    async with aiohttp.ClientSession() as session:
        batch_num = 1
        while True:
            await run_batch(session, batch_num)
            batch_num += 1

if name == "main":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n📝 Stopped by user.")