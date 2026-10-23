from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
PRODUCTION_WORKFLOW = REPO / ".github/workflows/deploy-production.yml"


def test_production_deploy_is_manual_and_refuses_other_refs_before_ssh():
    text = PRODUCTION_WORKFLOW.read_text()
    on_block = re.search(r"^on:\n(?P<body>(?:  .*\n)*)", text, re.M)
    assert on_block, "workflow must declare an on: block"
    triggers = on_block.group("body")
    assert "workflow_dispatch:" in triggers
    assert "push:" not in triggers
    assert "pull_request:" not in triggers
    assert "group: deploy-production" in text
    assert "cancel-in-progress: false" in text

    refuse_at = text.find("github.ref != 'refs/heads/main'")
    assert refuse_at != -1
    assert "exit 1" in text[refuse_at : refuse_at + 400]
    for action in ("appleboy/ssh-action", "appleboy/scp-action"):
        action_at = text.find(action)
        assert action_at == -1 or action_at > refuse_at, (
            f"{action} runs before a non-main ref is refused"
        )


def test_production_deploy_waits_for_pytest_on_main():
    deploy = PRODUCTION_WORKFLOW.read_text()
    test_workflow = (REPO / ".github/workflows/test.yml").read_text()
    deploy_job = re.search(r"^  deploy:\n(?P<body>(?:    .*\n)*)", deploy, re.M)
    assert deploy_job, "production workflow must have a deploy job"
    assert re.search(r"needs:\s*test\b", deploy_job.group("body")), (
        "deploy must wait for the test job"
    )
    assert "uses: ./.github/workflows/test.yml" in deploy

    triggers = re.search(r"^on:\n(?P<body>(?:[ ].*\n)*)", test_workflow, re.M)
    assert triggers, "test workflow must declare an on: block"
    body = triggers.group("body")
    assert "workflow_call:" in body
    assert "push:" in body
    assert "pull_request:" in body
    assert "- main" in body
    assert "postgres:16" in test_workflow
    assert "TEST_DATABASE_URL:" in test_workflow
    assert "mike-ai-bot-hkt" in test_workflow
    assert "tests were skipped" in test_workflow


def test_production_deploy_ships_runner_images_and_keeps_env():
    text = PRODUCTION_WORKFLOW.read_text()
    assert "docker compose build bot admin-web partner-web tma-web" in text
    assert "mike-phuket-app:local" in text
    assert "mike-phuket-admin-web:local" in text
    assert "mike-phuket-partner-web:local" in text
    assert "mike-phuket-tma-web:local" in text
    assert "docker load" in text
    assert "docker image prune -af" in text
    assert "*-json.log" in text
    assert "512000" in text
    assert "/opt/mike-phuket-incoming" in text
    assert "target: /tmp" not in text
    assert "--exclude .env" in text
    assert "cp -a /opt/mike-phuket-ai/mike-ai-bot-hkt/.env" in text
    assert "cp -a /tmp/mike-phuket.env.bak /opt/mike-phuket-ai/mike-ai-bot-hkt/.env" in text
    assert "SKIP_GIT_PULL=1" in text
    assert "SKIP_IMAGE_BUILD=1" in text
    assert "deploy_production.sh" in text
    assert "secrets.PRODUCTION_HOST" in text
    timeouts = [int(m) for m in re.findall(r"command_timeout:\s*(\d+)m", text)]
    assert timeouts and max(timeouts) >= 20


def test_production_hand_deploy_builds_with_swap_and_ci_skips_it():
    script = (ROOT / "scripts" / "deploy_production.sh").read_text()
    git_before, git_sep, git_after = script.partition(
        'if [[ "${SKIP_GIT_PULL:-}" != "1" ]];'
    )
    assert git_sep, "CI must set SKIP_GIT_PULL so git is not used after a tar overlay"
    assert "git rev-parse" not in git_before
    assert 'PRODUCTION_BRANCH="main"' in git_after or 'PRODUCTION_BRANCH="main"' in script
    assert "git rev-parse --abbrev-ref HEAD" in git_after
    assert "Refusing to deploy" in git_after

    build_before, build_sep, build_after = script.partition(
        'if [[ "${SKIP_IMAGE_BUILD:-}" != "1" ]];'
    )
    assert build_sep, "CI must set SKIP_IMAGE_BUILD when the runner already loaded images"
    assert "swapon" not in build_before
    assert "docker compose build" not in build_before
    hand_build = build_after.split("→ Starting containers", 1)[0]
    assert "swapon" in hand_build
    assert "systemd-resolved" in hand_build
    assert "registry-1.docker.io" in hand_build
    for service in ("bot", "admin-web", "partner-web", "tma-web"):
        assert f"docker compose build {service}" in hand_build


