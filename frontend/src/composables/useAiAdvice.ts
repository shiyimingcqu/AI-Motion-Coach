import { ref } from "vue";
import { apiPost } from "../api/client";

export interface AiAdvicePayload {
  exercise: string;
  stage?: string;
  errors: string[];
  feedbacks: string[];
  metrics?: Record<string, number | string>;
}

export interface AiAdviceResult {
  text: string;
  source: string;
}

export function useAiAdvice() {
  const aiAdvice = ref("");
  const aiLoading = ref(false);
  const voiceEnabled = ref(false);
  const lastSpokenAdvice = ref("");

  async function requestAiAdvice(payload: AiAdvicePayload) {
    if (!payload.exercise) {
      aiAdvice.value = "无法生成建议：缺少动作类型信息。";
      return;
    }

    aiLoading.value = true;
    aiAdvice.value = "";

    try {
      const response = await apiPost<AiAdviceResult>("/ai/advice", {
        exercise: payload.exercise,
        stage: payload.stage || "completed",
        errors: payload.errors,
        feedbacks: payload.feedbacks,
        metrics: payload.metrics || {},
      });

      aiAdvice.value = response.text;

      // 语音播报
      if (voiceEnabled.value && aiAdvice.value && aiAdvice.value !== lastSpokenAdvice.value) {
        speakAdvice(aiAdvice.value);
        lastSpokenAdvice.value = aiAdvice.value;
      }
    } catch (error) {
      console.error("AI 建议生成失败:", error);
      aiAdvice.value = "AI 建议生成失败，请稍后重试。";
    } finally {
      aiLoading.value = false;
    }
  }

  function speakAdvice(text: string) {
    if (!("speechSynthesis" in window)) return;

    // 去除 Markdown 符号，便于语音播报
    const cleanText = text
      .replace(/\*\*(.+?)\*\*/g, "$1")
      .replace(/\*(.+?)\*/g, "$1")
      .replace(/`(.+?)`/g, "$1")
      .replace(/^#{1,6}\s+/gm, "")
      .replace(/\n{2,}/g, " ")
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = "zh-CN";
    utterance.rate = 1;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }

  function clearAdvice() {
    aiAdvice.value = "";
    lastSpokenAdvice.value = "";
  }

  return {
    aiAdvice,
    aiLoading,
    voiceEnabled,
    requestAiAdvice,
    clearAdvice,
  };
}
