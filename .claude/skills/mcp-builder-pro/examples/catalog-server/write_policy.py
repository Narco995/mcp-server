"""Owned in-memory fake, not an MCP tool and not a production approval service."""

from dataclasses import dataclass
from threading import Lock
from typing import Literal

Outcome = Literal["committed", "unknown"]


@dataclass(frozen=True)
class Approval:
    actor: str
    tenant: str
    payload: str
    expires_at: int


class FixtureWrites:
    def __init__(self):
        self._lock = Lock()
        self._reservations: dict[tuple[str, str, str], tuple[str, Outcome]] = {}
        self._upstream: dict[tuple[str, str, str], str] = {}

    @property
    def committed_count(self):
        return len(self._upstream)

    def commit(
        self,
        *,
        actor,
        tenant,
        key,
        payload,
        approval,
        now,
        authorized=True,
        timeout=False,
    ):
        if (
            not authorized
            or not isinstance(approval, Approval)
            or (actor, tenant, payload)
            != (approval.actor, approval.tenant, approval.payload)
            or key == ""
            or now >= approval.expires_at
        ):
            raise PermissionError("approval does not authorize this operation")
        scoped = actor, tenant, key
        with self._lock:
            if scoped in self._reservations:
                previous, outcome = self._reservations[scoped]
                if previous != payload:
                    raise ValueError("idempotency key reused with a different payload")
                return outcome
            self._upstream[scoped] = payload
            outcome: Outcome = "unknown" if timeout else "committed"
            self._reservations[scoped] = (payload, outcome)
            return outcome

    def reconcile(self, *, actor, tenant, key, authorized=True):
        if not authorized:
            raise PermissionError("lookup not authorized")
        scoped = actor, tenant, key
        with self._lock:
            if scoped not in self._reservations:
                return "not_committed"
            payload, outcome = self._reservations[scoped]
            if outcome == "unknown" and self._upstream.get(scoped) == payload:
                self._reservations[scoped] = (payload, "committed")
                return "committed"
            return outcome
