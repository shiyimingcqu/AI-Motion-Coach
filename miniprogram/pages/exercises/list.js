// 动作库列表页
const ApiClient = require('../../utils/api');
const { EXERCISE_CONFIG } = require('../../utils/constants');

const EXERCISE_IMAGES = {
  squat: '/assets/fitness/exercise-squat.png',
  push_up: '/assets/fitness/exercise-pushup.png',
  jumping_jack: '/assets/fitness/exercise-jumping-jack.png',
  plank: '/assets/fitness/exercise-plank.png',
  lunge: '/assets/fitness/exercise-squat.png',
  burpee: '/assets/fitness/exercise-pushup.png',
  high_knees: '/assets/fitness/exercise-jumping-jack.png',
};

Page({
  data: {
    keyword: '',
    categories: ['全部', '下肢力量', '上肢力量', '核心稳定', '心肺训练', '全身'],
    activeCategory: '全部',
    exercises: [],
    filteredExercises: [],
    loading: true
  },

  onLoad() {
    this.loadExercises();
  },

  async loadExercises() {
    this.setData({ loading: true });

    try {
      const res = await ApiClient.get('/api/exercises');
      // 合并后端数据与本地配置
      const exercises = (res.items || res || []).map(item => {
        const config = EXERCISE_CONFIG[item.key] || {};
        return {
          key: item.key,
          name: item.name || config.name,
          category: item.category || config.category,
          level: item.level || config.level,
          duration: item.duration || '10 分钟',
          description: item.description || '',
          accentColor: config.accentColor || '#3b82f6',
          icon: config.icon || '🏋️',
          image: EXERCISE_IMAGES[item.key] || '',
          modes: item.modes || [],
          errors: item.errors || [],
        };
      });

      this.setData({ exercises, loading: false });
      this.applyFilter();
    } catch (err) {
      console.error('Load exercises error:', err);
      // 使用本地配置兜底
      const exercises = Object.values(EXERCISE_CONFIG).map(item => ({
        ...item,
        image: EXERCISE_IMAGES[item.key] || '',
      }));
      this.setData({ exercises, loading: false });
      this.applyFilter();
    }
  },

  onSearch(e) {
    this.setData({ keyword: e.detail.value });
    this.applyFilter();
  },

  switchCategory(e) {
    this.setData({ activeCategory: e.currentTarget.dataset.category });
    this.applyFilter();
  },

  applyFilter() {
    const { exercises, keyword, activeCategory } = this.data;

    let filtered = exercises;

    // 分类过滤
    if (activeCategory !== '全部') {
      filtered = filtered.filter(e => e.category === activeCategory);
    }

    // 关键词搜索
    if (keyword.trim()) {
      const kw = keyword.trim().toLowerCase();
      filtered = filtered.filter(e =>
        e.name.toLowerCase().includes(kw) ||
        e.key.toLowerCase().includes(kw)
      );
    }

    this.setData({ filteredExercises: filtered });
  },

  goToDetail(e) {
    const key = e.currentTarget.dataset.key;
    wx.navigateTo({ url: `/pages/exercises/detail?key=${key}` });
  }
});
