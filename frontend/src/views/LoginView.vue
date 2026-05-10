<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const isRegister = ref(false);
const name = ref("");
const phone = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);

async function submit() {
  error.value = "";
  loading.value = true;
  try {
    if (isRegister.value) {
      await authStore.register(name.value, phone.value, password.value);
    } else {
      await authStore.login(phone.value, password.value);
    }
    if (authStore.isAdmin()) {
      router.push("/admin");
    } else {
      router.push("/chat");
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || "操作失败，请重试";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-apple-bg">
    <div class="w-full max-w-md p-8 bg-apple-card rounded-2xl shadow-sm">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-semibold text-gray-900">OmniSupport AI</h1>
        <p class="mt-1 text-sm text-apple-gray">企业级全链路智能客服系统</p>
      </div>

      <form @submit.prevent="submit" class="space-y-4">
        <div v-if="isRegister">
          <label class="block text-sm font-medium text-gray-700 mb-1">姓名</label>
          <input
            v-model="name"
            type="text"
            required
            class="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-apple-blue focus:ring-1 focus:ring-apple-blue outline-none transition text-sm"
            placeholder="请输入姓名"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">账号</label>
          <input
            v-model="phone"
            type="text"
            required
            class="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-apple-blue focus:ring-1 focus:ring-apple-blue outline-none transition text-sm"
            placeholder="请输入账号"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">密码</label>
          <input
            v-model="password"
            type="password"
            required
            class="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-apple-blue focus:ring-1 focus:ring-apple-blue outline-none transition text-sm"
            placeholder="请输入密码"
          />
        </div>

        <p v-if="error" class="text-sm text-apple-red">{{ error }}</p>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-2.5 bg-apple-blue text-white rounded-xl font-medium text-sm hover:opacity-90 transition disabled:opacity-50"
        >
          {{ loading ? "处理中..." : (isRegister ? "注册" : "登录") }}
        </button>
      </form>

      <p class="mt-4 text-center text-sm text-apple-gray">
        {{ isRegister ? "已有账号？" : "没有账号？" }}
        <button
          @click="isRegister = !isRegister; error = ''"
          class="text-apple-blue hover:underline font-medium"
        >
          {{ isRegister ? "去登录" : "去注册" }}
        </button>
      </p>

    </div>
  </div>
</template>
