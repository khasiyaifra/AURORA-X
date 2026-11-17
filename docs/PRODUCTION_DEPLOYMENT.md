# Production deployment

## Environment

Copy `backend/.env.example` to `backend/.env`. Set a strong `JWT_SECRET`, PostgreSQL `DATABASE_URL`, CORS origins and optional AI/translation credentials.

Never commit `.env` files or private upload directories.

## Database

Run migrations before starting the API:

```powershell
cd backend
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

PostgreSQL must be provisioned and tested against migrations and concurrent checkout before production use. Current automated verification uses SQLite.

## Frontend

Set `VITE_API_URL` for the deployed API and run:

```powershell
npm install
npm run build
npm run preview
```

## Health

- `/api/health`: process health
- `/api/ready`: database readiness

Configure load-balancer probes separately. Database backups and restore drills are mandatory before commerce deployment.

## PostgreSQL setup

Install PostgreSQL 16 or ensure Docker/PostgreSQL is available. Create a database and credentials, set `DATABASE_URL`, then run migrations and tests:

```powershell
docker compose up -d postgres
copy backend/.env.example backend/.env
# Replace development values and set DATABASE_URL to PostgreSQL.
cd backend
python -m alembic upgrade head
python -m pytest -q
```

PostgreSQL was not available to this environment, so the commands above are setup instructions until an actual PostgreSQL migration and concurrent checkout test is executed.

## Backup and restore

Use provider-managed snapshots or PostgreSQL `pg_dump`/`pg_restore`. Test restoration to a separate database before production:

```powershell
pg_dump -h localhost -U aurora -d aurora -Fc -f aurora.dump
pg_restore --clean --if-exists --no-owner -h localhost -U aurora -d aurora_restore aurora.dump
```

Never run restore against the live database without a staged verification and maintenance window.
