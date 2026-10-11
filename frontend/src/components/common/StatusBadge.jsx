/** Coloured status pill. */
import PropTypes from "prop-types";

const TONES = {
  Confirmed: "bg-blue-100 text-blue-800",
  Paid: "bg-blue-100 text-blue-800",
  "Pending Payment": "bg-yellow-100 text-yellow-900",
  "Payment Failed": "bg-red-100 text-red-800",
};

export default function StatusBadge({ status }) {
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${TONES[status] || "bg-neutral-100 text-neutral-700"}`}>
      {status}
    </span>
  );
}

StatusBadge.propTypes = {
  status: PropTypes.string.isRequired,
};
