---
title: "The Mullet Stack"
subtitle: "A working refresher on modern Python and modern JavaScript, built by shipping one feature across both"
author: "Sean Helvey"
date: "Accurate as of August 2026 — dependencies will have drifted by the time you read this"
---

# Why this exists

I'm prepping for interviews, and the thing I keep losing track of isn't syntax —
it's the architecture underneath it. Agentic tools now generate a FastAPI route or
a React component in seconds, which is great, except it means I can go a long time
without consciously deciding *why* the generated code looks the way it does, or
what the alternative would have been. This zine is me forcing that decision back
into view, one small feature at a time.

It is not a Python-vs-JavaScript showdown. That ground is well-trodden and mostly
a waste of pixels. Instead: build one tiny real feature — a backend that returns a
list of items, and a frontend that fetches and renders it — properly on both sides,
and let the actual differences surface where they're real instead of manufacturing
them for symmetry. Python and React aren't competing answers to the same question.
They're two different layers of one pipeline, built by two ecosystems that grew up
solving different problems. Hence the mullet: JavaScript in the front, Python in
the back.

I'm still learning both of these out loud. If a take here is wrong or shallow,
that's the working-refresher framing doing its job — better to write down what I
currently believe and be correctable than to perform authority I don't have.

The whole thing is backed by a real, small, running app in this repo
(`app/backend`, `app/frontend`) — every snippet below is lifted from code that
actually runs and passes its tests, occasionally trimmed to the lines under
discussion, never invented for the page.

---

# 1. Setting up

Before either side does anything interesting, get the smallest possible version of
each running side by side. Nothing shared yet, no wiring — just "hello" on two
different ports.

**Backend.** Python projects declare dependencies in `pyproject.toml`:

```toml
[project]
name = "mullet-backend"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
]
```

```bash
uv sync                    # resolves and installs into a local .venv
uv run fastapi dev         # serves on :8000, reloads on save
```

**Frontend.** JavaScript projects declare theirs in `package.json`:

```json
{
  "dependencies": { "react": "^19.2.8", "react-dom": "^19.2.8" },
  "devDependencies": { "vite": "^8.2.1", "typescript": "^5.9.3", "vitest": "^4.1.10" }
}
```

```bash
npm install                # resolves and installs into node_modules
npm run dev                # serves on :5173, reloads on save
```

Two commands, two dev servers, nothing talking to each other yet. Point a browser
at `:8000/docs` and `:5173` and you have two blank slates.

**A packaging note, since I'm doing this live anyway.** `uv sync` and `npm install`
look like the same step, but the resolvers underneath make different bets. npm
resolves a deep, often-duplicated tree of transitive dependencies and — by
default — lets any package in that tree run arbitrary code at install time via
`postinstall` scripts. That's a real, frequently-exploited supply-chain surface;
it's why `npm audit` exists and why lockfile review matters more than it looks
like it should. Python's wheel format sidesteps most of that: a wheel is
pre-built, and installing one just copies files — no code runs. The exposure
moves earlier, to whoever built the wheel, not to everyone who installs it. uv
writes a lockfile (`uv.lock`) the same way `package-lock.json` does, so both
ecosystems now default to reproducible installs — that convergence is recent
history, not something either language shipped with originally. Where they still
differ is trust model, not reproducibility: PyPI package names are a flat global
namespace with no scoping, same as npm's unscoped packages, so typosquatting risk
exists on both sides and neither has fully solved it.

---

# 2. Backend: FastAPI + Pydantic

This is Python's whole job in this build: define the shape of an item, and serve
a list of them.

```python
# app/models.py
from pydantic import BaseModel


class Item(BaseModel):
    id: int
    name: str
    description: str | None = None
    tags: list[str] = []
    in_stock: bool = True
```

```python
# app/main.py
from fastapi import FastAPI
from app.models import Item

app = FastAPI(title="mullet-stack backend")

ITEMS = [
    Item(id=1, name="Enamel mug", tags=["kitchen", "camping"]),
    Item(id=2, name="Field notebook", description="Grid pages, pocket-sized", tags=["stationery"]),
    Item(id=3, name="Multitool", tags=["hardware"], in_stock=False),
]


@app.get("/items", response_model=list[Item])
def list_items() -> list[Item]:
    return ITEMS
```

`uv run fastapi dev` and `curl localhost:8000/items` gets back a JSON array. So
does a browser at `localhost:8000/docs` — FastAPI reads the type hints on `Item`
and the route signature and generates an interactive OpenAPI page from them,
without a separate schema file to keep in sync.

