<template>
  <div class="home-container">
    <!-- 背景装饰（保留原样式） -->
    <div class="bg-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>

    <!-- 页面标题（电商版） -->
    <div class="page-header">
      <div class="icon-wrapper">
        <span class="icon">🛒</span>
      </div>
      <h1 class="page-title">智能电商导购助手</h1>
      <p class="page-subtitle">基于AI的个性化商品推荐、比价、测评，让购物更省心更划算</p>
    </div>

    <a-card class="form-card" :bordered="false">
      <a-form
        :model="formData"
        layout="vertical"
        @finish="handleSubmit"
      >
        <!-- 第一步: 商品类别与预算 -->
        <div class="form-section">
          <div class="section-header">
            <span class="section-icon">📱</span>
            <span class="section-title">商品类别与预算</span>
          </div>

          <a-row :gutter="24">
            <a-col :span="8">
              <a-form-item name="product_category" :rules="[{ required: true, message: '请输入商品类别' }]">
                <template #label>
                  <span class="form-label">商品类别</span>
                </template>
                <a-input
                  v-model:value="formData.product_category"
                  placeholder="例如: 智能手机、笔记本电脑"
                  size="large"
                  class="custom-input"
                >
                  <template #prefix>
                    <span style="color: #1890ff;">🏷️</span>
                  </template>
                </a-input>
              </a-form-item>
            </a-col>
            <a-col :span="6">
              <a-form-item :rules="[{ required: true, message: '请输入最低预算' }]">
                <template #label>
                  <span class="form-label">最低预算(元)</span>
                </template>
                <a-input-number
                  v-model:value="formData.budget_range.min"
                  :min="0"
                  style="width: 100%"
                  size="large"
                  placeholder="最低预算"
                />
              </a-form-item>
            </a-col>
            <a-col :span="6">
              <a-form-item :rules="[{ required: true, message: '请输入最高预算' }]">
                <template #label>
                  <span class="form-label">最高预算(元)</span>
                </template>
                <a-input-number
                  v-model:value="formData.budget_range.max"
                  :min="0"
                  style="width: 100%"
                  size="large"
                  placeholder="最高预算"
                />
              </a-form-item>
            </a-col>
            <a-col :span="4">
              <a-form-item>
                <template #label>
                  <span class="form-label">预算区间</span>
                </template>
                <div class="days-display-compact">
                  <span class="days-value">{{ formData.budget_range.min }}-{{ formData.budget_range.max }}</span>
                  <span class="days-unit">元</span>
                </div>
              </a-form-item>
            </a-col>
          </a-row>
        </div>

        <!-- 第二步: 购物偏好设置 -->
        <div class="form-section">
          <div class="section-header">
            <span class="section-icon">⚙️</span>
            <span class="section-title">购物偏好设置</span>
          </div>

          <a-row :gutter="24">
            <a-col :span="8">
              <a-form-item name="brand_preference">
                <template #label>
                  <span class="form-label">品牌倾向</span>
                </template>
                <div class="preference-tags">
                  <a-checkbox-group v-model:value="formData.brand_preference" class="custom-checkbox-group">
                    <a-checkbox value="华为" class="preference-tag">华为</a-checkbox>
                    <a-checkbox value="苹果" class="preference-tag">苹果</a-checkbox>
                    <a-checkbox value="小米" class="preference-tag">小米</a-checkbox>
                    <a-checkbox value="联想" class="preference-tag">联想</a-checkbox>
                  </a-checkbox-group>
                </div>
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item name="usage_scenarios">
                <template #label>
                  <span class="form-label">使用场景</span>
                </template>
                <div class="preference-tags">
                  <a-checkbox-group v-model:value="formData.usage_scenarios" class="custom-checkbox-group">
                    <a-checkbox value="游戏" class="preference-tag">🎮 游戏</a-checkbox>
                    <a-checkbox value="办公" class="preference-tag">💼 办公</a-checkbox>
                    <a-checkbox value="拍照" class="preference-tag">📷 拍照</a-checkbox>
                    <a-checkbox value="便携" class="preference-tag">🎒 便携</a-checkbox>
                  </a-checkbox-group>
                </div>
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item name="core_features">
                <template #label>
                  <span class="form-label">核心功能</span>
                </template>
                <div class="preference-tags">
                  <a-checkbox-group v-model:value="formData.core_features" class="custom-checkbox-group">
                    <a-checkbox value="防水" class="preference-tag">🌊 防水</a-checkbox>
                    <a-checkbox value="快充" class="preference-tag">⚡ 快充</a-checkbox>
                    <a-checkbox value="大内存" class="preference-tag">💾 大内存</a-checkbox>
                    <a-checkbox value="高刷" class="preference-tag">🖥️ 高刷屏</a-checkbox>
                  </a-checkbox-group>
                </div>
              </a-form-item>
            </a-col>
          </a-row>
        </div>

        <!-- 第三步:额外要求 -->
        <div class="form-section">
          <div class="section-header">
            <span class="section-icon">💬</span>
            <span class="section-title">个性化要求</span>
          </div>

          <a-form-item name="free_text_input">
            <a-textarea
              v-model:value="formData.free_text_input"
              placeholder="请输入您的个性化要求,例如:要正品、优先百亿补贴、拒绝二手等..."
              :rows="3"
              size="large"
              class="custom-textarea"
            />
          </a-form-item>
        </div>

        <!-- 提交按钮 -->
        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            :loading="loading"
            size="large"
            block
            class="submit-button"
          >
            <template v-if="!loading">
              <span class="button-icon">🚀</span>
              <span>生成专属导购方案</span>
            </template>
            <template v-else>
              <span>正在生成中...</span>
            </template>
          </a-button>
        </a-form-item>

        <!-- 加载进度条 -->
        <a-form-item v-if="loading">
          <div class="loading-container">
            <a-progress
              :percent="loadingProgress"
              status="active"
              :stroke-color="{
                '0%': '#667eea',
                '100%': '#764ba2',
              }"
              :stroke-width="10"
            />
            <p class="loading-status">
              {{ loadingStatus }}
            </p>
          </div>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { generateShoppingReport } from '@/services/api'
