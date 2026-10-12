"""A disposable combined-input candidate; no production setting or allowance."""

import json
import os
from dataclasses import replace
from pathlib import Path

from tests.integration.runner.installed_file_child import assembly as original
from uaw.infrastructure.installed_helper import NAMESPACE_ENV
from uaw.shared.errors import CapabilityUnavailable


class MetadataCandidateAssembly:
    async def create(self, identity):
        if (
            os.environ.get("UAW_A18_INPUT_CANDIDATE") != "1"
            or os.environ.get("UAW_D_INSTALLED_FIXTURE") != "1"
            or not os.environ.get(NAMESPACE_ENV, "").startswith("web-platform-test-")
        ):
            raise CapabilityUnavailable("a18.disposable_candidate_only")
        application = await original.create(identity)
        store = application.helper.container.records
        assert store is application.helper.current_source.commands.store
        assert not store.checked_metadata
        store._checked_metadata = True
        close = application.helper.close

        async def closing():
            try:
                await close()
            finally:
                store._checked_metadata = False
                store._read_plans.clear()
                Path(os.environ["UAW_D_METRICS"]).with_name("a18-candidate-reset.json").write_text(
                    json.dumps({"checked_metadata_restored": not store.checked_metadata}),
                    encoding="utf-8",
                )

        application.helper.close = closing
        return replace(application)


assembly = MetadataCandidateAssembly()
