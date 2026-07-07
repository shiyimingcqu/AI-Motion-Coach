// 首页 Dashboard
const ApiClient = require('../../utils/api');
const { EXERCISE_CONFIG, getScoreLevel } = require('../../utils/constants');
const { formatDate, formatDuration } = require('../../utils/util');
const app = getApp();

const FITNESS_ASSETS = {
  squat: '/assets/fitness/exercise-squat.png',
  push_up: '/assets/fitness/exercise-pushup.png',
  plank: '/assets/fitness/exercise-plank.png',
  jumping_jack: '/assets/fitness/exercise-jumping-jack.png',
};

const RECOMMEND_LIST = [
  { key: 'squat', image: FITNESS_ASSETS.squat, name: '深蹲', level: '初级', duration: '8 分钟', people: 86 },
  { key: 'push_up', image: FITNESS_ASSETS.push_up, name: '俯卧撑', level: '中级', duration: '10 分钟', people: 142 },
  { key: 'plank', image: FITNESS_ASSETS.plank, name: '平板支撑', level: '初级', duration: '5 分钟', people: 68 },
  { key: 'jumping_jack', image: FITNESS_ASSETS.jumping_jack, name: '开合跳', level: '初级', duration: '6 分钟', people: 95 },
  { key: 'lunge', image: FITNESS_ASSETS.squat, name: '弓步蹲', level: '中级', duration: '9 分钟', people: 53 },
  { key: 'high_knees', image: FITNESS_ASSETS.jumping_jack, name: '高抬腿', level: '中级', duration: '5 分钟', people: 71 },
];

Page({
  data: {
    statusBarHeight: 44,
    userInfo: {},
    stats: {
      todaySessions: 0,
      weekSessions: 0,
      averageScore: 0,
      totalDuration: 0
    },
    recommended: null,
    loading: true
  },

  onLoad() {
    try {
      const sysInfo = wx.getSystemInfoSync();
      this.setData({ statusBarHeight: sysInfo.statusBarHeight || 44 });
    } catch (e) {}
  },

  onShow() {
    this.pickRecommend();
    this.loadDashboard();
  },

  pickRecommend() {
    const list = RECOMMEND_LIST;
    const idx = Math.floor(Math.random() * list.length);
    this.setData({ recommended: list[idx] });
  },

  async loadDashboard() {
    const userInfo = app.globalData.userInfo || {};
    this.setData({ userInfo, loading: true });

    try {
      const stats = await ApiClient.get('/api/dashboard/stats').catch(() => ({}));

      this.setData({
        stats: {
          todaySessions: stats.today_sessions || 0,
          weekSessions: stats.week_sessions || stats.total_sessions || 0,
          averageScore: Math.round(stats.average_score || 0),
          totalDuration: stats.total_duration_minutes || 0,
        },
        loading: false
      });
    } catch (err) {
      console.error('Load dashboard error:', err);
      this.setData({ loading: false });
    }
  },

  goToTraining() {
    wx.switchTab({ url: '/pages/exercises/list' });
  },

  goToVideoAnalysis() {
    wx.navigateTo({ url: '/pages/video-upload/video-upload' });
  },

  goToReports() {
    wx.switchTab({ url: '/pages/reports/reports' });
  },

  goToExercises() {
    wx.switchTab({ url: '/pages/exercises/list' });
  },

  goToRecommend() {
    const r = this.data.recommended;
    if (!r) return;
    wx.navigateTo({ url: `/pages/exercises/detail?key=${r.key}` });
  },

  shuffleRecommend() {
    this.pickRecommend();
  },

  goToWarmup() {
    wx.showToast({ title: '功能开发中', icon: 'none' });
  },
  goToStretch() {
    wx.showToast({ title: '功能开发中', icon: 'none' });
  },
  goToPlan() {
    wx.showToast({ title: '功能开发中', icon: 'none' });
  },
  goToFavorites() {
    wx.showToast({ title: '功能开发中', icon: 'none' });
  }
});
