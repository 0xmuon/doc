/** One order in a history list. An optional detail line is for extra text such as the payment method. */
import PropTypes from "prop-types";
import { Link } from "react-router-dom";
import StatusBadge from "../common/StatusBadge";
import { statusLabels } from "../../utils/statusLabels";
import { inr } from "../../utils/money";

export default function OrderListItem({ order, detail }) {
  return (
    <li className="panel p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="font-semibold text-slate-900">{order.order_number}</p>
          <p className="text-sm text-slate-500">{new Date(order.order_date).toLocaleString()}</p>
          {detail ? <p className="text-sm text-slate-700">{detail}</p> : null}
          <p className="mt-1 text-sm font-medium text-slate-800">Total {inr(order.total_amount)}</p>
          <div className="mt-1 flex flex-wrap gap-2">
            {statusLabels(order).map((label) => (
              <StatusBadge key={label} status={label} />
            ))}
          </div>
        </div>
        <Link to={`/orders/${order.order_id}`} className="btn-primary">
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
