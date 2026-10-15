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
    <span className={`inline-block rounded-full px-2.5 py-1 text-xs font-semibold ${TONES[status] || "bg-slate-100 text-slate-700"}`}>
      {status}
    </span>
  );
}

StatusBadge.propTypes = {
  status: PropTypes.string.isRequired,
};
