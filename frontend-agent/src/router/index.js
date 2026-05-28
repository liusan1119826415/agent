import { createRouter, createWebHistory } from 'vue-router';
import { useUserStore } from '@/stores/userStore';
import Login from '@/components/Login.vue';
import ChatInterface from '@/components/ChatInterface.vue';

const routes = [
  {
    path: '/',
    redirect: '/chat'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresGuest: true }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: ChatInterface,
    meta: { requiresAuth: true }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore();
  
  // 初始化认证状态
  if (!userStore.isAuthenticated && localStorage.getItem('token')) {
    try {
      await userStore.initAuth();
    } catch (error) {
      console.log('Auth init failed:', error);
    }
  }

  //检查路由权限
  if (to.meta.requiresAuth && !userStore.isAuthenticated) {
    next('/login');
  } else if (to.meta.requiresGuest && userStore.isAuthenticated) {
    next('/chat');
  } else {
    next();
  }
});

export default router;