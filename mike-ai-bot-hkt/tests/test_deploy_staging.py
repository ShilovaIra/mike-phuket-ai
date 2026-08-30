from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
WORKFLOW = REPO / ".github/workflows/deploy-staging.yml"


def test_ssh_deploy_timeout_allows_full_compose_build():
    text = WORKFLOW.read_text()
    timeouts = [int(m) for m in re.findall(r"command_timeout:\s*(\d+)m", text)]
    assert timeouts, (
        "Set appleboy/ssh-action command_timeout (default is 10m). "
        "Staging compose --build exceeds that and fails with Run Command Timeout."
    )
    assert max(timeouts) >= 20


def test_ssh_deploy_copies_the_tree_from_the_runner():
    text = WORKFLOW.read_text()
    assert "actions/checkout@v4" in text
    assert "appleboy/scp-action@" in text
    assert "mike-phuket-ai.tgz" in text
    assert "RUNNER_TEMP" in text, (
        "Write the tarball outside the tree. tar czf ./archive . exits 1 with "
        "'file changed as we read it'."
    )
    assert "docker compose build bot admin-web partner-web" in text
    assert "docker load" in text
    assert "SKIP_GIT_PULL=1" in text
    assert "SKIP_IMAGE_BUILD=1" in text
    assert "script_stop" not in text, (
        "appleboy/ssh-action v1.2.5 has no script_stop input; set -e in the script is enough"
    )


def test_deploy_script_repairs_dns_before_image_builds():
    script = (ROOT / "scripts" / "deploy_staging.sh").read_text()
    assert "swapon" in script
    assert "systemd-resolved" in script
    assert "registry-1.docker.io" in script


def test_deploy_script_builds_images_one_at_a_time():
    script = (ROOT / "scripts" / "deploy_staging.sh").read_text()
    assert "docker compose build bot" in script
    assert "docker compose build admin-web" in script
    assert "docker compose build partner-web" in script
    assert "docker compose up -d --build" not in script, (
        "up --build compiles all images in parallel and OOMs 1 GB Droplets"
    )


def test_deploy_script_skips_image_build_when_ci_loaded_images():
    script = (ROOT / "scripts" / "deploy_staging.sh").read_text()
    assert "SKIP_IMAGE_BUILD" in script


def test_web_services_have_named_images_for_docker_save():
    compose = (ROOT / "docker-compose.yml").read_text()
    assert "image: mike-phuket-admin-web:local" in compose
    assert "image: mike-phuket-partner-web:local" in compose


def test_bot_and_admin_api_share_one_image():
    compose = (ROOT / "docker-compose.yml").read_text()
    images = re.findall(r"^  (bot|admin-api):\n(?:    .*\n)*?    image: (\S+)", compose, re.M)
    by_service = dict(images)
    assert by_service.get("bot"), "bot must set image: so compose can reuse the build"
    assert by_service.get("admin-api") == by_service["bot"], (
        "bot and admin-api must share one image so pip install runs once per deploy"
    )
