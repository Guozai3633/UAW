"""MS-C7 port boundary tests; no SQL adapter or authorization is simulated as real."""

from copy import deepcopy
from dataclasses import FrozenInstanceError

import pytest

from uaw.context.contracts import RecordReadKey
from uaw.context.read_batch import ContextRecordReads
from uaw.shared.errors import DomainError
from uaw.shared.stores import Record, StoreMissing


class Records:
    def __init__(self):
        self.calls = []
        self.row = Record("named", "entry", 1, "Ref", {"nested": ["body"]})

    async def get(self, principal, namespace, resource_id, *, revision=None):
        self.calls.append((principal, namespace, resource_id, revision))
        if namespace != "named" or resource_id != "entry":
            raise StoreMissing()
        return self.row


class Batch:
    def __init__(self, rows):
        self.rows, self.calls = rows, []

    async def read(self, principal, keys):
        self.calls.append((principal, keys))
        return self.rows


async def test_sequential_compatibility_duplicates_and_isolation(principal):
    store = Records()
    keys = (RecordReadKey("named", "entry"), RecordReadKey("named", "entry", 1))
    reads = ContextRecordReads(store)
    rows = await reads.read(principal, keys)
    assert len(store.calls) == 2 and rows == (store.row, store.row)
    rows[0].payload["nested"].append("consumer change")
    assert store.row.payload == {"nested": ["body"]}
    assert (await reads.read(principal, keys))[0].payload == {"nested": ["body"]}
    assert not await reads.read(principal, ())
    with pytest.raises(FrozenInstanceError):
        keys[0].revision = 2


async def test_port_order_complete_principal_and_no_fallback(principal):
    store = Records()
    keys = (RecordReadKey("named", "entry", 1),) * 2
    batch = Batch((store.row, deepcopy(store.row)))
    assert await ContextRecordReads(store, batch=batch).read(principal, keys) == batch.rows
    assert batch.calls == [(principal, keys)] and not store.calls
    batch.rows = ()
    with pytest.raises(DomainError) as caught:
        await ContextRecordReads(store, batch=batch).read(principal, keys)
    assert caught.value.failure.code == "context_record_batch_invalid" and not store.calls


@pytest.mark.parametrize("required", [(), (RecordReadKey("named", "entry"),)])
async def test_required_missing_is_unavailable(principal, required):
    with pytest.raises(DomainError) as caught:
        await ContextRecordReads(Records(), required=True).read(principal, required)
    assert caught.value.failure.code == "capability_unavailable"


@pytest.mark.parametrize(
    "keys",
    [
        [RecordReadKey("named", "entry")],
        (RecordReadKey("named", "entry"),) * 129,
        (RecordReadKey("", "entry"),),
        (RecordReadKey("named", ""),),
        (RecordReadKey("named", "entry", True),),
        (RecordReadKey("named", "entry", 0),),
        (RecordReadKey("named", "entry", -1),),
        (RecordReadKey("named", "entry", 2147483648),),
    ],
)
async def test_invalid_keys_before_io(principal, keys):
    store = Records()
    with pytest.raises(DomainError):
        await ContextRecordReads(store).read(principal, keys)
    assert not store.calls


@pytest.mark.parametrize(
    "rows",
    [
        [],
        (),
        (Record("foreign", "entry", 1, "Ref", {}),),
        (Record("named", "other", 1, "Ref", {}),),
        (Record("named", "entry", 2, "Ref", {}),),
        (Record("named", "entry", True, "Ref", {}),),
        (Record("named", "entry", 1, "", {}),),
        (Record("named", "entry", 1, "Ref", []),),
    ],
)
async def test_bad_adapter_output(principal, rows):
    store = Records()
    with pytest.raises(DomainError):
        await ContextRecordReads(store, batch=Batch(rows)).read(
            principal, (RecordReadKey("named", "entry", 1),)
        )
    assert not store.calls


async def test_fresh_error_and_maximum(principal):
    store = Records()
    reads = ContextRecordReads(store)
    assert len(await reads.read(principal, (RecordReadKey("named", "entry"),) * 128)) == 128
    with pytest.raises(StoreMissing):
        await reads.read(
            principal, (RecordReadKey("named", "entry"), RecordReadKey("named", "missing"))
        )
    # Rows fetched before the error never escape as partial success.


async def test_principal_mutation_is_rejected_without_mutating_caller(principal):
    store = Records()
    original = principal.model_copy(deep=True)

    class MutatingBatch:
        async def read(self, offered, keys):
            offered.__dict__["id"] = "foreign"
            return (store.row,)

    with pytest.raises(DomainError) as caught:
        await ContextRecordReads(store, batch=MutatingBatch()).read(
            principal, (RecordReadKey("named", "entry"),)
        )
    assert caught.value.status_code == 403 and principal == original


async def test_duplicate_records_must_agree_and_payloads_are_independent(principal):
    store = Records()
    keys = (RecordReadKey("named", "entry"),) * 2
    batch = Batch((store.row, store.row))
    rows = await ContextRecordReads(store, batch=batch).read(principal, keys)
    rows[0].payload["nested"].append("consumer")
    assert rows[1].payload == store.row.payload == {"nested": ["body"]}
    batch.rows = (store.row, Record("named", "entry", 2, "Ref", {}))
    with pytest.raises(DomainError):
        await ContextRecordReads(store, batch=batch).read(principal, keys)
