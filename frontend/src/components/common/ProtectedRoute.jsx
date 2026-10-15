/** Pages that need a login. The path is remembered so login can come back here. */
import PropTypes from "prop-types";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../context/auth-context";
import { LoadingState } from "./StatusMessage";

export default function ProtectedRoute({ children }) {
  const { user, ready } = useAuth();
  const location = useLocation();
  if (!ready) return <LoadingState label="Checking your session..." />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return children;
}

ProtectedRoute.propTypes = {
  children: PropTypes.node.isRequired,
};
