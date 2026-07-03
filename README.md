# Client Website

## Run locally

```bash
python main.py
```

## Deploy permanently

This app needs a Python host such as Render.

### Render setup

1. Create a new Web Service from this GitHub repo.
2. Use the included `render.yaml` or set:
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn wsgi:app`
3. Leave auto-deploy enabled so pushes to `main` publish automatically.

The repo is public, so the hosted site can also be public.