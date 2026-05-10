<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  nodeStatus: Record<string, string>;
}>();

const nodes = [
  { id: "supervisor", label: "Supervisor", x: 160, y: 20, desc: "意图识别" },
  { id: "presales", label: "PreSales", x: 40, y: 140, desc: "售前咨询" },
  { id: "aftersales", label: "AfterSales", x: 160, y: 140, desc: "售后处理" },
  { id: "complaint", label: "Complaint", x: 280, y: 140, desc: "投诉建议" },
  { id: "human_review", label: "HITL", x: 100, y: 260, desc: "人工审批" },
  { id: "finalize", label: "Response", x: 220, y: 260, desc: "生成回复" },
];

const edges = [
  { from: "supervisor", to: "presales" },
  { from: "supervisor", to: "aftersales" },
  { from: "supervisor", to: "complaint" },
  { from: "presales", to: "finalize" },
  { from: "aftersales", to: "human_review" },
  { from: "aftersales", to: "finalize" },
  { from: "complaint", to: "human_review" },
  { from: "complaint", to: "finalize" },
  { from: "human_review", to: "finalize" },
];

function statusOf(id: string) {
  const s = props.nodeStatus[id] || "";
  if (s.includes("completed")) return "completed";
  if (s.includes("running")) return "running";
  return "pending";
}

function statusColor(s: string) {
  if (s === "completed") return "#34C759";
  if (s === "running") return "#007AFF";
  return "#E5E5EA";
}

function statusLabel(s: string) {
  if (s === "completed") return "完成";
  if (s === "running") return "运行中";
  return "等待";
}
</script>

<template>
  <div class="p-4">
    <h2 class="text-sm font-semibold text-gray-900 mb-4">工作流状态</h2>

    <div class="relative" style="height: 360px">
      <svg viewBox="0 0 360 320" class="w-full">
        <!-- Edges -->
        <line
          v-for="edge in edges"
          :key="`${edge.from}-${edge.to}`"
          :x1="nodes.find(n => n.id === edge.from)!.x"
          :y1="nodes.find(n => n.id === edge.from)!.y + 24"
          :x2="nodes.find(n => n.id === edge.to)!.x"
          :y2="nodes.find(n => n.id === edge.to)!.y"
          :stroke="statusOf(edge.from) === 'completed' ? '#34C759' : '#E5E5EA'"
          stroke-width="1.5"
          stroke-dasharray="4"
        />

        <!-- Nodes -->
        <g v-for="node in nodes" :key="node.id">
          <rect
            :x="node.x - 32"
            :y="node.y"
            width="64"
            height="48"
            rx="10"
            :fill="statusOf(node.id) === 'running' ? '#EBF5FF' : 'white'"
            :stroke="statusColor(statusOf(node.id))"
            stroke-width="1.5"
            class="transition-all duration-300"
          />
          <text
            :x="node.x"
            :y="node.y + 22"
            text-anchor="middle"
            class="text-[10px] font-medium"
            :fill="statusColor(statusOf(node.id))"
          >
            {{ node.label }}
          </text>
          <text
            :x="node.x"
            :y="node.y + 36"
            text-anchor="middle"
            class="text-[9px]"
            fill="#8E8E93"
          >
            {{ node.desc }}
          </text>
          <!-- Breathe animation dot for running nodes -->
          <circle
            v-if="statusOf(node.id) === 'running'"
            :cx="node.x + 22"
            :cy="node.y + 8"
            r="4"
            fill="#007AFF"
            class="animate-breathe"
          />
        </g>
      </svg>
    </div>

    <!-- Legend -->
    <div class="mt-4 space-y-2">
      <h3 class="text-xs font-medium text-gray-500 mb-2">节点状态</h3>
      <div v-for="node in nodes" :key="'legend-' + node.id" class="flex items-center justify-between">
        <span class="text-xs text-gray-600">{{ node.label }}</span>
        <span
          class="text-xs px-2 py-0.5 rounded-full"
          :class="{
            'bg-gray-100 text-gray-500': statusOf(node.id) === 'pending',
            'bg-blue-100 text-blue-600': statusOf(node.id) === 'running',
            'bg-green-100 text-green-600': statusOf(node.id) === 'completed',
          }"
        >
          {{ statusLabel(statusOf(node.id)) }}
        </span>
      </div>
    </div>
  </div>
</template>
