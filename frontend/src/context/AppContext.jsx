import { createContext, useContext, useReducer } from "react";

const AppContext = createContext(null);
const DispatchContext = createContext(null);

const initialState = {
  papers: [],
  papersLoading: false,
  conversations: [],
  conversationsLoading: false,
  activeConversation: null,
  error: null,
};

function reducer(state, action) {
  switch (action.type) {
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
  return (
    <AppContext.Provider value={state}>
      <DispatchContext.Provider value={dispatch}>{children}</DispatchContext.Provider>
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
