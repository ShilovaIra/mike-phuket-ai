from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
WORKFLOW = REPO / ".github/workflows/deploy-staging.yml"


def test_ssh_deploy_timeout_allows_full_compose_build():
    text = WORKFLOW.read_text()
    match = re.search(r"command_timeout:\s*(\d+)m", text)
    assert match, (
        "Set appleboy/ssh-action command_timeout (default is 10m). "
        "Staging compose --build exceeds that and fails with Run Command Timeout."
    )
    assert int(match.group(1)) >= 20


def test_bot_and_admin_api_share_one_image():
    compose = (ROOT / "docker-compose.yml").read_text()
    images = re.findall(r"^  (bot|admin-api):\n(?:    .*\n)*?    image: (\S+)", compose, re.M)
    by_service = dict(images)
    assert by_service.get("bot"), "bot must set image: so compose can reuse the build"
    assert by_service.get("admin-api") == by_service["bot"], (
        "bot and admin-api must share one image so pip install runs once per deploy"
    )
