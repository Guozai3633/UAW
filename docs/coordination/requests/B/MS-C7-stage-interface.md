# B/MS-C7 M1 fixed batch interface

Baseline: `ms-i2i-start` = `d8023eb07e1460961782f297697da7428f6ad247`.
Worktree `E:/UAW/.worktrees/context`, branch `dev/context`.

```python
from uaw.context.contracts import RecordReadKey
from uaw.context.ports import ContextRecordBatchPort

# A implements this port over its actual owner-isolated named-record SQL store.
async def read(principal: Principal,
               keys: tuple[RecordReadKey, ...]) -> tuple[Record, ...]: ...

# M2 consumption constructor; existing keyword arguments remain compatible.
inputs = RegisteredContextInputs(..., record_batch=adapter,
                                 batch_required=True)
# Default compatibility: record_batch=None, batch_required=False, sequential get.
```

RecordReadKey is a frozen dataclass `(namespace: str, resource_id: str,
revision: int | None = None)`. None means current non-deleted revision; an integer
is an exact positive revision. **Ordered tuple including duplicates**, <=128 keys;
empty tuple returns empty. Missing/deleted/foreign rows fail the whole call. A must
filter by the complete Principal (kind/id/tenant), never return partial rows or
permit a historical revision of a deleted resource. Record identity fields are
namespace/resource_id/revision/schema_name/payload, **not `Record.id`**.

ContextRecordReads validates shape, length, identities and pinned revisions, and
copies payloads. Adapter errors propagate; a failing adapter never silently falls
back. `batch_required=True` without an adapter raises
`capability_unavailable` (`context.record_batch`), including an empty call. Invalid
keys/shape raise `context_record_batch_invalid`. Current owner/Run/scope/model,
policy, recipe, tool, cancellation, deadline and source checks remain in Context;
this port reads data and grants no permission. SQL consistency is not an atomic
external source/ACL/blob guarantee.

M1 helper is executable. M2 will connect fresh operation-local groups, without
retaining Record or Reading on components or across operations. No ORM in Context.
M1 baseline measurements and M2 source/example SHA follow in the next stage record;
SQL adapter is A's work and is **not** implemented by this proposal. Only declared
sequential-get compatibility will be measured until a published A adapter exists.
Measurements will separate setup, build, ModelInput, Reader/assessor calls, record
get and observed SQL statement executions; controlled advice/tool validators are
not production Model semantic quality or production ToolAccess evidence.

M1 source commit: `cd577ab01e59313341d15d30662703adb017b02f`.
Validation: `.venv/Scripts/python.exe -m pytest tests/unit/context/test_read_batch.py -q`
→ **21 passed**, no failures/skips. Ruff on these five source/test files passed.
Own PowerShell dot-sourced `ops/start-dev-db.ps1 -Session B`, PostgreSQL55433 ready;
`.venv/Scripts/python.exe -m alembic upgrade head` exited 0.
Baseline matrix is running under `--require-postgres`; no collection-only success
is called a SQL pass. Receipts: ignored `tests/.artifacts/B/MS-C7/m1-baseline.log`.
