import { useState } from "react";
import { usePapers } from "../hooks/usePapers";
import { comparePapers } from "../api/queries";
import LoadingSpinner from "../components/LoadingSpinner";

export default function ComparePage() {
  const { papers, papersLoading } = usePapers();
  const [selectedIds, setSelectedIds] = useState([]);
  const [dimensions, setDimensions] = useState("");
  const [comparing, setComparing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const processed = papers.filter((p) => p.status === "processed");

  const togglePaper = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id],
    );
    setResult(null);
    setError(null);
  };

  const handleCompare = async () => {
    if (selectedIds.length < 2) return;
    setComparing(true);
    setResult(null);
    setError(null);
    try {
      const dims = dimensions
        ? dimensions.split(",").map((d) => d.trim()).filter(Boolean)
        : undefined;
      const res = await comparePapers(selectedIds, dims);
      setResult(res.data.comparison);
    } catch (err) {
      setError(err.message);
    } finally {
      setComparing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-primary mb-6">Compare Papers</h2>

      {papersLoading ? (
        <LoadingSpinner text="Loading papers..." />
      ) : processed.length === 0 ? (
        <div className="flex flex-col items-center justify-center text-center px-4 py-16">
          <div className="w-14 h-14 rounded-full bg-accent-soft flex items-center justify-center mb-4">
            <span className="text-2xl">⇄</span>
          </div>
          <h3 className="text-lg font-semibold text-primary mb-1">Nothing to compare yet</h3>
          <p className="text-sm text-muted max-w-sm">
            Upload and process at least two papers, then return here to compare them side by side.
          </p>
        </div>
      ) : (
        <>
          <p className="text-sm text-secondary mb-3">
            Select 2+ processed papers to compare ({selectedIds.length} selected)
          </p>

          <div className="flex flex-wrap gap-2 mb-4">
            {processed.map((p) => (
              <button
                key={p.id}
                onClick={() => togglePaper(p.id)}
                className={`text-xs px-3 py-1.5 rounded-full border transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 ${
                  selectedIds.includes(p.id)
                    ? "bg-accent text-white border-accent hover:bg-accent-hover"
                    : "bg-surface text-primary border-border hover:border-accent active:bg-surface-hover"
                }`}
              >
                {p.title}
              </button>
            ))}
          </div>

          <div className="mb-4">
            <label className="block text-sm text-secondary mb-1">
              Comparison dimensions (optional, comma-separated)
            </label>
            <input
              type="text"
              value={dimensions}
              onChange={(e) => setDimensions(e.target.value)}
              placeholder="e.g. dataset, method, results"
              className="w-full border border-border rounded-lg px-3 py-2 text-sm bg-surface text-primary focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>

          <button
            onClick={handleCompare}
            disabled={selectedIds.length < 2 || comparing}
            className="bg-accent text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-accent-hover active:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 flex items-center gap-2"
          >
            {comparing && (
              <span className="w-4 h-4 border-2 border-white/70 border-t-transparent rounded-full animate-spin" />
            )}
            {comparing ? "Comparing..." : "Compare"}
          </button>

          {error && (
            <div className="mt-4 p-3 bg-danger-soft text-danger text-sm rounded-lg border border-danger-border">
              {error}
            </div>
          )}

          {result && (
            <div className="mt-6 bg-surface border border-border rounded-xl p-5">
              <h3 className="text-lg font-semibold text-primary mb-3">Comparison Result</h3>
              <div className="text-sm text-primary whitespace-pre-line leading-relaxed">{result}</div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
