/** One order in a history list. An optional detail line is for extra text such as the payment method. */
import PropTypes from "prop-types";
import { Link } from "react-router-dom";
import StatusBadge from "../common/StatusBadge";
import { statusLabels } from "../../utils/statusLabels";
import { inr } from "../../utils/money";

export default function OrderListItem({ order, detail }) {
  return (
    <li className="rounded border border-rose-100 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="font-medium">{order.order_number}</p>
          <p className="text-sm text-neutral-600">{new Date(order.order_date).toLocaleString()}</p>
          {detail ? <p className="text-sm">{detail}</p> : null}
          <p className="text-sm">Total {inr(order.total_amount)}</p>
          <div className="mt-1 flex flex-wrap gap-2">
            {statusLabels(order).map((label) => (
              <StatusBadge key={label} status={label} />
            ))}
          </div>
        </div>
        <Link to={`/orders/${order.order_id}`} className="rounded bg-blue-600 px-3 py-2 text-sm text-white hover:bg-blue-700">
          View details
        </Link>
      </div>
    </li>
  );
}

OrderListItem.propTypes = {
  order: PropTypes.shape({
    order_id: PropTypes.number.isRequired,
    order_number: PropTypes.string.isRequired,
    order_date: PropTypes.string.isRequired,
    total_amount: PropTypes.number.isRequired,
    payment_status: PropTypes.string,
    order_status: PropTypes.string,
  }).isRequired,
  detail: PropTypes.string,
};
