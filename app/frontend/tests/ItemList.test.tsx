import { render, screen } from "@testing-library/react";
import { ItemList } from "../src/ItemList";

const items = [
  { id: 1, name: "Enamel mug", description: null, tags: ["kitchen"], in_stock: true },
  { id: 2, name: "Multitool", description: null, tags: [], in_stock: false },
];

beforeEach(() => {
  globalThis.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve(items),
  }) as jest.Mock;
});

test("renders a list item for each item returned by the API", async () => {
  render(<ItemList />);

  expect(await screen.findByText("Enamel mug")).toBeInTheDocument();
  expect(screen.getByText("Multitool")).toBeInTheDocument();
});

test("flags items that are out of stock", async () => {
  render(<ItemList />);

  const multitool = await screen.findByText("Multitool");
  expect(multitool.closest("li")).toHaveTextContent("(out of stock)");
});

test("shows an error message when the request fails", async () => {
  globalThis.fetch = jest.fn().mockResolvedValue({ ok: false, status: 500 }) as jest.Mock;

  render(<ItemList />);

  expect(await screen.findByRole("alert")).toHaveTextContent("Couldn't load items");
});
