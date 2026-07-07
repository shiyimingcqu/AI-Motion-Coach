<template>
  <div class="page admin-page template-admin-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Scoring Templates</p>
        <h1>评分模板管理</h1>
        <p class="subtle">为每个动作维护一个启用模板，小程序实时训练会按该模板计算单次动作相似度。</p>
      </div>
      <button class="primary-button" type="button" @click="openUpload">上传模板视频</button>
    </header>

    <section class="template-toolbar panel">
      <label>
        <span>动作</span>
        <select v-model="selectedExercise" @change="loadTemplates">
          <option :value="ALL_EXERCISES">全部动作</option>
          <option v-for="exercise in exercises" :key="exercise.key" :value="exercise.key">
            {{ exercise.name }}
          </option>
        </select>
      </label>
      <div class="template-summary">
        <strong>{{ summaryTitle }}</strong>
        <span>{{ summaryDescription }}</span>
      </div>
    </section>

    <section class="admin-table panel">
      <div v-if="loading" class="admin-empty">加载中...</div>
      <template v-else-if="templates.length">
        <div class="admin-table-head admin-template-grid">
          <span>模板</span>
          <span>动作</span>
          <span>来源</span>
          <span>视角</span>
          <span>帧数</span>
          <span>状态</span>
          <span>操作</span>
        </div>
        <div v-for="template in templates" :key="`${template.action}:${template.template_id}`" class="admin-table-row admin-template-grid">
          <div>
            <strong>{{ template.name }}</strong>
            <small class="row-desc">{{ template.template_id }} · {{ template.version || "default" }}</small>
          </div>
          <span>{{ exerciseName(template.action) }}</span>
          <span>{{ sourceName(template.source) }}</span>
          <span>{{ viewName(template.view) }}</span>
          <span>{{ template.valid_frames || 0 }}</span>
          <span class="status-pill" :class="template.is_enabled ? 'good' : 'idle'">
            {{ template.is_enabled ? "已启用" : "未启用" }}
          </span>
          <div class="admin-row-actions">
            <button
              v-if="template.is_enabled"
              class="text-button danger"
              type="button"
              @click="disableTemplate(template)"
            >
              取消启用
            </button>
            <button
              v-else
              class="text-button"
              type="button"
              @click="enableTemplate(template)"
            >
              启用
            </button>
          </div>
        </div>
      </template>
      <div v-else class="admin-empty">当前动作还没有评分模板，请上传一段完整标准动作视频。</div>
    </section>

    <div v-if="showUploadModal" class="modal-overlay" @click.self="closeUpload">
      <div class="modal-card">
        <h3 class="modal-title">上传评分模板视频</h3>
        <div class="modal-form">
          <label>
            <span>动作</span>
            <select v-model="uploadForm.exercise">
              <option v-for="exercise in exercises" :key="exercise.key" :value="exercise.key">
                {{ exercise.name }}
              </option>
            </select>
          </label>
          <label>
            <span>模板名称</span>
            <input v-model="uploadForm.name" type="text" placeholder="例如：深蹲侧面标准模板" />
          </label>
          <label>
            <span>视角</span>
            <select v-model="uploadForm.view">
              <option value="side">侧面</option>
              <option value="front">正面</option>
              <option value="diagonal">斜侧</option>
            </select>
          </label>
          <label>
            <span>版本</span>
            <input v-model="uploadForm.version" type="text" placeholder="v1" />
          </label>
          <label class="file-label">
            <span>视频文件</span>
            <div class="file-drop" @click="fileInput?.click()">
              <span>{{ selectedFile ? selectedFile.name : "点击选择视频文件" }}</span>
            </div>
            <input ref="fileInput" type="file" accept="video/*" hidden @change="onFileChange" />
          </label>
        </div>
        <div class="modal-actions">
          <button class="secondary-button" type="button" :disabled="uploading" @click="closeUpload">取消</button>
          <button class="primary-button" type="button" :disabled="uploading || !selectedFile" @click="submitUpload">
            {{ uploading ? "提取模板中..." : "上传并生成模板" }}
          </button>
        </div>
        <p v-if="uploadError" class="form-error">{{ uploadError }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { apiDelete, apiGet, apiPost, apiUpload } from "@/api/client";
import { getSimpleExercises, type ExerciseLibItem } from "@/api/exercises";

type TemplateItem = {
  template_id: string;
  action: string;
  name: string;
  view: string;
  version?: string;
  valid_frames?: number;
  source: string;
  is_enabled?: boolean;
};

const fallbackExercises: ExerciseLibItem[] = [
  { key: "squat", name: "深蹲", description: "", supported_metrics: [] },
  { key: "push_up", name: "俯卧撑", description: "", supported_metrics: [] },
  { key: "plank", name: "平板支撑", description: "", supported_metrics: [] },
  { key: "lunge", name: "弓步蹲", description: "", supported_metrics: [] },
  { key: "jumping_jack", name: "开合跳", description: "", supported_metrics: [] },
  { key: "burpee", name: "波比跳", description: "", supported_metrics: [] },
  { key: "high_knees", name: "高抬腿", description: "", supported_metrics: [] },
];

const route = useRoute();
const ALL_EXERCISES = "__all__";
const exercises = ref<ExerciseLibItem[]>(fallbackExercises);
const selectedExercise = ref(typeof route.query.exercise === "string" ? route.query.exercise : "squat");
const templates = ref<TemplateItem[]>([]);
const loading = ref(false);
const showUploadModal = ref(false);
const uploading = ref(false);
const uploadError = ref("");
const selectedFile = ref<File | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);

