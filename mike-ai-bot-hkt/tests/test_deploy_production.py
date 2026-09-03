from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
