<template>
  <div>
    <el-card shadow="never" class="section-card">
      <template #header>
        <span><b>策略模板</b> — 内置行情网格策略，开箱即用</span>
      </template>
      <el-row :gutter="16">
        <el-col v-for="tpl in templates" :key="tpl.id" :span="8">
          <el-card shadow="hover" class="template-card" :body-style="{ padding: '16px' }">
            <h4 style="margin:0 0 8px">{{ tpl.name }}</h4>
            <p style="font-size:13px;color:#666;margin:0 0 4px 0;min-height:52px">{{ tpl.description }}</p>
            <el-tag size="small" style="margin-top:4px">{{ DIRECTION_MAP[tpl.direction_type] || tpl.direction_type }}</el-tag>
            <div v-if="tpl.default_params" style="margin-top:10px;font-size:12px;color:#909399;border-top:1px solid #eee;padding-top:8px">
              <div>下跌间距 <b>{{ tpl.default_params.grid_spacing }}%</b>｜上涨间距 <b>{{ templateSellSpacing(tpl) }}%</b></div>
              <div>不对称比 <b>{{ tpl.default_params.asymmetry_ratio }}</b>｜层数 <b>{{ tpl.default_params.grid_layers }}</b></div>
            </div>
            <el-button type="primary" size="small" style="margin-top:10px;width:100%" @click="useTemplate(tpl)">使用此模板</el-button>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
    <el-card shadow="never" class="section-card">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="策略列表" name="strategies">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <span style="font-size:13px;color:#909399">每个策略可绑定一个标的，创建 / 编辑时在下方表单中选择</span>
            <el-button type="primary" size="small" @click="openCreateDialog">
              <el-icon><Plus /></el-icon> 新建策略
            </el-button>
          </div>
          <el-table :data="pagedInstances" stripe v-loading="loading" style="width:100%">
            <el-table-column prop="id" label="ID" width="90">
              <template #header>
                <div class="header-filter">
                  <span>ID</span>
                  <el-input v-model="strategyFilters.id" placeholder="搜索" size="small" clearable />
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="name" label="策略名称" min-width="140">
              <template #header>
                <div class="header-filter">
                  <span>策略名称</span>
                  <el-input v-model="strategyFilters.name" placeholder="搜索" size="small" clearable />
                </div>
              </template>
            </el-table-column>
            <el-table-column label="模板" width="130">
              <template #header>
                <div class="header-filter">
                  <span>模板</span>
                  <el-input v-model="strategyFilters.template" placeholder="搜索" size="small" clearable />
                </div>
              </template>
              <template #default="{ row }">{{ row.template?.name || '-' }}</template>
            </el-table-column>
            <el-table-column label="绑定标的" min-width="150">
              <template #header>
                <div class="header-filter">
                  <span>绑定标的</span>
                  <el-input v-model="strategyFilters.stock" placeholder="搜索" size="small" clearable />
                </div>
              </template>
              <template #default="{ row }">
                <span v-if="row.stock_id">{{ getStockLabel(row.stock_id) }}</span>
                <el-tag v-else type="info" size="small">未绑定</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="base_price" label="基准价" width="100">
              <template #header>
                <div class="header-filter">
                  <span>基准价</span>
                  <el-input v-model="strategyFilters.base_price" placeholder="搜索" size="small" clearable />
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="grid_spacing" label="间距%" width="90">
              <template #header>
                <div class="header-filter">
                  <span>间距%</span>
                  <el-input v-model="strategyFilters.grid_spacing" placeholder="搜索" size="small" clearable />
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="grid_layers" label="层数" width="80">
              <template #header>
                <div class="header-filter">
                  <span>层数</span>
                  <el-input v-model="strategyFilters.grid_layers" placeholder="搜索" size="small" clearable />
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="asymmetry_ratio" label="不对称比" width="90">
              <template #header>
                <div class="header-filter">
                  <span>不对称比</span>
                  <el-input v-model="strategyFilters.asymmetry_ratio" placeholder="搜索" size="small" clearable />
                </div>
              </template>
            </el-table-column>
            <el-table-column label="资金（网格/底仓）" width="180">
              <template #header>
                <div class="header-filter">
                  <span>资金（网格/底仓）</span>
                  <el-input v-model="strategyFilters.funds" placeholder="搜索" size="small" clearable />
                </div>
              </template>
              <template #default="{ row }">
                <div>{{ row.total_funds }}</div>
                <div style="font-size:12px;color:#909399">网格 {{ row.grid_funds ?? row.total_funds }} / 底仓 {{ row.position_funds ?? 0 }}</div>
              </template>
            </el-table-column>
            <el-table-column label="切分方式" width="110">
              <template #header>
                <div class="header-filter">
                  <span>切分方式</span>
                  <el-input v-model="strategyFilters.split_mode" placeholder="搜索" size="small" clearable />
                </div>
              </template>
              <template #default="{ row }">
                <el-tag :type="row.split_mode === 'shares' ? 'warning' : 'info'" size="small">
                  {{ row.split_mode === 'shares' ? '份额切分' : '金额切分' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90">
              <template #header>
                <div class="header-filter">
                  <span>状态</span>
                  <el-input v-model="strategyFilters.status" placeholder="搜索" size="small" clearable />
                </div>
              </template>
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                  {{ row.status === 'active' ? '启用' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
                <el-button link type="danger" size="small" @click="confirmDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="table-footer">
            <el-pagination
              v-model:current-page="strategyPage"
              v-model:page-size="strategyPageSize"
              :total="filteredInstances.length"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              background
            />
          </div>
        </el-tab-pane>
        <el-tab-pane label="标的库" name="stocks">
          <StockLibrary ref="stockLibraryRef" />
        </el-tab-pane>
      </el-tabs>
    </el-card>
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑策略' : '新建策略'" width="560px">
      <el-form :model="form" label-width="100px" size="small">
        <el-form-item label="策略名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="关联模板">
          <el-select v-model="form.template_id" clearable style="width:100%" @change="onTemplateChange">
            <el-option v-for="t in templates" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="绑定标的">
          <el-select
            v-model="form.stock_id"
            filterable
            remote
            :remote-method="remoteSearchStock"
            :loading="stockSearching"
            clearable
            placeholder="输入代码或名称搜索 A股 / ETF（也可下方手工录入）"
            style="width:100%"
            @change="onStockChange"
          >
            <el-option
              v-for="opt in stockOptions"
              :key="opt.code"
              :label="stockOptionLabel(opt)"
              :value="opt.stock_id || opt.code"
            />
            <template #empty>
              <div style="padding:8px;font-size:12px;color:#909399;text-align:left">
                <div v-if="stockSearching">搜索中…</div>
                <div v-else-if="stockKeyword">未找到匹配，可手工录入下方代码和名称</div>
                <div v-else>输入代码或名称搜索，或手工录入</div>
              </div>
            </template>
          </el-select>
          <div style="display:flex;gap:8px;margin-top:8px;align-items:center">
            <el-input v-model="manualStockCode" placeholder="代码，如 600519 / 510300" style="width:130px" />
            <el-input v-model="manualStockName" placeholder="名称（手工录入）" style="flex:1" />
            <el-button size="small" @click="manualAddStock" :loading="stockSaving">添加并绑定</el-button>
          </div>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item>
              <template #label>
                基准价
                <el-tooltip content="网格中心参考价格，买卖各层围绕它上下分布，建议填当前市价" placement="top">
                  <el-icon style="margin-left:2px;color:#909399;cursor:help"><QuestionFilled /></el-icon>
                </el-tooltip>
              </template>
              <el-input-number v-model="form.base_price" :min="0.01" :step="0.1" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item>
              <template #label>
                间距(%)
                <el-tooltip content="下跌格距：价格每下跌该百分比，触发买入一档（用于计算各买入层价格）" placement="top">
                  <el-icon style="margin-left:2px;color:#909399;cursor:help"><QuestionFilled /></el-icon>
                </el-tooltip>
              </template>
              <el-input-number v-model="form.grid_spacing" :min="0.01" :step="0.1" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item>
              <template #label>
                层数
                <el-tooltip content="网格买卖单侧层数（每层含一买一卖），层数越多网格越密、资金占用越多" placement="top">
                  <el-icon style="margin-left:2px;color:#909399;cursor:help"><QuestionFilled /></el-icon>
                </el-tooltip>
              </template>
              <el-input-number v-model="form.grid_layers" :min="1" :max="50" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item>
              <template #label>
                不对称比
                <el-tooltip content="= 上涨格距 ÷ 下跌格距。>1 涨疏跌密（震荡向上），=1 对称，<1 涨密跌疏（震荡向下）" placement="top">
                  <el-icon style="margin-left:2px;color:#909399;cursor:help"><QuestionFilled /></el-icon>
                </el-tooltip>
              </template>
              <el-input-number v-model="form.asymmetry_ratio" :min="0.1" :step="0.1" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="切分方式">
          <el-radio-group v-model="form.split_mode">
            <el-radio-button value="amount">基于金额</el-radio-button>
            <el-radio-button value="shares">基于份额</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <template v-if="form.split_mode === 'amount'">
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="底仓资金">
                <el-input v-model="form.position_funds" placeholder="请输入底仓资金">
                  <template #append>元</template>
                </el-input>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="网格资金">
                <el-input v-model="form.grid_funds" placeholder="请输入网格资金">
                  <template #append>元</template>
                </el-input>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="总资金">
                <el-input :model-value="autoAmountTotalFunds" readonly>
                  <template #append>元</template>
                </el-input>
              </el-form-item>
            </el-col>
          </el-row>
          <div style="font-size:12px;color:#909399;margin:-4px 0 12px 100px">金额模式：总资金 = 网格资金 + 底仓资金（自动计算，底仓不参与网格买卖）</div>
        </template>
        <template v-else>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="底仓资金">
                <el-input v-model="form.position_funds" placeholder="请输入底仓资金">
                  <template #append>元</template>
                </el-input>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="网格资金">
                <el-input :model-value="autoGridFunds" readonly>
                  <template #append>元</template>
                </el-input>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="总资金">
                <el-input :model-value="autoTotalFunds" readonly>
                  <template #append>元</template>
                </el-input>
              </el-form-item>
            </el-col>
          </el-row>
          <div style="font-size:12px;color:#909399;margin:-4px 0 12px 100px">份额模式：网格资金按各层份额自动计算，总资金 = 网格资金 + 底仓资金</div>
        </template>
        <el-form-item v-if="form.split_mode === 'amount'" label="资金分配">
          <el-select v-model="form.fund_allocation" style="width:100%">
            <el-option label="等额均分" value="equal" />
            <el-option label="金字塔分配" value="pyramid" />
          </el-select>
        </el-form-item>
        <el-row v-if="form.split_mode === 'shares'" :gutter="12">
          <el-col :span="12">
            <el-form-item label="买入份额">
              <el-input-number v-model="form.layer_shares.buy" :min="100" :step="100" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="卖出份额">
              <el-input-number v-model="form.layer_shares.sell" :min="100" :step="100" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="止损策略">
          <el-select v-model="form.stop_loss_strategy" style="width:100%">
            <el-option label="不启用" value="none" />
            <el-option label="暂停触发层" value="stop_layer" />
          </el-select>
        </el-form-item>
        <el-form-item label="基准重置(天)">
          <el-input-number v-model="form.reset_cycle_days" :min="0" :max="365" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button @click="previewStrategy" :loading="previewing">策略预览</el-button>
        <el-button type="primary" @click="saveStrategy" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
    <el-dialog v-model="previewDialog" title="策略预览 - 操作明细" width="720px">
      <el-table :data="previewLayers" stripe size="small" style="width:100%">
        <el-table-column prop="layer_index" label="层" width="60" />
        <el-table-column label="类型" width="70">
          <template #default="{ row }">
            <el-tag :type="row.layer_type === 'position' ? 'warning' : 'primary'" size="small">{{ row.layer_type === 'position' ? '底仓' : '网格' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="方向" width="70">
          <template #default="{ row }">
            <el-tag :type="row.direction === 'buy' ? 'danger' : 'success'" size="small">{{ row.direction === 'buy' ? '买入' : '卖出' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="trigger_price" label="触发价" width="100" />
        <el-table-column prop="quantity" label="数量" width="90" />
        <el-table-column prop="amount" label="金额" width="110" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'holding' ? 'warning' : 'info'" size="small">{{ row.status === 'holding' ? '持仓' : '等待触发' }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="previewDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getStrategyTemplates, getStrategyInstances, createStrategyInstance, updateStrategyInstance, deleteStrategyInstance, getStocks, createStock, searchStocks, previewGridLayers } from '../api/index.js'
import StockLibrary from '../components/StockLibrary.vue'

const DIRECTION_MAP = { oscillation_up: '震荡向上', oscillation: '震荡', oscillation_down: '震荡向下' }
const activeTab = ref('strategies')
const stockLibraryRef = ref(null)
const templates = ref([])
const instances = ref([])
const stocks = ref([])
const loading = ref(false)
const strategyFilters = ref({
  id: '',
  name: '',
  template: '',
  stock: '',
  base_price: '',
  grid_spacing: '',
  grid_layers: '',
  asymmetry_ratio: '',
  funds: '',
  split_mode: '',
  status: '',
})
const strategyPage = ref(1)
const strategyPageSize = ref(10)
const saving = ref(false)
const previewing = ref(false)
const previewDialog = ref(false)
const previewLayers = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const round2 = (n) => Math.round((Number(n) || 0) * 100) / 100
const filteredInstances = computed(() => {
  const f = strategyFilters.value
  const hasFilter = Object.values(f).some(v => (v || '').trim() !== '')
  if (!hasFilter) return instances.value
  const match = (field, value) => !(field || '').trim() || String(value ?? '').includes((field || '').trim())
  return instances.value.filter(row => {
    const fundsText = `${row.total_funds ?? ''} ${row.grid_funds ?? row.total_funds ?? ''} ${row.position_funds ?? ''}`
    return match(f.id, row.id)
      && match(f.name, row.name)
      && match(f.template, row.template?.name || '-')
      && match(f.stock, getStockLabel(row.stock_id) || '未绑定')
      && match(f.base_price, row.base_price)
      && match(f.grid_spacing, row.grid_spacing)
      && match(f.grid_layers, row.grid_layers)
      && match(f.asymmetry_ratio, row.asymmetry_ratio)
      && match(f.funds, fundsText)
      && match(f.split_mode, row.split_mode === 'shares' ? '份额切分' : '金额切分')
      && match(f.status, row.status === 'active' ? '启用' : '停用')
  })
})
const pagedInstances = computed(() => {
  const start = (strategyPage.value - 1) * strategyPageSize.value
  return filteredInstances.value.slice(start, start + strategyPageSize.value)
})
watch([filteredInstances, strategyPageSize], () => {
  const maxPage = Math.max(1, Math.ceil(filteredInstances.value.length / strategyPageSize.value))
  if (strategyPage.value > maxPage) strategyPage.value = maxPage
})
watch(strategyPageSize, () => { strategyPage.value = 1 })
// 份额切分模式：按每层买入/卖出份额与网格参数自动计算网格资金、总资金
const autoGridFunds = computed(() => {
  if (form.value.split_mode !== 'shares') return form.value.grid_funds ?? 0
  const base = Number(form.value.base_price) || 0
  const spacing = Number(form.value.grid_spacing) || 0
  const layers = Number(form.value.grid_layers) || 0
  const ratio = Number(form.value.asymmetry_ratio) || 1
  const buyShare = Number(form.value.layer_shares?.buy) || 0
  const sellShare = Number(form.value.layer_shares?.sell) || 0
  let total = 0
  for (let i = 1; i <= layers; i++) {
    const buyPrice = base * (1 - i * spacing / 100)
    const sellPrice = base * (1 + i * spacing * ratio / 100)
    if (buyPrice > 0) total += buyShare * buyPrice
    if (sellPrice > 0) total += sellShare * sellPrice
  }
  return round2(total)
})
const autoTotalFunds = computed(() => round2(autoGridFunds.value + (Number(form.value.position_funds) || 0)))
// 金额切分模式：总资金 = 网格资金 + 底仓资金（自动计算，只读展示）
const autoAmountTotalFunds = computed(() => round2((Number(form.value.grid_funds) || 0) + (Number(form.value.position_funds) || 0)))
const defaultForm = { template_id: null, name: '', stock_id: null, grid_spacing: 1.0, grid_layers: 5, asymmetry_ratio: 1.0, base_price: null, stop_loss_strategy: 'none', fund_allocation: 'equal', total_funds: 100000, grid_funds: 100000, position_funds: 0, split_mode: 'amount', layer_shares: { buy: 100, sell: 100 }, reset_cycle_days: 0 }
const form = ref({ ...defaultForm })

const stockOptions = ref([])
const stockSearching = ref(false)
const stockSaving = ref(false)
const stockKeyword = ref('')
const manualStockCode = ref('')
const manualStockName = ref('')
let stockSearchTimer = null

async function fetchData() {
  loading.value = true
  try {
    const [t, i, s] = await Promise.all([getStrategyTemplates(), getStrategyInstances(), getStocks()])
    templates.value = t.data
    instances.value = i.data
    stocks.value = s.data
    stockOptions.value = localStockOptions()
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}
function getStockLabel(stockId) {
  const s = stocks.value.find(x => x.id === stockId)
  return s ? `${s.code} ${s.name}` : ''
}
function localStockOptions() {
  return stocks.value.map(s => ({
    code: s.code,
    name: s.name,
    type: s.type,
    stock_id: s.id,
    strategy_instance_id: s.strategy_instance_id,
    is_local: true,
  }))
}
function stockOptionLabel(opt) {
  const base = `${opt.code} ${opt.name}`
  if (opt.stock_id) {
    const local = stocks.value.find(s => s.id === opt.stock_id)
    if (local) {
      if (local.strategy_instance_id === editingId.value) return `${base}（当前绑定）`
      if (local.strategy_instance_id) return `${base}（已绑定策略#${local.strategy_instance_id}）`
    }
  }
  if (!opt.stock_id && !opt.is_local) return `${base}（未收录，选中后自动保存）`
  return base
}
async function onStockChange(val) {
  if (!val) {
    form.value.stock_id = null
    return
  }
  if (typeof val === 'number') {
    const target = stocks.value.find(s => s.id === val)
    if (!target) return
    if (target.strategy_instance_id && target.strategy_instance_id !== editingId.value) {
      try {
        await ElMessageBox.confirm(
          `该标的已绑定策略#${target.strategy_instance_id}，切换后将自动解除原绑定，是否继续？`,
          '提示'
        )
      } catch {
        form.value.stock_id = isEdit.value ? instances.value.find(i => i.id === editingId.value)?.stock_id || null : null
      }
    }
    return
  }
  // 远程搜索到但本地未收录：先自动入库再绑定
  const opt = stockOptions.value.find(o => o.code === val)
  if (!opt) return
  stockSaving.value = true
  try {
    let res
    try {
      res = await createStock({ code: opt.code, name: opt.name, type: opt.type })
    } catch (e) {
      if (e.response?.status === 400) {
        res = { data: stocks.value.find(s => s.code === opt.code) }
        if (!res.data) {
          const list = await getStocks()
          res = { data: list.data.find(s => s.code === opt.code) }
          stocks.value = list.data
        }
      } else {
        throw e
      }
    }
    if (!res.data) throw new Error('标的创建失败')
    const newStock = res.data
    if (!stocks.value.some(s => s.id === newStock.id)) stocks.value.push(newStock)
    opt.stock_id = newStock.id
    form.value.stock_id = newStock.id
    ElMessage.success(`已自动收录 ${opt.code} ${opt.name}`)
  } catch {
    ElMessage.error('标的保存失败，请改用手工录入')
    form.value.stock_id = null
  } finally {
    stockSaving.value = false
  }
}
function remoteSearchStock(keyword) {
  const kw = (keyword || '').trim()
  stockKeyword.value = keyword || ''
  if (!kw) {
    stockOptions.value = localStockOptions()
    return
  }
  clearTimeout(stockSearchTimer)
  stockSearchTimer = setTimeout(() => doSearchStock(kw), 300)
}
async function doSearchStock(kw) {
  stockSearching.value = true
  try {
    const res = await searchStocks(kw)
    const remote = res.data
    const codes = new Set(remote.map(r => r.code))
    const extras = localStockOptions().filter(
      s => !codes.has(s.code) && (s.code.includes(kw) || s.name.includes(kw))
    )
    stockOptions.value = [...remote, ...extras]
  } catch {
    ElMessage.warning('实时搜索暂不可用，已显示本地标的，可手工录入')
    stockOptions.value = localStockOptions().filter(
      s => s.code.includes(kw) || s.name.includes(kw)
    )
  } finally {
    stockSearching.value = false
  }
}
function inferStockType(code) {
  if (/^5\d{5}$/.test(code)) return 'etf'
  if (/^1[5-8]\d{4}$/.test(code)) return 'etf'
  return 'stock'
}
async function manualAddStock() {
  const code = (manualStockCode.value || '').trim().toUpperCase()
  const name = (manualStockName.value || '').trim()
  if (!code || !name) {
    ElMessage.warning('请输入代码和名称')
    return
  }
  stockSaving.value = true
  try {
    let res
    try {
      res = await createStock({ code, name, type: inferStockType(code) })
    } catch (e) {
      if (e.response?.status === 400) {
        res = { data: stocks.value.find(s => s.code === code) }
        if (!res.data) {
          const list = await getStocks()
          res = { data: list.data.find(s => s.code === code) }
          stocks.value = list.data
        }
      } else {
        throw e
      }
    }
    const stock = res.data
    if (!stock) throw new Error('标的创建失败')
    if (!stocks.value.some(s => s.id === stock.id)) stocks.value.push(stock)
    form.value.stock_id = stock.id
    stockOptions.value = localStockOptions()
    manualStockCode.value = ''
    manualStockName.value = ''
    ElMessage.success(`已添加并绑定 ${stock.code} ${stock.name}`)
  } catch {
    ElMessage.error('添加失败，请检查代码是否正确')
  } finally {
    stockSaving.value = false
  }
}
// 模板：上涨间距 = 下跌间距 × 不对称比
function templateSellSpacing(tpl) {
  const sp = Number(tpl.default_params?.grid_spacing) || 0
  const ratio = Number(tpl.default_params?.asymmetry_ratio) || 1
  return Math.round(sp * ratio * 100) / 100
}
// 选择关联模板：自动带出模板参数（间距/层数/不对称比/资金分配/止损）
function onTemplateChange(tid) {
  const tpl = templates.value.find(t => t.id === tid)
  if (!tpl?.default_params) return
  const p = tpl.default_params
  form.value.grid_spacing = p.grid_spacing ?? form.value.grid_spacing
  form.value.grid_layers = p.grid_layers ?? form.value.grid_layers
  form.value.asymmetry_ratio = p.asymmetry_ratio ?? form.value.asymmetry_ratio
  form.value.fund_allocation = p.fund_allocation ?? form.value.fund_allocation
  form.value.stop_loss_strategy = p.stop_loss_strategy ?? form.value.stop_loss_strategy
  const sell = Math.round((Number(p.grid_spacing) || 0) * (Number(p.asymmetry_ratio) || 1) * 100) / 100
  ElMessage.success(`已应用模板：下跌 ${p.grid_spacing}% 买｜上涨 ${sell}% 卖，层数 ${p.grid_layers}，不对称比 ${p.asymmetry_ratio}`)
}
// 使用模板：按 default_params 填充表单并打开新建对话框
function useTemplate(tpl) {
  isEdit.value = false
  editingId.value = null
  const params = tpl.default_params || {}
  form.value = {
    ...defaultForm,
    template_id: tpl.id,
    name: tpl.name,
    grid_spacing: params.grid_spacing ?? defaultForm.grid_spacing,
    grid_layers: params.grid_layers ?? defaultForm.grid_layers,
    asymmetry_ratio: params.asymmetry_ratio ?? defaultForm.asymmetry_ratio,
    fund_allocation: params.fund_allocation ?? defaultForm.fund_allocation,
    stop_loss_strategy: params.stop_loss_strategy ?? defaultForm.stop_loss_strategy,
  }
  stockOptions.value = localStockOptions()
  manualStockCode.value = ''
  manualStockName.value = ''
  dialogVisible.value = true
}
function openCreateDialog() {
  isEdit.value = false
  editingId.value = null
  form.value = { ...defaultForm }
  stockOptions.value = localStockOptions()
  manualStockCode.value = ''
  manualStockName.value = ''
  dialogVisible.value = true
}
function openEditDialog(row) {
  isEdit.value = true
  editingId.value = row.id
  form.value = { ...defaultForm, ...row, layer_shares: row.layer_shares || { buy: 100, sell: 100 } }
  stockOptions.value = localStockOptions()
  manualStockCode.value = ''
  manualStockName.value = ''
  dialogVisible.value = true
}
// 组装提交/预览 payload（金额与份额两种模式，总资金自动计算）
function buildPayload() {
  const base = Number(form.value.base_price)
  if (!base || base <= 0) {
    ElMessage.warning('请填写基准价')
    return null
  }
  const isShares = form.value.split_mode === 'shares'
  const p = Number(form.value.position_funds) || 0
  if (isShares) {
    const buy = Number(form.value.layer_shares?.buy) || 0
    const sell = Number(form.value.layer_shares?.sell) || 0
    if (buy <= 0 || sell <= 0) {
      ElMessage.warning('份额切分需填写买入/卖出每层份额（≥100）')
      return null
    }
    return {
      ...form.value,
      total_funds: autoTotalFunds.value,
      grid_funds: autoGridFunds.value,
      position_funds: round2(p),
      layer_shares: form.value.layer_shares,
    }
  }
  const g = Number(form.value.grid_funds) || 0
  return {
    ...form.value,
    total_funds: autoAmountTotalFunds.value,
    grid_funds: round2(g),
    position_funds: round2(p),
    layer_shares: null,
  }
}

async function saveStrategy() {
  const payload = buildPayload()
  if (!payload) return
  saving.value = true
  try {
    if (isEdit.value) {
      await updateStrategyInstance(editingId.value, payload)
      ElMessage.success('已更新')
    } else {
      await createStrategyInstance(payload)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    await fetchData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  }
  finally { saving.value = false }
}

// 策略预览：按当前表单参数计算操作明细（不落库）
async function previewStrategy() {
  const payload = buildPayload()
  if (!payload) return
  previewing.value = true
  try {
    const res = await previewGridLayers(payload)
    previewLayers.value = res.data
    previewDialog.value = true
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '预览失败')
  }
  finally { previewing.value = false }
}
async function confirmDelete(row) {
  try {
    await ElMessageBox.confirm('确定要删除此策略吗？', '确认')
    await deleteStrategyInstance(row.id)
    ElMessage.success('已删除')
    await fetchData()
  } catch (e) {
    // 用户主动取消时不提示，其余错误展示给用户
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error(e.response?.data?.detail || '删除失败，请稍后重试')
    }
  }
}
onMounted(fetchData)

// 切换到「标的库」tab 时刷新其数据，避免新建/编辑策略后显示旧数据
watch(activeTab, (val) => {
  if (val === 'stocks') stockLibraryRef.value?.fetchData()
})

</script>

<style scoped>
.header-filter {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.header-filter .el-input {
  width: 100%;
}
.table-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
</style>
