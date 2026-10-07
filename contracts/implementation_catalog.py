"""Reviewed operation-level implementation scope; this does not mark entire modules complete."""

HTTP = (
    "conversations.create", "conversations.get", "conversations.items", "turns.submit",
    "runs.get", "runs.control", "events.read", "events.payload", "models.list",
    "admin.providers.configure", "admin.providers.revoke", "admin.models.register",
    "admin.policies.register", "admin.environments.register", "admin.secrets.put",
    "admin.configuration.stage", "admin.configuration.get", "admin.configuration.validate",
    "admin.configuration.activate",
)

IMPLEMENTATIONS = {
    operation: {"scope": "development_control_plane", "entrypoint": "src/uaw/api/routes.py",
                "evidence": ["docs/implementation/P0-03.md", "docs/implementation/P0-04.md",
                             "docs/implementation/evidence/p0-tests.xml"]}
    for operation in HTTP
}
IMPLEMENTATIONS["RunRuntime.create"] = {
    "scope": "development_run_admission", "entrypoint": "src/uaw/run/facade.py",
    "evidence": ["docs/implementation/P0-04.md", "docs/implementation/evidence/p0-tests.xml"],
}
IMPLEMENTATIONS["ModelRuntime.generate"] = {
    "scope": "development_model_protocol", "entrypoint": "src/uaw/model/facade.py",
    "evidence": ["docs/implementation/P0-05.md", "docs/implementation/evidence/p0-tests.xml"],
}
for operation in ("IntentRuntime.understand", "IntentRuntime.revise", "tasks.frame"):
    IMPLEMENTATIONS[operation] = {
        "scope": "development_intent_protocol",
        "entrypoint": "src/uaw/api/routes.py" if operation == "tasks.frame" else "src/uaw/intent/facade.py",
        "evidence": ["docs/implementation/P1-01.md", "docs/implementation/evidence/p0-tests.xml"],
    }
for operation in ("approvals.get", "approvals.decide"):
    IMPLEMENTATIONS[operation] = {
        "scope": "development_manual_consent_no_executor",
        "entrypoint": "src/uaw/api/routes.py",
        "evidence": ["docs/implementation/MS-I2a.md", "docs/implementation/evidence/p0-tests.xml"],
    }
