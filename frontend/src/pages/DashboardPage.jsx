import { usePapers } from "../hooks/usePapers";
import { useConversations } from "../hooks/useConversations";
import LoadingSpinner from "../components/LoadingSpinner";

export default function DashboardPage() {
  const { papers, papersLoading } = usePapers();
  const { conversations, conversationsLoading } = useConversations();

  if (papersLoading || conversationsLoading) {
    return <LoadingSpinner text="Loading dashboard..." />;
  }

  const processed = papers.filter((p) => p.status === "processed").length;
  const failed = papers.filter((p) => p.status === "failed").length;
  const pending = papers.length - processed - failed;

  const cards = [
    { label: "Total Papers", value: papers.length, color: "bg-blue-500" },
    { label: "Processed", value: processed, color: "bg-green-500" },
    { label: "Pending", value: pending, color: "bg-yellow-500" },
    { label: "Failed", value: failed, color: "bg-red-500" },
    { label: "Conversations", value: conversations.length, color: "bg-purple-500" },
  ];

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-primary mb-6">Dashboard</h2>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {cards.map((c) => (
          <div key={c.label} className="border border-border rounded-xl p-4 bg-surface shadow-sm">
            <div className={`w-3 h-3 rounded-full ${c.color} mb-2`} />
            <p className="text-2xl font-bold text-primary">{c.value}</p>
            <p className="text-xs text-secondary mt-1">{c.label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