import type { ShoppingFormData, ShoppingReport } from '@/types'

const router = useRouter()
const loading = ref(false)
const loadingProgress = ref(0)
const loadingStatus = ref('')

// 电商表单数据（对齐后端模型）
const formData = reactive<ShoppingFormData>({
  product_category: '',
  budget_range: {
    min: 1000,
    max: 5000
  },
  usage_scenarios: [],
  brand_preference: [],
  core_features: [],
  free_text_input: ''
})

// 监听预算合法性
watch([() => formData.budget_range.min, () => formData.budget_range.max], ([min, max]) => {
  if (min > max && max !== 0) {
    message.warning('最低预算不能高于最高预算')
    formData.budget_range.min = max
  }
})

const handleSubmit = async () => {
  // 基础校验
  if (!formData.product_category.trim()) {
    message.error('请输入商品类别')
    return
  }
  if (formData.budget_range.min <= 0 || formData.budget_range.max <= 0) {
    message.error('请输入有效的预算金额')
    return
  }

  loading.value = true
  loadingProgress.value = 0
  loadingStatus.value = '正在初始化...'

  // 模拟进度更新
  const progressInterval = setInterval(() => {
    if (loadingProgress.value < 90) {
      loadingProgress.value += 10
      if (loadingProgress.value <= 30) {
        loadingStatus.value = '🔍 正在筛选商品...'
      } else if (loadingProgress.value <= 50) {
        loadingStatus.value = '💰 正在全网比价...'
      } else if (loadingProgress.value <= 70) {
        loadingStatus.value = '⭐ 正在口碑测评...'
      } else {
        loadingStatus.value = '📊 正在生成导购报告...'
      }
    }
  }, 500)

  try {
    // 调用后端接口
    const response = await generateShoppingReport(formData)
    console.log('✅ 接口返回数据：', response) // 调试日志

    // 强制完成进度
    clearInterval(progressInterval)
    loadingProgress.value = 100
    loadingStatus.value = '✅ 完成!'

    // 🔥 核心修复：严格校验并存储报告数据
    if (response && response.success === true && response.data) {
      // 永久存储报告（确保Result.vue一定能读到）
      sessionStorage.setItem('shoppingReport', JSON.stringify(response.data))
      message.success('导购报告生成成功!')

      // 延迟跳转，确保存储完成
      setTimeout(() => {
        router.push('/result')
      }, 600)
    } else {
      message.error('报告生成失败：数据格式异常')
      console.error('后端返回异常：', response)
    }

  } catch (error: any) {
    clearInterval(progressInterval)
    console.error('❌ 生成失败：', error)
    message.error(error.message || '网络异常，请重试')
  } finally {
    // 延迟关闭加载状态
    setTimeout(() => {
      loading.value = false
      loadingProgress.value = 0
      loadingStatus.value = ''
    }, 1000)
  }
}
</script>
<style scoped>
/* 所有样式完全保留，精美动效、布局不变！ */
.home-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #2196f3 0%, #009688 100%);
  padding: 60px 20px;
  position: relative;
  overflow: hidden;
}