The thing worth naming here, because the code makes it concrete instead of
abstract: Python's type hints are not enforced by the interpreter. Write the
same annotation on a plain class and nothing stops you at runtime —

```python
class Plain:
    def __init__(self, id: int):
        self.id = id

Plain(id="not a number").id    # 'not a number', no complaint
```

— because hints are documentation and a hook for external tools like mypy or
pyright, checked before the code ever runs, not while it runs.

Pydantic is what closes that gap. `Item` carries the identical annotations, but
because it's a `BaseModel` those annotations became a runtime contract:
`Item(id="not a number", name="x")` raises `ValidationError` on the spot. Same
hints, same syntax, completely different enforcement — and the difference is a
library you chose to import, not anything the language did for you.

Worth being precise about where that contract actually sits on this endpoint,
though, because it's easy to overclaim. `GET /items` takes no request body, so
there's nothing incoming for Pydantic to reject — throw a malformed payload at
it and you'll get a cheerful `200`, because the handler never asked for input.
`response_model=list[Item]` guards the way *out*: it validates what the handler
returns. The 422-on-bad-input story everyone tells about FastAPI is real, but it
belongs to endpoints that declare a request body or typed query params. This one
doesn't. That's very in character for Python's gradual-typing story: types are
always optional, and how much they *do* depends entirely on what you bring in to
enforce them — and on where you actually wired it in.

/// aside | The road not taken: Django
If this were a full CRUD app with an admin panel and an ORM expected out of the
box, Django would be the batteries-included alternative to FastAPI's
minimal-core-plus-libraries approach — worth knowing it exists, not worth a
detour here.
///

---

# 3. Frontend: React + TypeScript

This is JavaScript's whole job: fetch that list and render it.

```typescript
// src/types.ts
export interface Item {
  id: number;
  name: string;
  description: string | null;
  tags: string[];
  in_stock: boolean;
}
```

```tsx
// src/ItemList.tsx
import { useEffect, useState } from "react";
import type { Item } from "./types";

const API_URL = "http://localhost:8000/items";

export function ItemList() {
  const [items, setItems] = useState<Item[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(API_URL)
      .then((response) => {
        if (!response.ok) throw new Error(`Request failed: ${response.status}`);
        return response.json();
      })
      .then((data: Item[]) => setItems(data))
      .catch((err: Error) => setError(err.message));
  }, []);

  if (error) return <p role="alert">Couldn't load items: {error}</p>;

  return (
    <ul>
      {items.map((item) => (
        <li key={item.id}>
          <strong>{item.name}</strong>
          {!item.in_stock && " (out of stock)"}
        </li>
      ))}
    </ul>
  );
}
```

Put `Item` from `types.ts` next to `Item` from `models.py` and the real
difference isn't the syntax — it's what kind of typing each one is. Pydantic's
`Item` is a class: two Python objects are only interchangeable if one is
actually built as (or subclasses) that class. TypeScript's `Item` is an
interface describing a *shape*: anything with the right fields satisfies it,
whether or not it ever heard of the name `Item`. That's structural typing —
TypeScript checks what an object has, not what it claims to be — and it's the
default posture of the whole language, not a special case for interfaces.

The sharper asymmetry, though, is what happens to each of these at runtime:
nothing, on the TypeScript side. `npm run build` strips every type annotation
on its way to plain JavaScript — by the time this code runs in a browser, `Item`
doesn't exist anymore in any form the running program can check against. If the
backend's `/items` response silently drifts from this shape, TypeScript will not
notice, because TypeScript never sees production traffic; it only ever saw the
code once, at build time. Pydantic, on the previous page, does the opposite: it
keeps its type information around specifically so it can enforce it while the
program is running. Same-looking type declaration, two completely different
lifetimes.

/// aside | The road not taken: Vue and Svelte
Vue's single-file components or Svelte's compiler-driven approach would express
this same list with noticeably less boilerplate than React's hooks — worth
knowing they exist if `useEffect` ever starts to feel like the tax rather than
the tool.
///

/// aside | The elephant: Next.js
It's the more common starting point than plain Vite + React these days, so it
deserves naming rather than a footnote. Next.js is React plus a framework's
worth of opinions — file-based routing, and server components that fetch
`/items` during render on the server instead of from `useEffect` in the
browser.

That last part quietly erases the boundary this zine draws in the next
section, because the "client" fetching the data is now Next's own server, not
a stranger's browser. Which is exactly why it's out of scope here: this zine
is about the seam between two separate processes, and Next.js's whole pitch is
blurring that seam. Worth knowing what it's blurring before you reach for it.
///

