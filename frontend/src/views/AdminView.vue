<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { useAdminWebSocket } from "../composables/useWebSocket";
import { adminApi } from "../api/client";
import PendingQueue from "../components/admin/PendingQueue.vue";
import InterventionPanel from "../components/admin/InterventionPanel.vue";

const router = useRouter();
const authStore = useAuthStore();

const { connected, pendingReviews, adminError, connect, sendReviewAction, disconnect } = useAdminWebSocket();
const selectedReview = ref<any>(null);
const loading = ref(false);

async function selectReview(reviewId: number) {
  loading.value = true;
  try {
    selectedReview.value = await adminApi.getReviewDetail(reviewId);
  } catch {
    selectedReview.value = null;
  } finally {
    loading.value = false;
  }
}

function handleAction(action: string, message?: string) {
  if (!selectedReview.value) return;
  sendReviewAction(selectedReview.value.review.id, action, message);
  selectedReview.value = null;
}

function logout() {
  disconnect();
  authStore.logout();
  router.push("/login");
}

onMounted(() => {
  if (!authStore.isLoggedIn() || !authStore.isAdmin()) {
    router.push("/login");
    return;
  }
  connect(authStore.token);
});
</script>

<template>
  <div class="h-screen flex flex-col bg-apple-bg">
    <!-- Header -->
    <header class="flex items-center justify-between px-5 py-3 bg-white/80 backdrop-blur-md border-b border-gray-100">
      <div class="flex items-center gap-3">
        <h1 class="text-base font-semibold text-gray-900">管理后台</h1>
        <span
          class="px-2 py-0.5 rounded-full text-xs"
          :class="connected ? 'bg-apple-green/10 text-apple-green' : 'bg-apple-red/10 text-apple-red'"
          :title="adminError"
        >
          {{ connected ? "已连接" : (adminError || "未连接") }}
        </span>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-sm text-apple-gray">{{ authStore.userName }} (管理员)</span>
        <button @click="router.push('/chat')" class="text-sm text-apple-blue hover:underline">用户端</button>
        <button @click="logout" class="text-sm text-apple-gray hover:text-apple-red transition">退出</button>
      </div>
    </header>

    <div class="flex-1 flex overflow-hidden">
      <!-- Left: Pending Queue -->
      <div class="w-80 border-r border-gray-200 bg-white overflow-y-auto">
        <PendingQueue
          :reviews="pendingReviews"
          :selected-id="selectedReview?.review?.id"
          :loading="loading"
          @select="selectReview"
        />
      </div>

      <!-- Right: Intervention Panel -->
      <div class="flex-1 overflow-y-auto">
        <InterventionPanel
          v-if="selectedReview"
          :review="selectedReview"
          @action="handleAction"
        />
        <div v-else class="flex items-center justify-center h-full">
          <div class="text-center">
            <svg class="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
            </svg>
            <p class="text-sm text-apple-gray">选择一个待处理任务</p>
            <p class="text-xs text-gray-400 mt-1">左侧队列中显示需要人工干预的对话</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
