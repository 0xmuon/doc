/** Catalog calls. Search uses this API's name and category query. */
import { api } from "./client";

export function fetchCategories() {
  return api("/api/categories");
}

export function fetchProducts() {
  return api("/api/products");
}

export function searchProducts({ name, category }) {
  const params = new URLSearchParams();
  if (name) params.set("name", name);
  if (category) params.set("category", category);
  return api(`/api/products/search?${params}`);
}

export function fetchProduct(productId) {
  return api(`/api/products/${productId}`);
}
