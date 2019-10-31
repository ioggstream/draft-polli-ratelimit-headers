#
# QUART_APP=api:app quart run
#

from base64 import decodebytes
import random
from quart import Quart, request
from asyncio import sleep

app = Quart(__name__)

def _get_user(request):
    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("basic "):
        return decodebytes(authorization[6:].encode("ascii")).split(b":", 1)[0].decode("ascii")
    return ""


@app.route("/echo/<int:eid>")
async def index(eid=None):
    user = _get_user(request)
    return (
        f"Hello World {eid} {request.headers} {user}",
        200,
        {
            "ratelimit-remaining": str(random.randint(0, 5)),
            "user": user,
        },
    )


@app.cli.command("run")
def run():
    app.run(host="0.0.0.0", port=443, certfile="rsa.pem", keyfile="rsa.key")
