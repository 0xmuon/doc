/** Live search. The page waits 300 ms before it calls the API. */
export default function SearchBar({ value, onChange }) {
  return (
    <input
      type="search"
      value={value}
      onChange={(event) => onChange(event.target.value)}
      placeholder="Search products by name or category..."
      className="w-full rounded border px-3 py-2"
      aria-label="Search products"
      maxLength={100}
    />
  );
}