.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: hidden;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 20s infinite ease-in-out;
}

.circle-1 {
  width: 300px;
  height: 300px;
  top: -100px;
  left: -100px;
  animation-delay: 0s;
}

.circle-2 {
  width: 200px;
  height: 200px;
  top: 50%;
  right: -50px;
  animation-delay: 5s;
}

.circle-3 {
  width: 150px;
  height: 150px;
  bottom: -50px;
  left: 30%;
  animation-delay: 10s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-30px) rotate(180deg);
  }
}

.page-header {
  text-align: center;
  margin-bottom: 50px;
  animation: fadeInDown 0.8s ease-out;
  position: relative;
  z-index: 1;
}

.icon-wrapper {
  margin-bottom: 20px;
}

.icon {
  font-size: 80px;
  display: inline-block;
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20px);
  }
}

.page-title {
  font-size: 56px;
  font-weight: 800;
  color: #ffffff;
  margin-bottom: 16px;
  text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.3);
  letter-spacing: 2px;
}

.page-subtitle {
  font-size: 20px;
  color: rgba(255, 255, 255, 0.95);
  margin: 0;
  font-weight: 300;
}

.form-card {
  max-width: 1400px;
  margin: 0 auto;
  border-radius: 24px;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.4);
  animation: fadeInUp 0.8s ease-out;
  position: relative;
  z-index: 1;
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.98) !important;
}

.form-section {
  margin-bottom: 32px;
  padding: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  border-radius: 16px;
  border: 1px solid #e8e8e8;
  transition: all 0.3s ease;
}

.form-section:hover {
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.15);
  transform: translateY(-2px);
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #667eea;
}

.section-icon {
  font-size: 24px;
  margin-right: 12px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.form-label {
  font-size: 15px;
  font-weight: 500;
  color: #555;
}

.custom-input :deep(.ant-input),
.custom-input :deep(.ant-picker) {
  border-radius: 12px;
  border: 2px solid #e8e8e8;
  transition: all 0.3s ease;
}

.custom-input :deep(.ant-input:hover),
.custom-input :deep(.ant-picker:hover) {
  border-color: #667eea;
}

.custom-input :deep(.ant-input:focus),
.custom-input :deep(.ant-picker-focused) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.custom-select :deep(.ant-select-selector) {
  border-radius: 12px !important;
  border: 2px solid #e8e8e8 !important;
  transition: all 0.3s ease;
}

.custom-select:hover :deep(.ant-select-selector) {
  border-color: #667eea !important;
}

.custom-select :deep(.ant-select-focused .ant-select-selector) {
  border-color: #667eea !important;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
}

.days-display-compact {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.days-display-compact .days-value {
  font-size: 20px;
  font-weight: 700;
  margin-right: 4px;
}

.days-display-compact .days-unit {
  font-size: 14px;
}

.preference-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.custom-checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  width: 100%;
}

.preference-tag :deep(.ant-checkbox-wrapper) {
  margin: 0 !important;
  padding: 8px 16px;
  border: 2px solid #e8e8e8;
  border-radius: 20px;
  transition: all 0.3s ease;
  background: white;
  font-size: 14px;
}

.preference-tag :deep(.ant-checkbox-wrapper:hover) {
  border-color: #667eea;
  background: #f5f7ff;
}

.preference-tag :deep(.ant-checkbox-wrapper-checked) {
  border-color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.custom-textarea :deep(.ant-input) {
  border-radius: 12px;
  border: 2px solid #e8e8e8;
  transition: all 0.3s ease;
}

.custom-textarea :deep(.ant-input:hover) {
  border-color: #667eea;
}

.custom-textarea :deep(.ant-input:focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.submit-button {
  height: 56px;
  border-radius: 28px;
  font-size: 18px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
}

.submit-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.5);
}

.submit-button:active {
  transform: translateY(0);
}

.button-icon {
  margin-right: 8px;
  font-size: 20px;
}

.loading-container {
  text-align: center;
  padding: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  border-radius: 16px;
  border: 2px dashed #667eea;
}

.loading-status {
  margin-top: 16px;
  color: #667eea;
  font-size: 18px;
  font-weight: 500;
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>