import time as t, requests as r
from concurrent.futures import ThreadPoolExecutor as e, as_completed as c

a="https://starfish-app-fknmx.ondigitalocean.app/wapi/api/external-api/verify-task"
b=1000
c1=300
d=10
e1=7
f=100000000

g=input("📥 Please enter your x-init-data:\n> ").strip()

def h():
    return 1000

def i():
    x=int(t.time())
    y={"taskId":b,"taskContents":{"viewedTimes":1,"lastViewed":x}}
    z={
        "Content-Type":"application/json",
        "accept":"*/*",
        "origin":"https://app.w-coin.io",
        "referer":"https://app.w-coin.io/",
        "user-agent":"Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
        "x-init-data":g,
        "x-request-timestamp":str(x)
    }
    try:
        res=r.post(a,headers=z,json=y,timeout=5)
        print(f"[{x}] Status: {res.status_code} | {res.text}")
    except Exception as ex:
        print(f"Request error: {ex}")

def j(k):
    print(f"  >> Starting batch {k}")
    with e(max_workers=c1) as ex:
        futures=[ex.submit(i) for _ in range(c1)]
        for _ in c(futures): pass
    print(f"  >> Finished batch {k}")

while True:
    l=h()
    if l>=f:
        print(f"Balance limit reached ({l} >= {f}), stopping.")
        break
    print(f"\n=== New round: {d} batches of {c1} requests ===")
    m=t.time()
    with e(max_workers=d) as ex:
        futures=[ex.submit(j,i+1) for i in range(d)]
        for _ in c(futures): pass
    print(f"=== Round completed in {t.time()-m:.2f} seconds ===")
    print(f"Waiting {e1} seconds before next round...\n")
    t.sleep(e1)
