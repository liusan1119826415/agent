<template>
  <div class="chat-layout">
    <!-- 顶部导航栏 -->
    <div class="top-nav">
      <div class="nav-left">
        <h1>智能客服系统</h1>
      </div>
      <div class="nav-right">
        <button @click="toggleSearchMode" class="nav-btn" :class="{ active: isSearchMode }">
          🔍 联网搜索
        </button>
        <button @click="toggleHumanService" class="nav-btn" :class="{ active: showHumanService }">
          👨‍💼 人工客服
        </button>
        <div class="user-info">
          <span>欢迎, {{ userStore.user?.username || '用户' }}</span>
          <button @click="handleLogout" class="logout-btn">退出</button>
        </div>
      </div>
    </div>

    <!-- 主聊天区域 -->
    <div class="main-content">
      <!-- 侧边栏 - 会话列表 -->
      <div class="sidebar">
        <div class="sidebar-header">
          <h3>会话历史</h3>
          <button @click="startNewConversation" class="btn btn-primary new-conversation-btn">
            + 新建会话
          </button>
        </div>
        <div class="conversations-list">
          <div
            v-for="conversation in chatStore.conversations"
            :key="conversation.id"
            :class="['conversation-item', { active: conversation.id === chatStore.currentConversationId }]"
            @click="loadConversation(conversation.id)"
          >
            <div class="conversation-info">
              <div class="conversation-title">{{ conversation.title || '未命名会话' }}</div>
              <div class="conversation-time">{{ formatDate(conversation.created_at || conversation.createdAt) }}</div>
            </div>
            <button 
              @click.stop="deleteConversation(conversation.id)" 
              class="delete-btn"
              title="删除会话"
            >
              ×
            </button>
          </div>
          <div v-if="chatStore.conversations.length === 0" class="no-conversations">
            暂无会话记录
          </div>
        </div>
      </div>

      <!-- 聊天主区域 -->
      <div class="chat-main">
        <!-- 聊天头部 -->
        <div class="chat-header">
          <h2>{{ currentConversationTitle }}</h2>
          <div class="header-actions">
            <input
              v-if="chatStore.currentConversationId"
              v-model="editingTitle"
              @blur="saveTitle"
              @keyup.enter="saveTitle"
              @dblclick.stop
              class="conversation-title-input"
              placeholder="双击编辑标题"
            />
            <button @click="startNewConversation" class="btn btn-secondary">
              新建会话
            </button>
          </div>
        </div>

        <!-- 消息区域 -->
        <div class="chat-messages" ref="messagesContainer">
          <div 
            v-for="message in chatStore.messages" 
            :key="message.id"
            :class="['message', message.sender]"
          >
            <div class="message-avatar">
              {{ message.sender === 'user' ? '👤' : message.sender === 'ai' ? '🤖' : '🔔' }}
            </div>
            <div class="message-content">
              <div class="message-text" v-html="formatMessage(message.content)"></div>
              <div class="message-time">{{ formatTime(message.timestamp) }}</div>
            </div>
          </div>
          
          <!-- 加载指示器 -->
          <div v-if="chatStore.isLoading" class="message ai">
            <div class="message-avatar">🤖</div>
            <div class="message-content">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>

          <!-- 人工客服信息展示 -->
          <div v-if="showHumanServiceInfo" class="message system">
            <div class="message-avatar">👨‍💼</div>
            <div class="message-content">
              <div class="human-service-info">
                <h3>{{ humanServiceInfo.customer_service_info?.name }}</h3>
                <p>{{ humanServiceInfo.customer_service_info?.description }}</p>
                
                <div class="contact-methods">
                  <div 
                    v-for="method in humanServiceInfo.customer_service_info?.contact_methods" 
                    :key="method.type"
                    class="contact-method"
                  >
                    <h4>{{ method.name }}</h4>
                    <p v-if="method.type === 'link'">
                      <a :href="method.url" target="_blank" class="contact-link">
                        {{ method.description }}
                      </a>
                    </p>
                    <p v-else-if="method.type === 'phone'">
                      电话: {{ method.number }}<br>
                      {{ method.description }}
                    </p>
                    <p v-else-if="method.type === 'wechat'">
                      微信: {{ method.account }}<br>
                      {{ method.description }}
                    </p>
                  </div>
                </div>
                
                <div class="service-info">
                  <p><strong>预计等待时间:</strong> {{ humanServiceInfo.customer_service_info?.estimated_wait_time }}</p>
                  <p><strong>服务时间:</strong> {{ humanServiceInfo.customer_service_info?.service_hours }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="chat-input-area">
          <form @submit.prevent="sendMessage" class="input-form">
            <!-- 图片预览 -->
            <div v-if="selectedImage" class="image-preview">
              <img :src="imagePreviewUrl" alt="Selected image" class="preview-image" />
              <button type="button" @click="removeImage" class="remove-image-btn">×</button>
            </div>
            
            <div class="input-row">
              <input
                type="file"
                ref="fileInputRef"
                accept="image/*"
                @change="handleImageSelect"
                class="file-input"
              />
              <button 
                type="button" 
                @click="selectImage" 
                :disabled="chatStore.isLoading"
                class="image-upload-btn"
                title="上传图片"
              >
                📷
              </button>
              
              <textarea
                v-model="inputMessage"
                @keydown="handleKeyDown"
                placeholder="请输入您的问题..."
                rows="1"
                :disabled="chatStore.isLoading"
                ref="inputRef"
                class="input-textarea"
              ></textarea>
              
              <button 
                type="submit" 
                :disabled="(!inputMessage.trim() && !selectedImage) || chatStore.isLoading"
                class="send-button"
              >
                {{ chatStore.isLoading ? '发送中...' : '发送' }}
              </button>
            </div>
            
            <!-- 模式提示 -->
            <div v-if="isSearchMode" class="mode-indicator search-mode">
              当前模式: 联网搜索
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, watch, computed } from 'vue';
import { useChatStore } from '@/stores/chatStore';
import { useUserStore } from '@/stores/userStore';
import { useRouter } from 'vue-router';

