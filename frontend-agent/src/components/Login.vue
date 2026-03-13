<template>
  <div class="login-container">
    <div class="login-form">
      <div class="logo">
        <h1>智能客服系统</h1>
        <p>欢迎使用AI助手服务</p>
      </div>
      
      <!-- SSO登录提示 -->
      <div v-if="hasEcommerceSession" class="sso-prompt">
        <div class="sso-info">
          <h3>检测到电商网站登录</h3>
          <p>您已在电商网站登录，可以直接使用客服服务</p>
          <button @click="handleSSOLogin" class="sso-btn" :disabled="isSSOLoading">
            {{ isSSOLoading ? '登录中...' : '直接使用客服服务' }}
          </button>
        </div>
      </div>
      
      <!-- 传统登录表单 -->
      <form v-else @submit.prevent="handleLogin" class="form">
        <div class="form-group">
          <label for="username">用户名/邮箱</label>
          <input
            id="username"
            v-model="loginForm.username"
            type="text"
            placeholder="请输入用户名或邮箱"
            required
            :disabled="isLoading"
          />
        </div>
        
        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            required
            :disabled="isLoading"
          />
        </div>
        
        <button 
          type="submit" 
          class="login-btn"
          :disabled="isLoading || !loginForm.username || !loginForm.password"
        >
          {{ isLoading ? '登录中...' : '登录' }}
        </button>
        
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
      </form>
      
      <div class="register-link">
        <p>还没有账号？<a href="#" @click="showRegister = true">立即注册</a></p>
      </div>
    </div>
    
    <!-- 注册模态框 -->
    <div v-if="showRegister" class="modal-overlay" @click="showRegister = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>用户注册</h2>
          <button class="close-btn" @click="showRegister = false">×</button>
        </div>
        
        <form @submit.prevent="handleRegister" class="register-form">
          <div class="form-group">
            <label for="reg-username">用户名</label>
            <input
              id="reg-username"
              v-model="registerForm.username"
              type="text"
              placeholder="请输入用户名"
              required
              :disabled="isRegistering"
            />
          </div>
          
          <div class="form-group">
            <label for="reg-email">邮箱</label>
            <input
              id="reg-email"
              v-model="registerForm.email"
              type="email"
              placeholder="请输入邮箱"
              required
              :disabled="isRegistering"
            />
          </div>
          
          <div class="form-group">
            <label for="reg-password">密码</label>
            <input
              id="reg-password"
              v-model="registerForm.password"
              type="password"
              placeholder="请输入密码"
              required
              :disabled="isRegistering"
            />
          </div>
          
          <div class="form-group">
            <label for="reg-confirm-password">确认密码</label>
            <input
              id="reg-confirm-password"
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="请确认密码"
              required
              :disabled="isRegistering"
            />
          </div>
          
          <button 
            type="submit" 
            class="register-btn"
            :disabled="isRegistering || !isRegisterFormValid"
          >
            {{ isRegistering ? '注册中...' : '注册' }}
          </button>
          
          <div v-if="registerError" class="error-message">
            {{ registerError }}
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useUserStore } from '@/stores/userStore';
import { useRouter } from 'vue-router';

const userStore = useUserStore();
const router = useRouter();

const loginForm = ref({
  username: '',
  password: ''
});

const registerForm = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
});

const isLoading = ref(false);
const isSSOLoading = ref(false);
const isRegistering = ref(false);
const errorMessage = ref('');
const registerError = ref('');
const showRegister = ref(false);
const hasEcommerceSession = ref(false);

const isRegisterFormValid = computed(() => {
  return registerForm.value.username &&
         registerForm.value.email &&
         registerForm.value.password &&
         registerForm.value.password === registerForm.value.confirmPassword;
});

// 检查是否存在电商网站会话
const checkEcommerceSession = () => {
  // 检查cookie或localStorage中是否有电商网站的会话标识
  const ecommerceSession = localStorage.getItem('ecommerce_session_id') || 
                          getCookie('ecommerce_session');
  
  hasEcommerceSession.value = !!ecommerceSession;
  return ecommerceSession;
};

