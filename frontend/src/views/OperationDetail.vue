<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span><b>网格操作明细</b></span>
          <el-button type="primary" size="small" @click="generateLayers" :loading="generating">
            <el-icon><Refresh /></el-icon> 重新生成
          </el-button>
        </div>
      </template>
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">
        <el-select v-model="selectedInstance" placeholder="选择策略" style="width:300px" @change="loadLayers">
          <el-option v-for="inst in instances" :key="inst.id" :label="(inst.name || '策略#'+inst.id)" :value="inst.id" />
        </el-select>
        <span v-if="currentStockLabel" style="font-size:13px;color:#606266">
          标的：<b>{{ currentStockLabel }}</b>
        </span>
        <el-tag v-else-if="selectedInstance" type="info" size="small">未绑定标的</el-tag>
      </div>
      <el-table :data="layers" stripe v-loading="loading" style="width:100%">
        <el-table-column prop="layer_index" label="层" width="60" />
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.layer_type === 'position' ? 'warning' : 'primary'" size="small">
              {{ row.layer_type === 'position' ? '底仓' : '网格' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="方向" width="80">
          <template #default="{ row }">
            <el-tag :type="row.direction === 'buy' ? 'danger' : 'success'" size="small">
              {{ row.direction === 'buy' ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="trigger_price" label="触发价格" width="120" />
        <el-table-column prop="quantity" label="数量" width="100" />
        <el-table-column prop="amount" label="金额" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'triggered' ? 'success' : row.status === 'invalid' ? 'danger' : row.status === 'holding' ? 'warning' : 'info'" size="small">
              {{ row.status === 'holding' ? '持仓' : row.status === 'pending' ? '等待触发' : row.status === 'triggered' ? '已触发' : '已失效' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!selectedInstance" description="请先选择一个策略" style="padding:40px 0" />
    </el-card>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getStrategyInstances, getGridLayers, generateGridLayers, getStocks } from '../api/index.js'
const instances = ref([]); const stocks = ref([]); const layers = ref([])
const selectedInstance = ref(null); const loading = ref(false); const generating = ref(false)
const currentStockLabel = computed(() => {
  if (!selectedInstance.value) return ''
  const inst = instances.value.find(i => i.id === selectedInstance.value)
  if (!inst?.stock_id) return ''
  const stock = stocks.value.find(s => s.id === inst.stock_id)
  return stock ? `${stock.code} ${stock.name}` : ''
})
async function loadInstances() {
  try {
    const [a, b] = await Promise.all([getStrategyInstances(), getStocks()])
    instances.value = a.data; stocks.value = b.data
  } catch {}
}
async function loadLayers() {
  if (!selectedInstance.value) return; loading.value = true
  try { const r = await getGridLayers(selectedInstance.value); layers.value = r.data }
  catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}
async function generateLayers() {
  if (!selectedInstance.value) { ElMessage.warning('请先选择策略'); return }
  generating.value = true
  try { await generateGridLayers(selectedInstance.value); ElMessage.success('已生成'); await loadLayers() }
  catch { ElMessage.error('生成失败') }
  finally { generating.value = false }
}
onMounted(loadInstances)
</script>
