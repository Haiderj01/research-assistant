import client from "./client";

export function askQuestion(question, paperIds, conversationId) {
  return client.post("/ask", {
    question,
    paper_ids: paperIds,
    conversation_id: conversationId,
  });
}

export function summarizePaper(paperId, forceRegenerate = false) {
  return client.post(
    "/summarize",
    {
      paper_id: paperId,
      force_regenerate: forceRegenerate,
    },
    // Large papers summarize in multiple paced batches and can take
    // several minutes; the default 5-minute client timeout would abort.
    { timeout: 1200000 }
  );
}

export function comparePapers(paperIds, dimensions) {
  return client.post("/compare", {
    paper_ids: paperIds,
    dimensions: dimensions,
  });
}
