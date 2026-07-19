<template>
  <div class="result-container">
    <div class="page-header">
      <a-button class="back-button" size="large" @click="goBack">
        ← 返回首页
      </a-button>
      <a-space size="middle">
        <a-dropdown>
          <template #overlay>
            <a-menu>
              <a-menu-item key="image" @click="exportAsImage">📷 导出为图片</a-menu-item>
              <a-menu-item key="pdf" @click="exportAsPDF">📄 导出为PDF</a-menu-item>
            </a-menu>
          </template>
          <a-button type="default">📥 导出报告 <DownOutlined /></a-button>
        </a-dropdown>
      </a-space>
    </div>
    <div v-if="shoppingReport" class="content-wrapper">
      <div class="side-nav">
        <a-affix :offset-top="80">
          <a-menu mode="inline" :selected-keys="[activeSection]" @click="scrollToSection">
            <a-menu-item key="overview"><span>📋 导购概览</span></a-menu-item>
            <a-menu-item key="metrics"><span>⚡ 链路监控</span></a-menu-item>
            <a-menu-item key="products"><span>🛍️ 推荐商品</span></a-menu-item>
            <a-menu-item key="compare"><span>📊 参数对比</span></a-menu-item>
            <a-menu-item key="price"><span>💰 价格分析</span></a-menu-item>
            <a-menu-item key="suggest"><span>💡 购买建议</span></a-menu-item>
          </a-menu>
        </a-affix>
      </div>
      <div class="main-content">
        <a-card id="overview" title="📋 导购报告概览" :bordered="false" class="overview-card">
          <div class="overview-content">
            <div class="info-item"><span class="info-label">🏷️ 类别:</span> {{ shoppingReport.category }}</div>
            <div class="info-item"><span class="info-label">💰 预算:</span> {{ shoppingReport.budget_range }}</div>
            <div class="info-item"><span class="info-label">⏰ 时间:</span> {{ shoppingReport.search_timestamp }}</div>
            <div class="info-item"><span class="info-label">🎯 数量:</span> {{ shoppingReport.recommended_products.length }} 款</div>
          </div>
        </a-card>
        <a-card id="metrics" title="⚡ 实时链路监控 (Full-Link Monitoring)" :bordered="false" class="metrics-card">
          <a-row :gutter="16">
            <a-col :span="8">
              <a-statistic title="响应耗时 (Latency)" :value="shoppingReport.metrics?.latency_ms || 0" suffix="ms" :value-style="{ color: '#722ed1' }">
                <template #prefix><HistoryOutlined /></template>
              </a-statistic>
              <div class="metric-desc">多 Agent 协同总耗时</div>
            </a-col>
            <a-col :span="8">
              <a-statistic title="调用成本 (LLM Cost)" :value="shoppingReport.metrics?.llm_cost_cny || 0" :precision="4" prefix="¥" :value-style="{ color: '#fa8c16' }">
                <template #prefix><AccountBookOutlined /></template>
              </a-statistic>
              <div class="metric-desc">Token 消耗实时换算</div>
            </a-col>
            <a-col :span="8">
              <a-statistic title="系统累计请求" :value="shoppingReport.metrics?.total_requests || 0" :value-style="{ color: '#13c2c2' }">
                <template #prefix><LineChartOutlined /></template>
              </a-statistic>
              <div class="metric-desc">后端并发压力监控</div>
            </a-col>
          </a-row>
        </a-card>
        <a-card id="products" title="🛍️ 精选推荐商品" :bordered="false" class="products-card">
          <a-list :data-source="shoppingReport.recommended_products" :grid="{ gutter: 16, column: 2 }">
            <template #renderItem="{ item, index }">
              <a-list-item>
                <a-card :title="`${index + 1}. ${item.name}`" size="small" class="product-card">
                  <div class="product-image-wrapper">
                    <img :src="getProductImage(item, index)" class="product-image" @error="handleImageError" />
                    <div class="price-tag">¥{{ item.price_info.current_price }}</div>
                  </div>
                  <p><strong>🏷️ 品牌:</strong> {{ item.brand }}</p>
                  <p><strong>⭐ 评分:</strong> {{ item.sentiment.expert_score }} / 10</p>
                  <p><strong>💡 理由:</strong> {{ item.recommend_reason }}</p>
                  <a-button type="primary" block @click="handleBuy(item.buy_link)">🔗 前往购买</a-button>
                </a-card>
              </a-list-item>
            </template>
          </a-list>
        </a-card>

        <!-- 全参数对比（已修复匹配问题） -->
        <a-card id="compare" title="📊 全参数对比" :bordered="false" class="compare-card">
          <a-table
            :columns="compareColumns"
            :data-source="shoppingReport?.decision_matrix || []"
            row-key="项目"
            bordered
            size="middle"
            :pagination="false"
          />
        </a-card>

        <a-card id="price" title="💰 价格走势分析" :bordered="false" class="price-card">
          <div class="price-content">
            <a-statistic title="均价" :value="avgPrice" prefix="¥" :value-style="{color: '#1890ff'}" />
            <a-statistic title="最低价" :value="minPrice" prefix="¥" :value-style="{color: '#52c41a'}" />
            <a-statistic title="最高价" :value="maxPrice" prefix="¥" :value-style="{color: '#ff4d4f'}" />
          </div>
        </a-card>
        <a-card id="suggest" title="💡 专家购买建议" :bordered="false" class="suggest-card">
          <div class="suggest-content">
            <div class="suggest-item">✅ <strong>首选推荐：</strong>{{ shoppingReport.best_overall }}</div>
            <div class="suggest-item">💰 <strong>性价比首选：</strong>{{ shoppingReport.best_budget }}</div>
            <div class="suggest-item">⚠️ <strong>避雷提示：</strong>{{ shoppingReport.expert_tips.join('；') }}</div>
            <div class="suggest-item">🎯 <strong>总结：</strong>{{ shoppingReport.overall_summary }}</div>
          </div>
        </a-card>
      </div>
    </div>
    <a-empty v-else description="暂无导购报告">
      <a-button type="primary" @click="goBack">返回首页</a-button>
    </a-empty>
    <a-back-top />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  DownOutlined, HistoryOutlined, AccountBookOutlined, LineChartOutlined
} from '@ant-design/icons-vue'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'
const router = useRouter()
const shoppingReport = ref<any>(null)
const activeSection = ref('overview')
// 1. 挂载时读取数据
onMounted(() => {
  const data = sessionStorage.getItem('shoppingReport')
  if (data) {
    shoppingReport.value = JSON.parse(data)
    console.log("📊 链路监控数据：", shoppingReport.value.metrics)
  }
})
// 2. 价格统计逻辑（增加保护，防止 NaN）
const avgPrice = computed(() => {
  const products = shoppingReport.value?.recommended_products || []
  if (products.length === 0) return 0
  const prices = products.map((p: any) => p.price_info.current_price)
  return Math.round(prices.reduce((a: number, b: number) => a + b, 0) / prices.length)
})
const minPrice = computed(() => {
  const prices = shoppingReport.value?.recommended_products.map((p: any) => p.price_info.current_price) || []
  return prices.length > 0 ? Math.min(...prices) : 0
})
const maxPrice = computed(() => {
  const prices = shoppingReport.value?.recommended_products.map((p: any) => p.price_info.current_price) || []
  return prices.length > 0 ? Math.max(...prices) : 0
})

