import gzip
import json
from base64 import encodebytes, decodebytes

PAYLOAD = json.dumps({"a": "1" * 100}).encode()


def message_body(payload, headers):
    ret = "\n".join([f"{k}: {v}" for k, v in headers.items()])
    ret += "\n\n"
    ret += encodebytes(payload).decode("ascii")
    return ret


def test_print_request_compress():
    headers = {"Content-Type": "application/json", "Content-Encoding": "gzip"}
    print(message_body(gzip.compress(PAYLOAD), headers))


test_print_request_compress()
