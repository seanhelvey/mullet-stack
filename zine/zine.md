---
title: "The Mullet Stack"
subtitle: "JavaScript in the front, Python in the back."
author: "Sean Helvey"
date: "Accurate as of August 2026. Dependencies will have drifted by the time you read this"
---

# Why this exists

I wanted to create a field guide to stay current on modern full-stack web
development with JavaScript and Python. While it is so easy to generate a ton of
code these days, we still need to understand both low level syntax and higher
level trade-offs between different libraries and frameworks.

React and TypeScript have matured into something you can be productive in
without fighting the tooling, and the browser is still where users actually are.
Python has several great web frameworks and is widely used for AI. Hence the
mullet: JavaScript in the front, Python in the back.

We build one tiny real feature: a backend that returns a list of items, and a
frontend that fetches and renders it. Both ends describe the same `Item`, both
have a type system they're proud of, and neither one knows the other exists. How
they come together is the real story.

The example code is in this repo (`app/backend`, `app/frontend`). I'm a beginner
for life and feedback is welcome!

---

# 1. Setting up

Before either side does anything interesting, get the smallest possible version
of each running side by side. Nothing shared yet, no wiring, just "hello" on two
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

Two commands, two dev servers. Point a browser at `:8000/docs` and `:5173` and
you have the front and back ends.

**A packaging note.** `uv sync` and `npm install` look like the same step, but
npm ran arbitrary code at install time via lifecycle scripts until npm 12 turned
that off by default in July 2026, while Python wheels never did. Worth digging
deeper another time to learn more.

---

# 2. Backend: FastAPI + Pydantic

We use Python on the backend to define the shape and serve a list of items:

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

`uv run fastapi dev` and `localhost:8000/items` returns a JSON array. FastAPI
reads the type hints on `Item` and the route signature then generates an
interactive OpenAPI page from them at `localhost:8000/docs` without a separate
schema file to keep in sync.

Which is worth pausing on, because those hints do nothing by themselves.
Python's type hints are not enforced by the interpreter. Write the same
annotation on a plain class and nothing stops you at runtime:

```python
class Plain:
    def __init__(self, id: int):
        self.id = id

Plain(id="not a number").id    # 'not a number', no complaint
```

Hints are documentation and a hook for external tools like mypy or pyright,
checked before the code ever runs, not while it runs. Pydantic is what closes
that gap. `Item` carries the identical annotations, but because it's a
`BaseModel` those annotations became a runtime contract: `Item(id="not a
number", name="x")` raises `ValidationError` on the spot. Same hints, same
syntax, completely different enforcement.

But `GET /items` takes no request body, so there's nothing incoming for Pydantic
to reject. Send a malformed payload and you'll get a `200`, because the handler
never asked for input. `response_model=list[Item]` guards the way *out*: it
validates what the handler returns. FastAPI can help with input validation, but
only with endpoints that declare a request body or typed query params. That's
Python's gradual typing: annotations are always optional, and how much they *do*
depends entirely on what you bring in to enforce them.

/// aside | The roads not taken: Django, Flask, Ninja
Django is the batteries-included option: if you expect an admin panel and an ORM
out of the box, that's the trade against FastAPI's minimal-core-plus-libraries
approach. Flask is the older minimal one, close to FastAPI in spirit but without
the type hints doing double duty as validation and OpenAPI docs. Django Ninja
splits the difference, putting FastAPI-style typed routes on top of Django's ORM
and admin. Worth knowing they exist, not worth a detour here.
///

---

# 3. Frontend: React + TypeScript

We fetch that list and render it with JavaScript:

