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
bind the supplied complete Principal (id/kind/auth_session_id/delegated_by), never return partial rows or
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

## M2 source ready for A wiring

Source: `ff8a4323b73f482a8702f6cbf0ba110af30aa553` (parent M1 source/doc retained).
Constructor now implements the shown optional `record_batch`/`batch_required` keywords.
`GenericModelInputs`, Reader and TokenCounter public signatures are unchanged.
`RegisteredContextInputs.read_many(pins: tuple[Ref,...], ctx) -> tuple[Reading,...]`
is an additional gated, <=128-source entry; it never retains its readings on the
instance. Existing read/check/build/snapshot routes still work without an adapter.

Current Run checks bracket every public group. Recipe metadata reads five current
rows before **and after** the Tool validator. Source groups read owner/payload/seal
and re-read them after actual blob I/O (including the seal, stronger than the old
post-blob pair). At most 42 source slots /126 record keys in a group. Inspection
has two fresh independent passes around tool/recipe waits. An original just read
and hash/classification checked by the actual Run Reader satisfies the same exact
source within that pass; it is freshly read again in the next pass. No policy,
permission, cancellation, revocation, old Reading, assessor output or model output
is cached. SourceResolver/public checks and Composer/ModelInput commit/dispatch
checks remain unchanged.

Example default: `RegisteredContextInputs(..., record_batch=None)` uses sequential
get; no SQL batching or shared cache claim. Strict: `(..., record_batch=actual_A_port,
batch_required=True)`. Adapter errors never fall back. A may inject its adapter
at construction; no composition/shared/SQL store edits were made by B.

M2 receipts: **274 Context unit tests passed**, Ruff passed for changed B files.
An initial boundary assertion incorrectly expected 126 keys although one slot was
an original (actual group123); fixed test now checks <=126 and the remainder69.
Failure `m2-unit-02.log` and successful `m2-unit-03.log` are retained under ignored
`tests/.artifacts/B/MS-C7`. Baseline real SQL matrix is still in progress; completed
single/no-tool build: get9134 / SQL9168 /26.725s; cold+warm ModelInput each get/SQL7753,
23.577s/25.018s. Controlled semantic advice/tool checks never imply production
semantic quality or ToolAccess. M3/M4 continue without waiting for A's adapter.

## M3 refined wait boundary and source

Source `fecd2184e4533f66624cef1a9e5b1ecb3b9df166`. Protocol/dataclass/constructor
signatures unchanged. M3 replaces the initial M2 original-reading reuse with
validation of each pass's actual source Reading against admitted originals/patches.
No prior original Reading crosses a batch-port await. Each of the two passes
still reads the actual Run original once, validates user identity/trust/required/
hash, and independently reads all current registered sources. Added final-batch
original-deletion and controlled original-change counterexamples. Owner/metadata/
seal rows are re-read after blobs; public gates, assessor waits, commit and final
ModelInput checks remain. Principal copies and per-row detached duplicate payloads
are validated; no adapter errors fall back.

Current unit277, routing3, Ruff37 files and mypy17 source files pass. Instrumented
fixed-baseline and final real PostgreSQL55433 matrices each4 passed. Actual Run
reads decrease37.7–39.3%; SQL executions decrease4.0–5.6%; blob/public Reader/assessor
counts identical. Cold/warm input estimates identical, pure format1→0. Raw timing
includes a warm-input regression, so no production latency claim. Controlled get
port consumes actual SQL but is not A's production SQL batch adapter.
Full121 SQL regression is running; interrupted earlier run retained at52% and not
counted as a complete pass. Final receipt and handoff will follow; no accepted label.