const chatStore = useChatStore();
const userStore = useUserStore();
const router = useRouter();

const inputMessage = ref('');
const messagesContainer = ref(null);
const inputRef = ref(null);
const fileInputRef = ref(null);
const selectedImage = ref(null);
const imagePreviewUrl = ref('');
const editingTitle = ref('');
const isSearchMode = ref(false);
const showHumanService = ref(false);
const showHumanServiceInfo = ref(false);
const humanServiceInfo = ref({});

// 计算属性
const currentConversationTitle = computed(() => {
  if (chatStore.currentConversationId) {
    const conversation = chatStore.conversations.find(c => c.id === chatStore.currentConversationId);
    return conversation?.name || '当前会话';
  }
  return isSearchMode.value ? '联网搜索会话' : '新建会话';
});

// 自动滚动到底部
watch(chatStore.messages, async () => {
  await nextTick();
  scrollToBottom();
});

// 加载会话列表
onMounted(async () => {
  await chatStore.loadConversations();
});

// 切换搜索模式
const toggleSearchMode = () => {
  isSearchMode.value = !isSearchMode.value;
  if (isSearchMode.value) {
    showHumanService.value = false;
  }
};

// 切换人工客服
const toggleHumanService = () => {
  showHumanService.value = !showHumanService.value;
  if (showHumanService.value) {
    isSearchMode.value = false;
    // 显示人工客服信息
    showHumanServiceInfo.value = true;
    humanServiceInfo.value = {
      customer_service_info: {
        name: "智能客服小助手",
        description: "我们的专业客服团队将为您提供一对一服务",
        contact_methods: [
          {
            type: "link",
            name: "在线客服",
            url: "https://your-company.com/live-chat",
            description: "点击进入在线客服聊天室"
          },
          {
            type: "phone",
            name: "客服热线",
            number: "400-123-4567",
            description: "工作时间：周一至周日 9:00-21:00"
          },
          {
            type: "wechat",
            name: "微信客服",
            account: "YourCompany_Service",
            description: "添加微信客服，随时为您服务"
          }
        ],
        estimated_wait_time: "2-5分钟",
        service_hours: "24小时在线"
      }
    };
  } else {
    showHumanServiceInfo.value = false;
  }
};

// 选择图片
const selectImage = () => {
  if (chatStore.isLoading) return;
  fileInputRef.value?.click();
};

// 处理图片选择
const handleImageSelect = (event) => {
  const file = event.target.files[0];
  if (file) {
    selectedImage.value = file;
    imagePreviewUrl.value = URL.createObjectURL(file);
  }
};

// 移除图片
const removeImage = () => {
  selectedImage.value = null;
  imagePreviewUrl.value = '';
  if (fileInputRef.value) {
    fileInputRef.value.value = '';
  }
};

// 发送消息
const sendMessage = async () => {
  if ((!inputMessage.value.trim() && !selectedImage.value) || chatStore.isLoading) return;
  
  const message = inputMessage.value;
  const imageFile = selectedImage.value;
  
  inputMessage.value = '';
  removeImage(); // 清除选中的图片
  
  // 检查是否是人工客服请求
  const humanServiceKeywords = ["人工客服", "转人工", "客服", "人工"];
  if (showHumanService.value && humanServiceKeywords.some(keyword => message.includes(keyword))) {
    showHumanServiceInfo.value = true;
    return;
  }
  
  await chatStore.sendMessage(message, imageFile, isSearchMode.value);
};

