import { ref, onUnmounted } from "vue";

export function useChatWebSocket() {
  const ws = ref<WebSocket | null>(null);
  const connected = ref(false);
  const messages = ref<any[]>([]);
  const nodeStatus = ref<Record<string, string>>({});
  const finalResponse = ref("");
  const error = ref("");

  let reconnectTimer: number | null = null;

  function connect(token: string) {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${protocol}//${window.location.host}/ws/chat`;

    ws.value = new WebSocket(url);

    ws.value.onopen = () => {
      connected.value = true;
      ws.value!.send(JSON.stringify({ token }));
    };

    ws.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === "error") {
          error.value = data.content;
          return;
        }

        if (data.type === "final") {
          finalResponse.value = data.content;
          messages.value.push({ role: "assistant", content: data.content });
          return;
        }

        // Handle node status updates
        if (data.node_status) {
          Object.assign(nodeStatus.value, data.node_status);
        }

        // Handle messages from graph events
        if (data.messages) {
          const msgs = Array.isArray(data.messages) ? data.messages : [data.messages];
          for (const msg of msgs) {
            try {
              const content = typeof msg === "string" ? JSON.parse(msg) : msg;
              if (content.role === "node_status") {
                const statusInfo = JSON.parse(content.content);
                nodeStatus.value[statusInfo.node] = statusInfo.status;
                messages.value.push({
                  role: "node_status",
                  node: statusInfo.node,
                  status: statusInfo.status,
                  message: statusInfo.message || "",
                });
              } else if (content.role === "user" || content.role === "assistant") {
                messages.value.push(content);
              }
            } catch {
              if (typeof msg === "object" && msg.role) {
                messages.value.push(msg);
              }
            }
          }
        }
      } catch (e) {
        // Ignore parse errors for non-JSON messages
      }
    };

    ws.value.onclose = () => {
      connected.value = false;
      // Auto-reconnect after 3s
      reconnectTimer = window.setTimeout(() => {
        if (!connected.value) {
          connect(token);
        }
      }, 3000);
    };

    ws.value.onerror = () => {
      error.value = "WebSocket 连接错误";
    };
  }

  function sendMessage(message: string) {
    if (ws.value && connected.value) {
      messages.value.push({ role: "user", content: message });
      ws.value.send(JSON.stringify({ message }));
    }
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
    }
    ws.value?.close();
    connected.value = false;
  }

  onUnmounted(() => {
    disconnect();
  });

  return { connected, messages, nodeStatus, finalResponse, error, connect, sendMessage, disconnect };
}

export function useAdminWebSocket() {
  const ws = ref<WebSocket | null>(null);
  const connected = ref(false);
  const pendingReviews = ref<any[]>([]);
  const adminError = ref("");

  function connect(token: string) {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${protocol}//${window.location.host}/ws/admin`;

    ws.value = new WebSocket(url);

    ws.value.onopen = () => {
      connected.value = true;
      adminError.value = "";
      ws.value!.send(JSON.stringify({ token }));
    };

    ws.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "error") {
          adminError.value = data.content || "权限不足";
          connected.value = false;
          return;
        }
        if (data.type === "pending_queue") {
          pendingReviews.value = data.reviews || [];
        } else if (data.type === "new_review") {
          pendingReviews.value = [data.review, ...pendingReviews.value];
        }
      } catch {
        // ignore parse errors
      }
    };

    ws.value.onclose = () => {
      connected.value = false;
    };

    ws.value.onerror = () => {
      connected.value = false;
      adminError.value = "WebSocket 连接失败，请确认后端已启动";
    };
  }

  function sendReviewAction(reviewId: number, action: string, message?: string) {
    if (ws.value && connected.value) {
      ws.value.send(JSON.stringify({
        type: "review_action",
        review_id: reviewId,
        action,
        message,
      }));
    }
  }

  function disconnect() {
    ws.value?.close();
    connected.value = false;
  }

  onUnmounted(() => {
    disconnect();
  });

  return { connected, pendingReviews, adminError, connect, sendReviewAction, disconnect };
}
