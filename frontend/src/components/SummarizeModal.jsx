import { useState, useEffect } from "react";
import { summarizePaper } from "../api/queries";
import LoadingSpinner from "./LoadingSpinner";

export default function SummarizeModal({ paperId, paperTitle, onClose, onDone }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    summarizePaper(paperId)
      .then((res) => { if (!cancelled) setSummary(res.data.summary); })
      .catch((err) => { if (!cancelled) setError(err.message); })
      .finally(() => {
        if (!cancelled) setLoading(false);
        if (typeof onDone === "function") onDone();
      });
    return () => { cancelled = true; };
  }, [paperId, onDone]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div
        className="bg-surface rounded-xl shadow-xl max-w-lg w-full mx-4 max-h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <h3 className="text-lg font-semibold text-primary truncate">{paperTitle}</h3>
          <button
            onClick={onClose}
            className="text-muted hover:text-primary text-xl leading-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:rounded"
            title="Close"
          >
            &times;
          </button>
        </div>
        <div className="px-5 py-4 overflow-y-auto flex-1">
          {loading && (
            <LoadingSpinner size="sm" text="Summarizing..." />
          )}
          {error && <p className="text-sm text-danger">{error}</p>}
          {summary && <p className="text-sm text-primary whitespace-pre-line leading-relaxed">{summary}</p>}
        </div>
      </div>
    </div>
  );
}
