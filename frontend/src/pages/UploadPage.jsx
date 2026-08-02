import { useState, useCallback, useEffect } from "react";
import { useAppState, useAppDispatch } from "../context/AppContext";
import { uploadPapers as uploadApi } from "../api/uploads";
import { listPapers, deletePaper } from "../api/papers";
import FileUploader from "../components/FileUploader";
import PaperCard from "../components/PaperCard";
import SummarizeModal from "../components/SummarizeModal";

export default function UploadPage() {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [summarizeTarget, setSummarizeTarget] = useState(null);
  const { papers } = useAppState();
  const dispatch = useAppDispatch();

  useEffect(() => {
    listPapers()
      .then((res) => dispatch({ type: "SET_PAPERS", payload: res.data.papers }))
      .catch(() => {});
  }, [dispatch]);

  const hasPending = papers.some((p) => p.status === "pending" || p.status === "processing");
  useEffect(() => {
    if (!hasPending) return;
    const interval = setInterval(() => {
      listPapers()
        .then((res) => dispatch({ type: "SET_PAPERS", payload: res.data.papers }))
        .catch(() => {});
    }, 3000);
    return () => clearInterval(interval);
  }, [hasPending, dispatch]);

  const handleUpload = useCallback(
    async (files) => {
      setUploading(true);
      setError(null);
      try {
        const res = await uploadApi(files);
        dispatch({ type: "ADD_PAPERS", payload: res.data.papers });
      } catch (err) {
        console.error("Upload failed:", err);
        setError(err.message);
      } finally {
        setUploading(false);
      }
    },
    [dispatch],
  );

  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-2xl font-bold text-primary mb-6">Upload Papers</h2>

      <FileUploader onUpload={handleUpload} loading={uploading} />

      {error && (
        <div className="mt-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg border border-red-200">
          {error}
        </div>
      )}

      {papers.length > 0 && (
        <div className="mt-8">
          <h3 className="text-lg font-semibold text-primary mb-3">
            Recently Uploaded
          </h3>
          <div className="space-y-3">
            {papers.map((p) => (
              <PaperCard
                key={p.id}
                paper={p}
                onSummarize={(id, title) => setSummarizeTarget({ id, title })}
                onDelete={async (id) => {
                  try {
                    await deletePaper(id);
                    const res = await listPapers();
                    dispatch({ type: "SET_PAPERS", payload: res.data.papers });
                  } catch {}
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
