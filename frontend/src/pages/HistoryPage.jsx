import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useConversations } from "../hooks/useConversations";
import { renameConversation } from "../api/history";
import LoadingSpinner from "../components/LoadingSpinner";

export default function HistoryPage() {
  const navigate = useNavigate();
  const { conversations, conversationsLoading, fetchConversations } = useConversations();
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState("");

  const startEdit = (c) => {
    setEditingId(c.id);
    setEditValue(c.title || "");
  };

  const saveEdit = async (id) => {
    const title = editValue.trim();
    if (!title) return;
    try {
      await renameConversation(id, title);
      setEditingId(null);
      fetchConversations();
    } catch {
      setEditingId(null);
    }
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditValue("");
  };

  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-2xl font-bold text-primary mb-6">Conversation History</h2>

      {conversationsLoading ? (
        <LoadingSpinner text="Loading history..." />
      ) : conversations.length === 0 ? (
        <div className="flex flex-col items-center justify-center text-center px-4 py-16">
          <div className="w-14 h-14 rounded-full bg-accent-soft flex items-center justify-center mb-4">
            <span className="text-2xl">📋</span>
          </div>
          <h3 className="text-lg font-semibold text-primary mb-1">No conversations yet</h3>
          <p className="text-sm text-muted max-w-sm">
            Upload a paper and ask a question to get started — your conversation history will
            appear here.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {conversations.map((c) => (
            <div
              key={c.id}
              className="border border-border rounded-xl p-4 bg-surface shadow-sm transition-shadow hover:shadow-md"
            >
              {editingId === c.id ? (
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && saveEdit(c.id)}
                    autoFocus
                    className="flex-1 border border-border rounded-lg px-2 py-1 text-sm bg-surface text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                  <button onClick={() => saveEdit(c.id)} className="text-xs font-medium text-accent hover:text-accent-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:rounded">Save</button>
                  <button onClick={cancelEdit} className="text-xs font-medium text-secondary hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:rounded">Cancel</button>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <h3
                    className="font-semibold text-primary cursor-pointer hover:text-accent transition-colors flex-1 min-w-0 truncate"
                    onClick={() => navigate(`/chat?conversationId=${c.id}`)}
                    title="Open conversation"
                  >
                    {c.title || "Untitled conversation"}
                  </h3>
                  <button
                    onClick={(e) => { e.stopPropagation(); startEdit(c); }}
                    className="shrink-0 ml-2 text-xs font-medium text-muted hover:text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:rounded"
                    title="Rename"
                  >
                    Rename
                  </button>
                </div>
              )}
              <p className="text-xs text-secondary mt-1">
                {new Date(c.updated_at).toLocaleString()} &middot;{" "}
                {c.paper_ids.length} paper{c.paper_ids.length !== 1 ? "s" : ""}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
