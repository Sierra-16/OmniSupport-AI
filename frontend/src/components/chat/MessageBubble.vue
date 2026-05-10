<script setup lang="ts">
import { computed } from "vue";
import MarkdownIt from "markdown-it";

const props = defineProps<{
  content: string;
  role: string;
  isError?: boolean;
  isStreaming?: boolean;
}>();

const md = new MarkdownIt({ breaks: true, linkify: true });

const rendered = computed(() => {
  try {
    return md.render(props.content || "");
  } catch {
    return props.content;
  }
});

const isUser = computed(() => props.role === "user");
const isSystem = computed(() => props.role === "system");
</script>

<template>
  <div
    class="flex animate-slide-up"
    :class="isUser ? 'justify-end' : 'justify-start'"
  >
    <div
      class="max-w-[75%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed"
      :class="{
        'bg-apple-blue text-white': isUser,
        'bg-white text-gray-900 shadow-sm border border-gray-100': !isUser && !isError && !isStreaming,
        'bg-apple-red/10 text-apple-red border border-apple-red/20': isError,
        'bg-white text-gray-900 shadow-sm border border-blue-200': isStreaming,
      }"
    >
      <div v-if="isUser">{{ content }}</div>
      <div v-else-if="isStreaming" class="streaming-content">
        <span class="prose prose-sm" v-html="rendered"></span>
        <span class="streaming-cursor"></span>
      </div>
      <div v-else class="prose prose-sm" v-html="rendered"></div>
    </div>
  </div>
</template>

<style scoped>
.streaming-cursor {
  display: inline-block;
  width: 2px;
  height: 1.1em;
  background-color: #3b82f6;
  margin-left: 1px;
  vertical-align: text-bottom;
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>
