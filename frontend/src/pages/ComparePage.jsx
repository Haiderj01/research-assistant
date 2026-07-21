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
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Compare Papers</h2>

      {papersLoading ? (
        <LoadingSpinner text="Loading papers..." />
      ) : processed.length === 0 ? (
        <p className="text-gray-500 text-sm">Upload and process at least two papers to compare.</p>
      ) : (
        <>
          <p className="text-sm text-gray-500 mb-3">
            Select 2+ processed papers to compare ({selectedIds.length} selected)
          </p>

          <div className="flex flex-wrap gap-2 mb-4">
            {processed.map((p) => (
              <button
                key={p.id}
                onClick={() => togglePaper(p.id)}
                className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                  selectedIds.includes(p.id)
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-700 border-gray-300 hover:border-blue-400"
                }`}
              >
                {p.title}
              </button>
            ))}
          </div>

          <div className="mb-4">
            <label className="block text-sm text-gray-600 mb-1">
              Comparison dimensions (optional, comma-separated)
            </label>
            <input
              type="text"
              value={dimensions}
              onChange={(e) => setDimensions(e.target.value)}
              placeholder="e.g. dataset, method, results"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            onClick={handleCompare}
            disabled={selectedIds.length < 2 || comparing}
            className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
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
            <div className="mt-6 bg-white border border-gray-200 rounded-xl p-5">
              <h3 className="font-semibold text-gray-900 mb-3">Comparison Result</h3>
              <div className="text-sm text-gray-800 whitespace-pre-line">{result}</div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