```typescript
// the Item the frontend works with, doc comments trimmed
Item: {
    id: number;
    name: string;
    description?: string | null;
    tags: string[];
    in_stock: boolean;
};
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

Compare that `Item` to `Item` from `models.py` above. The syntax is very
similar, but the kind of typing is much different. Pydantic's `Item` is a class:
two Python objects are only interchangeable if one is actually built as (or
subclasses) that class. TypeScript's `Item` is an interface describing a
*shape*: anything with the right fields satisfies it, whether or not it ever
heard of the name `Item`. That's structural typing: TypeScript checks what an
object has, not what it claims to be. It works that way generally, not just for
interfaces.

The bigger difference is what happens at runtime: nothing, on the TypeScript
side. `npm run build` strips every type annotation on its way to plain
JavaScript. By the time this code runs in a browser, `Item` doesn't exist
anymore in any form the running program can check against. If the backend's
`/items` response silently drifts from this shape, TypeScript will not notice,
because TypeScript never sees production traffic; it only ever saw the code
once, at build time. Pydantic does the opposite: it keeps its type information
around specifically so it can enforce it while the program is running.
Same-looking type declaration, two completely different lifetimes.

/// aside | The road not taken: Vue and Svelte
Vue's single-file components or Svelte's compiler-driven approach would express
this same list with noticeably less boilerplate than React's hooks.
///

/// aside | The elephant: Next.js
It's the more common starting point than plain Vite (build tool) + React these
days, so it deserves naming rather than a footnote. Next.js is React plus a
framework's worth of opinions: file-based routing, and server components that
fetch `/items` during render on the server instead of from `useEffect` in the
browser.
///

---

# 4. Testing what we built

Each side works on its own now, so both get a test before we wire them together:

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
import type { Item } from "../src/types";

const items: Item[] = [
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

We use Vitest over Jest here because it reads the same `vite.config.ts` the dev
server already uses. Jest would mean a second setup (`ts-jest`, a JSDOM
environment, its own config) doing work Vite is doing anyway. The API is nearly
identical either way, so the tests above would look the same in both.

Writing the two files back to back, two things stood out. pytest uses a plain
`assert` and still prints a useful failure message. JavaScript goes the other
way with chained matchers like `expect(x).toBeInTheDocument()`, a different
method for each kind of check. Also mocking is built into the JavaScript runner.
`vi.fn()` is just there. In Python you reach for `unittest.mock` and write
`Mock()` or `@patch` on purpose.

---

# 5. Connecting: where the types stop

First, the thing that breaks before anything else. `:5173` and `:8000` are
different origins, so the browser will not hand the response to our JavaScript
unless the server says that origin is allowed:

```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
)
```

Now the `Item` question. There is one in `models.py` and one in `types.ts`,
describing the same thing. Keep two copies by hand and nothing anywhere checks
they still agree: rename a field on the backend and the frontend compiles
happily, then breaks later, in a browser, on someone else's machine.

But FastAPI publishes that contract already. Every route feeds an OpenAPI
document, generated from the same Pydantic model:

```json
"in_stock": { "type": "boolean", "default": true, "title": "In Stock" }
```

So a hand-written `types.ts` is a copy of a machine-readable file we already
have. Instead the backend dumps that file and the frontend generates from it:

```bash
uv run python scripts/dump_openapi.py    # backend, writes openapi.json
npm run generate:types                   # frontend, writes src/api-types.ts
```

`types.ts` is now three lines that re-export the generated `Item`, and CI fails
if either file is stale. The two type systems are one type system with a
direction: Python defines the shape, TypeScript derives it.

Switching over immediately caught a mistake in the version we had been keeping
by hand. It said `description: string | null`, required. The schema says
`description?:`, optional, because the field has a default. Small, but exactly
the kind of thing that drifts unnoticed.

There are a few tools for this, and they differ mostly in how much they hand
you. Weekly downloads and versions as of August 2026:

| tool                 | downloads | version | what you get                    |
| -------------------- | --------- | ------- | ------------------------------- |
| `openapi-typescript` | 5.4M      | 7.13.0  | types only                      |
| `@hey-api/openapi-ts`| 3.6M      | 0.99.0  | types and a generated client    |
| `orval`              | 1.6M      | 8.24.0  | client, React Query, mocks, Zod |

FastAPI's own docs point at Hey API, which is worth knowing even though it is
still pre-1.0. We went with `openapi-typescript` because the fetch call above
was already written and only the types were missing, and it happens to be both
the most downloaded and the one with a settled major version. If the frontend
were bigger, generating the client too would probably win.

That closes the gap I started with. The two declarations cannot drift apart
anymore, because only one of them is written by a person.

/// aside | The roads not taken: GraphQL, tRPC, HTMX
GraphQL makes the schema the contract by design, so clients generate types from
it the same way. It is a bigger change than a build step, and worth it for
different reasons: several clients wanting different shapes of one dataset, or
data that is really a graph. Not for a longer list. Adoption peaked near 40%
around 2021 and has settled closer to 25%, while REST still shows up in 70% of
job listings.

tRPC removes the boundary instead of describing it, but only works if both ends
are TypeScript, which rules it out here.

HTMX skips the JSON API entirely and swaps in server-rendered HTML, which makes
the whole question disappear.
///

/// aside | One thing codegen still cannot do
Generated types agree with the schema, but they are erased before the code runs,
so nothing checks the response itself. If the server ever sends data that does
not match its own schema, a fully typed client accepts it without complaint. Zod
at the fetch boundary is the usual answer. Not the same problem as drift, and
not something I needed here.
///

---

# 6. Conclusion

Both sides have annotations that look almost identical and do different jobs.
Python's do nothing on their own. Pydantic is what makes them real, and it
checks at runtime, at the edge of the API. TypeScript's get checked everywhere
while you build, then stripped out before anything runs.

That difference is what lets the two ends agree. Pydantic's types are real
enough to describe, so FastAPI publishes a schema from the back, and the front
derives its types from it and checks them at build time. Python defines the
shape, TypeScript derives it.

If I keep one thing from building this, it's that the annotations are the easy
part. What matters is what enforces them, and when.

/// aside | Off to one side: concurrency
Not part of the thread above, but the difference I found most surprising. Node's
event loop is the only model it has ever had, so every I/O call in the ecosystem
grew up async. Python added async later, and the seam between sync and async
code runs through the whole ecosystem. FastAPI sits right on it: routes can be
`def` or `async def`, and putting blocking work in an `async def` handler stalls
the event loop for every other request the process is serving, not just that
one.

The GIL is the other half of that story, keeping multi-threaded Python off more
than one core at a time. Free-threaded builds landed experimentally in 3.13 and
became officially supported in 3.14, which is what this repo runs on, so that
may not stay true for long.
///