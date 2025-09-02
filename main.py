import asyncio
import aiohttp
import time
import random

# --- Config ---
API_URL = "https://starfish-app-fknmx.ondigitalocean.app/wapi/api/external-api/verify-task"
TASK_ID = 528
TIMEOUT = 15
REQUESTS_PER_BATCH = 100000   # Huge batch size
MAX_BATCHES = 7               # Run up to 7 batches
CONCURRENCY_LIMIT = 500       # How many requests at once
MAX_RETRIES = 7               # Retry attempts
BATCH_DELAY = 10              # Delay (sec) between batches

# --- Ask for x-init-data ---
X_INIT_DATA = input("Paste your x-init-data: ").strip()


async def send_request(session, payload, attempt=1):
    """
    Sends a single request with retries & exponential backoff.
    """
    headers = {
        "Content-Type": "application/json",
        "x-init-data": X_INIT_DATA
    }

    try:
        async with session.post(API_URL, json=payload, headers=headers, timeout=TIMEOUT) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                return {"error": f"HTTP {resp.status}"}
    except Exception as e:
        if attempt < MAX_RETRIES:
            wait_time = 2 ** attempt + random.uniform(0, 1)
            await asyncio.sleep(wait_time)
            return await send_request(session, payload, attempt + 1)
        return {"error": str(e)}


async def run_batch(batch_num):
    """
    Runs a single batch of requests.
    """
    start_time = time.time()
    connector = aiohttp.TCPConnector(limit=CONCURRENCY_LIMIT)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            send_request(session, {"task_id": TASK_ID})
            for _ in range(REQUESTS_PER_BATCH)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    success = sum(1 for r in results if isinstance(r, dict) and "error" not in r)
    failed = REQUESTS_PER_BATCH - success
    elapsed = time.time() - start_time

    print(f"\n--- Batch {batch_num} Finished ---")
    print(f"Success: {success}, Failed: {failed}")
    print(f"Time taken: {elapsed:.2f} sec")
    return success, failed


async def main():
    total_success, total_failed = 0, 0
    for batch_num in range(1, MAX_BATCHES + 1):
        success, failed = await run_batch(batch_num)
        total_success += success
        total_failed += failed
        if batch_num < MAX_BATCHES:
            print(f"Waiting {BATCH_DELAY} sec before next batch...")
            await asyncio.sleep(BATCH_DELAY)

    print("\n=== All Batches Completed ===")
    print(f"Total Success: {total_success}, Total Failed: {total_failed}")


if __name__ == "__main__":
    asyncio.run(main())