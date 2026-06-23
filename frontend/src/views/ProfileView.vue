<template>
  <div class="page">
    <button class="back-link" type="button" @click="goHome">
      <ArrowLeft :size="24" />
      返回首页
    </button>

    <header class="page-header">
      <div>
        <p class="eyebrow">Profile</p>
        <h1>个人资料</h1>
        <p class="subtle">修改后会自动保存在当前浏览器中。</p>
      </div>
      <span class="status-pill good">已自动保存</span>
    </header>

    <section class="profile-hero panel">
      <div class="profile-avatar-picker">
        <button class="profile-avatar-button" type="button" aria-label="修改头像" @click="openAvatarModal">
          <UserAvatar size="lg" />
        </button>
        <small>点击头像修改</small>
        <div v-if="avatarSuccessVisible" class="avatar-success-badge" role="status">
          <Check :size="16" />
          头像修改成功
        </div>
      </div>
      <div class="profile-hero-form">
        <label class="profile-field">
          <span>姓名</span>
          <input v-model="profile.name" type="text" placeholder="请输入姓名" />
        </label>
        <label class="profile-field">
          <span>训练目标</span>
          <input v-model="profile.trainingGoal" type="text" placeholder="请输入训练目标" />
        </label>
      </div>
    </section>

    <section class="profile-grid">
      <article class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Basic Info</p>
            <h2>基础信息</h2>
          </div>
        </div>
        <div class="profile-form-list">
          <label class="profile-field">
            <span>职业</span>
            <select v-model="profile.occupation">
              <option v-for="occupation in occupationOptions" :key="occupation" :value="occupation">
                {{ occupation }}
              </option>
            </select>
          </label>
          <label class="profile-field">
            <span>身高 (cm)</span>
            <input v-model="profile.height" type="number" min="0" placeholder="172" />
          </label>
          <label class="profile-field">
            <span>体重 (kg)</span>
            <input v-model="profile.weight" type="number" min="0" placeholder="62" />
          </label>
        </div>
      </article>

      <article class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Training</p>
            <h2>训练概况</h2>
          </div>
        </div>
        <dl class="info-list info-list-readonly">
          <div>
            <dt>累计训练</dt>
            <dd>36 次</dd>
          </div>
          <div>
            <dt>平均评分</dt>
            <dd>86 分</dd>
          </div>
          <div>
            <dt>最常训练</dt>
            <dd>深蹲</dd>
          </div>
          <div>
            <dt>重点纠正</dt>
            <dd>下蹲深度不足</dd>
          </div>
        </dl>
      </article>
    </section>

    <section class="panel">
      <div class="section-title">
        <div>
          <p class="eyebrow">Preference</p>
          <h2>训练偏好</h2>
        </div>
        <span class="goal-count">{{ profile.trainingPreferences.length }}/5</span>
      </div>
      <p class="goal-hint">请选择 1 至 5 项训练偏好，系统将据此优化训练建议与提醒重点。</p>
      <div class="goal-picker">
        <button
          v-for="option in trainingPreferenceOptions"
          :key="option"
          class="goal-option"
          :class="{
            active: profile.trainingPreferences.includes(option),
            disabled: isPreferenceDisabled(option)
          }"
          type="button"
          @click="toggleTrainingPreference(option)"
        >
          {{ option }}
        </button>
      </div>
      <p v-if="preferenceMessage" class="goal-message">{{ preferenceMessage }}</p>
    </section>

    <section class="panel profile-logout-panel">
      <button class="logout-link" type="button" @click="logout">退出登录</button>
    </section>

    <Teleport to="body">
      <div v-if="showAvatarModal" class="avatar-modal-overlay" @click.self="closeAvatarModal">
        <div
          class="avatar-modal"
          :class="{ 'avatar-modal-crop': cropStep }"
          role="dialog"
          aria-modal="true"
          aria-labelledby="avatar-modal-title"
        >
          <button class="avatar-modal-close" type="button" aria-label="取消" @click="closeAvatarModal">
            <X :size="20" />
          </button>

          <template v-if="!cropStep">
            <h2 id="avatar-modal-title">更换头像</h2>
            <div class="avatar-modal-preview">
              <UserAvatar size="lg" />
            </div>
            <div class="avatar-modal-actions">
              <button class="avatar-action-btn avatar-action-btn-secondary" type="button" @click="selectDefaultAvatar">
                使用默认头像（姓氏）
              </button>
              <label class="avatar-action-btn avatar-action-btn-primary avatar-upload-label">
                上传图片
                <input
                  class="avatar-file-input"
                  type="file"
                  accept="image/*"
                  @change="handleAvatarSelect"
                />
              </label>
            </div>
            <p class="avatar-modal-hint">支持 png、jpg、webp、gif，最大 2MB。上传后可拖动方框裁剪正方形区域。</p>
          </template>

          <template v-else>
            <h2 id="avatar-modal-title">裁剪头像</h2>
            <AvatarCropper ref="cropperRef" :image-url="cropImageUrl" />
            <p class="avatar-modal-hint">拖动方框选择区域，右下角可缩放，比例固定为正方形。</p>
            <div class="avatar-modal-actions">
              <button class="avatar-action-btn avatar-action-btn-secondary" type="button" @click="backToAvatarOptions">
                重新选择
              </button>
              <button class="avatar-action-btn avatar-action-btn-primary" type="button" @click="confirmCrop">
                确认使用
              </button>
            </div>
          </template>

          <p v-if="avatarMessage" class="avatar-message">{{ avatarMessage }}</p>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { onUnmounted, ref } from "vue";
