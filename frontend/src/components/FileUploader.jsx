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
      className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors ${
        dragOver ? "border-blue-500 bg-blue-50" : "border-gray-300 bg-gray-50"
      }`}
    >
      {loading ? (
        <div className="flex flex-col items-center gap-2">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-gray-600">Processing papers...</p>
        </div>
      ) : (
        <>
          <p className="text-gray-600 mb-2">Drag & drop PDF files here</p>
          <p className="text-xs text-gray-400 mb-4">or</p>
          <label className="inline-block cursor-pointer bg-blue-600 text-white px-5 py-2 rounded-lg text-sm hover:bg-blue-700 transition-colors">
            Browse Files
            <input
              type="file"
              accept=".pdf"
              multiple
              onChange={handleChange}
              className="hidden"
            />
          </label>
          <p className="text-xs text-gray-400 mt-3">Only .pdf files accepted</p>
        </>
      )}
    </div>
  );
}
