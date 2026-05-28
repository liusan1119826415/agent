import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000', // 后端API基础URL
  timeout: 30000, // 请求超时时间
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 在发送请求之前做些什么，比如添加认证token
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// API方法定义
export const chatApi = {
  // 发送消息到LangGraph
  sendQuery: (query, userId, conversationId, imageFile = null) => {
    const formData = new FormData();
    formData.append('query', query);
    formData.append('user_id', userId);
    if (conversationId) {
      formData.append('conversation_id', conversationId);
    }
    if (imageFile) {
      formData.append('image', imageFile);
    }

    return api.post('/api/langgraph/query', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      responseType: 'stream',
    });
  },

  // 继续执行被中断的查询
  resumeQuery: (query, userId, conversationId) => {
    return api.post('/api/langgraph/resume', {
      query,
      user_id: userId,
      conversation_id: conversationId,
    });
  },

  // 获取会话列表
  getConversations: (userId) => {
    return api.get(`/api/conversations/user/${userId}`);
  },

  // 获取特定会话的消息
  getConversationMessages: (conversationId, userId) => {
    return api.get(`/api/conversations/${conversationId}/messages?user_id=${userId}`);
  },

  // 删除会话
  deleteConversation: (conversationId) => {
    return api.delete(`/api/conversations/${conversationId}`);
  },

  // 更新会话名称
  updateConversationName: (conversationId, name) => {
    return api.put(`/api/conversations/${conversationId}/name`, { name });
  },

  // 上传图片
  uploadImage: (imageFile, userId, conversationId = null) => {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('user_id', userId);
    if (conversationId) {
      formData.append('conversation_id', conversationId);
    }

    return api.post('/api/upload/image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

export default chatApi;