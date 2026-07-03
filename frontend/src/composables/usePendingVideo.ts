import { ref } from "vue";

/** 待保存的视频文件（从实时检测页面传过来） */
export const pendingVideoFile = ref<File | null>(null);
