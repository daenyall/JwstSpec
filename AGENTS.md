# JwstSpec agent instructions

## Project and scientific scope
- Backend: Python/FastAPI in `backend/`; frontend: Next.js/TypeScript in `frontend/`.
- Explore public JWST NIRISS/SOSS transmission spectra. Read `README.md` before work.
- Preserve quality rejection, uncertainty metadata, time-system handling, units and bin definitions. Explain any change to scientific calculations and validate it with a relevant numerical example.
- This pipeline does not perform atmospheric retrieval or establish molecular detections. Keep UI and documentation claims within its actual capabilities.

## Working process
- Inspect the relevant code and existing instructions first. Keep changes scoped to the requested result.
- Read `frontend/AGENTS.md` and installed Next.js documentation before frontend implementation.
- Use a task branch. Report the diff and actual checks; distinguish completed checks from checks blocked by dependencies or network access.
- Run available baseline checks before substantive changes. Do not rewrite tests to hide regressions.
- Report source revision and setup details with results. Passing these few unit tests is not validation of the complete scientific pipeline.

## Verification commands
From the repository root, with backend development dependencies installed:
```bash
PYTHONPATH=backend python -m pytest backend/tests -q
```
The runtime requirements do not currently include pytest; install it in the development environment.
For frontend checks:
```bash
cd frontend
npm ci
npm run lint
npx next typegen
npx tsc --noEmit
```
Run `npm run build` when changes affect deployment or build behavior. Next.js generates `LayoutProps` during type generation; generate these types before checking TypeScript in a clean checkout.

## Data and integrations
- Unit checks should use synthetic or small local fixtures. Do not trigger large MAST downloads as a routine test.
- Avoid committing FITS downloads, caches, credentials, local environments or node_modules. Some generated files are already tracked; ignore rules alone do not untrack them.
- Treat MAST/NASA responses as external data, with explicit failures and timeouts.
- Before proposing hosting, account for dataset size, peak memory, analysis duration, concurrent requests and durable cache requirements.
- Document required environment variables without embedding credentials.
