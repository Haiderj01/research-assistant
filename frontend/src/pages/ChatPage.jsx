import { useState, useRef, useEffect } from "react";
import { usePapers } from "../hooks/usePapers";
import { askQuestion } from "../api/queries";
import ChatBubble from "../components/ChatBubble";
import LoadingSpinner from "../components/LoadingSpinner";

export default function ChatPage() {
  const { papers, papersLoading } = usePapers();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [selectedPapers, setSelectedPapers] = useState([]);
  const [asking, setAsking] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [sources, setSources] = useState(null);
  const endRef = useRef(null);

  const processedPapers = papers.filter((p) => p.status === "processed");

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const q = input.trim();
    if (!q || selectedPapers.length === 0 || asking) return;

    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setInput("");
    setAsking(true);
    setSources(null);

    try {
      const res = await askQuestion(q, selectedPapers, conversationId);
      setMessages((prev) => [...prev, { role: "assistant", content: res.data.answer }]);
      setConversationId(res.data.conversation_id);
      setSources(res.data.sources);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${err.message}` },
      ]);
    } finally {
      setAsking(false);
    }
  };

  const togglePaper = (id) => {
    setSelectedPapers((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id],
    );
  };

  return (
    <div className="max-w-4xl mx-auto flex flex-col h-[calc(100vh-3rem)]">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Ask a Question</h2>

      {papersLoading ? (
        <LoadingSpinner text="Loading papers..." />
      ) : processedPapers.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-gray-500">
          <p>Upload and process a paper before asking questions.</p>
        </div>
      ) : (
        <>
          <div className="flex flex-wrap gap-2 mb-4">
            {processedPapers.map((p) => (
              <button
                key={p.id}
                onClick={() => togglePaper(p.id)}
                className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                  selectedPapers.includes(p.id)
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-700 border-gray-300 hover:border-blue-400"
                }`}
              >
                {p.title}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto bg-white rounded-xl border border-gray-200 p-4 mb-4">
            {messages.length === 0 && (
              <p className="text-gray-400 text-sm text-center pt-12">
                Select papers above and ask a question
              </p>
            )}
            {messages.map((m, i) => (
              <ChatBubble key={i} role={m.role} content={m.content} />
            ))}
            {asking && (
              <div className="flex justify-start mb-4">
                <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.1s]" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]" />
                  </div>
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>

          {sources && (
            <details className="mb-4 text-xs text-gray-500">
              <summary className="cursor-pointer hover:text-gray-700">
                Sources ({sources.length})
              </summary>
              <ul className="mt-2 space-y-1">
                {sources.map((s, i) => (
                  <li key={i} className="truncate">
                    [{s.score.toFixed(2)}] {s.text?.slice(0, 100)}...
                  </li>
                ))}
              </ul>
            </details>
          )}

          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your question..."
              disabled={asking}
              className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={asking || !input.trim() || selectedPapers.length === 0}
              className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              Ask
            </button>
          </form>
        </>
      )}
    </div>
  );
}
