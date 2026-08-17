# The Mullet Stack

JavaScript in the front, Python in the back — a zine built by shipping one tiny
feature (fetching a list of items) across both, with a real FastAPI backend and
a real React frontend behind every snippet in the text.

## Read the zine

Three ways, all zero-setup:

- **[📖 Read it online](https://seanhelvey.github.io/mullet-stack/zine/zine.html)**
  — the designed version, no clone required. Want a PDF or a paper copy? Print
  it (Ctrl/Cmd+P → Save as PDF); it has a print stylesheet, so it comes out
  looking like a zine rather than a screenshot of a webpage.
- **From a clone** — open [`zine/zine.html`](zine/zine.html). It's committed to
  the repo, so it's there the moment you clone: one self-contained file, no
  build, no server, no dependencies.
- **On GitHub** — [`zine/zine.md`](zine/zine.md) is the source and reads fine
  as plain Markdown. The only thing GitHub can't render is the `/// aside`
  sidebars, which show up as literal `///` markers; they're proper boxes in
  `zine.html`.

Everything else below is optional extra credit, not required reading.

## Layout

```
zine/
  zine.md             the zine, in Markdown (the source of truth)
  zine.html           the same zine, readable in a browser and printable
  build.py            renders zine.md + style.css -> one self-contained zine.html
  check_snippets.py   fails if a snippet drifts from the file it names
  style.css           the riso-fanzine look: screen, dark, and paper
  fonts/              display face, subset and embedded (SIL OFL, license included)
app/backend/          FastAPI + Pydantic — GET /items
app/frontend/         React + TypeScript — fetches and renders it
```

CI runs both test suites, type-checks and builds the frontend, verifies every
snippet in the zine still matches the source file it names, and fails if the
committed `zine.html` is stale.

## Running the app

**Backend** (needs [uv](https://docs.astral.sh/uv/)):

```bash
cd app/backend
uv sync
uv run fastapi dev        # http://localhost:8000, docs at /docs
uv run pytest -q
```

**Frontend** (needs Node 20.19+ or 22.12+ — see `.nvmrc`; Vite 8 won't start on
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

## Rebuilding the zine

Only needed if you edit `zine.md` or `style.css`. One command, no setup:

```bash
uv run --locked zine/build.py
```

`build.py` declares its own dependencies inline ([PEP 723](https://peps.python.org/pep-0723/)),
so `uv` fetches Markdown, PyMdown Extensions and Pygments into a throwaway
environment on the fly — nothing to install, no virtualenv to activate, nothing
added to your system. The script inlines the stylesheet, the syntax-highlighting
theme and the display font, so the output stays a single portable file you can
email, host anywhere, or print.

Writing an aside — the boxes taped into the margins — looks like this:

```markdown
/// aside | The road not taken: Django
Django would be the batteries-included alternative here.
///
```

## License

Code is [MIT](LICENSE); the zine's text is CC BY 4.0. The embedded display font
is Lato, under the SIL OFL — see [`zine/fonts/`](zine/fonts/).

## Why this repo exists

Interview prep, but not only that:

- **Architectural tradeoffs.** Agentic tools produce a FastAPI route or a React
  component in seconds, and it's easy to stop noticing why the generated code
  looks the way it does. Building one feature by hand on both sides keeps those
  decisions visible.
- **Current conventions.** Writing it down forces a pass over what's actually
  current rather than what we picked up years ago.
- **Something to print.** It renders to a zine we can read on a piece of paper,
  away from a screen.

Full framing is in the zine's opening section.
