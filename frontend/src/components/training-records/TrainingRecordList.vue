<template>
  <section class="tr-list">
    <header class="tr-list-header">
      <h3>训练记录列表</h3>
      <button class="tr-export-btn" type="button" @click="$emit('export')">
        <Download :size="14" />
        <span>导出记录</span>
      </button>
    </header>

    <div class="tr-list-body">
      <StateDisplay v-if="loading" type="loading" skeleton="list" :skeleton-rows="4" text="加载训练记录..." />
      <StateDisplay
        v-else-if="!records.length"
        type="empty"
        title="暂无训练记录"
        text="完成训练后，记录将在这里显示"
      />
      <template v-else>
        <TrainingRecordItem
          v-for="r in records"
          :key="r.session_id"
          :record="r"
          @click="(rec) => $emit('openDetail', rec.session_id)"
        />
        <div v-if="hasMore" class="tr-list-more">
          <button type="button" @click="$emit('loadMore')">加载更多</button>
        </div>
      </template>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Download } from "lucide-vue-next";
import StateDisplay from "@/components/StateDisplay.vue";
import TrainingRecordItem from "./TrainingRecordItem.vue";

defineProps<{
  records: any[];
  loading: boolean;
  hasMore: boolean;
}>();

defineEmits<{
  (e: "openDetail", id: string): void;
  (e: "loadMore"): void;
  (e: "export"): void;
}>();
</script>

<style scoped>
.tr-list {
  background: #ffffff;
  border: 1px solid #eef0f6;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(45, 35, 90, 0.06);
  overflow: hidden;
}

.tr-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px;
  border-bottom: 1px solid #f1f3f9;
}

.tr-list-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #15172A;
}

.tr-export-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 34px;
  padding: 0 14px;
  background: #ffffff;
  color: #6C3BFF;
  border: 1px solid #d4c5ff;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s;
}

.tr-export-btn:hover {
  background: #f1ecff;
  border-color: #6C3BFF;
}

.tr-list-body { padding: 0; }

.tr-list-more {
  display: flex;
  justify-content: center;
  padding: 18px;
}

.tr-list-more button {
  background: transparent;
  border: 0;
  color: #6C3BFF;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  padding: 8px 18px;
  border-radius: 8px;
  transition: background 0.18s;
}

.tr-list-more button:hover { background: #f1ecff; }
</style>
