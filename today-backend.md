# Backend changes

## 12 October 2026

No backend files were changed on 12 October.

The shop work after midnight was frontend only: search, footer, ESLint, and the week-4 check. `app/`, `provider/`, `tests/`, `docker-compose.yml`, and `pyproject.toml` have no uncommitted edits. The three commits from today (`87c7c4b`, `2a1b205`, `dadb1dd`) only touch `frontend/`.

The API still behaves as it did after the backend commit below.

## Last backend edits, 11 October 2026, 19:22

Commit `58ce7f8` (`frt`). These are the backend changes from this project work.

### Seed data — `app/db/seed.py`

- Product prices changed from US dollar amounts to whole INR amounts that end in 99: headphones 6599, stand 1499, shirt 1199, shoes 5399, Python book 2499, novel 999, mug 799, pan 2899, lamp 2099, power bank 2699.
- Each product now has an Unsplash photo URL.
- Running the seed again updates the price of a product that already exists. If that product has no photo, the seed fills the photo in. It does not create a second copy.

### Circuit breaker — `app/integrations/circuit_breaker.py`, `app/integrations/payment_gateway.py`, `.env.example`

- A declined card still does not count as a gateway failure.
- Three failed charges move the breaker to half-open. The default `CIRCUIT_MAX_FAILURES` is now 3, previously 5.
- One more failed charge while half-open turns the breaker fully off.
- While it is off, charges are skipped until the fake payment API reports mode `ok`. A timer no longer reopens it by itself.
- State changes are written to the API log.

### Payment message — `app/services/order_service.py`

- A failed charge now returns: “Payment was not completed. The order is on hold until payment succeeds.”
- A successful charge still returns: “Order placed successfully.”

### Pay again notifies — `app/routers/ops_router.py`

- `POST /api/payments/process` now sends the order notification in the background after a retry, the same way checkout does.

### Logs — `app/utils/logging_setup.py`, `app/integrations/notification.py`

- Log lines are printed to stdout so `docker compose logs api` shows them.
- Notification logs now include the email and the payment status as well as the order id.

### Tests — `tests/test_integrations.py`

- The breaker test expects half-open after three failures, then off after the next failure, and no further charge while it is off.
- A second test checks that one successful charge is allowed once the fake payment API is back, and that success closes the breaker.
