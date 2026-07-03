# Client Website

## Run locally

```bash
python main.py
```

## Deploy permanently

This app requires a Python host (Render, Railway, Heroku, DigitalOcean, Azure, etc.) that supports running Python web services. Typical settings:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn wsgi:app`

Connect your Git provider to the host and enable auto-deploys from `main` to publish updates automatically.

### Using Supabase (for Vercel or other serverless deployments)

This project can use a Postgres database instead of Excel files. To enable:

1. Create a Supabase project and note the Postgres connection string.
2. In GitHub repository Settings → Secrets → Actions, add `DATABASE_URL` with the connection string.
3. The app will auto-create required tables on startup via SQLAlchemy. You can deploy to Vercel only after moving storage (uploads, invoices) to object storage (Supabase Storage or S3).

Note: Switching to a DB requires configuring persistent storage for uploaded files. I can help migrate uploads and other data if you want.