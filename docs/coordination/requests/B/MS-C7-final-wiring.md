# B/MS-C7 final wiring and measured read costs

Worktree `E:/UAW/.worktrees/context`, branch `dev/context`.
Baseline `ms-i2i-start` = `d8023eb07e1460961782f297697da7428f6ad247`.
Clean start/fetch tags/ff-only merge/HEAD equality/uv sync --frozen succeeded.
M1 source `cd577ab01e59313341d15d30662703adb017b02f`, M1 interface handoff
`5c84c336b2893d832c0012d803457e7ab5deb3a3`; M2 source
`ff8a4323b73f482a8702f6cbf0ba110af30aa553`, M2 handoff
`b121c9b0e91667d152d918dbf249955835dfa9d6`. Prior accepted work retained.
Final implementation source `fecd2184e4533f66624cef1a9e5b1ecb3b9df166`, M3 stage
handoff `09a7cc3eb9b775808060eb61c067f61901e03352`. Final validation is complete:
277 unit +128 distinct real SQL =405 unique nodes, zero failures/errors/skips.
This is component delivery, not acceptance of a full P1/P4 round.

## Fixed interfaces and injection

```python
from uaw.context.contracts import RecordReadKey
from uaw.context.ports import ContextRecordBatchPort
from uaw.context.registered import RegisteredContextInputs
from uaw.context.readers import RegisteredRuleProvider
from uaw.context.cache import PureComputationCache

# A's adapter implements (no ORM added by B):
async def read(principal: Principal,
               keys: tuple[RecordReadKey, ...]) -> tuple[Record, ...]: ...

# Existing constructors still work, with declared sequential-get compatibility.
inputs = RegisteredContextInputs(controller=controller, records=records,
    blobs=blobs, transactions=transactions, runs=actual_run_sources,
    tool_validator=actual_current_tools, record_batch=None, batch_required=False)
# Optional strict production consumption after A implements its SQL adapter:
inputs = RegisteredContextInputs(controller=controller, records=records,
    blobs=blobs, transactions=transactions, runs=actual_run_sources,
    tool_validator=actual_current_tools, record_batch=actual_batch_adapter,
    batch_required=True)

# Existing assessor injection and fixed model remain mandatory for multiple rules.
provider = RegisteredRuleProvider(inputs, assessor=actual_fixed_model_assessor)
# Pure computation cache remains optional; zero capacity disables it.
cache = PureComputationCache(max_entries=128, max_bytes=2097152)
off = PureComputationCache(max_entries=0, max_bytes=0)
```

RecordReadKey is frozen, fields namespace/resource_id/revision=None. <=128 keys,
ordered including duplicates. Current non-deleted rows when revision=None;
positive exact revision otherwise. Missing/deleted/foreign is whole failure.
A must bind the supplied complete Principal; data never authorizes Run/Tool/Model.
Record fields are namespace/resource_id/revision/schema_name/payload. Invalid
shape/length/order/key/version/duplicate consistency or mutated Principal rejects
with context_record_batch_invalid; adapter errors propagate without fallback.
Required without adapter is capability_unavailable/context.record_batch. Empty
returns empty unless strict dependency is missing. Returned payloads are detached
per row including duplicates. No rows/readings/permissions are retained on the
component; no source or model output cache.

RegisteredContextInputs adds read_many(pins: tuple[Ref,...], ctx) -> tuple[Reading,...],
with a whole-operation deadline and fresh public authority before/after. Maximum
128 source slots, chunks42 / <=126 record keys. Owner/full metadata/seal are fresh,
actual blobs and hashes are read, then all three rows are read again after blob
await. Recipe reads its five rows before and after current Tool validator awaits.
Inspection makes two separate actual source passes around recipe/Tool waits. M3
refines M2: Run originals are read as sources in each pass, then validated against
current admitted original/patch refs, kind/user trust/required/hash. No earlier
original Reading crosses a batch-port await. Final-batch original deletion tests
cover this boundary. Public Reader.check/read, SourceResolver, rule assessor
before/after/exception checks, commit checks and ModelInput final checks remain.
GenericModelInputs/TokenCounter public signatures unchanged; purpose agent_step,
actual Run/fixed model/epoch/permission/window/unchanged original text retained.
Materials stay tagged data. Missing multi-rule assessor, nonempty-tool validator,
Reader or authority remains unavailable; no fabricated empty tool set.

