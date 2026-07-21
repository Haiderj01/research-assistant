import client from "./client";

export function uploadPapers(files) {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  return client.post("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 120000,
  });
}
