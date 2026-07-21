export default function PaperCard({ paper, onDelete }) {
  return (
    <div className="border border-gray-200 rounded-xl p-4 bg-white shadow-sm hover:shadow transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 truncate">{paper.title}</h3>
          <p className="text-xs text-gray-500 mt-1">
            {paper.page_count} page{paper.page_count !== 1 ? "s" : ""} &middot;{" "}
            {new Date(paper.upload_date).toLocaleDateString()}
          </p>
        </div>
        <span
          className={`shrink-0 ml-2 text-xs font-medium px-2 py-0.5 rounded-full ${
            paper.status === "processed"
              ? "bg-green-100 text-green-700"
              : paper.status === "failed"
                ? "bg-red-100 text-red-700"
                : "bg-yellow-100 text-yellow-700"
          }`}
        >
          {paper.status}
        </span>
      </div>
      {paper.keywords?.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-3">
          {paper.keywords.slice(0, 5).map((kw) => (
            <span key={kw} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
              {kw}
            </span>
          ))}
        </div>
      )}
      {onDelete && (
        <button
          onClick={() => onDelete(paper.id)}
          className="mt-3 text-xs text-red-600 hover:text-red-800 transition-colors"
        >
          Delete
        </button>
      )}
    </div>
  );
}
