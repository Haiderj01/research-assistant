import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAppDispatch } from "../context/AppContext";
import { setStoredToken, setStoredUser } from "../api/client";
import { fetchMe } from "../api/auth";

export default function OAuthCallbackPage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      navigate("/login", { replace: true });
      return;
    }

    setStoredToken(token);
    window.history.replaceState({}, "", "/oauth/callback");

    fetchMe()
      .then((res) => {
        setStoredUser(res.data.user);
        dispatch({ type: "AUTH_SUCCESS", payload: { token, user: res.data.user } });
        navigate("/upload", { replace: true });
      })
      .catch(() => {
        setStoredToken("");
        navigate("/login", { replace: true });
      });
  }, [searchParams, navigate, dispatch]);

  return (
    <div className="min-h-screen bg-background text-primary flex items-center justify-center p-4">
      <p className="text-sm text-secondary">Signing you in…</p>
    </div>
  );
}