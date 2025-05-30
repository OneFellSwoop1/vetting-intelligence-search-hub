# Vetting Intelligence Search Hub – Backend

This is the FastAPI backend for the Vetting Intelligence Search Hub.

## Setup

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
# App runs at http://localhost:8000
```

## Features
- Async endpoints for harmonised search
- Adapters for 6+ public data sources
- Redis caching
- Unit tests with pytest

## Testing

```bash
pytest
```

---
See root README for full-stack instructions. 