// 处理键盘事件
const handleKeyDown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
};

// 格式化时间
const formatTime = (date) => {
  if (!date) return '';
  const now = new Date();
  const msgDate = new Date(date);
  
  if (now.getDate() === msgDate.getDate() &&
      now.getMonth() === msgDate.getMonth() &&
      now.getFullYear() === msgDate.getFullYear()) {
    return msgDate.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  }
  
  return formatDate(date);
};

// 格式化日期
const formatDate = (date) => {
  if (!date) return '';
  const d = new Date(date);
  return d.toLocaleDateString('zh-CN');
};

// 格式化消息内容
const formatMessage = (content) => {
  if (!content) return '';
  
  // 转义HTML
  let escaped = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>');
  
  // 处理粗体
  escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // 处理斜体
  escaped = escaped.replace(/\*(.*?)\*/g, '<em>$1</em>');
  // 处理链接
  escaped = escaped.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
  
  return escaped;
};

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

// 开始新会话
const startNewConversation = () => {
  chatStore.startNewConversation();
  editingTitle.value = '';
  isSearchMode.value = false;
  showHumanService.value = false;
  showHumanServiceInfo.value = false;
};

// 加载会话
const loadConversation = async (conversationId) => {
  await chatStore.loadConversationMessages(conversationId);
  const conversation = chatStore.conversations.find(c => c.id === conversationId);
  editingTitle.value = conversation?.name || '';
  isSearchMode.value = false;
  showHumanService.value = false;
  showHumanServiceInfo.value = false;
};

// 删除会话
const deleteConversation = async (conversationId) => {
  if (confirm('确定要删除这个会话吗？')) {
    await chatStore.deleteConversation(conversationId);
  }
};

// 保存会话标题
const saveTitle = async () => {
  if (chatStore.currentConversationId && editingTitle.value.trim()) {
    await chatStore.updateConversationName(chatStore.currentConversationId, editingTitle.value.trim());
  }
};

// 用户登出
const handleLogout = async () => {
  if (confirm('确定要退出登录吗？')) {
    await userStore.logout();
    router.push('/login');
  }
};

// 自动调整文本框高度
const adjustTextareaHeight = () => {
  if (inputRef.value) {
    inputRef.value.style.height = 'auto';
    inputRef.value.style.height = Math.min(inputRef.value.scrollHeight, 150) + 'px';
  }
};

// 监听输入变化并调整高度
watch(inputMessage, () => {
  nextTick(adjustTextareaHeight);
});

onMounted(() => {
  adjustTextareaHeight();
});
</script>

<style scoped>
.chat-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1.5rem;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  z-index: 100;
}

.nav-left h1 {
  margin: 0;
  color: #333;
  font-size: 1.25rem;
  font-weight: 600;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.nav-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
  color: #666;
}

.nav-btn:hover {
  border-color: #007bff;
  color: #007bff;
  background: #f8f9ff;
}

.nav-btn.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-info span {
  font-size: 0.875rem;
  color: #666;
}

.logout-btn {
  padding: 0.5rem 1rem;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: background 0.2s;
}

.logout-btn:hover {
  background: #c82333;
}

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.sidebar {
  width: 280px;
  background: white;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 1rem;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 1rem;
  color: #333;
}

.new-conversation-btn {
  padding: 0.4rem 0.8rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
}

.new-conversation-btn:hover {
  background: #0056b3;
}

.conversations-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.conversation-item {
  padding: 0.75rem;
  border-radius: 6px;
  margin-bottom: 0.5rem;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background-color 0.2s;
  border: 1px solid transparent;
}

.conversation-item:hover {
  background: #f8f9fa;
  border-color: #e9ecef;
}

.conversation-item.active {
  background: #e3f2fd;
  border-color: #bbdefb;
}

.conversation-info {
  flex: 1;
}

.conversation-title {
  font-weight: 500;
  margin-bottom: 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 0.9rem;
}

.conversation-time {
  font-size: 0.75rem;
  color: #666;
}

.delete-btn {
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 1.2rem;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color 0.2s;
  flex-shrink: 0;
  margin-left: 0.5rem;
}

.delete-btn:hover {
  background: #ffcccc;
  color: #ff0000;
}

.no-conversations {
  padding: 1rem;
  text-align: center;
  color: #666;
  font-size: 0.9rem;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  overflow: hidden;
}

