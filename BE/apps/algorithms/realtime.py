"""Realtime evaluation (thesis outline §4.5: response time / latency, data consistency, handling a stream of events).

Everything goes through the real ASGI application (JWT auth middleware, consumers, services, database, the configured
channel layer – Redis in production), with WebSocket clients in the same process, so the numbers are the server's
share of the delay; the network round trip of a real phone or browser comes on top of it (`ping` shows the floor).

  ping        /ws/events/ ping → pong round trip                                         (transport floor)
  group       N members connected to /ws/groups/<id>/, every member sends a few messages;
              latency = arrival at each member − send, consistency = every member got every message once,
              in the same order; a resend with the same client_id must not create a second message
  dm          a private message (service → database → push_event) until it reaches /ws/events/ of both people
  flood       one connection sends a burst: the token bucket must accept BURST and refuse the rest
"""

import asyncio
import statistics
import time
import uuid

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from django.conf import settings

GROUP_MEMBERS = 6
PER_MEMBER = 8  # = the consumers' BURST, so pacing never trips the flood guard
DMS = 30
PINGS = 50
WAIT_S = 10.0


def stats(ms: list[float]) -> dict:
    if not ms:
        return {"n": 0}
    s = sorted(ms)
    pick = lambda q: round(s[min(len(s) - 1, int(q * len(s)))], 2)  # noqa: E731
    return {
        "n": len(s),
        "mean_ms": round(statistics.mean(s), 2),
        "p50_ms": pick(0.5),
        "p95_ms": pick(0.95),
        "p99_ms": pick(0.99),
        "max_ms": round(s[-1], 2),
    }


def _people(tag: str):
    from apps.accounts.models import User
    from apps.community.models import Group, GroupMember, UserFollow

    users = [
        User.objects.create_user(
            f"rt-{tag}-{i}@bench.invalid",
            uuid.uuid4().hex + "A!a1",
            display_name=f"RT {i}",
            learner_type="adult",
            email_verified=True,
        )
        for i in range(GROUP_MEMBERS)
    ]
    group = Group.objects.create(name=f"realtime-bench-{tag}", created_by=users[0])
    for u in users:
        GroupMember.objects.create(group=group, user=u, status="active")
    UserFollow.objects.create(follower=users[0], following=users[1])
    UserFollow.objects.create(follower=users[1], following=users[0])
    return users, group


def _cleanup(users, group):
    group.delete()
    for u in users:
        u.delete()


_TOKENS: dict[int, str] = {}  # made before the event loop starts (creating one writes to the database)


def _token(user) -> str:
    return _TOKENS[user.id]


async def _open(path: str):
    from channels.testing import WebsocketCommunicator

    from config.asgi import application

    comm = WebsocketCommunicator(application, path)
    ok, code = await comm.connect(timeout=5)
    if not ok:
        raise RuntimeError(f"không kết nối được {path.split('?')[0]} (mã {code})")
    return comm


async def _collect(comm, want: str, until: int, sink: list, deadline: float):
    """Read events of type `want` into sink as (payload, arrival) until `until` of them or the deadline."""
    got = 0
    while got < until and time.perf_counter() < deadline:
        try:
            msg = await comm.receive_json_from(timeout=max(0.05, deadline - time.perf_counter()))
        except TimeoutError:
            break
        if msg.get("event") == want:
            sink.append((msg["payload"], time.perf_counter()))
            got += 1


async def _ping(users) -> dict:
    comm = await _open(f"/ws/events/?token={_token(users[0])}")
    await comm.receive_json_from(timeout=5)  # "connected"
    rtt = []
    for _ in range(PINGS):
        t = time.perf_counter()
        await comm.send_json_to({"event": "ping"})
        while (await comm.receive_json_from(timeout=5)).get("event") != "pong":
            pass
        rtt.append((time.perf_counter() - t) * 1000)
    await _close(comm)
    return stats(rtt)


async def _group(users, group) -> dict:
    from apps.chat.models import GroupMessage

    comms = [await _open(f"/ws/groups/{group.id}/?token={_token(u)}") for u in users]
    total = len(users) * PER_MEMBER
    inbox: list[list] = [[] for _ in users]
    deadline = time.perf_counter() + WAIT_S + total * 0.05
    readers = [asyncio.create_task(_collect(c, "message", total, inbox[i], deadline)) for i, c in enumerate(comms)]
    sent: dict[str, tuple[int, float]] = {}
    for k in range(PER_MEMBER):  # round robin: every member sends one message, a little apart
        for i, c in enumerate(comms):
            cid = f"rt-{group.id}-{i}-{k}"
            sent[cid] = (i, time.perf_counter())
            await c.send_json_to({"action": "send", "content": f"tin {k} của RT {i}", "client_id": cid})
            await asyncio.sleep(0.02)
    await asyncio.gather(*readers)

    own, others, orders = [], [], []
    duplicates = missing = 0
    for i, box in enumerate(inbox):
        cids = [p["client_id"] for p, _ in box]
        duplicates += len(cids) - len(set(cids))
        missing += len(set(sent) - set(cids))
        orders.append([p["id"] for p, _ in box])
        for p, at in box:
            sender, t0 = sent.get(p["client_id"], (None, None))
            if t0 is not None:
                (own if sender == i else others).append((at - t0) * 1000)
    same_order = all(o == orders[0] for o in orders)
    increasing = all(o == sorted(o) for o in orders)

    # a resend of a message already stored (lost ack, retry from the app) must not create a second one
    rows_before = await database_sync_to_async(GroupMessage.objects.filter(group=group).count)()
    first = next(iter(sent))
    await comms[0].send_json_to({"action": "send", "content": "gửi lại", "client_id": first})
    await asyncio.sleep(0.5)
    rows_after = await database_sync_to_async(GroupMessage.objects.filter(group=group).count)()
    for c in comms:
        await _close(c)
    return {
        "members": len(users),
        "messages": total,
        "deliveries_expected": total * len(users),
        "deliveries": sum(len(b) for b in inbox),
        "missing": missing,
        "duplicates": duplicates,
        "same_order_everywhere": same_order,
        "ids_increasing": increasing,
        "stored": rows_before,
        "resend_creates_new": rows_after != rows_before,
        "to_other_members": stats(others),
        "echo_to_sender": stats(own),
    }


