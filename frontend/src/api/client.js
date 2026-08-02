import axios from "axios";

const client = axios.create({
  baseURL: "/api/v1",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

let onUnauthorized = null;

export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

export function getStoredToken() {
  try {
    return localStorage.getItem("auth_token");
  } catch {
    return null;
  }
}

export function clearStoredToken() {
  try {
    localStorage.removeItem("auth_token");
  } catch {
    // ignore storage access errors
  }
}

client.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      clearStoredToken();
      if (typeof onUnauthorized === "function") {
        onUnauthorized();
      }
    }
    const message = error.response?.data?.error?.message
      || error.response?.data?.message
      || error.message
      || "An unexpected error occurred.";
    return Promise.reject(new Error(message));
  }
);

export default client;
