import client from "./client";

export function login(email, password) {
  return client.post("/auth/login", { email, password });
}

export function register(name, email, password) {
  return client.post("/auth/register", { name, email, password });
}
