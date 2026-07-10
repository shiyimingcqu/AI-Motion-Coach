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
  },

  // 用户协议
  onAgreementTap() {
    wx.showModal({
      title: '用户协议',
      content: '本应用为智能运动姿态分析系统，通过摄像头采集用户运动姿态数据，经后端AI引擎分析后提供实时反馈与纠错建议。\n\n使用本服务即表示您同意我们收集必要的运动数据用于分析目的。您的数据将被安全存储并严格保密。',
      showCancel: false,
      confirmText: '我知道了',
    });
  },

  // 隐私政策
  onPrivacyTap() {
    wx.showModal({
      title: '隐私政策',
      content: '我们重视您的隐私保护：\n1. 运动数据仅用于姿态分析与训练评估\n2. 骨架识别在本地/服务端处理后即时存储\n3. 不向第三方共享您的个人运动数据\n4. 您可随时删除自己的训练记录',
      showCancel: false,
      confirmText: '我知道了',
    });
  }
});
