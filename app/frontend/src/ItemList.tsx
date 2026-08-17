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
          {item.description && <p>{item.description}</p>}
        </li>
      ))}
    </ul>
  );
}
