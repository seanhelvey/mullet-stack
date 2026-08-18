# The Mullet Stack

JavaScript in the front, Python in the back. A short field guide built by
shipping one tiny feature (fetching a list of items) across both, with a real
FastAPI backend and a real React frontend behind every snippet in the text.

## Read it

Three ways, all zero-setup:

- **[📖 Read it online](https://seanhelvey.github.io/mullet-stack/guide/)** is
  the designed version, no clone required.
- **From a clone.** Open [`guide/index.html`](guide/index.html). It's committed
  to the repo, so it's there the moment you clone: one self-contained file, no
  build, no server, no dependencies.
- **On GitHub.** [`guide/index.md`](guide/index.md) is the source and reads fine
  as plain Markdown. The only thing GitHub can't render is the `/// aside`
  sidebars, which show up as literal `///` markers; they're proper boxes in
  `index.html`.

Everything else below is optional extra credit, not required reading.

## Layout

```
guide/
  index.md            the source of truth, in Markdown
  index.html          the rendered page, committed so a clone is readable
  build.py            renders index.md + style.css -> one self-contained file
  check_snippets.py   fails if a snippet drifts from the file it names
  style.css           the look, in light and dark
  fonts/              display face, subset and embedded (SIL OFL, license included)
app/backend/          FastAPI + Pydantic, serving GET /items
  openapi.json        the schema, dumped from the app
  scripts/            dump_openapi.py writes that file
app/frontend/         React + TypeScript, fetches and renders it
  src/api-types.ts    generated from openapi.json, not hand-written
```

The frontend's types are generated from the backend's schema rather than typed
twice. Python defines the shape, TypeScript derives it.

CI runs both test suites, type-checks and builds the frontend, and fails if any
generated file is stale: `openapi.json`, `src/api-types.ts`, or `index.html`. It
also verifies every snippet still matches the source file it names.

## Running the app

**Backend** (needs [uv](https://docs.astral.sh/uv/)):

```bash
cd app/backend
uv sync
uv run fastapi dev        # http://localhost:8000, docs at /docs
uv run pytest -q
```

**Frontend** (needs Node 20.19+ or 22.12+, see `.nvmrc`; Vite 8 won't start on
older ones):

```bash
cd app/frontend
npm install
npm run dev                # http://localhost:5173
npm test                   # vitest
npm run build              # type-checks, then builds
```

Run both dev servers at once and the frontend at `:5173` will fetch its item
list live from the backend at `:8000`.

**After changing a model or a route**, regenerate the contract so the two ends
stay in step. CI fails if you forget:

```bash
cd app/backend  && uv run python scripts/dump_openapi.py   # -> openapi.json
cd app/frontend && npm run generate:types                  # -> src/api-types.ts
```

## Rebuilding the page

Only needed if you edit `index.md` or `style.css`. One command, no setup:

```bash
uv run --locked guide/build.py
```

`build.py` declares its own dependencies inline ([PEP 723](https://peps.python.org/pep-0723/)),
so `uv` fetches Markdown, PyMdown Extensions and Pygments into a throwaway
environment on the fly. Nothing to install, no virtualenv to activate, nothing
added to your system. The script inlines the stylesheet, the syntax-highlighting
theme and the display font, so the output stays a single portable file you can
email, host anywhere, or print.

Writing an aside, the boxes set off from the main text, looks like this:

```markdown
/// aside | The road not taken: Django
Django would be the batteries-included alternative here.
///
```

## License

Code is [MIT](LICENSE); the prose is CC BY 4.0. The embedded display font is
Lato, under the SIL OFL, see [`guide/fonts/`](guide/fonts/).

## Why this repo exists

Interview prep, but not only that:

- **Architectural tradeoffs.** Agentic tools produce a FastAPI route or a React
  component in seconds, and it's easy to stop noticing why the generated code
  looks the way it does. Building one feature by hand on both sides keeps those
  decisions visible.
- **Current conventions.** Writing it down forces a pass over what's actually
  current rather than what we picked up years ago.

Full framing is in the opening section.
