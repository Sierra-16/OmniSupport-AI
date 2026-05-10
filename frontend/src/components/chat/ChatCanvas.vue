<script setup lang="ts">
import { ref, watch, nextTick } from "vue";
import MessageBubble from "./MessageBubble.vue";

const props = defineProps<{
  messages: any[];
  streamingContent: string;
  loading?: boolean;
}>();

const container = ref<HTMLElement | null>(null);

function isNodeStatus(msg: any) {
  return msg.role === "node_status";
}

function isUser(msg: any) {
  return msg.role === "user";
}

// Auto-scroll when messages or streaming content change
watch(
  () => [props.messages.length, props.streamingContent],
  async () => {
    await nextTick();
    if (container.value) {
      container.value.scrollTop = container.value.scrollHeight;
    }
  }
);
</script>

<template>
  <div ref="container" class="flex-1 overflow-y-auto px-5 py-4 space-y-4">
    <div v-if="messages.length === 0 && !streamingContent" class="flex items-center justify-center h-full">
      <div class="text-center">
        <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-apple-blue/10 flex items-center justify-center">
          <svg class="w-8 h-8 text-apple-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        </div>
        <p class="text-lg font-medium text-gray-900">有什么可以帮您？</p>
        <p class="mt-1 text-sm text-apple-gray">您可以咨询商品、查询订单或申请售后</p>
      </div>
    </div>

    <template v-for="(msg, i) in messages" :key="i">
      <MessageBubble
        v-if="!isNodeStatus(msg)"
        :content="msg.content"
        :role="msg.role"
        :is-error="msg.isError"
      />
      <div
        v-else
        class="flex items-center gap-2 animate-fade-in"
      >
        <div
          class="w-2 h-2 rounded-full"
          :class="{
            'bg-gray-300': msg.status === 'pending',
            'bg-apple-blue animate-breathe': msg.status === 'running',
            'bg-apple-green': msg.status === 'completed',
            'bg-apple-red': msg.status === 'error',
          }"
        ></div>
        <span class="text-xs text-apple-gray">{{ msg.message }}</span>
      </div>
    </template>

    <!-- Streaming message bubble -->
    <MessageBubble
      v-if="streamingContent"
      :content="streamingContent"
      role="assistant"
      :is-streaming="true"
    />

    <!-- Loading indicator -->
    <div
      v-if="loading"
      class="flex items-center justify-center py-8"
    >
      <div class="flex gap-1">
        <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
        <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.15s"></div>
        <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.3s"></div>
      </div>
    </div>
  </div>
</template>
