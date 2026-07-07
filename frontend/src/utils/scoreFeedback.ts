export type ScoreTone = "excellent" | "good" | "encourage" | "improve";

export interface ScoreFeedback {
  title: string;
  message: string;
  tone: ScoreTone;
  emoji: string;
}

export function getScoreFeedback(score: number): ScoreFeedback {
  if (score >= 90) {
    return {
      title: "太棒了！",
      message: "动作几近完美，继续保持这股势头！",
      tone: "excellent",
      emoji: "🏆",
    };
  }
  if (score >= 80) {
    return {
      title: "做得不错！",
      message: "整体质量良好，再精进一点就能更上一层楼。",
      tone: "good",
      emoji: "👍",
    };
  }
  if (score >= 70) {
    return {
      title: "继续加油！",
      message: "已经有进步空间，盯住错误反馈练几组会有明显提升。",
      tone: "encourage",
      emoji: "💪",
    };
  }
  return {
    title: "别灰心！",
    message: "每次训练都是积累，对照截图纠正难点会慢慢变好。",
    tone: "improve",
    emoji: "🌱",
  };
}