def test_production_release_exits_2_when_localhost_checks_fail():
    script = (ROOT / "scripts" / "deploy_production.sh").read_text()
    start = script.index("→ Starting containers")
    before, after = script[:start], script[start:]
    missing_env = before.index("Missing .env")
    assert "exit 1" in before[missing_env : missing_env + 250]
    assert "exit 2" not in before

    for expected in (
        "Expected /api/stats → 401",
        "Expected /r/missing-token → 404",
        "Expected Mini App / → 200",
    ):
        at = after.index(expected)
        window = after[at : at + 250]
        assert "exit 2" in window
        assert "exit 1" not in window

    assert "exit 1" not in after
    warn_at = 0
    warnings = 0
    while True:
        found = after.find("not reachable yet", warn_at)
        if found == -1:
            break
        warnings += 1
        assert "exit" not in after[found : found + 180]
        warn_at = found + 1
    assert warnings >= 1


def test_production_deploy_rolls_back_images_and_resets_git_on_success():
    workflow = PRODUCTION_WORKFLOW.read_text()
    script = (ROOT / "scripts" / "deploy_production.sh").read_text()
    assert ":previous" not in script
    images = (
        "mike-phuket-app",
        "mike-phuket-admin-web",
        "mike-phuket-partner-web",
        "mike-phuket-tma-web",
    )
    for image in images:
        assert f"tag_if_present {image}" in workflow
    assert workflow.index("tag_if_present mike-phuket-app") < workflow.index("docker load")
    assert 'docker tag "$1:local" "$1:previous"' in workflow

    failed = workflow.index("Release failed")
    success, failure = workflow[:failed], workflow[failed:]
    assert "git fetch origin main" in success
    assert "git reset --hard origin/main" in success
    assert "git reset --hard origin/main" not in failure
    assert "restore_production_images.sh --up" in failure
    assert "restore_production_images.sh" in failure.replace(
        "restore_production_images.sh --up", ""
    )


def test_restore_production_images_retags_the_previous_release():
    text = (ROOT / "scripts" / "restore_production_images.sh").read_text()
    for name in (
        "mike-phuket-app",
        "mike-phuket-admin-web",
        "mike-phuket-partner-web",
        "mike-phuket-tma-web",
    ):
        assert name in text
    assert ":previous" in text
    assert ":local" in text
    assert "--profile tls" in text
    assert "--up" in text
    assert "Could not restore a full previous release." in text


def test_deploy_script_refuses_non_main_branch():
    script = (ROOT / "scripts" / "deploy_production.sh").read_text()
    assert 'PRODUCTION_BRANCH="main"' in script
    assert "Refusing to deploy" in script


def test_deploy_script_sets_partner_offer_base_to_production_domain():
    script = (ROOT / "scripts" / "deploy_production.sh").read_text()
    assert "partners.mikephuketai.com" in script
    assert "admin.mikephuketai.com" in script
    assert "PARTNER_PUBLIC_HOST" in script
    assert "ADMIN_PUBLIC_HOST" in script
    assert "PARTNER_OFFER_BASE_URL=" in script
    assert "/r/missing-token" in script
    assert "force-recreate bot" in script


def test_deploy_script_starts_caddy_tls_profile():
    script = (ROOT / "scripts" / "deploy_production.sh").read_text()
    assert script.count("--profile tls") >= 3
    assert "docker compose up -d --build" not in script


def test_production_env_example_uses_public_hosts():
    text = (ROOT / ".env.production.example").read_text()
    assert "PARTNER_PUBLIC_HOST=partners.mikephuketai.com" in text
    assert "ADMIN_PUBLIC_HOST=admin.mikephuketai.com" in text
    assert "COMPOSE_PROFILES=tls" in text
    assert "PARTNER_OFFER_BASE_URL=https://partners.mikephuketai.com" in text
