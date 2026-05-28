import { defineStore } from 'pinia';
import { ref } from 'vue';
import { chatApi } from '@/api/chatApi';
import { useUserStore } from '@/stores/userStore';

export const useChatStore = defineStore('chat', () => {
  // 状态
  const messages = ref([]);
  const isLoading = ref(false);
  const currentConversationId = ref(null);
  const conversations = ref([]); // 会话列表
  const userStore = useUserStore();

  // 方法
  const addMessage = (message) => {
    messages.value.push(message);
  };

  const clearMessages = () => {
    messages.value = [];
  };

  const startNewConversation = () => {
    clearMessages();
    currentConversationId.value = null;
  };

  const sendMessage = async (query, imageFile = null, isSearchMode = false) => {
    if ((!query.trim() && !imageFile) || isLoading.value) return;

    try {
      // 添加用户消息到本地
      const userMessage = {
        id: Date.now(),
        sender: 'user',
        content: query,
        timestamp: new Date(),
      };
      addMessage(userMessage);

      // 设置加载状态
      isLoading.value = true;

      // 构建请求参数
      const formData = new FormData();
      formData.append('query', query);
      formData.append('user_id', userStore.user?.id || 1);
      if (currentConversationId.value) {
        formData.append('conversation_id', currentConversationId.value);
      }
      if (imageFile) {
        formData.append('image', imageFile);
      }

      // 选择合适的API端点
      let response;
      if (isSearchMode) {
        // 联网搜索模式
        response = await fetch('http://localhost:8000/api/search', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${userStore.token}`
          },
          body: JSON.stringify({
            messages: [{ role: 'user', content: query }],
            user_id: userStore.user?.id || 1,
            conversation_id: currentConversationId.value || 0
          })
        });
      } else {
        // 普通聊天模式
        response = await fetch('http://localhost:8000/api/langgraph/query', {
          method: 'POST',
          body: formData,
        });
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // 处理响应
      if (isSearchMode) {
        // 搜索模式返回JSON
        const data = await response.json();
        const aiMessage = {
          id: Date.now() + 1,
          sender: 'ai',
          content: data.response || '搜索完成',
          timestamp: new Date(),
        };
        addMessage(aiMessage);
      } else {
        // 聊天模式处理SSE流
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        // 添加AI回复消息
        let aiMessage = {
          id: Date.now() + 1,
          sender: 'ai',
          content: '',
          timestamp: new Date(),
        };
        addMessage(aiMessage);

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          
          // 处理缓冲区中的数据块
          const lines = buffer.split('\n');
          buffer = lines.pop(); // 保留未完成的行

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6); // 移除 'data: ' 前缀
              try {
                const parsed = JSON.parse(data);
                
                // 检查是否是中断消息
                if (parsed.interruption) {
                  // 处理中断情况
                  currentConversationId.value = parsed.conversation_id;
                  break;
                } else if (parsed.type === 'human_service') {
                  // 处理人工客服响应
                  const humanMessage = {
                    id: Date.now() + 2,
                    sender: 'system',
                    content: parsed.message,
                    timestamp: new Date(),
                  };
                  addMessage(humanMessage);
                  break;
                } else {
                  // 更新AI消息内容
                  if (typeof parsed === 'string') {
                    aiMessage.content += parsed;
                  } else if (typeof parsed === 'object' && parsed.content) {
                    aiMessage.content += parsed.content;
                  } else {
                    aiMessage.content += JSON.stringify(parsed);
                  }
                  
                  // 更新消息数组引用以触发UI更新
                  const index = messages.value.findIndex(msg => msg.id === aiMessage.id);
                  if (index !== -1) {
                    messages.value[index] = { ...aiMessage };
                  }
                }
              } catch (e) {
                console.error('Error parsing SSE data:', e, data);
              }
            }
          }
        }

        // 获取会话ID（如果存在的话）
        const headers = [...response.headers.entries()].reduce((acc, [key, value]) => {
          acc[key.toLowerCase()] = value;
          return acc;
        }, {});
        
        const conversationId = headers['x-conversation-id'] || headers['x-conversationid'];
        if (conversationId) {
          currentConversationId.value = conversationId;
        }
      }
      
      // 刷新会话列表
      await loadConversations();
    } catch (error) {
      console.error('Error sending message:', error);
      
      // 添加错误消息
      const errorMessage = {
        id: Date.now(),
        sender: 'system',
        content: `发送消息时出现错误: ${error.message}`,
        timestamp: new Date(),
      };
      addMessage(errorMessage);
    } finally {
      isLoading.value = false;
    }
  };

  // 获取会话列表
  const loadConversations = async () => {
    try {
      const response = await chatApi.getConversations(userStore.user?.id || 1);
      conversations.value = Array.isArray(response.data) ? response.data : [];
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
  };

  // 加载特定会话的消息
  const loadConversationMessages = async (conversationId) => {
    try {
      isLoading.value = true;
      const response = await chatApi.getConversationMessages(conversationId, userStore.user?.id || 1);
      messages.value = Array.isArray(response.data) ? response.data : [];
      currentConversationId.value = conversationId;
    } catch (error) {
      console.error('Error loading conversation messages:', error);
      
      // 添加错误消息
      const errorMessage = {
        id: Date.now(),
        sender: 'system',
        content: `加载会话消息时出现错误: ${error.message}`,
        timestamp: new Date(),
      };
      addMessage(errorMessage);
    } finally {
      isLoading.value = false;
    }
  };

  // 删除会话
  const deleteConversation = async (conversationId) => {
    try {
      await chatApi.deleteConversation(conversationId);
      conversations.value = conversations.value.filter(conv => conv.id !== conversationId);
      
      // 如果删除的是当前会话，则开始新会话
      if (currentConversationId.value === conversationId) {
        startNewConversation();
      }
    } catch (error) {
      console.error('Error deleting conversation:', error);
      
      // 添加错误消息
      const errorMessage = {
        id: Date.now(),
        sender: 'system',
        content: `删除会话时出现错误: ${error.message}`,
        timestamp: new Date(),
      };
      addMessage(errorMessage);
    }
  };

  // 更新会话名称
  const updateConversationName = async (conversationId, name) => {
    try {
      await chatApi.updateConversationName(conversationId, name);
      const conversation = conversations.value.find(conv => conv.id === conversationId);
      if (conversation) {
        conversation.name = name;
      }
    } catch (error) {
      console.error('Error updating conversation name:', error);
      
      // 添加错误消息
      const errorMessage = {
        id: Date.now(),
        sender: 'system',
        content: `更新会话名称时出现错误: ${error.message}`,
        timestamp: new Date(),
      };
      addMessage(errorMessage);
    }
  };

  // 上传图片
  const uploadImage = async (imageFile) => {
    try {
      const response = await chatApi.uploadImage(imageFile, userStore.user?.id || 1, currentConversationId.value);
      return response.data;
    } catch (error) {
      console.error('Error uploading image:', error);
      throw error;
    }
  };

  return {
    messages,
    isLoading,
    currentConversationId,
    conversations,
    addMessage,
    clearMessages,
    startNewConversation,
    sendMessage,
    loadConversations,
    loadConversationMessages,
    deleteConversation,
    updateConversationName,
    uploadImage,
  };
});