# Staging on DigitalOcean (self-managed)

This guide sets up a **private staging environment** on DigitalOcean: one small VPS running Docker Compose (bot + Postgres). No customer involvement — use a separate Telegram bot and your own API keys.

**Branch rule:** staging deploys from the `staging` branch only. Do not run `main` or feature branches on this Droplet. Use `scripts/deploy_staging.sh` — it refuses to deploy if the checkout is not `staging`.

## What you get

| Component | Where it runs |
|---|---|
| Telegram bot (polling) | Docker container `bot` |
| PostgreSQL 16 | Docker container `db` (volume-backed) |
| Schema migration | Automatic on bot start (`SessionStore.create`) |
| Partner Dashboard | `https://partners-staging.mikephuketai.com/` (Caddy → `partner-web`) |
| Operator admin | `https://admin-staging.mikephuketai.com/` (Caddy → `admin-web`) |
| Mini App (v2) | `https://app-staging.mikephuketai.com/` (Caddy → `tma-web`) |
| Deploy source | Git branch `staging` only |

Postgres is **not** exposed to the internet — only the bot container talks to it on the internal Docker network.

---

## 1. Prerequisites (local)

- [DigitalOcean](https://www.digitalocean.com) account
- SSH key on your machine (`~/.ssh/id_ed25519.pub` or similar)
- A **staging** Telegram bot from [@BotFather](https://t.me/BotFather) (do not use production)
- OpenAI API key
- Your Telegram user ID for `ADMIN_CHAT_ID` (message [@userinfobot](https://t.me/userinfobot) or use `/myid` once the bot is up)

---

## 2. Create the Droplet

1. DigitalOcean → **Create** → **Droplets**
2. **Image:** Ubuntu 24.04 LTS
3. **Plan:** Basic → Regular → **$6/mo** (1 GB RAM) is enough for staging; use $12/mo if you plan heavy import/testing
4. **Region:** Singapore (`sgp1`) — closest to Phuket / Thailand
5. **Authentication:** SSH keys (recommended). Add your public key if not already on the account
6. **Hostname:** e.g. `mike-staging`
7. Create Droplet

Note the public IP (e.g. `164.92.x.x`).

### Firewall (recommended)

DigitalOcean → **Networking** → **Firewalls** → Create:

| Inbound | Protocol | Port | Sources |
|---|---|---|---|
| SSH | TCP | 22 | `0.0.0.0/0` (key-only auth; required for GitHub Actions deploy) |
| HTTP | TCP | 80 | `0.0.0.0/0` (Let’s Encrypt challenge + redirect to HTTPS) |
| HTTPS | TCP | 443 | `0.0.0.0/0` (`partners-staging`, `admin-staging`, `app-staging`) |

Attach the firewall to the droplet. Do **not** open **5432**, **8080**, **8081**, or **8082** — Caddy serves the sites on 443. The bot still uses outbound polling to Telegram.

### Domain (`mikephuketai.com`)

DigitalOcean DNS for `mikephuketai.com` (after the registrar uses DigitalOcean nameservers):

| Type | Hostname | Will direct to |
|---|---|---|
| **A** | `partners-staging` | staging Droplet (`152.42.221.33`) |
| **A** | `admin-staging` | staging Droplet |
| **A** | `app-staging` | staging Droplet |

Leave `@` and `www` empty. Production uses `partners` / `admin` on the production Droplet — see [PRODUCTION.md](PRODUCTION.md).

At the registrar set nameservers to `ns1.digitalocean.com`, `ns2.digitalocean.com`, `ns3.digitalocean.com`. Check:

```bash
dig NS mikephuketai.com +short
dig A partners-staging.mikephuketai.com +short
dig A admin-staging.mikephuketai.com +short
dig A app-staging.mikephuketai.com +short
```

Those A records must be the staging Droplet IP. Then Caddy can obtain certificates.

Production hostnames (`partners.` / `admin.`) are documented in [PRODUCTION.md](PRODUCTION.md).

Use **SSH key authentication only** (disable password login). Broad SSH source is needed so GitHub-hosted runners can reach the Droplet; do not reuse personal keys for CI — see [CI/CD auto-deploy](#cicd-auto-deploy) below.

---

## 3. Install Docker on the Droplet

SSH in:

```bash
ssh root@YOUR_DROPLET_IP
```

Install Docker (official convenience script):

```bash
apt-get update
apt-get install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sh
```

Verify:

```bash
docker --version
docker compose version
```

Optional: deploy as a non-root user — add them to the `docker` group:

```bash
adduser deploy
usermod -aG docker deploy
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy
```

---

## 4. Deploy the application (staging branch only)

### Option A — Clone from Git (recommended)

On the droplet, clone **only** the `staging` branch:

```bash
cd /opt
git clone --branch staging --single-branch \
  git@github.com:ShilovaIra/mike-phuket-ai.git
cd mike-phuket-ai

# Confirm branch
git branch --show-current   # must print: staging
```

If the repo is private, add a deploy SSH key on the Droplet and register it as a GitHub deploy key (read-only) for this repo.

### Option B — Copy from your laptop (one-off)

Only if Git clone is not ready yet. Prefer Option A so redeploys stay on `staging`.

```bash
# From your machine, while on the staging branch:
git checkout staging
rsync -avz --exclude .venv --exclude .env \
  /path/to/mike-phuket-ai/ \
  root@YOUR_DROPLET_IP:/opt/mike-phuket-ai/
```

### Configure environment

On the droplet:

```bash
cd /opt/mike-phuket-ai/mike-ai-bot-hkt
cp .env.staging.example .env
nano .env                 # fill tokens and POSTGRES_PASSWORD
```

Generate a strong Postgres password:

```bash
openssl rand -base64 32
```

### Dynamic assets (DigitalOcean Spaces)

Partner logos uploaded in the admin panel live in a Spaces bucket, not in the image. Mike's own logos and interface pictures stay bundled in the repo.

1. **Spaces Object Storage → Create Bucket** in `sgp1` (staging: `mike-phuket-staging-spaces`).
2. Bucket **Settings → CDN**: enable, add custom subdomain `cdn-staging` (enter only the subdomain; DigitalOcean appends `.mikephuketai.com`).
3. **Spaces Object Storage → Access Keys → Create Access Key**: *Limited Access*, this bucket only, Read/Write/Delete. Copy the secret now — it is shown once.
4. Fill the `S3_*` block in `.env` on the Droplet. Never put the key in `.env.*.example` files (they are committed).

Check from your laptop (uses your local `.env`):

```bash
python scripts/s3_smoke_test.py      # upload → fetch via CDN → delete
```

After the first deploy with logo uploads, move the bundled partner logos into the bucket and set the `tmp/` cleanup rule (safe to re-run):

```bash
docker compose exec bot python scripts/migrate_partner_logos.py
```

---

## 5. Start staging

```bash
cd /opt/mike-phuket-ai/mike-ai-bot-hkt
chmod +x scripts/deploy_staging.sh
./scripts/deploy_staging.sh
```

First-time equivalent without the script:

```bash
# must already be on staging
docker compose up -d --build
```

Check logs:

```bash
docker compose logs -f bot
```

You should see `Mike Phuket AI запущен...` and `Бот работает`.

Verify Postgres:

```bash
docker compose exec db psql -U mike -d mike -c '\dt'
```

Expected tables: `users`, `identities`, `conversations`, `messages`, `leads`, `webhook_events`.

---

## 6. Test the bot

1. Open your **staging** bot in Telegram
2. Send `/start` — should get the welcome keyboard
3. Send a few messages — history should persist across restarts:

   ```bash
   docker compose restart bot
   ```

4. Send `/reset` — new conversation thread
5. Trigger a lead flow (real-estate questions) if you want to test `leads` + admin notification

### Inspect data

```bash
docker compose exec db psql -U mike -d mike -c \
  "SELECT count(*) FROM users; SELECT count(*) FROM messages;"
```

---

## 7. Seed staging with half of a production export (one-time)

Use this **once** when establishing staging. Export JSON contains real chat data — it is **gitignored** and must never be committed.

### On your laptop

```bash
# From repo root — writes a half-sized file (also gitignored):
cd mike-ai-bot-hkt
python scripts/seed_staging_sessions.py \
  ../mike_sessions_export.json \
  --write-subset ../mike_sessions_export_staging.json

scp ../mike_sessions_export_staging.json \
  root@YOUR_DROPLET_IP:/opt/mike-phuket-ai/mike-ai-bot-hkt/
```

### On the Droplet (fresh DB only)

```bash
cd /opt/mike-phuket-ai/mike-ai-bot-hkt

# Optional pre-check:
docker compose run --rm bot python scripts/verify_export.py mike_sessions_export_staging.json

# One-shot seed: imports the file as-is (already half). Refuses if users exist.
# Mount the host JSON into the container (compose image has no bind of the app dir).
docker compose run --rm \
  -v "$PWD/mike_sessions_export_staging.json:/app/mike_sessions_export_staging.json:ro" \
  bot python scripts/seed_staging_sessions.py \
  --fraction 1 \
  mike_sessions_export_staging.json
```

If you scp the **full** export instead, keep the default half cut:

```bash
docker compose run --rm bot python scripts/seed_staging_sessions.py \
  mike_sessions_export.json
```

Confirm:

```bash
docker compose exec db psql -U mike -d mike -c \
  "SELECT count(*) AS users FROM users; SELECT count(*) AS messages FROM messages;"
```

Delete the JSON from the Droplet when done:

```bash
rm -f mike_sessions_export*.json
```

---

## 8. Day-to-day operations

### CI/CD auto-deploy

Push or merge to the **`staging`** branch runs [`.github/workflows/deploy-staging.yml`](../../.github/workflows/deploy-staging.yml). The workflow copies the tree, loads images, and runs `deploy_staging.sh` (bot, admin-api, admin-web, partner-web, Caddy). It then verifies the admin UI on port **8080**. You can also trigger it manually: GitHub → **Actions** → **Deploy staging** → **Run workflow**.

**First-time admin panel setup on the Droplet**

1. Ensure `.env` includes `ADMIN_JWT_SECRET`, `PARTNER_PUBLIC_HOST=partners-staging.mikephuketai.com`, `ADMIN_PUBLIC_HOST=admin-staging.mikephuketai.com`, `TMA_PUBLIC_HOST=app-staging.mikephuketai.com`, and `COMPOSE_PROFILES=tls`.
2. Firewall: TCP **80** + **443** to the world; do not open 8080/8081 (see [Firewall](#firewall-recommended)). `deploy_staging.sh` sets `PARTNER_OFFER_BASE_URL=https://partners-staging.mikephuketai.com` when it is empty or still an `http://IP:port` value.
3. After deploy, create an admin user once:

```bash
cd /opt/mike-phuket-ai/mike-ai-bot-hkt
docker compose run --rm bot python scripts/create_admin_user.py \
  --email you@example.com --password 'choose-a-strong-password'
```

4. Open `https://admin-staging.mikephuketai.com/` (operators) and `https://partners-staging.mikephuketai.com/` (Partner Users) after DNS is live.

**One-time setup**

1. On your laptop, generate a dedicated deploy key (do not reuse your personal SSH key):

```bash
ssh-keygen -t ed25519 -C "github-actions-staging-deploy" -f ./staging_deploy_key -N ""
```

2. On the Droplet, append the **public** key to the deploy user’s `authorized_keys` (e.g. `root` or `deploy`):

```bash
# from your laptop
ssh root@YOUR_DROPLET_IP "mkdir -p ~/.ssh && chmod 700 ~/.ssh"
cat staging_deploy_key.pub | ssh root@YOUR_DROPLET_IP "cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

3. In the GitHub repo → **Settings** → **Secrets and variables** → **Actions**, add:

| Secret | Value |
|---|---|
| `STAGING_HOST` | Droplet IP or hostname |
| `STAGING_SSH_USER` | `root` or `deploy` |
| `STAGING_SSH_KEY` | Full contents of `staging_deploy_key` (private key) |
| `STAGING_SSH_PORT` | Optional; defaults to `22` if unset |

4. Confirm the DigitalOcean firewall allows SSH from `0.0.0.0/0` with key-only auth (see [Firewall](#firewall-recommended)).

5. Delete the local key files after storing the private key in GitHub (`rm staging_deploy_key staging_deploy_key.pub`), or keep them only in a password manager.

**Failures:** open the failed run under **Actions** for SSH/script logs. On the Droplet, `docker compose logs -f bot admin-api admin-web` shows startup issues after a successful SSH deploy.

### Manual redeploy (fallback)

```bash
ssh root@YOUR_DROPLET_IP
cd /opt/mike-phuket-ai/mike-ai-bot-hkt
./scripts/deploy_staging.sh
```

That script pulls `origin/staging` with `--ff-only` and rebuilds. It exits with an error if the Droplet is not on `staging`.

| Task | Command |
|---|---|
| Auto-deploy | Push/merge to `staging` (or Actions → Run workflow) |
| Manual redeploy from `staging` | `./scripts/deploy_staging.sh` |
| Admin UI | `https://admin-staging.mikephuketai.com/` |
| Partner Dashboard / wrap | `https://partners-staging.mikephuketai.com/` (`/r/…` counts Referral Clicks) |
| Mini App | `https://app-staging.mikephuketai.com/` |
| Caddy logs | `docker compose --profile tls logs -f caddy` |
| View bot logs | `docker compose logs -f bot` |
| View admin API logs | `docker compose logs -f admin-api` |
| Restart bot | `docker compose restart bot` |
| Restart admin stack | `docker compose restart admin-api admin-web` |
| Confirm branch on server | `git -C /opt/mike-phuket-ai branch --show-current` |
| Stop everything | `docker compose down` |
| Stop but keep DB data | `docker compose down` (volume `postgres_data` persists) |
| Wipe DB and start fresh | `docker compose down -v` then `./scripts/deploy_staging.sh` |

### Run tests against staging DB (from laptop)

Temporarily expose Postgres only if needed — **not recommended on a public droplet**. Prefer running tests locally with `TEST_DATABASE_URL` or SSH tunnel:

```bash
ssh -L 5433:localhost:5432 root@YOUR_DROPLET_IP
# On droplet, temporarily publish 5432 in compose — or exec tests inside the network:
docker compose run --rm -e TEST_DATABASE_URL=postgresql://mike:PASSWORD@db:5432/mike_test bot pytest
```

(Create `mike_test` DB manually if you want isolated test DB on staging.)

---

## 9. Upgrading to Managed Postgres (later)

When you outgrow container Postgres:

1. DigitalOcean → **Databases** → Create **PostgreSQL 16** cluster (same region as droplet)
2. Add the droplet IP to **Trusted sources**
3. Remove the `db` service from `docker-compose.yml` (or never start it)
4. Set `DATABASE_URL` in `.env` to the managed connection string (DigitalOcean provides `postgresql://...`)
5. `docker compose up -d --build bot`

Schema still applies automatically on bot start.

---

## 10. Checklist before calling staging “ready”

- [ ] Droplet checkout is `staging` (`git branch --show-current`)
- [ ] Staging Telegram bot responds to `/start`
- [ ] Messages survive `docker compose restart bot`
- [ ] `\dt` shows all six tables
- [ ] One-time half-export seed run (section 7) — or skipped intentionally
- [ ] `leads` row created when lead flow completes (if tested)
- [ ] Production bot token is **not** in staging `.env`
- [ ] Firewall allows SSH from `0.0.0.0/0` with key-only auth (for GitHub Actions)
- [ ] GitHub Actions secrets set (`STAGING_HOST`, `STAGING_SSH_USER`, `STAGING_SSH_KEY`)
- [ ] Push to `staging` triggers a green **Deploy staging** workflow
- [ ] `partners-staging`, `admin-staging`, and `app-staging` A records point at the staging Droplet
- [ ] Firewall allows TCP 80/443 from the world; 8080, 8081, and 8082 closed
- [ ] `https://partners-staging.mikephuketai.com/` loads the Partner Dashboard
- [ ] `https://admin-staging.mikephuketai.com/` loads Operator admin
- [ ] `https://app-staging.mikephuketai.com/` loads the Mini App
- [ ] `POSTGRES_PASSWORD` is strong and not committed to git
- [ ] `mike_sessions_export*.json` deleted from Droplet and never committed

---

## Troubleshooting

**Bot exits immediately**

```bash
docker compose logs bot
```

Usually missing `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, or `POSTGRES_PASSWORD`.

**`database does not exist`**

Ensure `POSTGRES_DB=mike` matches `DATABASE_URL` and recreate volume if needed: `docker compose down -v`.

**Two bots with same token**

Telegram allows only one active poller per token. Staging must use its own bot from BotFather.

**Out of memory on $6 droplet**

During `docker compose up --build`, if OOM: upgrade to 2 GB or build locally and push an image to DO Container Registry (advanced).

**`https://partners-staging.mikephuketai.com` does not load**

1. `dig A partners-staging.mikephuketai.com +short` and `dig A admin-staging.mikephuketai.com +short` must be the Droplet IP.
2. Firewall inbound TCP **80** and **443** from `0.0.0.0/0`.
3. `docker compose --profile tls logs caddy` — Let’s Encrypt fails until the A record is correct.
4. Redeploy after DNS is live so Caddy retries: `./scripts/deploy_staging.sh`
