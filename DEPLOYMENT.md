# Vercel deployment

The app uses SQLite locally when no database URL is configured. On Vercel, use a hosted PostgreSQL database; the app uses the `psycopg` driver and requires SSL for PostgreSQL URLs that do not specify an `sslmode`.

## Environment variables

Add these variables to the Vercel project for every environment you deploy:

- `DATABASE_URL`: the PostgreSQL connection URL from your database provider. Use the provider's pooled URL if it supplies one.
- `SECRET_KEY`: a long, random value used to sign Flask sessions. Keep it private and use a different value from local development.

The app also recognizes `POSTGRES_URL`, `POSTGRES_PRISMA_URL`, and `POSTGRES_URL_NON_POOLING` if `DATABASE_URL` is not set. Redeploy after changing environment variables.

## Database setup and existing data

On startup, the app creates any missing tables with SQLAlchemy. This is enough to initialize a new empty database, but it does not copy data from the local `instance/devdb.db` file or apply future schema changes. Moving existing users, courses, and other records requires a one-time data migration from SQLite to PostgreSQL. Back up the source database before doing that.

Profile images are currently written to Vercel's temporary `/tmp` storage. They are not durable across deployments or serverless instances; use persistent object storage for profile images before relying on production uploads.