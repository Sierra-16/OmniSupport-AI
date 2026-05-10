<script setup lang="ts">
defineProps<{
  reviews: any[];
  selectedId: number | null;
  loading: boolean;
}>();

const emit = defineEmits<{
  select: [reviewId: number];
}>();

const priorityLabels: Record<string, string> = {
  refund_approval: "退款审批",
  takeover: "接管对话",
  escalation: "投诉升级",
};

const priorityColors: Record<string, string> = {
  refund_approval: "bg-apple-red/10 text-apple-red",
  takeover: "bg-apple-blue/10 text-apple-blue",
  escalation: "bg-yellow-100 text-yellow-700",
};
</script>

<template>
  <div class="p-4">
    <h2 class="text-sm font-semibold text-gray-900 mb-3">待处理队列</h2>

    <div v-if="loading" class="text-center py-8">
      <div class="animate-spin w-5 h-5 border-2 border-apple-blue border-t-transparent rounded-full mx-auto"></div>
    </div>

    <div v-else-if="reviews.length === 0" class="text-center py-8">
      <p class="text-sm text-apple-gray">暂无待处理任务</p>
    </div>

    <div v-else class="space-y-2">
      <button
        v-for="review in reviews"
        :key="review.id"
        @click="emit('select', review.id)"
        class="w-full text-left p-3 rounded-xl border transition hover:shadow-sm"
        :class="selectedId === review.id ? 'border-apple-blue bg-blue-50' : 'border-gray-100 bg-white'"
      >
        <div class="flex items-center justify-between mb-1">
          <span class="text-xs font-medium text-gray-900">
            #{{ review.id }} {{ priorityLabels[review.action_type] || review.action_type }}
          </span>
          <span
            class="px-2 py-0.5 rounded-full text-xs font-medium"
            :class="priorityColors[review.action_type] || 'bg-gray-100 text-gray-600'"
          >
            {{ review.action_type === 'refund_approval' ? '高' : review.action_type === 'escalation' ? '中' : '低' }}
          </span>
        </div>
        <p class="text-xs text-gray-500">{{ review.created_at }}</p>
      </button>
    </div>
  </div>
</template>
