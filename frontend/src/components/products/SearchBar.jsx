/** Live search. The page waits 300 ms before it calls the API. */
import PropTypes from "prop-types";

export default function SearchBar({ value, onChange }) {
  return (
    <div className="search-bar">
      <svg
        viewBox="0 0 24 24"
        className="h-5 w-5 shrink-0 text-neutral-700"
        aria-hidden="true"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-3.8-3.8" strokeLinecap="round" />
      </svg>
      <input
        type="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Search products by name or category..."
        className="search-bar__input"
        aria-label="Search products"
        maxLength={100}
      />
      {value ? (
        <button type="button" className="search-bar__clear" onClick={() => onChange("")} aria-label="Clear search">
          Clear
        </button>
      ) : null}
    </div>
  );
}

SearchBar.propTypes = {
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
};
