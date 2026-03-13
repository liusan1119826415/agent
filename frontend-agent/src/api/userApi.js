import axios from 'axios';
import CryptoJS from 'crypto-js'; // 添加加密库

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

//响应拦截器
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // token过期或无效，清除本地存储
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// SHA256加密函数
const hashPassword = (password) => {
  return CryptoJS.SHA256(password).toString();
};

export const userApi = {
  // 用户登录 - 使用SHA256哈希密码
  login: (email, password) => {
    const hashedPassword = hashPassword(password);
    return api.post('/api/token', {
      email: email,
      password: hashedPassword  // 发送哈希后的密码
    });
  },

  // 用户注册
  register: (username, email, password) => {
    const hashedPassword = hashPassword(password);
    return api.post('/api/register', {
      username,
      email,
      password: hashedPassword  // 注册时也使用哈希密码
    });
  },

  // 用户登出
  logout: () => {
    return api.post('/api/logout');
  },

  // 获取当前用户信息
  getCurrentUser: () => {
    return api.get('/api/users/me');
  },

  //刷新token
  refreshToken: () => {
    return api.post('/api/refresh');
  },

  // SSO登录 - 电商网站会话登录
  ssoLogin: (sessionId) => {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    return api.post('/api/auth/sso/token', formData);
  },

  //验证SSO令牌
  validateSsoToken: () => {
    return api.get('/api/auth/sso/validate');
  }
};

export default userApi;