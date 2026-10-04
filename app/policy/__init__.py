"""casbin is the policy.routes ask it,they dont grow their own if role == admin."""

from pathlib import Path

import casbin

_dir = Path(__file__).resolve().parent
_enforcer = casbin.Enforcer(str(_dir / "model.conf"), str(_dir / "policy.csv"))


def allow(role: str, user_id: int | None, resource: str, action: str, owner_id: int | None) -> bool:
    """one question.owner_id is the row's user when the rule is about ownership."""
    uid = "" if user_id is None else str(user_id)
    oid = "" if owner_id is None else str(owner_id)
    return bool(_enforcer.enforce(role, uid, resource, action, oid))
