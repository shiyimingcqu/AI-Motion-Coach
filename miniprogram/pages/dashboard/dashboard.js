// 首页 Dashboard
const ApiClient = require('../../utils/api');
const { EXERCISE_CONFIG, getScoreLevel } = require('../../utils/constants');
const { formatDate, formatDuration } = require('../../utils/util');
const app = getApp();

Page({
  data: {
    greeting: '早上好',
    userInfo: {},
    stats: {
      todaySessions: 0,
      totalSessions: 0,
      averageScore: 0,
      totalDuration: 0,
    },
    trendData: [],
    recentSessions: [],
    loading: true
  },

  onShow() {
    this.updateGreeting();
    this.loadDashboard();
  },

  updateGreeting() {
    const hour = new Date().getHours();
    let greeting = '早上好';
    if (hour >= 12 && hour < 18) greeting = '下午好';
    else if (hour >= 18) greeting = '晚上好';
    this.setData({ greeting });
  },

  async loadDashboard() {
    const userInfo = app.globalData.userInfo || {};
    this.setData({ userInfo, loading: true });

    try {
      const stats = await ApiClient.get('/api/dashboard/stats');

      // 处理趋势数据
      const trendData = (stats.recent_trend || []).map(item => {
        const level = getScoreLevel(item.score);
        const maxH = 140;
        const height = Math.max(4, (item.score / 100) * maxH);
        return {
          date: item.date ? item.date.slice(5) : '',  // MM-DD
          score: item.score,
          height,
          color: level.color
        };
      });

      // 处理最近训练
      const recentSessions = (stats.recent_sessions || []).slice(0, 5).map(s => {
        const config = EXERCISE_CONFIG[s.exercise];
        const level = getScoreLevel(s.average_score || s.score || 0);
        return {
          session_id: s.session_id,
          exercise_name: config ? config.name : (s.exercise || '未知'),
          date: formatDate(s.created_at, 'MM-DD HH:mm'),
          score: s.average_score || s.score || 0,
          scoreColor: level.color,
          duration: formatDuration(s.duration_seconds || 0),
        };
      });

      this.setData({
        stats: {
          todaySessions: stats.today_sessions || 0,
          totalSessions: stats.total_sessions || 0,
          averageScore: Math.round(stats.average_score || 0),
          totalDuration: stats.total_duration_minutes || 0,
        },
        trendData,
        recentSessions,
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

  goToSession(e) {
    const id = e.currentTarget.dataset.id;
    // 跳转到结果页（暂不支持从 session 恢复）
  }
});
