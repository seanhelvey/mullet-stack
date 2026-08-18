---
title: "The Mullet Stack"
subtitle: "JavaScript in the front, Python in the back."
author: "Sean Helvey"
date: "Accurate as of August 2026. Dependencies will have drifted by the time you read this"
---

# Why this exists

It is so easy to generate a ton of code these days, but we still need to
understand both low level syntax and higher level trade-offs between different
libraries and frameworks. I wanted to create a field guide to stay current on
modern full-stack web development with JavaScript and Python. Hence the mullet:
JavaScript in the front, Python in the back.

This project is not intended to be authoritative. I chose what seems like the
best combination of tools right now and tried to describe other options along
the way. My current full-time job is maintaining a Django app with a jQuery
front-end, so this is just me exploring and learning in public.

React and TypeScript have matured a lot in the last couple of years. Python's
web frameworks have evolved too, and we will focus on FastAPI with Pydantic for
this project. Each of their type systems implements the same `Item` in a
slightly different way. What is the best way to bring these two technologies
together into one stack?

The snippets ahead are windows into the repo rather than a build-along, so the
fastest way to follow is to clone it, start both servers, and poke at the files
as you read. It is a backend that returns a list of items, and a frontend that
fetches it. The example code is in this repo (`app/backend`, `app/frontend`).
Feedback is welcome!

---

# 1. Setting up

Before either side does anything interesting, get the smallest possible version
of each running side by side. Nothing shared yet, no wiring, just "hello" on two
different ports.

**Backend.** Python projects declare dependencies in `pyproject.toml`:

