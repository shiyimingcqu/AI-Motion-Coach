// 认证工具：wx.login → JWT 交换、token 存取
const ApiClient = require('./api');
const Storage = require('./storage');

class AuthManager {
  // 获取 token
  static getToken() {
    return Storage.get(Storage.KEYS.TOKEN);
  }

  // 获取用户信息
  static getUserInfo() {
    return Storage.get(Storage.KEYS.USER_INFO);
  }

  // 存储 token
  static setToken(token) {
    Storage.set(Storage.KEYS.TOKEN, token);
    // 6天后过期
    Storage.set(Storage.KEYS.TOKEN_EXPIRE, Date.now() + 6 * 24 * 3600 * 1000);
  }

  // 存储用户信息
  static setUserInfo(user) {
    Storage.set(Storage.KEYS.USER_INFO, user);
  }

  // 检查登录态
  static isLoggedIn() {
    const token = this.getToken();
    const expire = Storage.get(Storage.KEYS.TOKEN_EXPIRE);
    return !!(token && expire && expire > Date.now());
  }

  // 微信一键登录
  static async login() {
    try {
      // 1. 获取微信登录 code
      const loginRes = await new Promise((resolve, reject) => {
        wx.login({
          success: resolve,
          fail: reject
        });
      });

      if (!loginRes.code) {
        throw new Error('获取微信登录凭证失败');
      }

      // 2. 换取 JWT
      const res = await ApiClient.post('/api/auth/wechat-login', {
        code: loginRes.code
      });

      // 3. 存储
      this.setToken(res.access_token);
      this.setUserInfo(res.user);

      return res;
    } catch (err) {
      throw err;
    }
  }

  // 账号密码登录（备用）
  static async loginWithPassword(username, password) {
    try {
      const res = await ApiClient.postForm('/api/auth/login', {
        username: username,
        password: password
      });

      this.setToken(res.access_token);
      this.setUserInfo(res.user);

      return res;
    } catch (err) {
      throw err;
    }
  }

  // 退出登录
  static logout() {
    Storage.remove(Storage.KEYS.TOKEN);
    Storage.remove(Storage.KEYS.TOKEN_EXPIRE);
    Storage.remove(Storage.KEYS.USER_INFO);
  }

  // 获取当前用户信息（从后端刷新）
  static async fetchUserInfo() {
    try {
      const user = await ApiClient.get('/api/auth/me');
      this.setUserInfo(user);
      return user;
    } catch (err) {
      return null;
    }
  }
}

module.exports = AuthManager;
