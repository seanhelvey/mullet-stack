# The Mullet Stack

Business in the back, party in the front: a small zine comparing modern Python
and modern JavaScript, built around one tiny shared feature — fetching a list
of items — with a real FastAPI backend and a real React frontend behind every
snippet in the text.

Read the zine: [`zine/zine.md`](zine/zine.md) (or render it — see below).

## Layout

```
zine/           the zine itself, plus its pandoc build
app/backend/    FastAPI + Pydantic — GET /items
app/frontend/   React + TypeScript — fetches and renders it
```

## Running the app

**Backend** (needs [uv](https://docs.astral.sh/uv/)):

```bash
cd app/backend
uv sync
uv run fastapi dev        # http://localhost:8000, docs at /docs
uv run pytest -q
```

**Frontend** (needs Node 18+):

```bash
cd app/frontend
npm install
npm run dev                # http://localhost:5173
npm test
npm run build
```

Run both dev servers at once and the frontend at `:5173` will fetch its item
list live from the backend at `:8000`.

## Rendering the zine

Requires [pandoc](https://pandoc.org/installing.html):

```bash
cd zine
make html        # zine.html — clean, self-contained webpage
make pdf         # zine.pdf  — also needs a TeX engine (see Makefile)
```

## Why this repo exists

Personal interview prep, written to be honest about being personal interview
prep: a working refresher on the architectural choices under modern Python and
modern JavaScript, built by actually shipping the two of them together rather
than staging side-by-side syntax comparisons. Full framing is in the zine's
opening section.
