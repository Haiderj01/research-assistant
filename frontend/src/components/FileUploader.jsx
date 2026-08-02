import { useState, useCallback } from "react";

export default function FileUploader({ onUpload, loading }) {
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragOver(false);
      const files = Array.from(e.dataTransfer.files).filter((f) => f.name.endsWith(".pdf"));
      if (files.length > 0) onUpload(files);
    },
    [onUpload],
  );

  const handleChange = useCallback(
    (e) => {
      const files = Array.from(e.target.files);
      if (files.length > 0) onUpload(files);
    },
    [onUpload],
  );

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded-xl p-10 text-center transition-all ${
        dragOver
          ? "border-accent bg-accent-soft ring-2 ring-accent ring-inset"
          : "border-border bg-surface"
      }`}
    >
      {loading ? (
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-secondary">Processing papers...</p>
        </div>
      ) : (
        <>
          <p className="text-base font-medium text-primary mb-1">Drag & drop PDF files here</p>
          <p className="text-sm text-secondary mb-4">or</p>
          <label className="inline-block cursor-pointer bg-accent text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-accent-hover active:bg-accent-hover transition-colors focus-within:outline-none focus-within:ring-2 focus-within:ring-accent focus-within:ring-offset-2">
            Browse Files
            <input
              type="file"
              accept=".pdf"
              multiple
              onChange={handleChange}
              className="sr-only"
            />
          </label>
          <p className="text-xs text-muted mt-3">Only .pdf files accepted</p>
        </>
      )}
    </div>
  );
}
