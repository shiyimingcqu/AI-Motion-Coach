<template>
  <div class="page admin-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Rule Management</p>
        <h1>动作规则管理</h1>
        <p class="subtle">维护动作检测规则、评分阈值、错误提示和标准动作模板。</p>
      </div>
      <button v-if="authStore.isAdmin" class="primary-button" type="button" @click="openNewExerciseModal">
        <Plus :size="18" />
        新增动作
      </button>
    </header>

    <StateDisplay v-if="loading" type="loading" skeleton="cards" text="加载动作库..." />

    <section v-else class="split-layout">
      <aside class="filter-panel">
        <h2>筛选栏</h2>
        <div class="filter-group">
          <strong>动作类型</strong>
          <button
            v-for="exercise in exercises"
            :key="exercise.key"
            type="button"
            :class="{ active: selectedKey === exercise.key }"
            @click="selectedKey = exercise.key"
          >
            {{ exercise.name }}
          </button>
        </div>
      </aside>

      <section class="exercise-grid">
        <article v-for="exercise in visibleExercises" :key="exercise.key" class="exercise-card">
          <div class="exercise-visual" :style="{ '--accent': exercise.accent }">
            <Dumbbell :size="34" />
          </div>
          <div>
            <p class="eyebrow">{{ exercise.category }}</p>
            <h2>{{ exercise.name }}</h2>
          </div>
          <p>{{ exercise.description }}</p>
          <p>推荐时长 {{ exercise.duration }}，支持 {{ exercise.modes.join(" / ") }}。</p>
          <div class="error-chips compact">
            <span v-for="error in exercise.errors" :key="error">{{ error }}</span>
          </div>
          <div class="card-actions">
            <button class="primary-button" type="button" @click="start(exercise.key)">开始训练</button>
            <button class="secondary-button" type="button" @click="openEditModal(exercise)">编辑</button>
            <button
              v-if="authStore.isAdmin"
              class="template-button"
              type="button"
              @click="openTemplateModal(exercise)"
            >
              <Upload :size="16" />
              添加标准动作
            </button>
            <button
              v-if="authStore.isAdmin"
              class="secondary-button danger"
              type="button"
              @click="handleDelete(exercise)"
            >
              删除
            </button>
          </div>
        </article>
      </section>
    </section>

    <div v-if="showFormModal" class="modal-overlay" @click.self="closeFormModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ editingExercise ? "编辑动作" : "新增动作" }}</h3>
          <button class="close-button" type="button" @click="closeFormModal"><X :size="20" /></button>
        </div>
        <form class="template-form" @submit.prevent="submitExerciseForm">
          <label class="form-field">
            <span>动作 key</span>
            <input v-model="formData.key" type="text" placeholder="squat" :readonly="!!editingExercise" required />
          </label>
          <label class="form-field">
            <span>名称</span>
            <input v-model="formData.name" type="text" placeholder="深蹲" required />
          </label>
          <label class="form-field">
            <span>分类</span>
            <select v-model="formData.category">
              <option value="下肢力量">下肢力量</option>
              <option value="上肢力量">上肢力量</option>
              <option value="核心稳定">核心稳定</option>
              <option value="心肺训练">心肺训练</option>
              <option value="全身">全身</option>
            </select>
          </label>
          <label class="form-field">
            <span>难度</span>
            <select v-model="formData.level">
              <option value="初级">初级</option>
              <option value="中级">中级</option>
              <option value="高级">高级</option>
            </select>
          </label>
          <label class="form-field">
            <span>时长</span>
            <input v-model="formData.duration" type="text" placeholder="10 分钟" />
          </label>
          <label class="form-field">
            <span>描述</span>
            <textarea v-model="formData.description" placeholder="动作标准描述" rows="3" />
          </label>
          <label class="form-field">
            <span>常见错误（逗号分隔）</span>
            <input v-model="formData.errors" type="text" placeholder="膝盖内扣,下蹲深度不足" />
          </label>
          <div v-if="formError" class="error-message">{{ formError }}</div>
          <button class="primary-button" type="submit" :disabled="formSubmitting">
            {{ editingExercise ? "保存修改" : "创建动作" }}
          </button>
        </form>
      </div>
    </div>

    <div v-if="showTemplateModal" class="modal-overlay" @click.self="closeTemplateModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>添加标准动作模板 - {{ templateTarget?.name }}</h3>
          <button class="close-button" type="button" @click="closeTemplateModal"><X :size="20" /></button>
        </div>
        <div v-if="templateUploadSuccess" class="success-message">
          <CheckCircle :size="48" class="success-icon" />
          <h4>模板生成成功</h4>
          <p>有效帧数：{{ templateResult.valid_frames }} 帧</p>
          <p>模板路径：{{ templateResult.template_path }}</p>
          <button class="primary-button" type="button" @click="closeTemplateModal">确定</button>
        </div>
        <form v-else class="template-form" @submit.prevent="submitTemplate">
          <label class="form-field">
            <span>模板名称</span>
            <input v-model="templateForm.name" type="text" placeholder="例如：标准侧面深蹲" required />
          </label>
          <label class="form-field">
            <span>拍摄角度</span>
            <select v-model="templateForm.view">
              <option value="side">侧面</option>
              <option value="front">正面</option>
              <option value="diagonal">斜侧面</option>
            </select>
          </label>
          <label class="file-upload" :class="{ 'has-file': templateForm.videoFile }">
            <input ref="fileInput" type="file" accept="video/*" required @change="handleFileChange" />
            <Upload :size="32" />
            <span>{{ templateForm.videoFile ? templateForm.videoFile.name : "点击上传标准动作视频" }}</span>
            <small>支持 MP4、MOV、AVI 等常见格式</small>
          </label>
          <div v-if="templateError" class="error-message">{{ templateError }}</div>
          <button class="primary-button" type="submit" :disabled="isUploading || !templateForm.videoFile">
            <Loader2 v-if="isUploading" :size="18" class="spin" />
            <span v-else>生成模板</span>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useTrainingStore } from "@/stores/training";