## Actual measurement conditions and results

Own PostgreSQL55433, FS blobs, A published RegisteredRunContextSources actual
RunExecutionSources/fixed model/current policy. Single/two user rules, explicit
empty/nonempty tools, same text and output128/tool64 reserves. Fixture registration
is a separate excluded phase. Fixed baseline B registered.py is loaded from the
published SHA via git show for the instrumented comparison, **not** from another
session's developing source. Current module and original expansion oracle are
also compared on the same persisted versions in the equivalence SQL test.

SQL counts are actual before_cursor_execute events, not TCP packets or unobserved
BEGIN/COMMIT/pool pings. Per-namespace get, blob/actual Run/Reader/assessor counts,
inclusive elapsed times and Context preparation totals are in ignored raw JSON.
Inclusive I/O times overlap, so do not add them. ControlledAdvice and current SQL
ToolSpec checker are explicit fixtures, not actual LLM semantic quality or
production ToolAccess. Model HTTP calls=0; no Runner invoked. Both compatibility
and controlled port consumer still use real sequential get; **A's SQL batching
performance is not measured or claimed**.

| rules/tools | boundary | get baseline→final | SQL baseline→final | actual Run read | seconds baseline→final |
| --- | --- | --- | --- | --- | --- |
| 1/0 | build | 9134→8624 | 9168→8658 | 69→43 | 54.589→34.003 |
| 1/0 | ModelInput-cold | 7753→7371 | 7753→7371 | 53→33 | 45.740→27.587 |
| 1/0 | ModelInput-warm | 7753→7371 | 7753→7371 | 53→33 | 38.039→28.879 |
| 1/1 | build | 9200→8690 | 9234→8724 | 69→43 | 48.754→35.118 |
| 1/1 | ModelInput-cold | 7809→7427 | 7809→7427 | 53→33 | 33.700→32.238 |
| 1/1 | ModelInput-warm | 7809→7427 | 7809→7427 | 53→33 | 29.701→29.879 |
| 2/0 | build | 11777→11240 | 11815→11278 | 77→47 | 53.736→43.667 |
| 2/0 | ModelInput-cold | 10240→9823 | 10240→9823 | 61→37 | 57.033→39.003 |
| 2/0 | ModelInput-warm | 10240→9823 | 10240→9823 | 61→37 | 56.790→43.084 |
| 2/1 | build | 11851→11314 | 11889→11352 | 77→47 | 51.203→47.238 |
| 2/1 | ModelInput-cold | 10304→9887 | 10304→9887 | 61→37 | 44.055→39.214 |
| 2/1 | ModelInput-warm | 10304→9887 | 10304→9887 | 61→37 | 41.770→58.539 |

Queries decrease 4.0–5.6%; actual Run reads decrease 37.7–39.3%. Blob and public
Reader counts remain identical, and multi-rule assessor calls remain2 for each
build or ModelInput (single rule0). Full current checks remain on cold and warm
paths. Warm format calls=0 vs cold1; estimates unchanged 5972/6957/7271/8256 across
the four combinations. No Token savings or provider prompt-cache claim. Timing
varies: two-rule/nonempty-tool warm input actually regresses 41.770→58.539s in this
sample. Initial/intermediate raw measurements are retained too. Query reduction
and local format reuse do not promise production latency.

Receipts: tests/.artifacts/B/MS-C7/{baseline-full-*,final-*,comparison.json},
m1-baseline.log/m3-candidate.log/m4-baseline-full.log/m4-final-cost.log. All four
baseline and final matrix tests passed with --require-postgres. All 277 current
unit tests passed; original routing3 passed; mypy17 source files and Ruff passed.
Complete SQL regression passed121, final-sql.exit=0,3915.53s. Together with
routing3 and final matrix4,128 distinct real SQL nodes passed. Unit277 passed in
11.91s; original routing3 in30.96s; final measurement4 in498.07s. Final JUnit has
zero failures/errors/skips; validation.json records405 unique nodes and0 duplicate
nodes, all_complete=true. Receipt names: final-unit.xml/.log, final-sql.xml/.log/
.exit, routing.xml/.log, m4-final-cost.log, m4-baseline-full.log, final-ruff*.log,
m4-mypy-02.log. Historical failures/interruption remain separate and preserved.
No unresolved component test/type/format failure remains; production batch/Model/
Tool adapters are A wiring dependencies, not tests claimed as passed.

