import { useState } from "react";
import { usePapers } from "../hooks/usePapers";
import { comparePapers } from "../api/queries";
import { analyzeResearchGaps } from "../api/gapAnalysis";
import LoadingSpinner from "../components/LoadingSpinner";

export default function ComparePage() {
  const { papers, papersLoading } = usePapers();
  const [selectedIds, setSelectedIds] = useState([]);
  const [dimensions, setDimensions] = useState("");
  const [comparing, setComparing] = useState(false);
  const [analyzingGaps, setAnalyzingGaps] = useState(false);
  const [result, setResult] = useState(null);
  const [gapResult, setGapResult] = useState(null);
  const [error, setError] = useState(null);

  const processed = papers.filter((p) => p.status === "processed");
  const papersById = Object.fromEntries(papers.map((p) => [p.id, p]));

  const togglePaper = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id],
    );
    setResult(null);
    setGapResult(null);
    setError(null);
  };

  const handleCompare = async () => {
    if (selectedIds.length < 2) return;
    setComparing(true);
    setResult(null);
    setGapResult(null);
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

  const handleGapAnalysis = async () => {
    if (selectedIds.length < 2) return;
    setAnalyzingGaps(true);
    setGapResult(null);
    setResult(null);
    setError(null);
    try {
      const res = await analyzeResearchGaps(selectedIds);
      setGapResult(res.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setAnalyzingGaps(false);
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
            Select 2+ processed papers ({selectedIds.length} selected)
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

          <div className="flex flex-wrap gap-3">
            <button
              onClick={handleCompare}
              disabled={selectedIds.length < 2 || comparing || analyzingGaps}
              className="bg-accent text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-accent-hover active:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 flex items-center gap-2"
            >
              {comparing && (
                <span className="w-4 h-4 border-2 border-white/70 border-t-transparent rounded-full animate-spin" />
              )}
              {comparing ? "Comparing..." : "Compare"}
            </button>

            <button
              onClick={handleGapAnalysis}
              disabled={selectedIds.length < 2 || comparing || analyzingGaps}
              className="bg-surface border border-border text-primary px-5 py-2 rounded-lg text-sm font-medium hover:border-accent active:bg-surface-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 flex items-center gap-2"
            >
              {analyzingGaps && (
                <span className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />
              )}
              {analyzingGaps ? "Analyzing gaps..." : "Find Research Gaps"}
            </button>
          </div>

          {analyzingGaps && (
            <div className="mt-4 p-3 bg-accent-soft text-primary text-sm rounded-lg border border-accent">
              Analyzing {selectedIds.length} papers for research gaps... this may take a moment.
            </div>
          )}

          {error && (
            <div className="mt-4 p-3 bg-danger-soft text-danger text-sm rounded-lg border border-danger-border">
              {error}
            </div>
          )}

          {gapResult && (
            <div className="mt-6 space-y-4">
              <div className="bg-surface border border-border rounded-xl p-5">
                <h3 className="text-lg font-semibold text-primary mb-3">
                  Research Gap Analysis
                </h3>

                {gapResult.gaps.length === 0 ? (
                  <p className="text-sm text-secondary">
                    No clearly grounded gaps were identified across the selected papers.
                  </p>
                ) : (
                  <div className="space-y-4">
                    {gapResult.gaps.map((gap, i) => {
                      const isMultiple = gap.strength === "multiple";
                      return (
                        <div
                          key={i}
                          className={`border rounded-xl p-4 ${
                            isMultiple ? "border-accent bg-accent-soft" : "border-border bg-surface"
                          }`}
                        >
                          <div className="flex items-center gap-2 mb-2">
                            <span
                              className={`text-[10px] uppercase tracking-wide font-semibold px-2 py-0.5 rounded-full border ${
                                isMultiple
                                  ? "bg-accent text-white border-accent"
                                  : "bg-surface text-muted border-border"
                              }`}
                              title={
                                isMultiple
                                  ? "Mentioned by multiple papers"
                                  : "Mentioned by a single paper"
                              }
                            >
                              {isMultiple ? "✦ Multiple papers" : "Single paper"}
                            </span>
                          </div>
                          <p className="text-sm text-primary mb-2">{gap.description}</p>
                          <div className="flex flex-wrap items-center gap-1.5 mb-2">
                            {gap.supporting_papers.map((pid) => {
                              const paper = papersById[pid];
                              return (
                                <span
                                  key={pid}
                                  className="text-[10px] px-2 py-0.5 rounded-full bg-surface-hover text-secondary truncate max-w-[220px]"
                                  title={paper ? paper.title : pid}
                                >
                                  {paper ? paper.title : pid}
                                </span>
                              );
                            })}
                          </div>
                          {gap.suggested_direction && (
                            <p className="text-sm text-secondary">
                              <span className="font-medium text-primary">Suggested direction: </span>
                              {gap.suggested_direction}
                            </p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {gapResult.per_paper_summaries && (
                <details className="text-xs text-secondary">
                  <summary className="cursor-pointer hover:text-primary">
                    Per-paper limitation summaries ({gapResult.per_paper_summaries.length})
                  </summary>
                  <div className="mt-2 space-y-2">
                    {gapResult.per_paper_summaries.map((s) => {
                      const paper = papersById[s.paper_id];
                      return (
                        <div key={s.paper_id} className="bg-surface border border-border rounded-lg p-3">
                          <p className="font-medium text-primary mb-1">
                            {paper ? paper.title : s.title}
                          </p>
                          <p className="text-secondary whitespace-pre-line">{s.summary}</p>
                        </div>
                      );
                    })}
                  </div>
                </details>
              )}
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
