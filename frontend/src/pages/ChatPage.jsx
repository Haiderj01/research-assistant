import { useState, useRef, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { usePapers } from "../hooks/usePapers";
import { askQuestion } from "../api/queries";
import { getConversationMessages } from "../api/history";
import ChatBubble from "../components/ChatBubble";
import LoadingSpinner from "../components/LoadingSpinner";

export default function ChatPage() {
  const [searchParams] = useSearchParams();
  const { papers, papersLoading } = usePapers();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [selectedPapers, setSelectedPapers] = useState([]);
  const [asking, setAsking] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [sources, setSources] = useState(null);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const endRef = useRef(null);

  const processedPapers = papers.filter((p) => p.status === "processed");
  const papersById = new Map(papers.map((p) => [p.id, p]));

  const urlConversationId = searchParams.get("conversationId");
  const initialLoadDone = useRef(false);

  useEffect(() => {
    if (!urlConversationId || initialLoadDone.current) return;
    initialLoadDone.current = true;
    setLoadingMessages(true);
    getConversationMessages(urlConversationId)
      .then((res) => {
        const { conversation, messages: msgs } = res.data;
        setMessages(msgs);
        setConversationId(conversation.id);
        setSelectedPapers(conversation.paper_ids);
      })
      .catch(() => {})
      .finally(() => setLoadingMessages(false));
  }, [urlConversationId]);

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
    <div className="max-w-4xl mx-auto flex flex-col h-[calc(100dvh-4rem)] sm:h-[calc(100dvh-5rem)] lg:h-[calc(100dvh-6rem)]">
      <h2 className="text-2xl font-bold text-primary mb-4">Ask a Question</h2>

      {loadingMessages ? (
        <LoadingSpinner text="Loading conversation..." />
      ) : papersLoading ? (
        <LoadingSpinner text="Loading papers..." />
      ) : processedPapers.length === 0 && messages.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center px-4">
          <div className="w-14 h-14 rounded-full bg-accent-soft flex items-center justify-center mb-4">
            <span className="text-2xl">💬</span>
          </div>
          <h3 className="text-lg font-semibold text-primary mb-1">No questions yet</h3>
          <p className="text-sm text-muted max-w-sm">
            Upload and process a paper first, then select it above and ask a question to get
            started.
          </p>
        </div>
      ) : (
        <>
          <div className="flex flex-wrap gap-2 mb-4">
            {processedPapers.map((p) => (
              <button
                key={p.id}
                onClick={() => togglePaper(p.id)}
                className={`text-xs px-3 py-1.5 rounded-full border transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 ${
                  selectedPapers.includes(p.id)
                    ? "bg-accent text-white border-accent hover:bg-accent-hover"
                    : "bg-surface text-primary border-border hover:border-accent active:bg-surface-hover"
                }`}
              >
                {p.title}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto bg-surface rounded-xl border border-border p-4 mb-4">
            {messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-center px-4">
                <span className="text-3xl mb-3">💬</span>
                <p className="text-muted text-sm max-w-xs">
                  Select papers above and ask a question to begin the conversation.
                </p>
              </div>
            )}
            {messages.map((m, i) => (
              <ChatBubble key={i} role={m.role} content={m.content} />
            ))}
            {asking && (
              <div className="flex justify-start mb-4">
                <div className="bg-surface-hover rounded-2xl rounded-bl-md px-4 py-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-muted rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-muted rounded-full animate-bounce [animation-delay:0.1s]" />
                    <div className="w-2 h-2 bg-muted rounded-full animate-bounce [animation-delay:0.2s]" />
                  </div>
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>

          {sources && (
            <details className="mb-4 text-xs text-secondary">
              <summary className="cursor-pointer hover:text-primary">
                Sources ({sources.length})
              </summary>
              <ul className="mt-2 space-y-2">
                {sources.map((s, i) => {
                  const paper = papersById.get(s.paper_id);
                  return (
                    <li key={i} className="border border-border rounded-lg p-2">
                      <details>
                        <summary className="cursor-pointer hover:text-primary">
                          <span className="font-medium text-primary">
                            {paper?.title || "Unknown paper"}
                          </span>
                          {s.page_number != null && (
                            <span className="text-muted"> — p.{s.page_number}</span>
                          )}
                          <span className="text-muted"> · score {s.score.toFixed(2)}</span>
                        </summary>
                        <p className="mt-2 whitespace-pre-wrap text-secondary">
                          {s.text}
                        </p>
                      </details>
                    </li>
                  );
                })}
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
              className="flex-1 border border-border rounded-lg px-4 py-2 text-sm bg-surface text-primary focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={asking || !input.trim() || selectedPapers.length === 0}
              className="bg-accent text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-accent-hover active:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 flex items-center gap-2 shrink-0"
            >
              {asking && (
                <span className="w-4 h-4 border-2 border-white/70 border-t-transparent rounded-full animate-spin" />
              )}
              {asking ? "Asking..." : "Ask"}
            </button>
          </form>
        </>
      )}
    </div>
  );
}
