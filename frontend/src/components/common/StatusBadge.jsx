/** PAID is Placed. Any other payment status is On hold. */
import PropTypes from "prop-types";

export default function StatusBadge({ status }) {
  const placed = status === "PAID";
  return (
    <p className={`text-sm font-medium ${placed ? "text-blue-700" : "text-red-700"}`}>
      {placed ? "Placed" : "On hold"}
    </p>
  );
}

StatusBadge.propTypes = {
  status: PropTypes.string,
};
