import axios from 'axios'
// 替换为电商类型定义
import type { ShoppingFormData, ShoppingResponse } from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 600000, // 超时时间保留
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器（完全保留，不动）
apiClient.interceptors.request.use(
  (config) => {
    console.log('发送请求:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器（完全保留，不动）
apiClient.interceptors.response.use(
  (response) => {
    console.log('收到响应:', response.status, response.config.url)
    return response
  },
  (error) => {
    console.error('响应错误:', error.response?.status, error.message)
    return Promise.reject(error)
  }
)

/**
 * 生成电商导购报告（替换旅行计划接口）
 */
export async function generateShoppingReport(formData: ShoppingFormData): Promise<ShoppingResponse> {
  try {
    // 接口地址替换为电商路由
    const response = await apiClient.post<ShoppingResponse>('/api/shop/generate', formData)
    return response.data
  } catch (error: any) {
    console.error('生成电商导购报告失败:', error)
    throw new Error(error.response?.data?.detail || error.message || '生成电商导购报告失败')
  }
}

/**
 * 健康检查（保留，适配电商）
 */
export async function healthCheck(): Promise<any> {
  try {
    const response = await apiClient.get('/api/shop/health')
    return response.data
  } catch (error: any) {
    console.error('电商服务健康检查失败:', error)
    throw new Error(error.message || '电商服务健康检查失败')
  }
}

export default apiClient