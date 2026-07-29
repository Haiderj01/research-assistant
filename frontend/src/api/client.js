import axios from "axios";

const client = axios.create({
  baseURL: "/api/v1",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.error?.message
      || error.response?.data?.message
      || error.message
      || "An unexpected error occurred.";
    return Promise.reject(new Error(message));
  }
);

export default client;