const uploadForm = ref({
  exercise: selectedExercise.value,
  name: "",
  view: "side",
  version: "v1",
});

const activeTemplate = computed(() => templates.value.find((template) => template.is_enabled));
const enabledTemplates = computed(() => templates.value.filter((template) => template.is_enabled));
const summaryTitle = computed(() => {
  if (selectedExercise.value === ALL_EXERCISES) {
    return `全部动作模板：${templates.value.length} 个`;
  }
  return activeTemplate.value ? activeTemplate.value.name : "未启用模板";
});
const summaryDescription = computed(() => {
  if (selectedExercise.value === ALL_EXERCISES) {
    return `已启用 ${enabledTemplates.value.length} 个动作模板，未启用动作将继续使用规则评分兜底`;
  }
  return activeTemplate.value
    ? `当前标准：${activeTemplate.value.template_id}`
    : "未启用时将继续使用规则评分兜底";
});

async function loadExercises() {
  try {
    const response = await getSimpleExercises();
    if (response.items?.length) {
      exercises.value = response.items;
    }
  } catch {
    exercises.value = fallbackExercises;
  }
}

async function loadTemplates() {
  loading.value = true;
  try {
    if (selectedExercise.value === ALL_EXERCISES) {
      const responses = await Promise.all(
        exercises.value.map((exercise) =>
          apiGet<{ items: TemplateItem[] }>(`/exercises/${exercise.key}/templates`)
        )
      );
      templates.value = responses.flatMap((response) => response.items || []);
    } else {
      const response = await apiGet<{ items: TemplateItem[] }>(`/exercises/${selectedExercise.value}/templates`);
      templates.value = response.items || [];
    }
  } catch (err: any) {
    templates.value = [];
    uploadError.value = err?.message || "模板列表加载失败";
  } finally {
    loading.value = false;
  }
}

function openUpload() {
  uploadError.value = "";
  uploadForm.value.exercise = selectedExercise.value === ALL_EXERCISES
    ? exercises.value[0]?.key || "squat"
    : selectedExercise.value;
  showUploadModal.value = true;
}

function closeUpload() {
  showUploadModal.value = false;
  uploading.value = false;
  uploadError.value = "";
  selectedFile.value = null;
  if (fileInput.value) fileInput.value.value = "";
}

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  selectedFile.value = input.files?.[0] ?? null;
}

