<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { historyApi } from "../api/client";
import ChatCanvas from "../components/chat/ChatCanvas.vue";
import ChatInput from "../components/chat/ChatInput.vue";
import WorkflowVisualizer from "../components/workflow/WorkflowVisualizer.vue";

const router = useRouter();
const authStore = useAuthStore();

const messages = ref<any[]>([]);
const streamingContent = ref("");
const nodeStatus = ref<Record<string, string>>({});
const isConnected = ref(false);
const sidebarOpen = ref(false);
const historyOpen = ref(false);
const conversations = ref<any[]>([]);
const currentConversationId = ref<number | null>(null);
const loadingHistory = ref(false);

let ws: WebSocket | null = null;

async function loadConversations() {
  try {
    conversations.value = await historyApi.getConversations();
  } catch {
    // Ignore errors
  }
}

async function loadMessages(convId: number) {
  loadingHistory.value = true;
  currentConversationId.value = convId;
  nodeStatus.value = {};
  streamingContent.value = "";
  try {
    const data = await historyApi.getMessages(convId);
    messages.value = data.messages.map((m: any) => ({
      role: m.role,
      content: m.content,
    }));
    await nextTick();
  } catch {
    messages.value = [];
  } finally {
    loadingHistory.value = false;
  }
}

function newConversation() {
  currentConversationId.value = null;
  messages.value = [];
  nodeStatus.value = {};
  streamingContent.value = "";
  historyOpen.value = false;
}

async function deleteConversation(convId: number, event: Event) {
  event.stopPropagation();
  if (!confirm("确定要删除这条对话记录吗？")) return;
  try {
    await historyApi.deleteConversation(convId);
    if (currentConversationId.value === convId) {
      newConversation();
    }
    await loadConversations();
  } catch {
    // Ignore errors
  }
}

function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${protocol}//${window.location.host}/ws/chat`;

  ws = new WebSocket(url);

  ws.onopen = () => {
    isConnected.value = true;
    ws!.send(JSON.stringify({ token: authStore.token }));
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);

      // Error message
      if (data.type === "error") {
        streamingContent.value = "";
        messages.value.push({ role: "system", content: data.content, isError: true });
        return;
      }

      // Streaming token — accumulate into current response
      if (data.type === "token") {
        streamingContent.value += data.content;
        return;
      }

      // Real-time node status update
      if (data.type === "node_status") {
        try {
          const si = JSON.parse(data.content);
          // Dedup: only push if status actually changed
          if (nodeStatus.value[si.node] !== si.status) {
            nodeStatus.value[si.node] = si.status;
            messages.value.push({
              role: "node_status",
              node: si.node,
              status: si.status,
              message: si.message || "",
            });
          }
        } catch {
          // Ignore parse errors
        }
        return;
      }

      // Final response — commit the streaming content to messages
      if (data.type === "final") {
        nodeStatus.value["finalize"] = "completed";
        messages.value.push({ role: "assistant", content: data.content });
        streamingContent.value = "";
        loadConversations();
        return;
      }

      // Legacy: graph event objects (full state snapshots)
      const processObj = (obj: any) => {
        if (obj.messages) {
          for (const m of Array.isArray(obj.messages) ? obj.messages : [obj.messages]) {
            if (typeof m === "string") {
              try {
                const parsed = JSON.parse(m);
                if (parsed.role === "node_status") {
                  const si = JSON.parse(parsed.content);
                  nodeStatus.value[si.node] = si.status;
                  messages.value.push({
                    role: "node_status",
                    node: si.node,
                    status: si.status,
                    message: si.message || "",
                  });
                }
              } catch {
                // Ignore parse errors
              }
            }
          }
        }
        if (obj.node_status) {
          Object.assign(nodeStatus.value, obj.node_status);
        }
      };

      if (typeof data === "object") {
        processObj(data);
      }
    } catch {
      // Non-JSON message
    }
  };

  ws.onclose = () => {
    isConnected.value = false;
  };

  ws.onerror = () => {
    isConnected.value = false;
  };
}

function sendMessage(text: string) {
  if (!ws || !isConnected.value) return;
  if (currentConversationId.value) {
    newConversation();
    loadConversations();
  }
  messages.value.push({ role: "user", content: text });
  nodeStatus.value = {};
  streamingContent.value = "";
  ws.send(JSON.stringify({ message: text }));
}

