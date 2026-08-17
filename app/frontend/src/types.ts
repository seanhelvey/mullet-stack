export interface Item {
  id: number;
  name: string;
  description: string | null;
  tags: string[];
  in_stock: boolean;
}
