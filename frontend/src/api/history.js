import client from "./client";

export function getHistory(limit) {
  const params = limit ? { limit } : {};
  return client.get("/history", { params });
}

export function renameConversation(id, title) {
  return client.patch(`/conversation/${id}`, { title });
}

export function getConversationMessages(id) {
  return client.get(`/conversation/${id}/messages`);
}
