import { defineStore } from "pinia";

export const useTrainingStore = defineStore("training", {
  state: () => ({
    currentExercise: "squat",
    count: 12,
    validCount: 10,
    score: 86,
    errors: ["下蹲深度不足"],
    taskStatus: "pending"
  }),
  actions: {
    setExercise(exercise: string) {
      this.currentExercise = exercise;
    }
  }
});
