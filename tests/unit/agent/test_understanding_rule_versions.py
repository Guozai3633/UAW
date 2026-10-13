"""New understanding policy cannot silently impersonate a previously pinned instruction."""

import hashlib
from types import SimpleNamespace

import pytest

from uaw.context.intent import UnderstandingRules, understanding_template
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError


async def authorize(_):
    return None


@pytest.mark.parametrize("name", ["intent-understand-v1", "intent-understand-v2"])
async def test_pinned_old_and_new_rules_keep_their_exact_distinct_bytes(name):
    rules = UnderstandingRules(SimpleNamespace(authorize=authorize))
    text = understanding_template(name)
    ref = Ref(
        kind="rule", id=name, version="1", content_hash=hashlib.sha256(text.encode()).hexdigest()
    )
    reading = await rules.read(ref, "pinned", None)
    assert reading.text == text and reading.ref == ref and reading.trust == "platform"
    other = understanding_template(
        "intent-understand-v2" if name.endswith("v1") else "intent-understand-v1"
    )
    assert other != text
    with pytest.raises(DomainError) as rejected:
        await rules.read(
            ref.model_copy(update={"content_hash": hashlib.sha256(other.encode()).hexdigest()}),
            "pinned",
            None,
        )
    assert rejected.value.failure.code == "source_changed"