function logout() {
  if (ws) ws.close();
  authStore.logout();
  router.push("/login");
}

onMounted(() => {
  if (!authStore.isLoggedIn()) {
    router.push("/login");
    return;
  }
  connectWebSocket();
  loadConversations();
});

onUnmounted(() => {
  if (ws) ws.close();
});
</script>

<template>
  <div class="h-screen flex flex-col bg-apple-bg">
    <!-- Header -->
    <header class="flex items-center justify-between px-5 py-3 bg-white/80 backdrop-blur-md border-b border-gray-100">
      <div class="flex items-center gap-3">
        <button
          @click="historyOpen = !historyOpen"
          class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 transition"
          title="聊天记录"
        >
          <div class="space-y-1">
            <div class="w-4 h-0.5 bg-gray-500 rounded"></div>
            <div class="w-4 h-0.5 bg-gray-500 rounded"></div>
          </div>
        </button>
        <h1 class="text-base font-semibold text-gray-900">OmniSupport AI</h1>
        <span
          class="px-2 py-0.5 rounded-full text-xs"
          :class="isConnected ? 'bg-apple-green/10 text-apple-green' : 'bg-apple-red/10 text-apple-red'"
        >
          {{ isConnected ? "在线" : "离线" }}
        </span>
      </div>
      <div class="flex items-center gap-3">
        <button
          @click="sidebarOpen = !sidebarOpen"
          class="text-sm text-apple-gray hover:text-blue-500 transition"
        >
          工作流
        </button>
        <span class="text-sm text-apple-gray">{{ authStore.userName }}</span>
        <button
          @click="logout"
          class="text-sm text-apple-gray hover:text-apple-red transition"
        >
          退出
        </button>
      </div>
    </header>

    <div class="flex-1 flex overflow-hidden">
      <!-- Sidebar: Chat History -->
      <transition name="slide">
        <aside
          v-if="historyOpen"
          class="w-72 border-r border-gray-200 bg-white flex flex-col flex-shrink-0"
        >
          <div class="p-4 border-b border-gray-100">
            <button
              @click="newConversation"
              class="w-full py-2 px-4 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition"
            >
              + 新建对话
            </button>
          </div>
          <div class="flex-1 overflow-y-auto">
            <div v-if="conversations.length === 0" class="p-4 text-sm text-gray-400 text-center">
              暂无聊天记录
            </div>
            <div
              v-for="conv in conversations"
              :key="conv.id"
              @click="loadMessages(conv.id)"
              class="group px-4 py-3 border-b border-gray-50 cursor-pointer hover:bg-gray-50 transition relative"
              :class="{ 'bg-blue-50': currentConversationId === conv.id }"
            >
              <div class="text-sm text-gray-700 truncate pr-6">
                {{ conv.summary || "对话 #" + conv.id }}
              </div>
              <div class="text-xs text-gray-400 mt-1">
                {{ conv.created_at?.slice(0, 16).replace("T", " ") }}
                <span
                  class="ml-2 px-1.5 py-0.5 rounded text-xs"
                  :class="conv.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'"
                >
                  {{ conv.status === "active" ? "进行中" : "已结束" }}
                </span>
              </div>
              <button
                @click="deleteConversation(conv.id, $event)"
                class="absolute top-2 right-2 w-5 h-5 flex items-center justify-center rounded-full text-gray-400 hover:text-red-500 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition text-xs"
                title="删除对话"
              >
                &times;
              </button>
            </div>
          </div>
        </aside>
      </transition>

      <!-- Chat area -->
      <div class="flex-1 flex flex-col min-w-0">
        <ChatCanvas
          :messages="messages"
          :streaming-content="streamingContent"
          :loading="loadingHistory"
        />
        <ChatInput :connected="isConnected" @send="sendMessage" />
      </div>

      <!-- Sidebar: Workflow Visualizer -->
      <transition name="slide">
        <aside
          v-if="sidebarOpen"
          class="w-80 border-l border-gray-200 bg-white overflow-y-auto flex-shrink-0"
        >
          <WorkflowVisualizer :node-status="nodeStatus" />
        </aside>
      </transition>
    </div>
  </div>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: width 0.25s ease;
}
.slide-enter-from,
.slide-leave-to {
  width: 0;
}
</style>
