"""Disposable test tenant: first confirmation is controlled, root UI always rejects.

This tests pre-UI production composition only, never human consent or file access.
"""

import os

from uaw_runner.native_dialog import WindowsNativeDialog

from uaw.infrastructure.installed_helper import NAMESPACE_ENV, InstalledHelperAssembly
from uaw.shared.errors import reject


def controlled_dialog(self, prompt, stopped, deadline):
    if os.environ.get("UAW_TEST_INSTALLED_DIAGNOSTIC") != "1" or not os.environ.get(
        NAMESPACE_ENV, ""
    ).startswith("web-platform-"):
        raise reject("diagnostic_fixture_denied", "Disposable test tenant required", 403)
    if prompt.select_root:
        raise reject("diagnostic_reached_native", "Controlled root UI rejects", 409)
    return None


WindowsNativeDialog.show = controlled_dialog
assembly = InstalledHelperAssembly()
