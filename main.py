# Config
START_WORKERS = 100       # start big
MAX_WORKERS = 500         # allow higher scaling
MIN_WORKERS = 50          # don't go below this
BATCHES_PER_ROUND = 3
WAIT_BETWEEN_ROUNDS = 2
BALANCE_LIMIT = 10000000

...

# Main loop
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

    # Auto-tuning
    if success_rate > 90 and round_time < 6 and current_workers < MAX_WORKERS:
        current_workers += 50   # scale up faster
        print(f"✅ Increasing workers to {current_workers}")
    elif success_rate < 60 or round_time > 15:
        current_workers = max(MIN_WORKERS, current_workers - 50)  # drop sharply
        print(f"⚠️ Decreasing workers to {current_workers}")

    print(f"Waiting {WAIT_BETWEEN_ROUNDS} seconds before next round...\n")
    t.sleep(WAIT_BETWEEN_ROUNDS)