.chat-header {
  padding: 1rem;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-header h2 {
  margin: 0;
  color: #333;
  font-size: 1.1rem;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.conversation-title-input {
  padding: 0.3rem 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  outline: none;
  width: 150px;
}

.conversation-title-input:focus {
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.btn {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.btn-primary {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
  border-color: #6c757d;
}

.btn-secondary:hover {
  background: #5a6268;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  background: #fafafa;
}

.message {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  max-width: 90%;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.user .message-content {
  background: #007bff;
  color: white;
  border-radius: 18px 4px 18px 18px;
  max-width: 80%;
}

.message.ai .message-content {
  background: white;
  border-radius: 4px 18px 18px 18px;
  max-width: 80%;
  border: 1px solid #e0e0e0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.message.system .message-content {
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  color: #856404;
  border-radius: 18px;
  max-width: 80%;
}

.message-avatar {
  font-size: 1.2rem;
  flex-shrink: 0;
  margin-top: 0.25rem;
}

.message-content {
  padding: 0.75rem 1rem;
  position: relative;
  word-wrap: break-word;
  min-width: 50px;
}

.message-text {
  line-height: 1.5;
  white-space: pre-wrap;
}

.message-text strong {
  font-weight: bold;
}

.message-text em {
  font-style: italic;
}

.message-text a {
  color: #007bff;
  text-decoration: underline;
}

.message-time {
  font-size: 0.75rem;
  color: #666;
  margin-top: 0.25rem;
  text-align: right;
}

.typing-indicator {
  display: flex;
  gap: 0.25rem;
  align-items: center;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #666;
  border-radius: 50%;
  display: inline-block;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.chat-input-area {
  padding: 1rem;
  border-top: 1px solid #e0e0e0;
  background: white;
}

.input-form {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.image-preview {
  position: relative;
  max-width: 200px;
  margin-bottom: 0.5rem;
}

.preview-image {
  max-width: 100%;
  max-height: 150px;
  border-radius: 8px;
  border: 1px solid #ddd;
}

.remove-image-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #ff4444;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.input-row {
  display: flex;
  gap: 0.5rem;
  align-items: flex-end;
}

.file-input {
  display: none;
}

.image-upload-btn {
  padding: 0.75rem;
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1.2rem;
  transition: background-color 0.2s;
  border: none;
}

.image-upload-btn:hover {
  background: #e9ecef;
}

.image-upload-btn:disabled {
  background: #f8f9fa;
  cursor: not-allowed;
  opacity: 0.6;
}

.input-textarea {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  resize: none;
  min-height: 40px;
  max-height: 150px;
  font-family: inherit;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s;
  line-height: 1.5;
}

.input-textarea:focus {
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.send-button {
  padding: 0.75rem 1.5rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.2s;
  white-space: nowrap;
}

.send-button:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.send-button:not(:disabled):hover {
  background: #0056b3;
}

.mode-indicator {
  margin-top: 0.5rem;
  padding: 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  text-align: center;
}

.search-mode {
  background: #e8f5e8;
  color: #2e7d32;
  border: 1px solid #c8e6c9;
}

.human-service-info {
  max-width: 100%;
}

.human-service-info h3 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1.1rem;
}

.human-service-info p {
  margin: 0 0 1rem 0;
  color: #666;
  line-height: 1.5;
}

.contact-methods {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin: 1rem 0;
}

.contact-method {
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.contact-method h4 {
  margin: 0 0 0.5rem 0;
  color: #495057;
  font-size: 0.9rem;
}

.contact-link {
  color: #007bff;
  text-decoration: none;
  font-weight: 500;
}

.contact-link:hover {
  text-decoration: underline;
}

.service-info {
  background: #e3f2fd;
  padding: 1rem;
  border-radius: 8px;
  border-left: 4px solid #2196f3;
}

.service-info p {
  margin: 0.25rem 0;
  color: #1976d2;
  font-size: 0.9rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-layout {
    height: 100vh;
  }
  
  .top-nav {
    padding: 0.5rem 1rem;
  }
  
  .nav-left h1 {
    font-size: 1rem;
  }
  
  .nav-right {
    gap: 0.5rem;
  }
  
  .nav-btn {
    padding: 0.4rem 0.6rem;
    font-size: 0.8rem;
  }
  
  .sidebar {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 90;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }
  
  .sidebar.show {
    transform: translateX(0);
  }
  
  .chat-main {
    width: 100%;
  }
  
  .message {
    max-width: 95%;
  }
  
  .message.user .message-content,
  .message.ai .message-content {
    max-width: 90%;
  }
  
  .contact-methods {
    grid-template-columns: 1fr;
  }
}
</style>