async function submitUpload() {
  if (!selectedFile.value) return;
  uploading.value = true;
  uploadError.value = "";
  try {
    const shouldReturnToAll = selectedExercise.value === ALL_EXERCISES;
    const fd = new FormData();
    fd.append("file", selectedFile.value);
    fd.append("name", uploadForm.value.name || `${exerciseName(uploadForm.value.exercise)}评分模板`);
    fd.append("view", uploadForm.value.view);
    fd.append("version", uploadForm.value.version || "v1");
    await apiUpload(`/exercises/${uploadForm.value.exercise}/templates/from-video`, fd);
    selectedExercise.value = shouldReturnToAll ? ALL_EXERCISES : uploadForm.value.exercise;
    closeUpload();
    await loadTemplates();
  } catch (err: any) {
    uploadError.value = err?.message || "上传失败，请检查视频是否能提取到有效关键点";
  } finally {
    uploading.value = false;
  }
}

async function enableTemplate(template: TemplateItem) {
  await apiPost("/admin/templates/active", {
    action: template.action,
    template_id: template.template_id,
  });
  await loadTemplates();
}

async function disableTemplate(template: TemplateItem) {
  await apiDelete(`/admin/templates/active/${template.action}`);
  await loadTemplates();
}

function exerciseName(key: string): string {
  return exercises.value.find((exercise) => exercise.key === key)?.name || key;
}

function sourceName(source: string): string {
  return source === "builtin" ? "内置" : "上传";
}

function viewName(view: string): string {
  const map: Record<string, string> = { side: "侧面", front: "正面", diagonal: "斜侧", default: "默认" };
  return map[view] || view;
}

onMounted(async () => {
  await loadExercises();
  if (selectedExercise.value !== ALL_EXERCISES && !exercises.value.some((exercise) => exercise.key === selectedExercise.value)) {
    selectedExercise.value = exercises.value[0]?.key || "squat";
  }
  await loadTemplates();
  if (route.query.exercise) {
    openUpload();
  }
});
</script>

<style scoped>
.template-admin-page {
  display: grid;
  gap: 18px;
}

.template-toolbar {
  display: grid;
  grid-template-columns: minmax(220px, 320px) 1fr;
  gap: 18px;
  align-items: end;
  padding: 18px;
}

.template-toolbar label,
.modal-form label {
  display: grid;
  gap: 8px;
  color: #475569;
  font-size: 13px;
}

.template-toolbar select,
.modal-form input,
.modal-form select {
  min-height: 40px;
  border: 1px solid #d7deea;
  border-radius: 8px;
  padding: 0 12px;
  background: #fff;
  color: #111827;
  outline: none;
}

.template-summary {
  display: grid;
  gap: 4px;
  color: #64748b;
}

.template-summary strong {
  color: #0f172a;
}

.admin-template-grid {
  display: grid;
  grid-template-columns: minmax(220px, 1.7fr) 0.8fr 0.7fr 0.7fr 0.6fr 0.7fr 1fr;
  align-items: center;
  gap: 0 12px;
}

.row-desc {
  display: block;
  margin-top: 3px;
  color: #64748b;
  font-size: 12px;
}

.admin-empty {
  padding: 42px;
  text-align: center;
  color: #64748b;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 999;
  display: grid;
  place-items: center;
  background: rgba(15, 23, 42, 0.42);
  padding: 20px;
}

.modal-card {
  width: min(520px, 100%);
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.22);
}

.modal-title {
  margin: 0 0 18px;
  font-size: 18px;
  color: #0f172a;
}

.modal-form {
  display: grid;
  gap: 14px;
}

.file-drop {
  min-height: 46px;
  display: flex;
  align-items: center;
  border: 1px dashed #9fb0c7;
  border-radius: 8px;
  padding: 0 14px;
  background: #f8fafc;
  cursor: pointer;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.form-error {
  margin: 12px 0 0;
  color: #dc2626;
  font-size: 13px;
}

.danger {
  color: #dc2626 !important;
}

@media (max-width: 1000px) {
  .template-toolbar,
  .admin-template-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }
}
</style>
