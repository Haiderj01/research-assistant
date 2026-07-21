import { useConversations } from "../hooks/useConversations";
import LoadingSpinner from "../components/LoadingSpinner";

export default function HistoryPage() {
  const { conversations, conversationsLoading } = useConversations();

  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Conversation History</h2>

      {conversationsLoading ? (
        <LoadingSpinner text="Loading history..." />
      ) : conversations.length === 0 ? (
        <p className="text-gray-500 text-sm">No conversations yet.</p>
      ) : (
        <div className="space-y-3">
          {conversations.map((c) => (
            <div
              key={c.id}
              className="border border-gray-200 rounded-xl p-4 bg-white shadow-sm"
            >
              <h3 className="font-semibold text-gray-900">
                {c.title || "Untitled conversation"}
              </h3>
              <p className="text-xs text-gray-500 mt-1">
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
