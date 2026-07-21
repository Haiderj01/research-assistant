import { useEffect, useCallback } from "react";
import { useAppState, useAppDispatch } from "../context/AppContext";
import { listPapers, deletePaper } from "../api/papers";

export function usePapers() {
  const { papers, papersLoading } = useAppState();
  const dispatch = useAppDispatch();

  const fetchPapers = useCallback(
    async (status) => {
      dispatch({ type: "SET_PAPERS_LOADING" });
      try {
        const res = await listPapers(status);
        dispatch({ type: "SET_PAPERS", payload: res.data.papers });
      } catch (err) {
        dispatch({ type: "SET_ERROR", payload: err.message });
      }
    },
    [dispatch],
  );

  const removePaper = useCallback(
    async (id) => {
      try {
        await deletePaper(id);
        dispatch({ type: "REMOVE_PAPER", payload: id });
      } catch (err) {
        dispatch({ type: "SET_ERROR", payload: err.message });
      }
    },
    [dispatch],
  );

  useEffect(() => {
    fetchPapers();
  }, [fetchPapers]);

  return { papers, papersLoading, fetchPapers, removePaper };
}
