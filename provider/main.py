"""fake external api for charges and email.

the shopping api posts charges to http://provider:9000/payments/charge
and notices to http://provider:9000/notify.
change the mode without restarting:

    curl -X PUT http://localhost:9000/mode/ok
    curl -X PUT http://localhost:9000/mode/fail
    curl -X PUT http://localhost:9000/mode/slow
"""

import asyncio
import secrets
from typing import Literal

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="fake external apis(notification+payment)",
    description="",
    version="1.0.0",
    openapi_tags=[
        {"name": "Notifications", "description": "Email notices. A failed notice does not change the order."},
        {"name": "Charges", "description": "Payment charges. The same Idempotency-Key is not charged twice."},
    ],
)

Mode = Literal["ok", "fail", "slow"]
mode: Mode = "ok"
# notices that got a 200.tests can read this after the shopping api calls us.
sent: list[dict] = []
# paid charges, keyed by Idempotency-Key.a repeat of that key returns the same reference.
charges: dict[str, dict] = {}
# tests set this to 0.the running provider waits the full 10 seconds.
SLOW_SECONDS = 10


class Notice(BaseModel):
    order_id: int
    email: str
    payment_status: str


class Charge(BaseModel):
    order_id: int
    amount: str
    payment_method: str
    order_number: str = ""


async def _apply_mode() -> None:
    if mode == "fail":
        raise HTTPException(status_code=503, detail="External API is down")
    if mode == "slow":
        await asyncio.sleep(SLOW_SECONDS)


@app.get("/mode", summary="Get mode")
def read_mode():
    return {"mode": mode}


@app.put("/mode/{next_mode}", summary="Set mode")
def set_mode(next_mode: Mode):
    global mode
    mode = next_mode
    return {"mode": mode}


@app.get("/sent", include_in_schema=False)
def list_sent():
    return sent


@app.delete("/sent", include_in_schema=False)
def clear_sent():
    sent.clear()
    return {"cleared": True}


@app.post("/notify", tags=["Notifications"], summary="Send notice")
async def notify(body: Notice):
    await _apply_mode()
    sent.append({"order_id": body.order_id, "email": body.email, "payment_status": body.payment_status})
    print(
        f"SENT order {body.order_id} to {body.email} status {body.payment_status} mode {mode}",
        flush=True,
    )
    return {"status": "sent", "mode": mode}


@app.post("/payments/charge", tags=["Charges"], summary="Charge")
async def charge(body: Charge, idempotency_key: str = Header(default="")):
    key = idempotency_key
    if key and key in charges:
        saved = charges[key]
        return {"status": "PAID", "reference": saved["reference"], "order_id": body.order_id}
    await _apply_mode()
    reference = f"PAY-{secrets.token_hex(4).upper()}"
    record = {"order_id": body.order_id, "reference": reference, "amount": body.amount}
    if key:
        charges[key] = record
    return {"status": "PAID", "reference": reference, "order_id": body.order_id}


@app.delete("/payments/charges", include_in_schema=False)
def clear_charges():
    charges.clear()
    return {"cleared": True}
