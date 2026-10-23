# Production on DigitalOcean (self-managed)

Production runs Docker Compose (bot + Postgres) from the **`main` Git branch only**.

Production does not deploy on push. Merge `staging` into `main`, wait until the **pytest** check is green, then run [`.github/workflows/deploy-production.yml`](../../.github/workflows/deploy-production.yml) by hand from `main`. The workflow refuses any other ref. A second run waits until the first one finishes.

The workflow runs pytest again, builds the images on the GitHub runner, copies them to the production Droplet, and starts `/opt/mike-phuket-ai`. It keeps the Droplet `.env` at `mike-ai-bot-hkt/.env`.

If admin `/api/stats` is not 401, partner `/r/missing-token` is not 404, or the Mini App `/` is not 200 on localhost, the Droplet points the image tags back at the previous release and starts that release again. The GitHub job stays red. Image rollback does not restore the database. Public HTTPS staying down does not roll back.

Keep `db/schema.sql` additive. A `DROP`, a `NOT NULL` column with no default, or a rewrite of existing rows can make the previous image crash after the new one has already applied the schema. Deploy that kind of change by hand on the Droplet. That path does not retag `:previous`.

Every deploy recreates the containers, so the Telegram bot restarts for a short time. The first successful image deploy has no `:previous` tags, so a failed first boot cannot roll back.

## What you get

| Component | Where it runs |
|---|---|
| Telegram bot (polling) | Docker container `bot` |
| PostgreSQL 16 | Docker container `db` (volume-backed), or managed Postgres |
| Schema migration | Automatic on bot start (`SessionStore.create`) |
| Partner Dashboard | `https://partners.mikephuketai.com/` (Caddy → `partner-web`) |
| Operator admin | `https://admin.mikephuketai.com/` (Caddy → `admin-web`) |
| Mini App | `https://app.mikephuketai.com/` (Caddy → `tma-web`) |
| Deploy source | Git branch `main` only, manual GitHub Actions run |

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

Use a **separate** DigitalOcean firewall from staging. Attach it only to the production Droplet.

| Inbound | Protocol | Port | Sources |
|---|---|---|---|
| SSH | TCP | 22 | `0.0.0.0/0` (key-only auth; required for GitHub Actions) |
| HTTP | TCP | 80 | `0.0.0.0/0` (Let’s Encrypt challenge + redirect to HTTPS) |
| HTTPS | TCP | 443 | `0.0.0.0/0` (`partners`, `admin`, and `app`) |

Do **not** open **5432**, **8080**, **8081**, or **8082**. Caddy serves the sites on 443. Use a new deploy key for this Droplet. Do not reuse the staging key or a personal key.

GitHub-hosted runners have no stable IP. A firewall that allows SSH only from your home IP will accept a laptop login and still reject the workflow.

## Domain (`mikephuketai.com`)

The apex is already in DigitalOcean DNS (same zone as staging). Add **production** A records that point at the **production** Droplet — not `152.42.221.33` (staging).

| Type | Hostname | Will direct to |
|---|---|---|
| **A** | `partners` | **production** Droplet |
| **A** | `admin` | **production** Droplet |
| **A** | `app` | **production** Droplet |

Leave `@` and `www` empty unless you add a marketing site later. Keep `partners-staging` / `admin-staging` on the staging Droplet.

Check (replace with the production IP you see in DigitalOcean):

```bash
dig A partners.mikephuketai.com +short
dig A admin.mikephuketai.com +short
dig A app.mikephuketai.com +short
```

Each must be the production Droplet IPv4. Then Caddy can obtain certificates.

Partner Users: `https://partners.mikephuketai.com/`  
Operators: `https://admin.mikephuketai.com/`  
Mini App: `https://app.mikephuketai.com/`

## GitHub Actions secrets

Do this on your Mac. The production Droplet only receives the public half of a key that your Mac creates. GitHub later receives the private half. Leave the staging host, `STAGING_SSH_KEY`, and the staging bot token as they are.

You need the production address and user you already use to log in, for example `ssh root@203.0.113.10`. Replace `USER` and `HOST` below with those two values.

### 1. Create the key on the Mac

```bash
cd ~
ssh-keygen -t ed25519 -f production_deploy -C "github-actions-production" -N ""
```

`-N ""` means the key has no passphrase. GitHub Actions cannot type a passphrase.

### 2. Install the public key on the Droplet, still from the Mac

```bash
ssh-copy-id -i ~/production_deploy.pub USER@HOST
```

### 3. Prove the new key opens the Droplet

```bash
ssh -i ~/production_deploy -o IdentitiesOnly=yes USER@HOST
```