// 👇 唯一修改处：修复商品名称不匹配问题（模糊匹配兼容逻辑）
const compareColumns = computed(() => {
  if (!shoppingReport.value?.recommended_products?.length || !shoppingReport.value?.decision_matrix?.length) return []

  // 1. 从后端返回的decision_matrix第一行，提取真实的商品列名
  const backendProductNames = Object.keys(shoppingReport.value.decision_matrix[0]).filter(key => key !== '项目')

  // 2. 为每个前端推荐商品，找到最匹配的后端列名（模糊匹配前10个核心字符）
  const productColumns = shoppingReport.value.recommended_products.map((p: any) => {
    // 双向模糊匹配：忽略冒号、引号、后缀等细微差别
    const matchedName = backendProductNames.find(backendName =>
      backendName.includes(p.name.substring(0, 10)) ||
      p.name.includes(backendName.substring(0, 10))
    ) || p.name // 兜底：匹配失败用原名称

    return {
      title: p.name,
      dataIndex: matchedName, // 用匹配到的后端真实列名
      key: p.product_id || p.name,
      align: 'center'
    }
  })

  return [
    { title: '对比项', dataIndex: '项目', key: 'item', width: 120, fixed: 'left' },
    ...productColumns
  ]
})

// 4. 功能函数
const goBack = () => router.push('/')
const handleBuy = (url: string) => url ? window.open(url, '_blank') : message.error('购买链接不存在')
const scrollToSection = ({ key }: { key: string }) => {
  activeSection.value = key
  document.getElementById(key)?.scrollIntoView({ behavior: 'smooth' })
}
// 图片处理逻辑
const getProductImage = (item: any, index: number) => {
  if (item.main_image && item.main_image.startsWith('http')) return item.main_image
  return `data:image/svg+xml;base64,${btoa('<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"><rect width="100%" height="100%" fill="#eee"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-size="20">No Image</text></svg>')}`
}
const handleImageError = (e: any) => e.target.src = 'https://via.placeholder.com/400x300?text=Image+Error'
// 导出逻辑
const exportAsImage = async () => {
  const el = document.querySelector('.main-content') as HTMLElement
  const canvas = await html2canvas(el, { useCORS: true })
  const link = document.createElement('a')
  link.href = canvas.toDataURL()
  link.download = '导购报告.png'
  link.click()
}
const exportAsPDF = async () => {
  const el = document.querySelector('.main-content') as HTMLElement
  const canvas = await html2canvas(el)
  const pdf = new jsPDF('p', 'mm', 'a4')
  pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, 0, 211, (canvas.height * 211) / canvas.width)
  pdf.save('导购报告.pdf')
}
</script>
<style scoped>
.result-container { min-height: 100vh; background: #f0f2f5; padding: 30px; }
.page-header { max-width: 1200px; margin: 0 auto 20px; display: flex; justify-content: space-between; }
.content-wrapper { max-width: 1200px; margin: 0 auto; display: flex; gap: 20px; }
.side-nav { width: 200px; }
.main-content { flex: 1; }
/* 链路监控卡片样式 */
.metrics-card { margin-bottom: 20px; border-left: 5px solid #722ed1; }
.metric-desc { font-size: 12px; color: #999; margin-top: 5px; }
.overview-content { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.product-image { max-width: 100%; max-height: 100%; object-fit: contain; }
.product-image-wrapper {
  position: relative;
  height: 180px;
  background: #f7f9fa;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 1px solid #f0f0f0;
  margin-bottom: 12px;
}
.price-tag { position: absolute; top: 10px; right: 10px; background: #ff4d4f; color: white; padding: 2px 8px; border-radius: 4px; }
.price-content { display: flex; justify: space-around; padding: 20px 0; }
.suggest-item { margin-bottom: 10px; font-size: 15px; }
:deep(.ant-card-head) { background: #fafafa; font-weight: bold; }
</style>