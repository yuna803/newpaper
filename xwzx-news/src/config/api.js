/**
 * API配置文件
 * 包含API基础URL和AI问答功能所需的API参数
 */

// API基础URL配置
export const apiConfig = {
  // 后端API基础URL
  baseURL: 'http://127.0.0.1:8000',
}

// AI 问答已迁移到后端 RAG，前端不再直接调用 LLM API
// API Key 在后端环境变量 DASHSCOPE_API_KEY 中配置
