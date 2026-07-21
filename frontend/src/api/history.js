import client from "./client";

export function getHistory(limit) {
  const params = limit ? { limit } : {};
  return client.get("/history", { params });
}