// 获取cookie值
const getCookie = (name) => {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
};

// 处理SSO登录
const handleSSOLogin = async () => {
  const sessionId = checkEcommerceSession();
  if (!sessionId) {
    errorMessage.value = '未检测到有效的电商网站会话';
    return;
  }

  isSSOLoading.value = true;
  errorMessage.value = '';

  try {
    await userStore.ssoLogin(sessionId);
    router.push('/chat');
  } catch (error) {
    errorMessage.value = error.message || 'SSO登录失败';
  } finally {
    isSSOLoading.value = false;
  }
};

// 传统登录
const handleLogin = async () => {
  if (!loginForm.value.username || !loginForm.value.password) return;
  
  isLoading.value = true;
  errorMessage.value = '';
  
  try {
    await userStore.login(loginForm.value.username, loginForm.value.password);
    router.push('/chat');
  } catch (error) {
    errorMessage.value = error.message || '登录失败，请检查用户名和密码';
  } finally {
    isLoading.value = false;
  }
};

// 处理注册
const handleRegister = async () => {
  if (!isRegisterFormValid.value) return;
  
  isRegistering.value = true;
  registerError.value = '';
  
  try {
    await userStore.register(
      registerForm.value.username,
      registerForm.value.email,
      registerForm.value.password
    );
    
    // 注册成功后自动登录
    await userStore.login(registerForm.value.username, registerForm.value.password);
    router.push('/chat');
  } catch (error) {
    registerError.value = error.message || '注册失败';
  } finally {
    isRegistering.value = false;
  }
};

// 页面加载时检查会话
onMounted(() => {
  checkEcommerceSession();
});
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.login-form {
  background: white;
  padding: 2.5rem;
  border-radius: 12px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
  backdrop-filter: blur(10px);
}

.logo {
  text-align: center;
  margin-bottom: 2rem;
}

.logo h1 {
  color: #333;
  margin-bottom: 0.5rem;
  font-size: 1.8rem;
  font-weight: 600;
}

.logo p {
  color: #666;
  margin: 0;
  font-size: 1rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #333;
  font-weight: 500;
  font-size: 0.9rem;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.3s;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-group input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.login-btn, .register-btn {
  width: 100%;
  padding: 0.75rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 0.5rem;
}

.login-btn:hover:not(:disabled), .register-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.login-btn:disabled, .register-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.error-message {
  color: #e74c3c;
  margin-top: 1rem;
  text-align: center;
  font-size: 0.9rem;
  padding: 0.5rem;
  background: #fdeded;
  border-radius: 4px;
  border: 1px solid #f5c6cb;
}

.register-link {
  text-align: center;
  margin-top: 1.5rem;
  color: #666;
  font-size: 0.9rem;
}

.register-link a {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
  margin-left: 0.25rem;
}

.register-link a:hover {
  text-decoration: underline;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  position: relative;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #eee;
}

.modal-header h2 {
  margin: 0;
  color: #333;
  font-size: 1.5rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f0f0f0;
  color: #333;
}

.register-form {
  margin-top: 1rem;
}

.sso-prompt {
  background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
  border: 1px solid #c8e6c9;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  text-align: center;
}

.sso-info h3 {
  margin: 0 0 0.5rem 0;
  color: #2e7d32;
  font-size: 1.2rem;
}

.sso-info p {
  margin: 0 0 1rem 0;
  color: #388e3c;
  font-size: 0.9rem;
}

.sso-btn {
  width: 100%;
  padding: 0.75rem;
  background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.sso-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(76, 175, 80, 0.4);
}

.sso-btn:disabled {
  background: #a5d6a7;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-container {
    padding: 10px;
  }
  
  .login-form {
    padding: 1.5rem;
    margin: 10px;
  }
  
  .modal-content {
    width: 95%;
    margin: 20px;
    padding: 1.5rem;
  }
  
  .logo h1 {
    font-size: 1.5rem;
  }
  
  .modal-header h2 {
    font-size: 1.25rem;
  }
}
</style>