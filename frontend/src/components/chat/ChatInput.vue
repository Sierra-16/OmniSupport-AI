<script setup lang="ts">
import { ref } from "vue";

defineProps<{
  connected: boolean;
}>();

const emit = defineEmits<{
  send: [text: string];
}>();

const text = ref("");

function handleSend() {
  const trimmed = text.value.trim();
  if (!trimmed) return;
  emit("send", trimmed);
  text.value = "";
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
}
</script>

<template>
  <div class="px-5 py-3 bg-white/80 backdrop-blur-md border-t border-gray-100">
    <div class="flex items-end gap-3 max-w-3xl mx-auto">
      <textarea
        v-model="text"
        @keydown="handleKeydown"
        :disabled="!connected"
        rows="1"
        class="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 focus:border-apple-blue focus:ring-1 focus:ring-apple-blue outline-none resize-none text-sm placeholder:text-gray-400 disabled:bg-gray-50 transition"
        placeholder="输入您的问题..."
      ></textarea>
      <button
        @click="handleSend"
        :disabled="!connected || !text.trim()"
        class="px-5 py-2.5 bg-apple-blue text-white rounded-xl font-medium text-sm hover:opacity-90 disabled:opacity-40 transition flex-shrink-0"
      >
        发送
      </button>
    </div>
  </div>
</template>
