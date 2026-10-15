/** Live search. The page waits 300 ms before it calls the API. */
import PropTypes from "prop-types";

export default function SearchBar({ value, onChange }) {
  return (
    <input
      type="search"
      value={value}
      onChange={(event) => onChange(event.target.value)}
      placeholder="Search products by name or category..."
      className="field mt-0"
      aria-label="Search products"
      maxLength={100}
    />
  );
}

SearchBar.propTypes = {
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
};
