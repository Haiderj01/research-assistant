export default function PaperCard({ paper, onDelete, onSummarize, summarizing = false }) {
  return (
    <div className="border border-border rounded-xl p-4 bg-surface shadow-sm hover:shadow transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-primary truncate">{paper.title}</h3>
          <p className="text-xs text-secondary mt-1">
            {(paper.page_count ?? 0)} page{(paper.page_count ?? 0) !== 1 ? "s" : ""} &middot;{" "}
            {new Date(paper.upload_date).toLocaleDateString()}
          </p>
        </div>
        <span
          className={`shrink-0 ml-2 text-xs font-medium px-2 py-0.5 rounded-full ${
            paper.status === "processed"
              ? "bg-success-soft text-success"
              : paper.status === "failed"
                ? "bg-danger-soft text-danger"
                : "bg-warning-soft text-warning"
          }`}
        >
          {paper.status}
        </span>
      </div>
      {paper.keywords?.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-3">
          {paper.keywords.slice(0, 5).map((kw) => (
            <span key={kw} className="text-xs bg-surface-hover text-secondary px-2 py-0.5 rounded-full">
              {kw}
            </span>
          ))}
        </div>
      )}
      <div className="flex gap-3 mt-3">
        {paper.status === "processed" && onSummarize && (
          <button
            onClick={() => onSummarize(paper.id, paper.title)}
            disabled={summarizing}
            className={`text-xs font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:rounded ${
              summarizing
                ? "text-muted cursor-not-allowed"
                : "text-accent hover:text-accent-hover transition-colors"
            }`}
            title={summarizing ? "Summary is already being generated" : undefined}
          >
            {summarizing ? "Summarizing…" : "Summarize"}
          </button>
        )}
        {onDelete && (
          <button
            onClick={() => onDelete(paper.id)}
            className="text-xs font-medium text-danger hover:text-danger-hover transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-danger focus-visible:rounded"
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
}
