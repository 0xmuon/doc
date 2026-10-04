"""scripted httpx transport.so gateway tests do not open a socket."""

import json

import httpx


def scripted_transport(handler):
    """handler(request) returns an httpx.Response."""

    def _send(request: httpx.Request) -> httpx.Response:
        return handler(request)

    return httpx.MockTransport(_send)


def json_response(status: int, body: dict) -> httpx.Response:
    return httpx.Response(status, json=body)


def read_json(request: httpx.Request) -> dict:
    return json.loads(request.content.decode() or "{}")