---

# 4. Connecting: REST vs GraphQL

Here's the one place in this build with a genuine either/or, so it's the one
place a real "vs" section earns its keep.

What's actually wired up, in `ItemList.tsx` above, is REST: a plain `GET
/items` returning the full list, fetched with the browser's native `fetch`.
For a single flat resource like this, that's the right, boring choice — but
it's worth being honest about why, and where it stops being the right choice.

First, though, the thing that actually breaks before any of that becomes
relevant. Wire the two dev servers together exactly as written above and the
request fails — not on the shape of the data, on permission to ask for it at
all. `:5173` and `:8000` are different origins, so the browser refuses to hand
the response to my JavaScript unless the server explicitly says that origin is
allowed. The fix is four lines the backend section quietly skipped over:

```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
)
```

That's worth more than a troubleshooting footnote, because it's this zine's
whole thesis compressed into one error message. `curl localhost:8000/items`
works and always did — curl has no origin, no other tabs, nobody to protect. The
identical request from a browser is refused, because a browser is executing code
from strangers next to my logged-in sessions, and same-origin policy is the rule
that keeps one tab from reading another's data. Nothing about the data changed.
The *caller* changed, and the caller's threat model came with it. Business in
the back, party in the front: the party is the part where untrusted code runs on
someone else's machine, and this is the bouncer.

With that out of the way, the actual REST-versus-GraphQL tradeoffs.

**Over/under-fetching.** REST's `Item` response ships every field —
`description`, `tags`, `in_stock` — whether the component uses all of them or
just `name`. A view that only needs the name still pays for the rest of the
payload. GraphQL flips this: the client sends a query naming exactly the fields
it wants, and the server returns exactly that shape, no more. That matters more
as payloads and screens multiply — for one list of three items, it's not a real
cost yet.

**Nested data and the N+1 problem.** If each item eventually had a related
resource — a claim history, a set of reviews — REST typically means either a
second round trip per item (classic N+1: one request for the list, one more per
item for its detail) or a bespoke, list-specific endpoint that pre-joins the
data server-side. GraphQL lets the client ask for `items { name, reviews { rating } }`
in a single request and have the server resolve the nesting. That's a genuine
advantage — but it's not free: naive GraphQL resolvers can silently reintroduce
the exact same N+1 problem one level down, and the standard fix (batching
resolvers with something like DataLoader) is itself a piece of backend
architecture you now own.

**Caching.** REST's biggest quiet advantage: `GET /items` is a stable URL, so
the entire HTTP caching machinery — browser cache, `ETag`s, CDN edge caches —
works on it for free. GraphQL usually POSTs a single query document to a single
endpoint, which has no stable URL for that infrastructure to key on. Getting
comparable caching back means adopting a GraphQL-aware client (Apollo Client,
Relay) that builds its own normalized cache in memory, or adding persisted
queries — real solutions, but they're solving a problem REST didn't have in the
first place.

None of this makes GraphQL wrong — it makes it a trade against a specific kind
of complexity (nested, over-fetched, multi-consumer data) that this feature
doesn't have yet. For one endpoint returning one flat list to one frontend,
REST is the honest choice, not the naive one.

/// aside | The road not taken: HTMX
If neither side needs a client-rendered app at all — if the whole page could be
server-rendered and just swap in the new list — HTMX is worth a mention: it
gets you dynamic updates over plain HTTP without a JSON API or a frontend
framework in the loop at all.
///

---

# 5. Testing what we built

With a real feature running end to end, both sides get an actual test instead
of a toy one.

```python
# tests/test_items.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_items_returns_all_items():
    response = client.get("/items")
    assert response.status_code == 200

    items = response.json()
    assert len(items) == 3
    assert items[0]["name"] == "Enamel mug"


def test_list_items_matches_the_item_shape():
    response = client.get("/items")
    item = response.json()[0]

    assert set(item.keys()) == {"id", "name", "description", "tags", "in_stock"}
    assert isinstance(item["tags"], list)
```

```tsx
// tests/ItemList.test.tsx
import { render, screen } from "@testing-library/react";
import { ItemList } from "../src/ItemList";

const items = [
  { id: 1, name: "Enamel mug", description: null, tags: ["kitchen"], in_stock: true },
  { id: 2, name: "Multitool", description: null, tags: [], in_stock: false },
];

beforeEach(() => {
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve(items),
  } as unknown as Response);
});

