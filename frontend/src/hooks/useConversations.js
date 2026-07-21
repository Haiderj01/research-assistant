import { useEffect, useCallback } from "react";
import { useAppState, useAppDispatch } from "../context/AppContext";
import { getHistory } from "../api/history";

export function useConversations() {
  const { conversations, conversationsLoading } = useAppState();
  const dispatch = useAppDispatch();

  const fetchConversations = useCallback(async () => {
    dispatch({ type: "SET_CONVERSATIONS_LOADING" });
    try {
      const res = await getHistory();
      dispatch({ type: "SET_CONVERSATIONS", payload: res.data.conversations });
    } catch (err) {
      dispatch({ type: "SET_ERROR", payload: err.message });
    }
  }, [dispatch]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  return { conversations, conversationsLoading, fetchConversations };
}