import { apiUpload } from "@/api/client";
import {
  createExercise,
  deleteExercise,
  getExerciseLibrary,
  updateExercise,
  type ExerciseItem,
} from "@/api/exercises";
import { CheckCircle, Dumbbell, Loader2, Plus, Upload, X } from "lucide-vue-next";
import StateDisplay from "@/components/StateDisplay.vue";

const router = useRouter();
const trainingStore = useTrainingStore();
const authStore = useAuthStore();

const loading = ref(true);
const exercises = ref<ExerciseItem[]>([]);
const selectedKey = ref("");

const visibleExercises = computed(() =>
  selectedKey.value
    ? exercises.value.filter((exercise) => exercise.key === selectedKey.value)
    : exercises.value
);

function splitErrors(value: string) {
  return value
    .split(/[,，]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function start(exerciseKey: string) {
  trainingStore.setExercise(exerciseKey);
  router.push("/realtime");
}

const showFormModal = ref(false);
const editingExercise = ref<ExerciseItem | null>(null);
const formSubmitting = ref(false);
const formError = ref("");

const formData = reactive({
  key: "",
  name: "",
  category: "下肢力量",
  level: "中级",
  duration: "10 分钟",
  description: "",
  errors: "",
});

function openNewExerciseModal() {
  editingExercise.value = null;
  formData.key = "";
  formData.name = "";
  formData.category = "下肢力量";
  formData.level = "中级";
  formData.duration = "10 分钟";
  formData.description = "";
  formData.errors = "";
  formError.value = "";
  showFormModal.value = true;
}

function openEditModal(exercise: ExerciseItem) {
  editingExercise.value = exercise;
  formData.key = exercise.key;
  formData.name = exercise.name;
  formData.category = exercise.category;
  formData.level = exercise.level;
  formData.duration = exercise.duration;
  formData.description = exercise.description;
  formData.errors = exercise.errors.join(",");
  formError.value = "";
  showFormModal.value = true;
}

function closeFormModal() {
  showFormModal.value = false;
}

async function submitExerciseForm() {
  formSubmitting.value = true;
  formError.value = "";
  const payload = {
    name: formData.name,
    category: formData.category,
    level: formData.level,
    duration: formData.duration,
    description: formData.description,
    errors: splitErrors(formData.errors),
  };

  try {
    if (editingExercise.value) {
      await updateExercise(editingExercise.value.key, payload);
    } else {
      await createExercise({ key: formData.key, ...payload });
    }
    closeFormModal();
    await loadExercises();
  } catch (err) {
    formError.value = err instanceof Error ? err.message : "操作失败";
  } finally {
    formSubmitting.value = false;
  }
}

async function handleDelete(exercise: ExerciseItem) {
  if (!confirm(`确定删除动作「${exercise.name}」？`)) return;
  try {
    await deleteExercise(exercise.key);
    exercises.value = exercises.value.filter((item) => item.key !== exercise.key);
  } catch (err) {
    alert("删除失败: " + (err instanceof Error ? err.message : "网络错误"));
  }
}

const showTemplateModal = ref(false);
const templateTarget = ref<ExerciseItem | null>(null);
const isUploading = ref(false);
const templateUploadSuccess = ref(false);
const templateError = ref("");
const templateResult = reactive({ valid_frames: 0, template_path: "", curve_count: 0 });
const templateForm = reactive({ name: "", view: "side", videoFile: null as File | null });
const fileInput = ref<HTMLInputElement | null>(null);

function openTemplateModal(exercise: ExerciseItem) {
  templateTarget.value = exercise;
  templateForm.name = `标准${exercise.name}`;
  templateForm.view = "side";
  templateForm.videoFile = null;
  fileInput.value = null;
  templateError.value = "";
  templateUploadSuccess.value = false;
  showTemplateModal.value = true;
}

function closeTemplateModal() {
  showTemplateModal.value = false;
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  templateForm.videoFile = input.files?.[0] ?? null;
}

async function submitTemplate() {
  if (!templateForm.videoFile || !templateTarget.value) return;
  isUploading.value = true;
  templateError.value = "";
  try {
    const form = new FormData();
    form.append("video", templateForm.videoFile);
    form.append("name", templateForm.name);
    form.append("view", templateForm.view);
    form.append("version", "v1");
    const result = await apiUpload<any>(
      `/exercises/${templateTarget.value.key}/templates/from-video`,
      form
    );
    templateResult.valid_frames = result.valid_frames || 0;
    templateResult.template_path = result.template_path || "";
    templateResult.curve_count = result.curve_count || 0;
    templateUploadSuccess.value = true;
  } catch (err) {
    templateError.value = err instanceof Error ? err.message : "模板生成失败";
  } finally {
    isUploading.value = false;
  }
}

async function loadExercises() {
  try {
    const data = await getExerciseLibrary();
    exercises.value = data.items;
  } catch {
    exercises.value = [];
  } finally {
    loading.value = false;
  }
}

onMounted(loadExercises);
</script>

<style scoped>
.page { display: grid; gap: 24px; }
.split-layout { display: grid; grid-template-columns: 210px 1fr; gap: 24px; align-items: start; }
.filter-panel { background: rgba(15,23,42,0.96); border: 1px solid rgba(59,130,246,0.1); border-radius: 14px; padding: 20px; display: grid; gap: 18px; }
.filter-panel h2 { color: #f8fafc; font-size: 16px; margin: 0; }
.filter-group { display: grid; gap: 6px; }
.filter-group strong { color: #64748b; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; }
.filter-group button { padding: 8px 14px; border: 1px solid rgba(59,130,246,0.06); border-radius: 8px; background: rgba(8,13,26,0.5); color: #94a3b8; font-size: 13px; cursor: pointer; text-align: left; }
.filter-group button.active, .filter-group button:hover { background: rgba(59,130,246,0.12); border-color: rgba(59,130,246,0.2); color: #93c5fd; }
.exercise-grid { display: grid; gap: 16px; }
.exercise-card { padding: 20px; border-radius: 14px; background: linear-gradient(180deg, rgba(15,23,42,0.96), rgba(8,13,26,0.98)); border: 1px solid rgba(59,130,246,0.1); display: grid; gap: 10px; }
.exercise-visual { width: 48px; height: 48px; display: grid; place-items: center; border-radius: 12px; background: var(--accent); color: #fff; }
.exercise-card h2 { margin: 0; color: #f8fafc; font-size: 18px; }
.exercise-card span { color: #64748b; font-size: 12px; }
.exercise-card p { color: #94a3b8; margin: 0; font-size: 13px; line-height: 1.5; }
.error-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.error-chips span { padding: 3px 10px; border-radius: 999px; background: rgba(239,68,68,0.08); color: #f87171; font-size: 11px; font-weight: 600; }
.card-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px; }
.card-actions .primary-button, .card-actions .secondary-button { min-height: 34px; padding: 0 14px; border-radius: 8px; font-size: 12px; }
.card-actions .secondary-button.danger { border-color: rgba(239,68,68,0.2); color: #f87171; }
.card-actions .secondary-button.danger:hover { background: rgba(239,68,68,0.08); }
.template-button { min-height: 34px; padding: 0 14px; border: 1px solid rgba(59,130,246,0.1); border-radius: 8px; background: rgba(8,13,26,0.4); color: #cbd5e1; font-size: 12px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; }
.template-button:hover { background: rgba(59,130,246,0.08); border-color: rgba(59,130,246,0.2); }
.modal-overlay { position: fixed; inset: 0; z-index: 999; background: rgba(0,0,0,0.65); display: grid; place-items: center; padding: 24px; }
.modal-content { width: 100%; max-width: 520px; max-height: 90vh; overflow-y: auto; background: #0f172a; border: 1px solid rgba(59,130,246,0.15); border-radius: 16px; padding: 28px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.modal-header h3 { color: #f8fafc; font-size: 18px; margin: 0; }
.close-button { background: none; border: none; color: #64748b; cursor: pointer; }
.template-form { display: grid; gap: 16px; }
.form-field { display: grid; gap: 6px; }
.form-field span { color: #94a3b8; font-size: 13px; font-weight: 600; }
.form-field input, .form-field select, .form-field textarea { padding: 10px 14px; border: 1px solid rgba(59,130,246,0.1); border-radius: 8px; background: rgba(8,13,26,0.7); color: #f8fafc; font-size: 14px; }
.form-field textarea { resize: vertical; }
.file-upload { display: grid; gap: 6px; place-items: center; padding: 28px; border: 2px dashed rgba(59,130,246,0.15); border-radius: 10px; cursor: pointer; color: #64748b; }
.file-upload.has-file { border-color: rgba(16,185,129,0.3); }
.file-upload input { display: none; }
.file-upload span { font-size: 14px; }
.file-upload small { font-size: 11px; }
.error-message { color: #f87171; background: rgba(239,68,68,0.08); padding: 10px 14px; border-radius: 8px; font-size: 13px; }
.success-message { text-align: center; display: grid; gap: 8px; place-items: center; padding: 24px; }
.success-message h4 { color: #34d399; margin: 0; }
.success-message p { color: #94a3b8; }
.success-icon { color: #34d399; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 18px; }
.page-header h1 { color: #f8fafc; font-size: 28px; margin: 0; }
.page-header p { margin: 4px 0 0; color: #64748b; }
.primary-button { display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; border: none; border-radius: 9px; background: linear-gradient(135deg, #3b82f6, #6366f1); color: #fff; font-size: 14px; font-weight: 600; cursor: pointer; white-space: nowrap; }
.secondary-button { display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; border: 1px solid rgba(59,130,246,0.1); border-radius: 9px; background: rgba(8,13,26,0.5); color: #cbd5e1; font-size: 14px; font-weight: 600; cursor: pointer; }
.eyebrow { color: #60a5fa; font-size: 12px; text-transform: uppercase; letter-spacing: 0.1em; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 900px) { .split-layout { grid-template-columns: 1fr; } }
</style>
