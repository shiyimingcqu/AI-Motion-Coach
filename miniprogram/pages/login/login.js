// 登录页逻辑
const AuthManager = require('../../utils/auth');
const { showToast, showLoading, hideLoading } = require('../../utils/util');
const app = getApp();

Page({
  data: {
    showAccountLogin: false,
    username: '',
    password: '',
    loading: false
  },

  onLoad() {
    // 检查是否已登录
    if (AuthManager.isLoggedIn()) {
      this.goToDashboard();
    }
  },

  // 微信一键登录
  async handleWechatLogin() {
    if (this.data.loading) return;
    this.setData({ loading: true });
    showLoading('登录中...');

    try {
      const res = await AuthManager.login();
      app.setLoginState(res.access_token, res.user);
      hideLoading();
      showToast('登录成功', 'success');
      setTimeout(() => {
        this.goToDashboard();
      }, 1000);
    } catch (err) {
      hideLoading();
      showToast(err.message || '登录失败，请重试');
    } finally {
      this.setData({ loading: false });
    }
  },

  // 账号密码登录
  async handleAccountLogin() {
    const { username, password } = this.data;
    if (!username || !password) {
      showToast('请输入用户名和密码');
      return;
    }
    if (this.data.loading) return;
    this.setData({ loading: true });
    showLoading('登录中...');

    try {
      const res = await AuthManager.loginWithPassword(username, password);
      app.setLoginState(res.access_token, res.user);
      hideLoading();
      showToast('登录成功', 'success');
      setTimeout(() => {
        this.goToDashboard();
      }, 1000);
    } catch (err) {
      hideLoading();
      showToast(err.message || '登录失败，请重试');
    } finally {
      this.setData({ loading: false });
    }
  },

  // 切换账号密码登录
  toggleAccountLogin() {
    this.setData({
      showAccountLogin: !this.data.showAccountLogin
    });
  },

  onUsernameInput(e) {
    this.setData({ username: e.detail.value });
  },

  onPasswordInput(e) {
    this.setData({ password: e.detail.value });
  },

  // 跳转首页
  goToDashboard() {
    wx.switchTab({ url: '/pages/dashboard/dashboard' });
  }
});
