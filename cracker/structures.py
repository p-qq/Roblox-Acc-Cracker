import threading
import time
import random
from itertools import cycle
from http.client import HTTPSConnection

class Counter:
    def __init__(self):
        self.checkpoints = []

    def add(self):
        self.checkpoints.append(time.time())
    
    def filter(self):
        t = time.time()
        self.checkpoints = [
            t
            for t in self.checkpoints
            if time.time()-t <= 60
        ]

    def get_cpm(self):
        self.filter()
        return len(self.checkpoints)

class Proxy:
    def __init__(self, proxy):
        hostname, port = proxy.split(":", 1)
        self.hostname = hostname
        self.port = int(port)
        self.hostname_to_connection = {}

    def get_connection(self, hostname, **kwargs) -> HTTPSConnection:
        hostname = hostname.lower()

        if hostname in self.hostname_to_connection:
            return self.hostname_to_connection[hostname]
        else:
            conn = HTTPSConnection(self.hostname, self.port, **kwargs)
            conn.set_tunnel(hostname, 443)
            self.hostname_to_connection[hostname] = conn
            return conn

class ProxyHandler:
    def __init__(self, pool, proxy):
        self.pool = pool
        self.proxy = proxy
    
    def __enter__(self):
        return self.proxy

    def __exit__(self, x, *_):
        if not x:
            self.pool.alive.append(self.proxy)

class ProxyPool:
    def __init__(self, proxies):
        random.shuffle(proxies)
        self.proxy_iter = cycle(proxies)
        self.alive = []
        self.lock = threading.Lock()

    def __next__(self) -> Proxy:
        with self.lock:
            if self.alive:
                proxy = self.alive.pop()
            else:
                proxy = Proxy(next(self.proxy_iter))
            return ProxyHandler(self, proxy)

# designed to keep constant distance between credentials, in order to prevent rate-limiting them
class ComboQueue:
    def __init__(self):
        self.keys = []
        self.key_to_passwords = {}
        self.lock = threading.Lock()

    def __next__(self):
        while True:
            with self.lock:
                key = self.keys.pop()
                passwords = self.key_to_passwords[key]
                
                if passwords:
                    password = passwords.pop(0)

                    if passwords:
                        self.keys.insert(0, key)

                    return key, password

    def size(self):
        return sum(len(p) for p in self.key_to_passwords.values())

    def add(self, credential, password):
        credential = credential.lower()
        
        with self.lock:
            if not credential in self.key_to_passwords:
                self.key_to_passwords[credential] = []
            
            if not password in self.key_to_passwords[credential]:
                self.key_to_passwords[credential].append(password)

    def process(self):
        self.keys = list(self.key_to_passwords.keys())[::-1]