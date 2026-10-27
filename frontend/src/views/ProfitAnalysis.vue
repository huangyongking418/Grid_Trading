<template>
  <div>
    <el-row :gutter="16">
      <el-col :span="10">
        <el-card shadow="never" class="section-card">
          <template #header><span><b>策略收益概览</b></span></template>
          <el-select v-model="selectedInstance" placeholder="选择策略" style="width:100%" @change="loadProfit">
            <el-option v-for="inst in instances" :key="inst.id" :label="(inst.name || '策略#'+inst.id)" :value="inst.id" />
          </el-select>
          <div v-if="theoretical" style="margin-top:16px">
            <el-descriptions :column="2" size="small" border>
              <el-descriptions-item label="理论投资总额">{{ theoretical.total_investment }}</el-descriptions-item>
              <el-descriptions-item label="理论收益率">
                <el-tag :type="theoretical.yield_rate >= 0 ? 'success' : 'danger'">{{ theoretical.yield_rate }}%</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="实际买入">{{ actual.total_buy }}</el-descriptions-item>
              <el-descriptions-item label="实际收益率">
                <el-tag :type="actual.yield_rate >= 0 ? 'success' : 'danger'">{{ actual.yield_rate }}%</el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
        <el-card shadow="never">
          <template #header><span><b>手工录入操作</b></span></template>
          <el-form :model="opForm" label-width="70px" size="small">
            <el-row :gutter="8">
              <el-col :span="12"><el-form-item label="价格"><el-input-number v-model="opForm.trigger_price" :min="0.01" :step="0.1" style="width:100%" /></el-form-item></el-col>
              <el-col :span="12"><el-form-item label="数量"><el-input-number v-model="opForm.quantity" :min="1" style="width:100%" /></el-form-item></el-col>
            </el-row>
            <el-row :gutter="8">
              <el-col :span="12"><el-form-item label="方向"><el-select v-model="opForm.direction" style="width:100%"><el-option label="买入" value="buy" /><el-option label="卖出" value="sell" /></el-select></el-form-item></el-col>
              <el-col :span="12"><el-form-item label="手续费"><el-input-number v-model="opForm.fee" :min="0" :step="1" style="width:100%" /></el-form-item></el-col>
            </el-row>
            <el-form-item><el-button type="primary" @click="submitOperation" :loading="submitting" style="width:100%">录入操作</el-button></el-form-item>
          </el-form>
          <el-table :data="operations" stripe size="small" max-height="250" style="width:100%">
            <el-table-column prop="trigger_price" label="价格" width="80" />
            <el-table-column prop="quantity" label="数量" width="60" />
            <el-table-column label="方向" width="60"><template #default="{ row }"><el-tag :type="row.direction === 'buy' ? 'danger' : 'success'" size="small">{{ row.direction === 'buy' ? '买' : '卖' }}</el-tag></template></el-table-column>
            <el-table-column prop="fee" label="手续费" width="70" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="14">
        <el-card shadow="never">
          <template #header><span><b>收益率曲线</b></span></template>
          <div ref="chartRef" style="width:100%;height:450px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { getStrategyInstances, getProfitTheoretical, getProfitActual, getOperations, createOperation } from '../api/index.js'
const chartRef = ref(null); let chartInstance = null
const instances = ref([]); const selectedInstance = ref(null)
const theoretical = ref(null)
const actual = ref({ total_buy: 0, total_sell: 0, yield_rate: 0 })
const operations = ref([]); const submitting = ref(false)
const opForm = ref({ instance_id: null, trigger_price: 10.0, quantity: 100, direction: 'buy', fee: 0 })
async function fetchInstances() { try { const r = await getStrategyInstances(); instances.value = r.data } catch {} }
async function loadProfit() {
  if (!selectedInstance.value) return; opForm.value.instance_id = selectedInstance.value
  try {
    const [t, a, o] = await Promise.all([getProfitTheoretical(selectedInstance.value), getProfitActual(), getOperations({ log_type: 'actual' })])
    theoretical.value = t.data; actual.value = a.data; operations.value = o.data; updateChart()
  } catch {}
}
function updateChart() {
  if (!chartInstance) return
  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['理论收益率', '实际收益率'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: ['初始', '当前'] },
    yAxis: { type: 'value', axisLabel: { formatter: '{value}%' } },
    series: [
      { name: '理论收益率', type: 'line', smooth: true, data: [0, theoretical.value?.yield_rate || 0], lineStyle: { width: 3 }, areaStyle: { opacity: 0.1 } },
      { name: '实际收益率', type: 'line', smooth: true, data: [0, actual.value?.yield_rate || 0], lineStyle: { width: 3, type: 'dashed' }, areaStyle: { opacity: 0.1 } },
    ],
  })
}
async function submitOperation() {
  if (!selectedInstance.value) { ElMessage.warning('请先选择策略'); return }
  submitting.value = true
  try { await createOperation(opForm.value); ElMessage.success('已录入'); await loadProfit() }
  catch { ElMessage.error('录入失败') }
  finally { submitting.value = false }
}
watch(selectedInstance, loadProfit)
onMounted(async () => { await fetchInstances(); await nextTick(); if (chartRef.value) { chartInstance = echarts.init(chartRef.value); updateChart() } })
onUnmounted(() => chartInstance?.dispose())
</script>