```toml
# pyproject.toml
[project]
name = "mullet-backend"
requires-python = ">=3.12"
dependencies = [
    "fastapi[standard]>=0.115",
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
approach, although async hasn't fully landed in Django at this point. Flask is
the older minimal approach, close to FastAPI in spirit but without real async
I/O (its `async def` views still run through a thread pool) and without type
hints doing double duty as validation and OpenAPI docs. Django Ninja splits the
difference, putting FastAPI-style async and typed routes on top of Django's ORM
and admin. Worth knowing they exist, not worth a detour here.
///

/// aside | A tangent: async on both sides
Every I/O call in Node's event loop is async out of the box. Python added async
later, and the seam between sync and async code runs through the whole
ecosystem. FastAPI sits right on it: routes can be `def` or `async def`, and
putting blocking work in an `async def` handler stalls the event loop for every
other request the process is serving, not just that one.

The GIL is the other half of that story, keeping multi-threaded Python off more
than one core at a time. Free-threaded builds landed experimentally in 3.13 and
became officially supported in 3.14, which is what this repo runs on, so that
may not stay true for long.
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

<figure class="diagram diagram--wide">
<svg viewBox="0 0 640 232" role="img" aria-label="A timeline of one request. TypeScript checks during the build and is then erased. Pydantic checks on the server while the request is handled. When the response reaches the browser, nothing checks it at all.">
<defs>
<marker id="tip2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
<polygon points="0,0 10,5 0,10" fill="currentColor"/>
</marker>
</defs>
<line x1="20" y1="128" x2="612" y2="128" stroke="currentColor" stroke-width="2" marker-end="url(#tip2)"/>
<line x1="216" y1="120" x2="216" y2="136" stroke="currentColor" stroke-width="2"/>
<line x1="412" y1="120" x2="412" y2="136" stroke="currentColor" stroke-width="2"/>
<path d="M 28 96 L 28 76 L 208 76 L 208 96" fill="none" stroke="currentColor" stroke-width="2"/>
<text x="118" y="45" text-anchor="middle" font-size="15">TypeScript</text>
<text x="118" y="64" text-anchor="middle" font-size="13">checks, then erases</text>
<path d="M 224 96 L 224 76 L 404 76 L 404 96" fill="none" stroke="currentColor" stroke-width="2"/>
<text x="314" y="45" text-anchor="middle" font-size="15">Pydantic</text>
<text x="314" y="64" text-anchor="middle" font-size="13">checks every response</text>
<path d="M 420 96 L 420 76 L 600 76 L 600 96" fill="none" stroke="var(--party)" stroke-width="2" stroke-dasharray="5 4"/>
<text x="510" y="45" text-anchor="middle" font-size="15" fill="var(--party)">nothing</text>
<text x="510" y="64" text-anchor="middle" font-size="13" fill="var(--party)">nothing left to check</text>
<text x="118" y="158" text-anchor="middle" font-size="15">build time</text>
<text x="118" y="177" text-anchor="middle" font-size="13">npm run build</text>
<text x="314" y="158" text-anchor="middle" font-size="15">server handles it</text>
<text x="314" y="177" text-anchor="middle" font-size="13">GET /items</text>
<text x="510" y="158" text-anchor="middle" font-size="15">browser receives it</text>
<text x="510" y="177" text-anchor="middle" font-size="13">response.json()</text>
</svg>
<figcaption>Each type system guards one end of the request and neither covers the far side.</figcaption>
</figure>

/// aside | The road not taken: Vue and Svelte
Vue's single-file components or Svelte's compiler-driven approach would express
this same list with noticeably less boilerplate than React's hooks.
///

/// aside | The elephant: Next.js
It's the more common starting point than plain Vite (build tool) + React these
days, so it deserves a footnote. Next.js is React plus a framework's worth of
opinions: file-based routing, and server components that fetch `/items` during
render on the server instead of from `useEffect` in the browser. If you want
full-stack JavaScript this is currently the default.
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

Now back to the `Item` question. There is one in `models.py` and one in
`types.ts`, describing the same thing. Keep two copies by hand and nothing
anywhere checks they still agree: rename a field on the backend and the frontend
compiles happily, then breaks later, in a browser, on someone else's machine.

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

<figure class="diagram">
<svg viewBox="0 0 400 344" role="img" aria-label="The Item shape starts in the Pydantic model, is dumped to an OpenAPI schema, generated into TypeScript types, and consumed by the React component. Only the first and last files are written by hand.">
<defs>
<marker id="tip" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
<polygon points="0,0 10,5 0,10" fill="currentColor"/>
</marker>
</defs>
<rect x="20" y="8" width="210" height="54" fill="none" stroke="currentColor" stroke-width="2"/>
<text x="125" y="31" text-anchor="middle" font-size="13">app/models.py</text>
<text x="125" y="49" text-anchor="middle" font-size="11">class Item(BaseModel)</text>
<line x1="125" y1="62" x2="125" y2="92" stroke="currentColor" stroke-width="2" marker-end="url(#tip)"/>
<text x="240" y="81" font-size="11">dump_openapi.py</text>
<rect x="20" y="98" width="210" height="42" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="5 4"/>
<text x="125" y="125" text-anchor="middle" font-size="13">openapi.json</text>
<line x1="125" y1="140" x2="125" y2="170" stroke="currentColor" stroke-width="2" marker-end="url(#tip)"/>
<text x="240" y="159" font-size="11">openapi-typescript</text>
<rect x="20" y="176" width="210" height="42" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="5 4"/>
<text x="125" y="203" text-anchor="middle" font-size="13">src/api-types.ts</text>
<line x1="125" y1="218" x2="125" y2="248" stroke="currentColor" stroke-width="2" marker-end="url(#tip)"/>
<text x="240" y="237" font-size="11">re-exported by types.ts</text>
<rect x="20" y="254" width="210" height="54" fill="none" stroke="currentColor" stroke-width="2"/>
<text x="125" y="277" text-anchor="middle" font-size="13">src/ItemList.tsx</text>
<text x="125" y="295" text-anchor="middle" font-size="11">useState&lt;Item[]&gt;</text>
<line x1="20" y1="328" x2="50" y2="328" stroke="currentColor" stroke-width="2"/>
<text x="57" y="332" font-size="11">written by hand</text>
<line x1="170" y1="328" x2="200" y2="328" stroke="currentColor" stroke-width="2" stroke-dasharray="5 4"/>
<text x="207" y="332" font-size="11">generated</text>
</svg>
<figcaption>The shape is authored once, in Python. Everything downstream is derived from it.</figcaption>
</figure>

`types.ts` is now three lines that re-export the generated `Item`, and CI fails
if either file is stale. The two type systems are now working together
automatically: Python defines the shape, TypeScript derives it.

Switching over immediately caught a mistake in the version we had been keeping
by hand. It said `description: string | null`, required. The generated one says
`description?:`, optional, because the schema never promises the field will be
there. Small, but exactly the kind of thing that drifts unnoticed.

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
the most downloaded and the one with a settled major version.

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

HTMX skips the JSON API entirely and transfers HTML fragments over the wire
instead of JSON, which is out of scope here.
///

/// aside | One thing codegen still cannot do
Generated types agree with the schema, but they are erased before the code runs,
so nothing checks the response itself. If the server ever sends data that does
not match its own schema, a fully typed client accepts it without complaint. Zod
at the fetch boundary is a tool for this that I am not yet familiar with.
///

---

# 6. Conclusion

When I started this project I was most curious to see a juxtaposition of the
differences in syntax, tooling, and ecosystems across modern JavaScript and
Python. I figured FastAPI with Pydantic and React with TypeScript were the
obvious picks, but wasn't quite sure how they'd fit together. I learned that
their annotations look almost identical but do very different jobs.

TypeScript's get checked everywhere while you build, then stripped out before
anything runs. Python's do nothing on their own. Pydantic is what makes them
real, and it checks at runtime, at the edge of the API. FastAPI publishes a
schema, and the frontend can derive types based on that at build time.

So: yes, these two languages work well from front to back today --- like a
mullet! React and FastAPI are a good pairing, and the thing that actually makes
it feel like one stack instead of two is generating the frontend's types from
the backend's schema instead of typing them twice.

Thoughts, corrections, questions, suggestions are all welcome. Please feel free
to reach out.