import client from "./client";

export function login(email, password) {
  return client.post("/auth/login", { email, password });
}

export function register(email, password) {
  return client.post("/auth/register", { email, password });
}