import { storeToRefs } from "pinia";
import { ArrowLeft, Check, X } from "lucide-vue-next";
import { useRouter } from "vue-router";

import AvatarCropper from "../components/AvatarCropper.vue";
import UserAvatar from "../components/UserAvatar.vue";
import { TRAINING_PREFERENCE_OPTIONS, OCCUPATION_OPTIONS, setCustomAvatar, setDefaultAvatar, useProfileStore } from "../stores/profile";

const router = useRouter();
const { profile } = storeToRefs(useProfileStore());
const trainingPreferenceOptions = TRAINING_PREFERENCE_OPTIONS;
const occupationOptions = OCCUPATION_OPTIONS;
const preferenceMessage = ref("");
const avatarMessage = ref("");
const showAvatarModal = ref(false);
const cropStep = ref(false);
const cropImageUrl = ref("");
const cropperRef = ref<InstanceType<typeof AvatarCropper> | null>(null);
const avatarSuccessVisible = ref(false);

let avatarSuccessTimer: ReturnType<typeof setTimeout> | null = null;

const MAX_AVATAR_SIZE = 2 * 1024 * 1024;

function showAvatarSuccess() {
  avatarSuccessVisible.value = true;
  if (avatarSuccessTimer) {
    clearTimeout(avatarSuccessTimer);
  }
  avatarSuccessTimer = setTimeout(() => {
    avatarSuccessVisible.value = false;
    avatarSuccessTimer = null;
  }, 2400);
}

onUnmounted(() => {
  if (avatarSuccessTimer) {
    clearTimeout(avatarSuccessTimer);
  }
});

function goHome() {
  router.push("/");
}

function logout() {
  localStorage.removeItem("pose-evaluation-auth");
  window.alert("已退出登录");
  router.push("/");
}

function resetCropState() {
  if (cropImageUrl.value) {
    URL.revokeObjectURL(cropImageUrl.value);
  }
  cropImageUrl.value = "";
  cropStep.value = false;
}

function openAvatarModal() {
  avatarMessage.value = "";
  resetCropState();
  showAvatarModal.value = true;
}

function closeAvatarModal() {
  resetCropState();
  showAvatarModal.value = false;
  avatarMessage.value = "";
}

function selectDefaultAvatar() {
  setDefaultAvatar(profile.value);
  closeAvatarModal();
  showAvatarSuccess();
}

function backToAvatarOptions() {
  resetCropState();
  avatarMessage.value = "";
}

function isImageFile(file: File) {
  if (file.type.startsWith("image/")) {
    return true;
  }
  return /\.(png|jpe?g|webp|gif)$/i.test(file.name);
}

function handleAvatarSelect(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";

  if (!file) {
    return;
  }

  if (!isImageFile(file)) {
    avatarMessage.value = "请上传 png、jpg、webp 或 gif 图片。";
    return;
  }

  if (file.size > MAX_AVATAR_SIZE) {
    avatarMessage.value = "图片大小不能超过 2MB。";
    return;
  }

  avatarMessage.value = "";
  resetCropState();
  cropImageUrl.value = URL.createObjectURL(file);
  cropStep.value = true;
}

async function confirmCrop() {
  if (!cropperRef.value) {
    avatarMessage.value = "裁剪组件未就绪，请稍后再试。";
    return;
  }

  try {
    const imageData = await cropperRef.value.getCroppedImage();
    setCustomAvatar(profile.value, imageData);
    closeAvatarModal();
    showAvatarSuccess();
  } catch (error) {
    avatarMessage.value = error instanceof Error ? error.message : "裁剪失败，请重新选择图片。";
  }
}

function isPreferenceDisabled(option: string) {
  return profile.value.trainingPreferences.length >= 5 && !profile.value.trainingPreferences.includes(option);
}

function toggleTrainingPreference(option: string) {
  preferenceMessage.value = "";
  const selected = profile.value.trainingPreferences.includes(option);

  if (selected) {
    if (profile.value.trainingPreferences.length <= 1) {
      preferenceMessage.value = "至少保留 1 项训练偏好。";
      return;
    }
    profile.value.trainingPreferences = profile.value.trainingPreferences.filter((item) => item !== option);
    return;
  }

  if (profile.value.trainingPreferences.length >= 5) {
    preferenceMessage.value = "最多只能选择 5 项训练偏好。";
    return;
  }

  profile.value.trainingPreferences = [...profile.value.trainingPreferences, option];
}
</script>
