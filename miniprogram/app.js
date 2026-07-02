// 运动姿态评估与纠错系统 - 微信小程序全局入口
const AuthManager = require('./utils/auth');

App({
  globalData: {
    userInfo: null,
    isLoggedIn: false,
    token: null
  },

  onLaunch() {
    // 检查登录态
    this.checkLoginStatus();
  },

  checkLoginStatus() {
    const isLoggedIn = AuthManager.isLoggedIn();
    this.globalData.isLoggedIn = isLoggedIn;
    if (isLoggedIn) {
      this.globalData.token = AuthManager.getToken();
      this.globalData.userInfo = AuthManager.getUserInfo();
    }
  },

  // 设置登录状态
  setLoginState(token, user) {
    this.globalData.token = token;
    this.globalData.userInfo = user;
    this.globalData.isLoggedIn = true;
    AuthManager.setToken(token);
    AuthManager.setUserInfo(user);
  },

  // 清除登录状态
  clearLoginState() {
    this.globalData.token = null;
    this.globalData.userInfo = null;
    this.globalData.isLoggedIn = false;
    AuthManager.logout();
  }
});
