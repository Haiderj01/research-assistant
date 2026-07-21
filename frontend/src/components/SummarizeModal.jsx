import { useState, useEffect } from "react";
import { summarizePaper } from "../api/queries";

export default function SummarizeModal({ paperId, paperTitle, onClose }) {
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
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [paperId]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div
        className="bg-white rounded-xl shadow-xl max-w-lg w-full mx-4 max-h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200">
          <h3 className="font-semibold text-gray-900 truncate">{paperTitle}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
        </div>
        <div className="px-5 py-4 overflow-y-auto flex-1">
          {loading && <p className="text-sm text-gray-500">Generating summary...</p>}
          {error && <p className="text-sm text-red-600">{error}</p>}
          {summary && <p className="text-sm text-gray-800 whitespace-pre-line">{summary}</p>}
        </div>
      </div>
    </div>
  );
}