## Validation and history

```powershell
. ./ops/start-dev-db.ps1 -Session B
.venv/Scripts/python.exe -m alembic upgrade head
$env:UAW_CONTEXT_EVIDENCE_DIR='tests/.artifacts/B/MS-C7'
$env:UAW_CONTEXT_FIXED_BASELINE='1'
$env:UAW_CONTEXT_COST_PHASE='baseline-full'
.venv/Scripts/python.exe -m pytest tests/integration/context/test_read_cost_postgres.py --require-postgres -vv
$env:UAW_CONTEXT_FIXED_BASELINE='0'
$env:UAW_CONTEXT_COST_PHASE='final'
.venv/Scripts/python.exe -m pytest tests/integration/context/test_read_cost_postgres.py --require-postgres -vv
.venv/Scripts/python.exe -m pytest tests/unit/context -q --junitxml=tests/.artifacts/B/MS-C7/final-unit.xml
.venv/Scripts/python.exe -m pytest tests/integration/context tests/integration/test_context_wiring.py --ignore=tests/integration/context/test_read_cost_postgres.py --require-postgres -vv --junitxml=tests/.artifacts/B/MS-C7/final-sql.xml
.venv/Scripts/python.exe -m pytest tests/integration/test_model_input_routing.py --require-postgres -vv --junitxml=tests/.artifacts/B/MS-C7/routing.xml
.venv/Scripts/python.exe -m ruff check src/uaw/context tests/unit/context tests/integration/context
.venv/Scripts/python.exe -m ruff format --check src/uaw/context tests/unit/context tests/integration/context
.venv/Scripts/python.exe -m mypy src/uaw/context --cache-dir .cache/mypy/B
```

History retained: initial test miscounted original slot vs registered keys (actual
123/69 rather than126/66), repaired boundary assertions. M3 fixture originally
used generic v1; changed only the new fixture to SQL numeric1, retaining production
numeric validation. Two mypy annotations repaired (typed duplicate map and exact
three-record tuple). Raw failed unit/type logs retained. Automatic approval once
failed from quota; user continued, normal review succeeded, no bypass. Long SQL
regression lost its process at52% with no final receipt; m4-sql-regression-01.log
retained and not treated as a complete pass. Re-run finite hidden own PowerShell
completed121 passed / exit0 and wrote final-sql.log/.xml/.exit, so the earlier
interruption is accounted separately from the complete pass.
No test failures, skips or collection-only status are hidden as acceptance.

## A wiring and remaining ownership

A supplies actual owner-isolated SQL batch adapter, full trusted current auth/Run,
fixed Model assessor, current Tool validator/Reader and cancellation/deadline.
Wire via constructor; no required change to shared schemas or existing public
get. Ordered complete response and deleted history semantics must be preserved.
Current Model routing/composition and final Model dispatch remain A's work.
Default compatibility path and default-off pure cache are immediately usable;
strict missing dependency fails. No controller or permission comes from body/model.

Changed files from the fixed baseline:

- src/uaw/context/{contracts,ports,read_batch,registered}.py
- tests/unit/context/{test_read_batch,test_record_groups}.py
- tests/integration/context/{registered_fixture,test_assessment_chain_postgres,
  test_read_cost_postgres,test_record_batch_postgres}.py
- docs/coordination/requests/B/{MS-C7-stage-interface,MS-C7-final-wiring}.md
- docs/coordination/handoffs/B.md

B modifies only these allowed source/tests and its requests/handoff. Old evidence defaults preserved;
old cost fixture now accepts own UAW_CONTEXT_EVIDENCE_DIR to avoid overwriting C6.
No seed/intent, shared/schema, Run/Model/API/composition/lock/flags/ops or other
worktree edits. A reviews/merges and handles public conflicts/full chain regression.
This package does not mark P1-02/P4-04 or whole P1/P4 accepted, does not decide
D01/D03/D06, and does not automatically start another package.
