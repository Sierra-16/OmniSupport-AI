<script setup lang="ts">
import { ref } from "vue";

const props = defineProps<{
  review: any;
}>();

const emit = defineEmits<{
  action: [action: string, message?: string];
}>();

const adminMessage = ref("");
const showMessageInput = ref(false);

const review = props.review?.review;
const messages = props.review?.messages || [];
const checkpoint = props.review?.checkpoint || {};

function handleAction(action: string) {
  if (action === "takeover" && showMessageInput.value) {
    emit("action", action, adminMessage.value);
    adminMessage.value = "";
    showMessageInput.value = false;
  } else {
    emit("action", action);
  }
}
</script>

<template>
  <div class="p-5" v-if="review">
    <!-- Review Header -->
    <div class="mb-4">
      <h2 class="text-lg font-semibold text-gray-900">
        {{ review.action_type === "refund_approval" ? "退款审批" : review.action_type === "escalation" ? "投诉升级" : "人工接管" }}
      </h2>
      <p class="text-sm text-apple-gray mt-0.5">
        待处理 #{{ review.id }} · 状态: {{ review.status }}
      </p>
    </div>

    <!-- Conversation History -->
    <div class="mb-5">
      <h3 class="text-sm font-medium text-gray-700 mb-2">对话历史</h3>
      <div class="space-y-2 max-h-64 overflow-y-auto bg-gray-50 rounded-xl p-3">
        <div
          v-for="(msg, i) in messages"
          :key="i"
          class="text-sm"
          :class="msg.role === 'user' ? 'text-apple-blue' : 'text-gray-700'"
        >
          <span class="text-xs font-medium text-gray-400">{{ msg.role === 'user' ? '用户' : 'AI' }}:</span>
          {{ msg.content }}
        </div>
        <p v-if="messages.length === 0" class="text-xs text-gray-400">暂无对话记录</p>
      </div>
    </div>

    <!-- AI Decision Chain -->
    <div class="mb-5">
      <h3 class="text-sm font-medium text-gray-700 mb-2">AI 决策链</h3>
      <div class="bg-gray-50 rounded-xl p-3">
        <pre class="text-xs text-gray-600 whitespace-pre-wrap">{{ JSON.stringify(checkpoint, null, 2) }}</pre>
      </div>
    </div>

    <!-- Admin Message Input (for takeover) -->
    <div v-if="showMessageInput" class="mb-4">
      <label class="block text-sm font-medium text-gray-700 mb-1">回复消息</label>
      <textarea
        v-model="adminMessage"
        rows="3"
        class="w-full px-3 py-2 rounded-xl border border-gray-200 focus:border-apple-blue focus:ring-1 focus:ring-apple-blue outline-none text-sm"
        placeholder="输入回复内容..."
      ></textarea>
    </div>

    <!-- Action Buttons -->
    <div class="flex gap-3">
      <button
        @click="handleAction('approved')"
        class="px-4 py-2 bg-apple-green text-white rounded-xl text-sm font-medium hover:opacity-90 transition"
      >
        审批通过
      </button>
      <button
        @click="handleAction('rejected')"
        class="px-4 py-2 bg-apple-red text-white rounded-xl text-sm font-medium hover:opacity-90 transition"
      >
        审批驳回
      </button>
      <button
        v-if="!showMessageInput"
        @click="showMessageInput = true"
        class="px-4 py-2 bg-apple-blue text-white rounded-xl text-sm font-medium hover:opacity-90 transition"
      >
        接管回复
      </button>
      <button
        v-if="showMessageInput"
        @click="handleAction('takeover')"
        :disabled="!adminMessage.trim()"
        class="px-4 py-2 bg-apple-blue text-white rounded-xl text-sm font-medium hover:opacity-90 transition disabled:opacity-40"
      >
        发送回复
      </button>
      <button
        @click="handleAction('close')"
        class="px-4 py-2 bg-gray-200 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-300 transition"
      >
        关闭工单
      </button>
    </div>
  </div>
</template>
