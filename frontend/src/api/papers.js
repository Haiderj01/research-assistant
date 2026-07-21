import client from "./client";

export function listPapers(status) {
  const params = status ? { status } : {};
  return client.get("/papers", { params });
}

export function getPaper(id) {
  return client.get(`/paper/${id}`);
}

export function deletePaper(id) {
  return client.delete(`/paper/${id}`);
}
