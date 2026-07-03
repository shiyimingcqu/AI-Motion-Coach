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
          <p>难度 {{ exercise.level }} | 推荐时长 {{ exercise.duration }}，支持 {{ exercise.modes.join(" / ") }}。</p>
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
              @click="goToTemplateUpload(exercise.key)"
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
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useTrainingStore } from "@/stores/training";
import {
  createExercise,
  deleteExercise,
  getExerciseLibrary,
  updateExercise,
  type ExerciseItem,
} from "@/api/exercises";
import { Dumbbell, Plus, Upload, X } from "lucide-vue-next";
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

function goToTemplateUpload(exerciseKey: string) {
  router.push({ path: "/admin/templates", query: { exercise: exerciseKey } });
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
.filter-panel { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 20px; display: grid; gap: 18px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.filter-panel h2 { color: #0f172a; font-size: 16px; margin: 0; }
.filter-group { display: grid; gap: 6px; }
.filter-group strong { color: #94a3b8; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; }
.filter-group button { padding: 8px 14px; border: 1px solid #e2e8f0; border-radius: 8px; background: #f8fbff; color: #64748b; font-size: 13px; cursor: pointer; text-align: left; }
.filter-group button.active, .filter-group button:hover { background: rgba(91,140,255,0.08); border-color: #5b8cff; color: #5b8cff; }
.exercise-grid { display: grid; gap: 16px; }
.exercise-card { padding: 20px; border-radius: 14px; background: #ffffff; border: 1px solid #e2e8f0; display: grid; gap: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.exercise-visual { width: 48px; height: 48px; display: grid; place-items: center; border-radius: 12px; background: var(--accent, #5b8cff); color: #fff; }
.exercise-card h2 { margin: 0; color: #0f172a; font-size: 18px; }
.exercise-card span { color: #94a3b8; font-size: 12px; }
.exercise-card p { color: #64748b; margin: 0; font-size: 13px; line-height: 1.5; }
.error-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.error-chips span { padding: 3px 10px; border-radius: 999px; background: rgba(239,68,68,0.08); color: #ef4444; font-size: 11px; font-weight: 600; }
.card-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px; }
.card-actions .primary-button, .card-actions .secondary-button { min-height: 34px; padding: 0 14px; border-radius: 8px; font-size: 12px; }
.card-actions .secondary-button.danger { border-color: rgba(239,68,68,0.2); color: #ef4444; }
.card-actions .secondary-button.danger:hover { background: rgba(239,68,68,0.08); }
.template-button { min-height: 34px; padding: 0 14px; border: 1px solid #e2e8f0; border-radius: 8px; background: #f8fbff; color: #475569; font-size: 12px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; }
.template-button:hover { background: rgba(91,140,255,0.06); border-color: #5b8cff; }
.modal-overlay { position: fixed; inset: 0; z-index: 999; background: rgba(0,0,0,0.4); display: grid; place-items: center; padding: 24px; }
.modal-content { width: 100%; max-width: 520px; max-height: 90vh; overflow-y: auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 28px; box-shadow: 0 8px 32px rgba(0,0,0,0.12); }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.modal-header h3 { color: #0f172a; font-size: 18px; margin: 0; }
.close-button { background: none; border: none; color: #94a3b8; cursor: pointer; }
.template-form { display: grid; gap: 16px; }
.form-field { display: grid; gap: 6px; }
.form-field span { color: #64748b; font-size: 13px; font-weight: 600; }
.form-field input, .form-field select, .form-field textarea { padding: 10px 14px; border: 1px solid #e2e8f0; border-radius: 8px; background: #f8fbff; color: #0f172a; font-size: 14px; }
.form-field textarea { resize: vertical; }
.file-upload { display: grid; gap: 6px; place-items: center; padding: 28px; border: 2px dashed #d6e3ff; border-radius: 10px; cursor: pointer; color: #94a3b8; background: #f8fbff; }
.file-upload.has-file { border-color: #25b87b; }
.file-upload input { display: none; }
.file-upload span { font-size: 14px; }
.file-upload small { font-size: 11px; }
.error-message { color: #ef4444; background: rgba(239,68,68,0.06); padding: 10px 14px; border-radius: 8px; font-size: 13px; }
.success-message { text-align: center; display: grid; gap: 8px; place-items: center; padding: 24px; }
.success-message h4 { color: #25b87b; margin: 0; }
.success-message p { color: #94a3b8; }
.success-icon { color: #25b87b; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 18px; }
.page-header h1 { color: #0f172a; font-size: 28px; margin: 0; }
.page-header p { margin: 4px 0 0; color: #64748b; }
.primary-button { display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; border: none; border-radius: 9px; background: linear-gradient(135deg, #5b8cff, #4f46e5); color: #fff; font-size: 14px; font-weight: 600; cursor: pointer; white-space: nowrap; }
.secondary-button { display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; border: 1px solid #e2e8f0; border-radius: 9px; background: #f8fbff; color: #475569; font-size: 14px; font-weight: 600; cursor: pointer; }
.eyebrow { color: #5b8cff; font-size: 12px; text-transform: uppercase; letter-spacing: 0.1em; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 900px) { .split-layout { grid-template-columns: 1fr; } }
</style>
