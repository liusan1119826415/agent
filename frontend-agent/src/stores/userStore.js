import { defineStore } from 'pinia';
import { ref } from 'vue';
import { userApi } from '@/api/userApi';

export const useUserStore = defineStore('user', () => {
  // 状态
  const user = ref(null);
  const token = ref(localStorage.getItem('token') || '');
  const isAuthenticated = ref(!!token.value);
  const isSSOUser = ref(false);

  // 方法
  const setUser = (userData, isSSO = false) => {
    user.value = userData;
    isAuthenticated.value = true;
    isSSOUser.value = isSSO;
  };

  const setToken = (authToken) => {
    token.value = authToken;
    localStorage.setItem('token', authToken);
    isAuthenticated.value = true;
  };

  const clearAuth = () => {
    user.value = null;
    token.value = '';
    isAuthenticated.value = false;
    isSSOUser.value = false;
    localStorage.removeItem('token');
  };

  const login = async (email, password) => {
    try {
      const response = await userApi.login(email, password);
    
      const { access_token, token_type } = response.data;
      
      setToken(access_token);
      // 登录成功后获取用户信息
      await getCurrentUser();
      
      return response.data;
    } catch (error) {
      console.error('Login failed:', error);
      throw new Error(error.response?.data?.detail || '登录失败');
    }
  };

  const ssoLogin = async (sessionId) => {
    try {
      const response = await userApi.ssoLogin(sessionId);
      const { access_token, user: userData } = response.data;
      
      setToken(access_token);
      if (userData) {
        setUser(userData, true);
      }
      
      return response.data;
    } catch (error) {
      console.error('SSO Login failed:', error);
      throw new Error(error.response?.data?.detail || 'SSO登录失败');
    }
  };

  const register = async (username, email, password) => {
    try {
      const response = await userApi.register(username, email, password);
      return response.data;
    } catch (error) {
      console.error('Registration failed:', error);
      throw new Error(error.response?.data?.detail || '注册失败');
    }
  };

  const logout = async () => {
    try {
      if (token.value) {
        await userApi.logout();
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      clearAuth();
    }
  };

  const getCurrentUser = async () => {
    if (!token.value) {
      throw new Error('No token available');
    }

    try {
      const response = await userApi.getCurrentUser();
      setUser(response.data);
      return response.data;
    } catch (error) {
      console.error('Get current user failed:', error);
      clearAuth();
      throw error;
    }
  };

  const validateSSOToken = async () => {
    if (!token.value || !isSSOUser.value) {
      return false;
    }

    try {
      const response = await userApi.validateSsoToken();
      return response.data.valid;
    } catch (error) {
      console.error('SSO token validation failed:', error);
      clearAuth();
      return false;
    }
  };

  // 初始化时检查认证状态
  const initAuth = async () => {
    if (token.value) {
      try {
        await getCurrentUser();
        // 如果是SSO用户，验证令牌有效性
        if (isSSOUser.value) {
          const isValid = await validateSSOToken();
          if (!isValid) {
            clearAuth();
          }
        }
      } catch (error) {
        console.log('Auth initialization failed:', error);
        clearAuth();
      }
    }
  };

  return {
    user,
    token,
    isAuthenticated,
    isSSOUser,
    setUser,
    setToken,
    clearAuth,
    login,
    ssoLogin,
    register,
    logout,
    getCurrentUser,
    validateSSOToken,
    initAuth
  };
});