test("renders a list item for each item returned by the API", async () => {
  render(<ItemList />);

  expect(await screen.findByText("Enamel mug")).toBeInTheDocument();
  expect(screen.getByText("Multitool")).toBeInTheDocument();
});
```

The runner on the JavaScript side is Vitest, which is worth a sentence of
justification since Jest is still the name most people reach for. This is a
Vite project, and Vitest reads the same `vite.config.ts` the dev server does —
one toolchain, one set of transform rules. Reaching for Jest instead means
installing a second transform pipeline (`ts-jest`, a JSDOM environment, its own
config) whose job is to re-derive what Vite already knows. The API is
Jest-compatible either way, so nothing below changes shape; what changes is how
many build systems you own.

Watching both get written back to back says more than any callout would. pytest
leans on the bare `assert` statement — `assert response.status_code == 200` —
and gets a readable failure message anyway, because pytest rewrites the
assertion at import time to capture the values on both sides of the comparison.
There's no special assertion API to learn. The JavaScript convention runs the
other way: `expect(x).toBeInTheDocument()`, chained matchers, one method per
kind of check. Part of why is structural — JS test runners don't have an
equivalent of pytest's import-time assertion rewriting, so the ecosystem built
expressiveness into chainable matcher objects instead of into the assert
statement itself.

The other thing that falls out of writing these side by side: mocking ships as
a first-class part of the runner — `vi.fn()` is just there, no import beyond
the runner itself (`jest.fn()` in Jest; same idea, same ergonomics). Python's
equivalent, `unittest.mock` (or `pytest-mock` on top of it), is a separate, more
deliberate affair — you reach for `Mock()` or `@patch` explicitly, and it feels
more like a tool you pick up than a feature the framework hands you by default.
Neither is better; it's just a different default about how much mocking
machinery a test file starts with for free.

---

# 6. What actually turned out to differ

Stepping back from the build: the differences that held up were not the ones
I'd have guessed going in from syntax alone.

**Typing.** Python's type hints are optional and unenforced by the interpreter
— they only became a runtime contract here because Pydantic chose to make them
one, at the specific boundary of the API. TypeScript's types are the opposite
shape: omnipresent at build time, then completely erased before the code ever
runs. One system chooses when to turn types into an enforced guarantee at all;
the other guarantees comprehensively and then guarantees nothing once the
program is actually running. Neither is strictly stronger — they're solving for
different moments in a program's life.

**Packaging and trust.** Both ecosystems converged on lockfiles and
reproducible installs; that part isn't a real difference anymore. What's still
different is where the risk sits: npm's install-time script execution puts
trust pressure on every dependency, every time you install, because arbitrary
code can run before your program does. Python's wheel format moves that
pressure upstream, to whoever built the wheel, and mostly spares the install
step itself. Different shape of the same underlying problem — you're trusting a
supply chain either way.

**Concurrency.** This is the one that actually surprised me. Node's event loop
is the only concurrency model it has ever had — every I/O call in the ecosystem
grew up async, because there was never a blocking version sitting next to it to
tempt anyone. Python's async support is bolted on by comparison: `async def`,
an event loop, and a real, load-bearing seam running through the entire
ecosystem between sync and async code, plus a GIL that keeps even
multi-threaded Python from running Python bytecode on more than one core at a
time. (That last part is finally in motion: free-threaded builds landed
experimentally in 3.13 and became officially supported in 3.14, which is what
this repo runs on. Not the default yet, and the ecosystem is still catching up,
but "Python has a GIL" is now a statement about which build you installed
rather than about the language.) FastAPI straddles that seam directly — it supports both `def` and `async
def` route handlers, and the failure mode is real: drop blocking, synchronous
work into an `async def` handler and it stalls the *entire* event loop for
every other request the process is serving, not just the one that made the
mistake. Node never gives you the footgun in the first place, because it never
gave you the synchronous option to reach for. That's not a small stylistic
difference — it's a different foundational assumption about what "running a
request handler" means.

Put together, the honest version of this zine's thesis is smaller than "Python
vs JavaScript": it's that a server process owning a database connection and a
browser tab owned by a stranger were never going to converge on the same
tradeoffs, no matter how similar `async` and `await` look sitting in each
language's syntax. The mullet isn't a joke about mismatched hair — it's an
accurate description of two environments doing genuinely different jobs, built
by two communities that optimized for the constraints they actually had. I
came in expecting to relearn syntax. I'm leaving with a clearer sense of why
the syntax ended up the way it did — which was the actual point.

I'll be wrong about some of this in a year. That's fine — that's what the
"accurate as of" on the cover is for.
