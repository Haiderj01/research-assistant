import { useState, useCallback } from "react";
import { useAppDispatch } from "../context/AppContext";
import { uploadPapers as uploadApi } from "../api/uploads";
import FileUploader from "../components/FileUploader";
import PaperCard from "../components/PaperCard";
import SummarizeModal from "../components/SummarizeModal";

export default function UploadPage() {
  const [uploading, setUploading] = useState(false);
  const [uploadedPapers, setUploadedPapers] = useState([]);
  const [error, setError] = useState(null);
  const [summarizeTarget, setSummarizeTarget] = useState(null);
  const dispatch = useAppDispatch();

  const handleUpload = useCallback(
    async (files) => {
      setUploading(true);
      setError(null);
      try {
        const res = await uploadApi(files);
        setUploadedPapers((prev) => [...res.data.papers, ...prev]);
        dispatch({ type: "ADD_PAPERS", payload: res.data.papers });
      } catch (err) {
        setError(err.message);
      } finally {
        setUploading(false);
      }
    },
    [dispatch],
  );

  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Upload Papers</h2>

      <FileUploader onUpload={handleUpload} loading={uploading} />

      {error && (
        <div className="mt-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg border border-red-200">
          {error}
        </div>
      )}

      {uploadedPapers.length > 0 && (
        <div className="mt-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            Recently Uploaded
          </h3>
          <div className="space-y-3">
            {uploadedPapers.map((p) => (
              <PaperCard
                key={p.id}
                paper={p}
                onSummarize={(id, title) => setSummarizeTarget({ id, title })}
                onDelete={(id) => {
                  setUploadedPapers((prev) => prev.filter((pp) => pp.id !== id));
                }}
              />
            ))}
          </div>
        </div>
      )}

      {summarizeTarget && (
        <SummarizeModal
          paperId={summarizeTarget.id}
          paperTitle={summarizeTarget.title}
          onClose={() => setSummarizeTarget(null)}
        />
      )}
    </div>
  );
}
