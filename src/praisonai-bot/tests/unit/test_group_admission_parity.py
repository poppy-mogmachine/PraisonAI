"""Cross-channel group admission parity via the core primitive (Issue #5908)."""

from types import SimpleNamespace

import pytest

from praisonai_bot.bots._protocol_mixin import MessageHookMixin


class _Bot(MessageHookMixin):
    platform = "test"

    def __init__(self, **cfg):
        self.config = SimpleNamespace(**cfg)


def _admit(bot, **kw):
    return bot.group_admission(chat_type=kw.pop("chat_type", "group"), **kw)


def test_dm_always_admitted():
    assert _admit(_Bot(group_policy="command_only"), chat_type="dm").admit
    assert _admit(_Bot(group_policy="command_only"), chat_type="im").admit


def test_mention_only_admits_explicit_and_reply_to_bot():
    bot = _Bot(group_policy="mention_only", mention_required=True)
    assert _admit(bot, explicit=True).admit
    assert _admit(bot, reply_to_bot=True).admit
    decision = _admit(bot)
    assert not decision.admit
    assert decision.reason_code == "group_mention_only"


def test_command_only_drops_mentions():
    # Gateway sets mention_required=False for command_only; it must not open
    # the gate to all group traffic.
    bot = _Bot(group_policy="command_only", mention_required=False)
    assert not _admit(bot, explicit=True).admit
    assert _admit(bot, is_command=True).admit


def test_observe_flags_passive_record():
    bot = _Bot(group_policy="observe", mention_required=False)
    decision = _admit(bot)
    assert not decision.admit and decision.observe


def test_legacy_mention_required_false_responds_all():
    assert _admit(_Bot(group_policy="mention_only", mention_required=False)).admit


@pytest.mark.parametrize("policy", [None, "bogus"])
def test_unset_or_unknown_policy_fails_safe(policy):
    assert not _admit(_Bot(group_policy=policy)).admit
