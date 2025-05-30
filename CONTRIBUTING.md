# Contributing to Vetting Intelligence Search Hub

## Development Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in required values
3. Run with Docker: `docker compose up --build`

## Project Structure

- `backend/` - FastAPI application
  - `app/adapters/` - Data source adapters
  - `app/routers/` - API endpoints
  - `tests/` - Unit tests
- `frontend/` - Next.js application
  - `pages/` - React pages
  - `components/` - Reusable components
  - `styles/` - CSS files

## Adding a New Data Source

1. Create adapter in `backend/app/adapters/`
2. Add tests in `backend/tests/`
3. Update search router to call new adapter
4. Update frontend to display new source results

## Code Style

- Python: Follow PEP 8
- JavaScript: Use Prettier/ESLint
- Commit messages: Use conventional commits

## Testing

- Backend: `pytest`
- Frontend: `npm test`
- Integration: `docker compose up` and manual testing

## Pull Requests

1. Create feature branch
2. Add tests for new functionality
3. Ensure CI passes
4. Request review 