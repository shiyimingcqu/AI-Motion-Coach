<script setup lang="ts">
import { computed } from "vue";
import { renderMarkdown } from "@/utils/markdown";

const props = withDefaults(
  defineProps<{
    content: string;
    placeholder?: string;
    theme?: "light" | "dark";
  }>(),
  {
    placeholder: "暂无 AI 建议。",
    theme: "dark",
  }
);

const html = computed(() => (props.content?.trim() ? renderMarkdown(props.content) : ""));
</script>

<template>
  <div
    class="ai-advice-markdown"
    :class="[`ai-advice-markdown--${theme}`, { 'ai-advice-markdown--empty-state': !html }]"
  >
    <div v-if="html" v-html="html" />
    <p v-else>{{ placeholder }}</p>
  </div>
</template>

<style scoped>
.ai-advice-markdown {
  margin: 0;
  font-size: 14px;
  line-height: 1.75;
  word-break: break-word;
}

.ai-advice-markdown--dark {
  color: #cbd5e1;
}

.ai-advice-markdown--light {
  color: #334155;
}

.ai-advice-markdown--empty-state p {
  margin: 0;
}

.ai-advice-markdown--dark.ai-advice-markdown--empty-state p {
  color: #94a3b8;
}

.ai-advice-markdown--light.ai-advice-markdown--empty-state p {
  color: #64748b;
}

.ai-advice-markdown :deep(p) {
  margin: 0 0 0.75em;
}

.ai-advice-markdown :deep(p:last-child) {
  margin-bottom: 0;
}

.ai-advice-markdown--dark :deep(strong) {
  color: #f1f5f9;
  font-weight: 600;
}

.ai-advice-markdown--light :deep(strong) {
  color: #0f172a;
  font-weight: 600;
}

.ai-advice-markdown--dark :deep(h1),
.ai-advice-markdown--dark :deep(h2),
.ai-advice-markdown--dark :deep(h3),
.ai-advice-markdown--dark :deep(h4) {
  margin: 0.9em 0 0.5em;
  color: #e2e8f0;
  font-size: 15px;
  font-weight: 600;
}

.ai-advice-markdown--light :deep(h1),
.ai-advice-markdown--light :deep(h2),
.ai-advice-markdown--light :deep(h3),
.ai-advice-markdown--light :deep(h4) {
  margin: 1em 0 0.55em;
  color: #0f172a;
  font-size: 15px;
  font-weight: 600;
}

.ai-advice-markdown :deep(h1:first-child),
.ai-advice-markdown :deep(h2:first-child),
.ai-advice-markdown :deep(h3:first-child),
.ai-advice-markdown :deep(h4:first-child) {
  margin-top: 0;
}

.ai-advice-markdown :deep(ul),
.ai-advice-markdown :deep(ol) {
  margin: 0.4em 0 0.8em;
  padding-left: 1.25em;
}

.ai-advice-markdown :deep(li) {
  margin-bottom: 0.35em;
}

.ai-advice-markdown--dark :deep(code) {
  padding: 0.1em 0.35em;
  border-radius: 4px;
  background: rgba(148, 163, 184, 0.15);
  font-size: 12px;
}

.ai-advice-markdown--light :deep(code) {
  padding: 0.1em 0.35em;
  border-radius: 4px;
  background: #eef2ff;
  color: #3730a3;
  font-size: 12px;
}

.ai-advice-markdown :deep(li:last-child) {
  margin-bottom: 0;
}
</style>
