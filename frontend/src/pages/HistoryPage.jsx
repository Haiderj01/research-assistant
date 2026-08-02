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
        <p className="text-secondary text-sm">No conversations yet.</p>
      ) : (
        <div className="space-y-3">
          {conversations.map((c) => (
            <div
              key={c.id}
              className="border border-border rounded-xl p-4 bg-surface shadow-sm"
            >
              {editingId === c.id ? (
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && saveEdit(c.id)}
                    autoFocus
                    className="flex-1 border border-border rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                  <button onClick={() => saveEdit(c.id)} className="text-xs text-accent hover:text-accent-hover">Save</button>
                  <button onClick={cancelEdit} className="text-xs text-secondary hover:text-primary">Cancel</button>
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
                    className="shrink-0 ml-2 text-xs text-muted hover:text-primary transition-colors"
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
