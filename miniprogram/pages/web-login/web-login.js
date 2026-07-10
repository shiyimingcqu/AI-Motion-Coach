// web-login 页 — 扫码自动登录
// 扫码进入时，scene 中携带 ticket，自动 wx.login + 提交登录
const ApiClient = require('../../utils/api');
const { showToast, showLoading, hideLoading } = require('../../utils/util');

Page({
  data: {
    status: 'processing', // processing | success | fail
    message: ''
  },

  onLoad(options) {
    const scene = decodeURIComponent(options.scene || '');
    const match = scene.match(/web_login=([a-f0-9]+)/);
    const ticket = match ? match[1] : null;

    if (!ticket) {
      this.setData({ status: 'fail', message: '无效的二维码' });
      return;
    }

    this.doLogin(ticket);
  },

  async doLogin(ticket) {
    showLoading('登录中...');
    try {
      const loginRes = await new Promise((resolve, reject) => {
        wx.login({
          success: res => res.code ? resolve(res) : reject(new Error('wx.login 失败')),
          fail: reject
        });
      });

      await ApiClient.post('/wechat/web-login/login', {
        code: loginRes.code,
        ticket: ticket
      });

      this.setData({ status: 'success', message: '登录成功，请返回 Web 端' });
      showToast('登录成功', 'success');

      setTimeout(() => {
        wx.navigateBack();
      }, 2000);
    } catch (err) {
      hideLoading();
      this.setData({ status: 'fail', message: err.message || '登录失败' });
      showToast(err.message || '登录失败');
    }
  }
});
