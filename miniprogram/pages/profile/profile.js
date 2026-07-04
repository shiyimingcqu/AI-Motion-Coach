// 个人中心
const ApiClient = require('../../utils/api');
const AuthManager = require('../../utils/auth');
const { showConfirm } = require('../../utils/util');
const app = getApp();

Page({
  data: {
    userInfo: {},
    stats: {
      totalSessions: 0,
      averageScore: 0,
      totalDuration: 0
    }
  },

  onShow() {
    this.loadProfile();
  },

  async loadProfile() {
    const userInfo = app.globalData.userInfo || AuthManager.getUserInfo() || {};
    this.setData({ userInfo });

    try {
      const stats = await ApiClient.get('/api/dashboard/stats');
      this.setData({
        stats: {
          totalSessions: stats.total_sessions || 0,
          averageScore: Math.round(stats.average_score || 0),
          totalDuration: stats.total_duration_minutes || 0,
        }
      });
    } catch (err) {
      console.error('Load profile error:', err);
    }
  },

  goToReports() {
    wx.switchTab({ url: '/pages/reports/reports' });
  },

  handleLogout() {
    wx.showModal({
      title: '退出登录',
      content: '确定要退出当前账号吗？',
      success: (res) => {
        if (res.confirm) {
          const AuthManager = require('../../utils/auth');
          AuthManager.logout();
          wx.reLaunch({ url: '/pages/login/login' });
        }
      },
    });
  },

  onTapSession(e) {
    // 暂不处理
  },

  goToSettings() {
    wx.showToast({ title: '设置功能开发中', icon: 'none' });
  },

  async handleLogout() {
    const confirmed = await showConfirm('退出登录', '确定要退出登录吗？');
    if (confirmed) {
      AuthManager.logout();
      app.clearLoginState();
      wx.reLaunch({ url: '/pages/login/login' });
    }
  }
});
