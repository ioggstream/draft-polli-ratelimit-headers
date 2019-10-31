import ssl
from base64 import encodebytes
from datetime import datetime
from itertools import cycle
from time import sleep, time
from sys import argv

import hyper
from hyper import HTTPConnection

hyper.tls._context = hyper.tls.init_context(cert_path="rsa.pem")


class Quota:
    """
    Mocks a quota database with some functions.s
    """
    def __init__(self):
        self.quota = {}

    def reset(self, user):
        self.quota[str(user)] = 5

    def has(self, user):
        return self.quota.get(str(user), 5) > 0

    def set(self, user, remaining):
        self.quota[str(user)] = int(remaining)


def request(conn, user, quota):
    """
    Send a request only if the user has enough quotas.
    :param conn:
    :param i:
    :param quota:
    :return:
    """
    if not quota.has(user):
        print(f"skipping {user} over quota")
        quota.reset(user)
        return None

    return conn.request(
        "GET",
        f"/echo/{user}",
        headers={
            "authorization": "basic %s"
            % encodebytes(f"{user}:{user}".encode()).decode("ascii")
        },
    )


if __name__ == '__main__':
    try:
        server = argv[1]
    except IndexError:
        server = "localhost"

    conn = HTTPConnection(f"{server}:443", secure=True)
    users = cycle(range(3))
    t = time()
    quota = Quota()
    n_requests = 10

    while time() < t + 2:

        print(f"sending {n_requests} requests")
        sent = [request(conn, next(users), quota=quota) for i in range(n_requests)]
        print("sent")

        for i in sent:
            if i is None:
                continue
            data = conn.get_response(i)

            if 'user' in data.headers:
                user = data.headers['user'][0].decode('ascii')
                quota.set(user, data.headers.get("ratelimit-remaining", 5)[0])
