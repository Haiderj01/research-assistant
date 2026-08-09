import { createContext, useContext, useEffect, useReducer, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { login as loginApi, register as registerApi } from "../api/auth";
import {
  setUnauthorizedHandler,
  getStoredToken,
  setStoredToken,
  clearStoredToken,
  getStoredUser,
  setStoredUser,
  clearStoredUser,
} from "../api/client";

const AppContext = createContext(null);
const DispatchContext = createContext(null);
const AuthActionsContext = createContext(null);

function getInitialTheme() {
  try {
    const saved = localStorage.getItem("theme");
    if (saved === "light" || saved === "dark") return saved;
    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      return "dark";
    }
  } catch {
    // ignore storage access errors
  }
  return "light";
}

const initialState = {
  theme: getInitialTheme(),
  user: getStoredUser(),
  token: getStoredToken(),
  authLoading: false,
  authError: null,
  papers: [],
  papersLoading: false,
  conversations: [],
  conversationsLoading: false,
  activeConversation: null,
  error: null,
};

function reducer(state, action) {
  switch (action.type) {
    case "TOGGLE_THEME":
      return { ...state, theme: state.theme === "dark" ? "light" : "dark" };
    case "SET_THEME":
      return { ...state, theme: action.payload };
    case "AUTH_LOADING":
      return { ...state, authLoading: true, authError: null };
    case "AUTH_SUCCESS":
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        authLoading: false,
        authError: null,
      };
    case "AUTH_ERROR":
      return { ...state, authLoading: false, authError: action.payload };
    case "AUTH_LOGOUT":
      return { ...state, user: null, token: null, authError: null };
    case "SET_PAPERS":
      return { ...state, papers: action.payload, papersLoading: false };
    case "SET_PAPERS_LOADING":
      return { ...state, papersLoading: true };
    case "ADD_PAPERS":
      return { ...state, papers: [...action.payload, ...state.papers] };
    case "REMOVE_PAPER":
      return { ...state, papers: state.papers.filter((p) => p.id !== action.payload) };
    case "SET_CONVERSATIONS":
      return { ...state, conversations: action.payload, conversationsLoading: false };
    case "SET_CONVERSATIONS_LOADING":
      return { ...state, conversationsLoading: true };
    case "SET_ACTIVE_CONVERSATION":
      return { ...state, activeConversation: action.payload };
    case "SET_ERROR":
      return { ...state, error: action.payload };
    case "CLEAR_ERROR":
      return { ...state, error: null };
    default:
      return state;
  }
}

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const navigate = useNavigate();

  useEffect(() => {
    const root = document.documentElement;
    if (state.theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    try {
      localStorage.setItem("theme", state.theme);
    } catch {
      // ignore storage access errors
    }
  }, [state.theme]);

  const applyAuth = useCallback(
    (result) => {
      setStoredToken(result.token);
      setStoredUser(result.user);
      dispatch({ type: "AUTH_SUCCESS", payload: result });
    },
    [],
  );

  const login = useCallback(
    async (email, password) => {
      dispatch({ type: "AUTH_LOADING" });
      try {
        const res = await loginApi(email, password);
        applyAuth({ token: res.data.token, user: res.data.user });
      } catch (err) {
        dispatch({ type: "AUTH_ERROR", payload: err.message });
        throw err;
      }
    },
    [applyAuth],
  );

  const register = useCallback(
    async (name, email, password) => {
      dispatch({ type: "AUTH_LOADING" });
      try {
        const res = await registerApi(name, email, password);
        applyAuth({ token: res.data.token, user: res.data.user });
      } catch (err) {
        dispatch({ type: "AUTH_ERROR", payload: err.message });
        throw err;
      }
    },
    [applyAuth],
  );

  const logout = useCallback(() => {
    clearStoredToken();
    clearStoredUser();
    dispatch({ type: "AUTH_LOGOUT" });
    navigate("/");
  }, [navigate]);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      clearStoredToken();
      clearStoredUser();
      dispatch({ type: "AUTH_LOGOUT" });
      navigate("/login");
    });
    return () => setUnauthorizedHandler(null);
  }, [navigate]);

  const authActions = { login, register, logout };

  return (
    <AppContext.Provider value={state}>
      <AuthActionsContext.Provider value={authActions}>
        <DispatchContext.Provider value={dispatch}>{children}</DispatchContext.Provider>
      </AuthActionsContext.Provider>
    </AppContext.Provider>
  );
}

export function useAppState() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useAppState must be used within AppProvider");
  return ctx;
}

export function useAppDispatch() {
  const ctx = useContext(DispatchContext);
  if (!ctx) throw new Error("useAppDispatch must be used within AppProvider");
  return ctx;
}

export function useAuthActions() {
  const ctx = useContext(AuthActionsContext);
  if (!ctx) throw new Error("useAuthActions must be used within AppProvider");
  return ctx;
}
