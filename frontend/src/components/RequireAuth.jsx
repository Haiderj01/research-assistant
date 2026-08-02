import { Navigate } from "react-router-dom";
import { useAppState } from "../context/AppContext";

export default function RequireAuth({ children }) {
  const { token } = useAppState();
  if (!token) return <Navigate to="/login" replace />;
  return children;
}
