# Repository Guidelines

## Project Structure & Module Organization
- `frontend/`: React 18 + Vite client with `src/components`, `src/pages`, and `src/types`.
- `backend/`: FastAPI app for local development; entry `app/api/main.py`, services in `app/services`, schemas in `app/core`.
- `lambda/`: Production Lambda handlers (e.g., `puzzle-register/`) reusing backend services; align dependencies with `uv.lock`.
- `terraform/`: AWS IaC, `modules/` reusable blocks, `environments/` per stage; run plans from the target environment folder.
- `docs/`, `images/`, and `scripts/` store documentation, assets, and deployment helpers; tests sit in `backend/tests`.

## Build, Test, and Development Commands
- `uv sync` to install Python deps; `uv run uvicorn app.api.main:app --reload` (from `backend/`) starts the API on :8000.
- `uv run pytest` runs backend tests; add `--cov=backend --cov-report=term-missing` when checking coverage.
- `uv run python scripts/sync_config.py backend` creates `backend/.env.local` with localhost defaults; pass `--environment dev` to mirror AWS dev settings.
- `uv run python scripts/sync_config.py frontend` generates `frontend/.env.local` pointing to localhost; add `--environment dev` (or staging/prod) to pull values from SSM.
- `npm install` then `npm run dev` (inside `frontend/`) launches the Vite dev server on :5173; `npm run build` emits the production bundle, `npm run lint` applies ESLint.
- For infra, `cd terraform/environments/<env>` and run `terraform init`, `terraform plan`, `terraform apply`; ship Lambda changes with `./scripts/deploy-lambda.sh`.

## Coding Style & Naming Conventions
- Python uses Black/Ruff (line length 100, 4-space indents); keep modules/functions `snake_case`, classes `PascalCase`, and annotate public interfaces.
- Concentrate FastAPI routers under `app/api/routes` and reusable helpers in `app/services`.
- TypeScript components stay PascalCase (`PuzzleUploader.tsx`); hooks are `useThing.ts`; favor explicit `Props` interfaces and place API clients in `src/services`.

## Testing Guidelines
- Backend tests belong in `backend/tests` with `test_*.py` files, `Test*` classes, and fixtures in `conftest.py`; pair async endpoints with `pytest-asyncio` and isolate AWS clients via `moto` or `pytest-mock`.
- Frontend currently relies on manual checks; if you add automated tests, prefer colocated `*.spec.tsx` files using Vitest + Testing Library and record outcomes in PRs.

## Commit & Pull Request Guidelines
- Write concise, imperative commit messages similar to the existing history (`CORS認証の修正`, `backendカバレッジ測定`); keep each commit focused on one change.
- PRs should describe the motivation, list executed checks (`uv run pytest`, `npm run lint`, manual smoke), highlight config or Terraform impacts, and include UI screenshots when relevant.

## Environment & Configuration Tips
- Export AWS variables (`AWS_REGION`, `S3_BUCKET_NAME`, etc.) before running the backend and never commit secrets or `.env` files.
- Backend・Frontend config values live in SSM under `/<project>/(backend|frontend)/<env>/`; local work uses the default sync commands (localhost設定)、`--environment dev` などを指定するとAWS値を取得できます。CI/CDは同じパラメータを使って値を注入します。
- Keep Lambda and backend dependencies aligned by regenerating lockfiles with `uv sync`, ensure Terraform state stays in the configured remote backend, and run `terraform fmt` before commits.
