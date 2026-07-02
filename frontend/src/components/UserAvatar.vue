<template>
  <span :class="['user-avatar', size === 'lg' ? 'user-avatar-lg' : 'user-avatar-sm']">
    <img v-if="showImage" :src="profile.avatarImage" alt="用户头像" class="user-avatar-image" />
    <span v-else class="user-avatar-text">{{ defaultText }}</span>
  </span>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { storeToRefs } from "pinia";

import { getDefaultAvatarText, shouldShowCustomAvatar, useProfileStore } from "../stores/profile";

defineProps<{ size?: "sm" | "lg" }>();

const { profile } = storeToRefs(useProfileStore());
const showImage = computed(() => shouldShowCustomAvatar(profile.value));
const defaultText = computed(() => getDefaultAvatarText(profile.value.name));
</script>
