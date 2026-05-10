import { defineStore } from "pinia";
import { ref } from "vue";
import { authApi } from "../api/client";

export const useAuthStore = defineStore("auth", () => {
  const token = ref(localStorage.getItem("token") || "");
  const role = ref(localStorage.getItem("role") || "");
  const userName = ref(localStorage.getItem("name") || "");
  const userId = ref(Number(localStorage.getItem("userId")) || 0);

  const isLoggedIn = () => !!token.value;
  const isAdmin = () => role.value === "admin";

  async function login(phone: string, password: string) {
    const data = await authApi.login(phone, password);
    token.value = data.access_token;
    role.value = data.role;
    userName.value = data.name;
    userId.value = data.user_id;
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("role", data.role);
    localStorage.setItem("name", data.name);
    localStorage.setItem("userId", String(data.user_id));
    return data;
  }

  async function register(name: string, phone: string, password: string) {
    const data = await authApi.register(name, phone, password);
    token.value = data.access_token;
    role.value = data.role;
    userName.value = data.name;
    userId.value = data.user_id;
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("role", data.role);
    localStorage.setItem("name", data.name);
    localStorage.setItem("userId", String(data.user_id));
    return data;
  }

  function logout() {
    token.value = "";
    role.value = "";
    userName.value = "";
    userId.value = 0;
    localStorage.clear();
  }

  return { token, role, userName, userId, isLoggedIn, isAdmin, login, register, logout };
});
