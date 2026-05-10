import axios from "axios";

const apiClient = axios.create({
  baseURL: "/api",
  timeout: 30000,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authApi = {
  login: async (phone: string, password: string) => {
    const resp = await apiClient.post("/auth/login", { phone, password });
    return resp.data;
  },
  register: async (name: string, phone: string, password: string) => {
    const resp = await apiClient.post("/auth/register", { name, phone, password });
    return resp.data;
  },
  me: async () => {
    const resp = await apiClient.get("/auth/me");
    return resp.data;
  },
};

export const adminApi = {
  getReviews: async () => {
    const resp = await apiClient.get("/admin/reviews");
    return resp.data;
  },
  getReviewDetail: async (reviewId: number) => {
    const resp = await apiClient.get(`/admin/reviews/${reviewId}`);
    return resp.data;
  },
  reviewAction: async (reviewId: number, action: string, message?: string) => {
    const resp = await apiClient.post(`/admin/reviews/${reviewId}/action`, {
      review_id: reviewId,
      action,
      message,
    });
    return resp.data;
  },
};

export default apiClient;

export const historyApi = {
  getConversations: async () => {
    const resp = await apiClient.get("/conversations");
    return resp.data;
  },
  getMessages: async (conversationId: number) => {
    const resp = await apiClient.get(`/conversations/${conversationId}/messages`);
    return resp.data;
  },
  deleteConversation: async (conversationId: number) => {
    const resp = await apiClient.delete(`/conversations/${conversationId}`);
    return resp.data;
  },
};
