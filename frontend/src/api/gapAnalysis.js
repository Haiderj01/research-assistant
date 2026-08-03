import client from "./client";

export function analyzeResearchGaps(paperIds) {
  return client.post("/gap-analysis", {
    paper_ids: paperIds,
  }, {
    timeout: 300000,
  });
}
