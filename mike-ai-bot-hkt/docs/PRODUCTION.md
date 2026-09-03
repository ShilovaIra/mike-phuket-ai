# Production on DigitalOcean (self-managed)

Production runs Docker Compose (bot + Postgres) from the **`main` Git branch only**.

**Branch rule:** do not deploy `staging` or feature branches to this Droplet. Use `scripts/deploy_production.sh` — it refuses to deploy if the checkout is not `main`.

Promote code by merging `staging` → `main` (PR or local merge), then redeploying on the production host.

## What you get

| Component | Where it runs |
|---|---|
| Telegram bot (polling) | Docker container `bot` |
| PostgreSQL 16 | Docker container `db` (volume-backed), or managed Postgres |
| Schema migration | Automatic on bot start (`SessionStore.create`) |
| Partner Dashboard | `https://partners.mikephuketai.com/` (Caddy → `partner-web`) |
| Operator admin | `https://admin.mikephuketai.com/` (Caddy → `admin-web`) |
| Deploy source | Git branch `main` only |

## Prerequisites

- Production Droplet with Docker installed (same setup as [STAGING.md](STAGING.md) §§2–3)
- Repo cloned on the Droplet on branch `main`
- Production Telegram bot token (never reuse the staging bot)
- Filled `.env` from `.env.production.example`

Typical paths (adjust if your host differs):

| Item | Value |
|---|---|
| Remote repo | `/opt/mike-phuket-ai` |
| App dir | `/opt/mike-phuket-ai/mike-ai-bot-hkt` |

## Firewall

Use a **separate** DigitalOcean firewall from staging (production SSH is not opened to GitHub Actions). Attach it only to the production Droplet.

| Inbound | Protocol | Port | Sources |
|---|---|---|---|
| SSH | TCP | 22 | Your IP / office VPN (key-only auth) |
| HTTP | TCP | 80 | `0.0.0.0/0` (Let’s Encrypt challenge + redirect to HTTPS) |
| HTTPS | TCP | 443 | `0.0.0.0/0` (`partners` and `admin`) |

Do **not** open **5432**, **8080**, or **8081**. Caddy serves both sites on 443.

## Domain (`mikephuketai.com`)

The apex is already in DigitalOcean DNS (same zone as staging). Add **production** A records that point at the **production** Droplet — not `152.42.221.33` (staging).

| Type | Hostname | Will direct to |
|---|---|---|
| **A** | `partners` | **production** Droplet |
| **A** | `admin` | **production** Droplet |

Leave `@` and `www` empty unless you add a marketing site later. Keep `partners-staging` / `admin-staging` on the staging Droplet.

Check (replace with the production IP you see in DigitalOcean):

```bash
dig A partners.mikephuketai.com +short
dig A admin.mikephuketai.com +short
```

Both must be the production Droplet IPv4. Then Caddy can obtain certificates.

Partner Users: `https://partners.mikephuketai.com/`  
Operators: `https://admin.mikephuketai.com/`

## First-time cutover (from old in-memory bot)

1. Merge `staging` into `main` and push `origin/main`.
2. On the Droplet: checkout `main`, copy `.env.production.example` → `.env`, fill **production** secrets. Keep `PARTNER_PUBLIC_HOST=partners.mikephuketai.com`, `ADMIN_PUBLIC_HOST=admin.mikephuketai.com`, and `COMPOSE_PROFILES=tls`.
3. If migrating existing chats, import the full export into the production DB (see [DATABASE.md](DATABASE.md)):

   ```bash
   python scripts/verify_export.py mike_sessions_export.json
   python scripts/import_sessions.py mike_sessions_export.json
   ```

4. Stop the old in-memory process so Telegram is not polled twice.
5. Start the new stack:

   ```bash
   chmod +x scripts/deploy_production.sh
   ./scripts/deploy_production.sh
   ```

6. Verify: `/start` on the production bot, then `docker compose restart bot` and confirm history survives. After DNS is live, open `https://admin.mikephuketai.com/` and `https://partners.mikephuketai.com/`.
7. Create an Operator login once:

```bash
cd /opt/mike-phuket-ai/mike-ai-bot-hkt
docker compose run --rm bot python scripts/create_admin_user.py \
  --email you@example.com --password 'choose-a-strong-password'
```

## Day-to-day redeploy

After merging to `main` and pushing:

```bash
ssh root@YOUR_PRODUCTION_IP
cd /opt/mike-phuket-ai/mike-ai-bot-hkt
./scripts/deploy_production.sh
```

The script pulls `origin/main` with `--ff-only` and rebuilds. It exits if the Droplet is not on `main`.

| Task | Command |
|---|---|
| Redeploy from `main` | `./scripts/deploy_production.sh` |
| Admin UI | `https://admin.mikephuketai.com/` |
| Partner Dashboard / wrap | `https://partners.mikephuketai.com/` |
| Caddy logs | `docker compose --profile tls logs -f caddy` |
| View bot logs | `docker compose logs -f bot` |
| Restart bot | `docker compose restart bot` |
| Confirm branch on server | `git -C /opt/mike-phuket-ai branch --show-current` |
| Stop but keep DB data | `docker compose down` |
| Wipe DB and start fresh | `docker compose down -v` then `./scripts/deploy_production.sh` |

## Managed Postgres (optional)

When you outgrow container Postgres on the Droplet, follow [STAGING.md §9](STAGING.md) / [DATABASE.md](DATABASE.md): set `DATABASE_URL` in `.env`, drop or ignore the `db` service, and run `docker compose up -d --build bot`.

## Checklist before calling production “ready”

- [ ] Droplet checkout is `main` (`git branch --show-current`)
- [ ] Production Telegram bot responds to `/start`
- [ ] Messages survive `docker compose restart bot`
- [ ] Staging bot token is **not** in production `.env`
- [ ] Old in-memory bot process is stopped
- [ ] Firewall: SSH from your IP only; TCP 80/443 from the world; 8080/8081 closed
- [ ] `partners` and `admin` A records point at the **production** Droplet
- [ ] `https://partners.mikephuketai.com/` loads the Partner Dashboard
- [ ] `https://admin.mikephuketai.com/` loads Operator admin
- [ ] `POSTGRES_PASSWORD` is strong and not committed to git

## Troubleshooting

**`https://partners.mikephuketai.com` does not load**

1. `dig A partners.mikephuketai.com +short` must be the **production** Droplet IP (not staging `152.42.221.33`).
2. Production firewall inbound TCP **80** and **443** from `0.0.0.0/0`.
3. `docker compose --profile tls logs caddy` — Let’s Encrypt fails until the A record is correct.
4. Redeploy after DNS is live: `./scripts/deploy_production.sh`
