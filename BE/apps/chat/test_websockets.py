"""The three WebSockets (ws/events/, ws/groups/<id>/, ws/support/<id>/) through the real ASGI app: who may connect,
flooding, oversized frames, and that one learner's events never reach another."""
import json

import pytest
from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.chat.consumers import BURST
from apps.chat.models import GroupMessage, SupportConversation
from apps.community.models import Group, GroupMember
from config.asgi import application

pytestmark = pytest.mark.django_db(transaction=True)  # consumers reach the database from another thread


def token(user):
    return str(RefreshToken.for_user(user).access_token)


def learner(n, **extra):
    return User.objects.create_user(email=f"ws{n}@example.com", password="Strong!Pass123", display_name=f"WS {n}",
                                    birth_date="1990-01-01", **extra)


async def _connect(path):
    comm = WebsocketCommunicator(application, path)
    connected, code = await comm.connect()
    if connected:
        await comm.disconnect()
    return comm, connected, code


def connect(path):
    return async_to_sync(_connect)(path)


def run(coro_fn, *args):
    return async_to_sync(coro_fn)(*args)


@pytest.fixture
def group():
    a, b = learner(1), learner(2)
    g = Group.objects.create(name="ws", created_by=a)
    GroupMember.objects.create(group=g, user=a, role="leader", status="active")
    GroupMember.objects.create(group=g, user=b, status="active")
    return g, a, b


@pytest.mark.parametrize("path", ["/ws/events/", "/ws/groups/{gid}/", "/ws/support/{sid}/"])
def test_no_token_or_a_forged_one_is_refused(group, path):
    g, a, _ = group
    conv = SupportConversation.objects.create(learner=a)
    path = path.format(gid=g.id, sid=conv.id)
    forged = token(a)[:-4] + "AAAA"
    for query in ("", "?token=", f"?token={forged}", "?token=not.a.jwt"):
        comm, connected, code = connect(path + query)
        assert not connected and code == 4401, (path, query, code)


def test_a_locked_account_cannot_connect(group):
    g, a, _ = group
    t = token(a)
    User.objects.filter(pk=a.pk).update(status=User.Status.LOCKED)
    comm, connected, code = connect(f"/ws/groups/{g.id}/?token={t}")
    assert not connected and code == 4401


def test_only_active_members_reach_a_group_chat(group):
    g, a, _ = group
    outsider, pending = learner(3), learner(4)
    GroupMember.objects.create(group=g, user=pending, status="pending")
    for user in (outsider, pending):
        comm, connected, code = connect(f"/ws/groups/{g.id}/?token={token(user)}")
        assert not connected and code == 4403
    comm, connected, _ = connect(f"/ws/groups/{g.id}/?token={token(a)}")
    assert connected


def test_another_learners_support_chat_is_closed():
    a, b = learner(1), learner(2)
    conv = SupportConversation.objects.create(learner=a)
    comm, connected, code = connect(f"/ws/support/{conv.id}/?token={token(b)}")
    assert not connected and code == 4403


def test_members_chat_and_a_flood_is_held_back(group):
    g, a, b = group
    ta, tb = token(a), token(b)  # minted outside the event loop: it writes to the database

    async def scenario():
        sender = WebsocketCommunicator(application, f"/ws/groups/{g.id}/?token={ta}")
        reader = WebsocketCommunicator(application, f"/ws/groups/{g.id}/?token={tb}")
        assert (await sender.connect())[0] and (await reader.connect())[0]
        await sender.send_json_to({"action": "send", "content": "xin chào", "client_id": "c1"})
        got = await reader.receive_json_from(timeout=5)
        assert got["event"] == "message" and got["payload"]["content"] == "xin chào"
        await sender.receive_json_from(timeout=5)  # its own echo
        errors = 0
        for i in range(40):  # a script hammering the room
            await sender.send_json_to({"action": "send", "content": f"spam {i}"})
        while not await sender.receive_nothing(timeout=1):  # a timed-out receive would cancel the app
            msg = await sender.receive_json_from()
            errors += msg["event"] == "error"
        await sender.disconnect()
        await reader.disconnect()
        return errors

    errors = run(scenario)
    sent = GroupMessage.objects.filter(group=g, user=g.created_by).count()
    assert sent <= BURST + 1, sent  # the first message + one burst, the rest refused
    assert errors >= 40 - BURST


def test_oversized_and_binary_frames_close_the_socket(group):
    g, a, _ = group
    ta = token(a)

    async def scenario(payload, binary):
        comm = WebsocketCommunicator(application, f"/ws/groups/{g.id}/?token={ta}")
        assert (await comm.connect())[0]
        if binary:
            await comm.send_to(bytes_data=payload)
        else:
            await comm.send_to(text_data=payload)
        out = await comm.receive_output(timeout=5)
        await comm.wait()
        return out

    big = json.dumps({"action": "send", "content": "x" * 9000})
    assert run(scenario, big, False) == {"type": "websocket.close", "code": 4413}
    assert run(scenario, b"\x00\x01", True) == {"type": "websocket.close", "code": 4413}
    assert not GroupMessage.objects.exists()


def test_events_reach_only_their_owner():
    from apps.notifications.services import notify

    a, b = learner(1), learner(2)
    ta, tb = token(a), token(b)

    async def scenario():
        ca = WebsocketCommunicator(application, f"/ws/events/?token={ta}")
        cb = WebsocketCommunicator(application, f"/ws/events/?token={tb}")
        assert (await ca.connect())[0] and (await cb.connect())[0]
        await ca.receive_json_from()  # "connected"
        await cb.receive_json_from()
        from channels.db import database_sync_to_async
        await database_sync_to_async(notify)(a, "system", "chỉ cho A")
        got = await ca.receive_json_from(timeout=5)
        b_silent = await cb.receive_nothing(timeout=1)
        await ca.disconnect()
        await cb.disconnect()
        return got, b_silent

    got, b_silent = run(scenario)
    assert got["event"] == "notification" and got["payload"]["title"] == "chỉ cho A"
    assert b_silent
