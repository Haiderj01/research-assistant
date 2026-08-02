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
        <p className="text-secondary text-sm">Upload and process at least two papers to compare.</p>
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
                className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                  selectedIds.includes(p.id)
                    ? "bg-accent text-white border-accent"
                    : "bg-surface text-primary border-border hover:border-accent"
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
              className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>

          <button
            onClick={handleCompare}
            disabled={selectedIds.length < 2 || comparing}
            className="bg-accent text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-accent-hover disabled:opacity-50 transition-colors"
          >
            {comparing ? "Comparing..." : "Compare"}
          </button>

          {comparing && <LoadingSpinner size="sm" text="Generating comparison..." />}

          {error && (
            <div className="mt-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg border border-red-200">
              {error}
            </div>
          )}

          {result && (
            <div className="mt-6 bg-surface border border-border rounded-xl p-5">
              <h3 className="font-semibold text-primary mb-3">Comparison Result</h3>
              <div className="text-sm text-primary whitespace-pre-line">{result}</div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