async def _dm(users) -> dict:
    from apps.chat import services

    a, b = users[0], users[1]
    thread = await database_sync_to_async(services.thread_with)(a, b)
    ca = await _open(f"/ws/events/?token={_token(a)}")
    cb = await _open(f"/ws/events/?token={_token(b)}")
    for c in (ca, cb):
        await c.receive_json_from(timeout=5)  # "connected"
    got_a, got_b = [], []
    deadline = time.perf_counter() + WAIT_S + DMS * 0.1
    readers = [
        asyncio.create_task(_collect(ca, "dm", DMS, got_a, deadline)),
        asyncio.create_task(_collect(cb, "dm", DMS, got_b, deadline)),
    ]
    sent, write_ms = {}, []
    send = database_sync_to_async(services.send_direct_message)
    for k in range(DMS):
        cid = f"rt-dm-{thread.id}-{k}"
        t0 = time.perf_counter()
        await send(a, thread, f"tin riêng {k}", cid)
        write_ms.append((time.perf_counter() - t0) * 1000)
        sent[cid] = t0
        await asyncio.sleep(0.03)
    await asyncio.gather(*readers)
    for c in (ca, cb):
        await _close(c)

    def side(box):
        cids = [p["client_id"] for p, _ in box]
        return {
            "received": len(box),
            "missing": len(set(sent) - set(cids)),
            "duplicates": len(cids) - len(set(cids)),
            "in_order": cids == [c for c in sent if c in cids],
            "latency": stats([(at - sent[p["client_id"]]) * 1000 for p, at in box if p["client_id"] in sent]),
        }

    return {
        "messages": DMS,
        "send_and_store": stats(write_ms),
        "to_recipient": side(got_b),
        "to_sender_devices": side(got_a),
    }


async def _flood(users, group) -> dict:
    from apps.chat.consumers import BURST

    comm = await _open(f"/ws/groups/{group.id}/?token={_token(users[2])}")
    n = BURST * 3
    for k in range(n):
        await comm.send_json_to({"action": "send", "content": f"dồn {k}", "client_id": f"rt-flood-{group.id}-{k}"})
    events = []
    await _collect_any(comm, events, n, time.perf_counter() + 5)  # one answer per frame: the message or a refusal
    await _close(comm)
    mine = [e for e in events if e.get("event") == "message" and e["payload"]["client_id"].startswith("rt-flood")]
    refused = [e for e in events if e.get("event") == "error"]
    return {"sent": n, "burst_allowed": BURST, "accepted": len(mine), "refused": len(refused)}


async def _collect_any(comm, sink, until, deadline):
    while len(sink) < until and time.perf_counter() < deadline:
        try:
            sink.append(await comm.receive_json_from(timeout=max(0.05, deadline - time.perf_counter())))
        except TimeoutError:
            break


async def _close(comm):
    """A read that timed out has already stopped the test connection; closing it again is fine."""
    try:
        await comm.disconnect()
    except (asyncio.CancelledError, Exception):
        pass


def run() -> dict:
    from rest_framework_simplejwt.tokens import RefreshToken

    users, group = _people(uuid.uuid4().hex[:8])
    _TOKENS.update({u.id: str(RefreshToken.for_user(u).access_token) for u in users})
    try:

        async def all_parts():
            return {
                "ping": await _ping(users),
                "group": await _group(users, group),
                "dm": await _dm(users),
                "flood": await _flood(users, group),
            }

        out = async_to_sync(all_parts)()
    finally:
        _cleanup(users, group)
        _TOKENS.clear()
    layer = settings.CHANNEL_LAYERS["default"]["BACKEND"].rsplit(".", 1)[-1]
    out["setup"] = {
        "channel_layer": layer,
        "group_members": GROUP_MEMBERS,
        "per_member": PER_MEMBER,
        "dms": DMS,
        "pings": PINGS,
    }
    out["note"] = (
        "Đo qua ứng dụng ASGI thật (xác thực JWT, consumer, cơ sở dữ liệu, channel layer) với client "
        "WebSocket chạy cùng máy chủ: con số là phần trễ của máy chủ. Trễ mạng thật của điện thoại / "
        "trình duyệt cộng thêm khoảng một vòng ping tới máy chủ."
    )
    return out
