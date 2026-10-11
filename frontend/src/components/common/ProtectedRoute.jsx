/** Pages that need a login. The path is remembered so login can come back here. */
import PropTypes from "prop-types";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../context/auth-context";

export default function ProtectedRoute({ children }) {
  const { user, ready } = useAuth();
  const location = useLocation();
  if (!ready) return <p className="text-sm">Checking your session...</p>;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return children;
}

ProtectedRoute.propTypes = {
  children: PropTypes.node.isRequired,
};
