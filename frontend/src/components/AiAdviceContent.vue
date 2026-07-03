<script setup lang="ts">
import { computed } from "vue";
import { renderMarkdown } from "@/utils";

const props = withDefaults(
  defineProps<{
    content: string;
    placeholder?: string;
  }>(),
  {
    placeholder: "暂无 AI 建议。",
  }
);

const html = computed(() => (props.content?.trim() ? renderMarkdown(props.content) : ""));
</script>

<template>
  <div v-if="html" class="ai-advice-markdown" v-html="html" />
  <p v-else class="ai-advice-markdown ai-advice-markdown--empty">{{ placeholder }}</p>
</template>

<style scoped>
.ai-advice-markdown {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: #475569;
  word-break: break-word;
}

.ai-advice-markdown--empty {
  color: #94a3b8;
}

.ai-advice-markdown :deep(p) {
  margin: 0 0 0.75em;
}

.ai-advice-markdown :deep(p:last-child) {
  margin-bottom: 0;
}

.ai-advice-markdown :deep(strong) {
  color: #0f172a;
  font-weight: 600;
}

.ai-advice-markdown :deep(h1),
.ai-advice-markdown :deep(h2),
.ai-advice-markdown :deep(h3),
.ai-advice-markdown :deep(h4) {
  margin: 0.9em 0 0.5em;
  color: #1e293b;
  font-size: 14px;
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

.ai-advice-markdown :deep(code) {
  padding: 0.1em 0.35em;
  border-radius: 4px;
  background: #f1f5f9;
  font-size: 12px;
}

.ai-advice-markdown :deep(li:last-child) {
  margin-bottom: 0;
}
</style>
