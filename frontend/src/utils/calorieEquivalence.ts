export interface FoodEquivalence {
  icon: string;
  name: string;
  amount: number;
  text: string;
}

const FOOD_REFERENCES = [
  { kcal: 52, icon: "🍎", name: "苹果", unit: "个" },
  { kcal: 89, icon: "🍌", name: "香蕉", unit: "根" },
  { kcal: 78, icon: "🥚", name: "煮鸡蛋", unit: "个" },
  { kcal: 155, icon: "🍚", name: "米饭", unit: "碗" },
  { kcal: 214, icon: "🍞", name: "面包", unit: "片" },
  { kcal: 140, icon: "🥛", name: "牛奶", unit: "杯" },
  { kcal: 95, icon: "🍊", name: "橙子", unit: "个" },
];

export function getFoodEquivalence(kcal: number): FoodEquivalence {
  const safe = Math.max(0, kcal);
  if (safe <= 0) {
    return { icon: "🥗", name: "轻食", amount: 0, text: "完成训练后将显示热量与食物等价" };
  }

  const ref = FOOD_REFERENCES.reduce((best, item) => {
    const diff = Math.abs(safe - item.kcal);
    const bestDiff = Math.abs(safe - best.kcal);
    return diff < bestDiff ? item : best;
  });

  const amount = Math.max(0.1, Math.round((safe / ref.kcal) * 10) / 10);
  return {
    icon: ref.icon,
    name: ref.name,
    amount,
    text: `相当于约 ${amount} ${ref.unit}${ref.name}`,
  };
}