You should get a shell on the Droplet. Type `exit` to return to the Mac.

### 4. Save repository secrets

Open [the Actions secrets page](https://github.com/ShilovaIra/mike-phuket-ai/settings/secrets/actions). These are repository secrets. Environment secrets are invisible to the workflow.

| Name | Value |
|---|---|
| `PRODUCTION_HOST` | The Droplet IP or hostname only. No `ssh://` and no `user@`. |
| `PRODUCTION_SSH_USER` | The same `USER` you just logged in as, such as `root`. |
| `PRODUCTION_SSH_KEY` | The whole private file. On the Mac run `pbcopy < ~/production_deploy`, then paste into the secret. |
| `PRODUCTION_SSH_PORT` | Only if SSH is not on port 22. Otherwise skip this secret. |

After the private key is saved, clear it from the clipboard with `pbcopy < /dev/null`. Never commit the private key.

## Branch protection

The workflow file does not block a direct push. After **pytest** has run once on a pull request into `main`:

1. Settings → Branches → Add a rule for `main`.
2. Require a pull request before merging.
3. Require status checks to pass, and select `pytest`.
4. Do not allow force pushes.

Turn that on after the first green `pytest` run. Requiring a check that has never run blocks every merge.

## Run a deploy

Actions → **Deploy production** → **Run workflow** → Branch: **main**.

The Droplet `.env` must already be the production one. The workflow preserves it and the script refuses to start when it is missing.

## First-time cutover (from old in-memory bot)

1. Merge `staging` into `main` and push `origin/main`.
2. On the Droplet: checkout `main`, copy `.env.production.example` → `.env`, fill **production** secrets. Keep `PARTNER_PUBLIC_HOST=partners.mikephuketai.com`, `ADMIN_PUBLIC_HOST=admin.mikephuketai.com`, `TMA_PUBLIC_HOST=app.mikephuketai.com`, and `COMPOSE_PROFILES=tls`.
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

## Dynamic assets (Spaces)

Same setup as [STAGING.md → Dynamic assets](STAGING.md), with a **separate** production bucket (e.g. `mike-phuket-prod-spaces`), CDN subdomain `cdn`, and a Limited Access key scoped to that bucket only. Fill the `S3_*` block in the production `.env`, then after the first deploy with logo uploads:

```bash
docker compose exec bot python scripts/migrate_partner_logos.py
```

## Hand deploy

On the Droplet, from a `main` checkout, including a schema change the previous image cannot boot:

```bash
cd /opt/mike-phuket-ai/mike-ai-bot-hkt
./scripts/deploy_production.sh
```

That path pulls `origin/main`, adds 1GB of swap if needed, repairs DNS, and builds one image at a time. It does not retag `:previous`. It exits if the checkout is not `main`.

After a healthy Actions deploy, the workflow runs `git fetch origin main` and `git reset --hard origin/main`, so this script can fast-forward. `.env` is gitignored and stays. A failed Actions release does not move `HEAD`.

## Day-to-day redeploy

Merge to `main`, wait for pytest, then run **Deploy production** from `main`.

| Task | Command |
|---|---|
| Redeploy from `main` | Actions → **Deploy production**, or `./scripts/deploy_production.sh` on the Droplet |
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
- [ ] `S3_*` point at the **production** bucket and key; `scripts/migrate_partner_logos.py` has run
- [ ] Old in-memory bot process is stopped
- [ ] Firewall: SSH from `0.0.0.0/0` with key-only auth; TCP 80/443 from the world; 5432, 8080, 8081, and 8082 closed
- [ ] GitHub Actions secrets set (`PRODUCTION_HOST`, `PRODUCTION_SSH_USER`, `PRODUCTION_SSH_KEY`)
- [ ] `partners`, `admin`, and `app` A records point at the **production** Droplet
- [ ] `https://partners.mikephuketai.com/` loads the Partner Dashboard
- [ ] `https://admin.mikephuketai.com/` loads Operator admin
- [ ] `https://app.mikephuketai.com/` loads the Mini App
- [ ] `POSTGRES_PASSWORD` is strong and not committed to git

## Troubleshooting

**`https://partners.mikephuketai.com` does not load**

1. `dig A partners.mikephuketai.com +short` must be the **production** Droplet IP (not staging `152.42.221.33`).
2. Production firewall inbound TCP **80** and **443** from `0.0.0.0/0`.
3. `docker compose --profile tls logs caddy` — Let’s Encrypt fails until the A record is correct.
4. Redeploy after DNS is live: Actions → **Deploy production**, or `./scripts/deploy_production.sh` on the Droplet.
