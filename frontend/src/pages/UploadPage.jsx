import { useState, useCallback, useEffect } from "react";
import { useNavigate } from "react-router-dom";
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
  const [summarizingId, setSummarizingId] = useState(null);
  const { papers, token } = useAppState();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  useEffect(() => {
    if (!token) return;
    listPapers()
      .then((res) => dispatch({ type: "SET_PAPERS", payload: res.data.papers }))
      .catch(() => {});
  }, [token, dispatch]);

  const hasPending = papers.some((p) => p.status === "pending" || p.status === "processing");
  useEffect(() => {
    if (!token || !hasPending) return;
    const interval = setInterval(() => {
      listPapers()
        .then((res) => dispatch({ type: "SET_PAPERS", payload: res.data.papers }))
        .catch(() => {});
    }, 3000);
    return () => clearInterval(interval);
  }, [token, hasPending, dispatch]);

  const handleUpload = useCallback(
    async (files) => {
      if (!token) {
        navigate("/login");
        return;
      }
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
    [token, dispatch, navigate],
  );

  const handleSummarizeDone = useCallback(() => setSummarizingId(null), []);

  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-2xl font-bold text-primary mb-6">Upload Papers</h2>

      <FileUploader onUpload={handleUpload} loading={uploading} />

      {error && (
        <div className="mt-4 p-3 bg-danger-soft text-danger text-sm rounded-lg border border-danger-border">
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
                summarizing={summarizingId === p.id}
                onSummarize={(id, title) => {
                  if (summarizingId) return; // one summary in flight at a time
                  setSummarizingId(id);
                  setSummarizeTarget({ id, title });
                }}
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
          onDone={handleSummarizeDone}
        />
      )}
    </div>
  );
}
