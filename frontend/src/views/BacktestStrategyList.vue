<template>
  <div>
    <el-card shadow="never" class="section-card">
      <template #header>
        <span><b>模拟回测</b> — 历史行情验证网格参数，数据与正式策略完全隔离</span>
      </template>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="模拟策略" name="strategies">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <span style="font-size:13px;color:#909399">创建模拟策略后生成网格价位，再设置回测周期执行回测</span>
            <el-button type="primary" size="small" @click="openCreateDialog">
              <el-icon><Plus /></el-icon> 新建模拟策略
            </el-button>
          </div>
          <el-table :data="pagedStrategies" stripe v-loading="loadingStrategies" style="width:100%">
            <el-table-column prop="id" label="ID" width="90">
              <template #header>
                <div class="header-filter">
                  <span>ID</span>
                  <el-input v-model="strategyFilters.id" placeholder="搜索" size="small" clearable />
                </div>
              </template>
            </el-table-column>
            <el-table-column label="策略名称" min-width="140">
              <template #header>
                <div class="header-filter">
                  <span>策略名称</span>
                  <el-input v-model="strategyFilters.name" placeholder="搜索" size="small" clearable />
                </div>
              </template>
              <template #default="{ row }">{{ row.name || `策略#${row.id}` }}</template>
            </el-table-column>
            <el-table-column label="标的" min-width="150">
              <template #header>
                <div class="header-filter">
                  <span>标的</span>
                  <el-input v-model="strategyFilters.stock" placeholder="搜索" size="small" clearable />
                </div>
              </template>
              <template #default="{ row }">{{ row.stock_code }} {{ row.stock_name }}</template>
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
                <div style="font-size:12px;color:#909399">网格 {{ row.grid_funds }} / 底仓 {{ row.position_funds }}</div>
              </template>
            </el-table-column>
            <el-table-column label="切分" width="110">
              <template #header>
                <div class="header-filter">
                  <span>切分</span>
                  <el-input v-model="strategyFilters.split_mode" placeholder="搜索" size="small" clearable />
                </div>
              </template>
              <template #default="{ row }">
                <el-tag :type="row.split_mode === 'shares' ? 'warning' : 'info'" size="small">
                  {{ row.split_mode === 'shares' ? '份额切分' : '金额切分' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="230" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
                <el-button link type="primary" size="small" @click="showPreview(row)">网格</el-button>
                <el-button link type="success" size="small" @click="openRunDialog(row)">回测</el-button>
                <el-button link type="danger" size="small" @click="confirmDeleteStrategy(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="table-footer">
            <el-pagination
              v-model:current-page="strategyPage"
              v-model:page-size="strategyPageSize"
              :total="filteredStrategies.length"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              background
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="回测历史" name="sessions">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <span style="font-size:13px;color:#909399">选择 2-5 条记录可对比关键绩效指标</span>
            <el-button size="small" :disabled="selectedSessions.length < 2" @click="openCompare">
              <el-icon><DataAnalysis /></el-icon> 对比选中（{{ selectedSessions.length }}）
            </el-button>
          </div>
          <el-table
            ref="sessionsTableRef"
            :data="pagedSessions"
            row-key="id"
            stripe
            v-loading="loadingSessions"
            style="width:100%"
            @selection-change="onSessionSelectionChange"
          >
            <el-table-column type="selection" width="45" reserve-selection />
            <el-table-column prop="id" label="ID" width="90">
              <template #header>
                <div class="header-filter">
                  <span>ID</span>
                  <el-input v-model="sessionFilters.id" placeholder="搜索" size="small" clearable />
                </div>
              </template>
            </el-table-column>
            <el-table-column label="策略" min-width="130">
              <template #header>
                <div class="header-filter">
                  <span>策略</span>
                  <el-input v-model="sessionFilters.strategy" placeholder="搜索" size="small" clearable />
                </div>
              </template>
              <template #default="{ row }">{{ row.strategy_name || `策略#${row.strategy_id}` }}</template>
            </el-table-column>
            <el-table-column label="标的" min-width="140">
              <template #header>
                <div class="header-filter">
                  <span>标的</span>
                  <el-input v-model="sessionFilters.stock" placeholder="搜索" size="small" clearable />
                </div>
              </template>
              <template #default="{ row }">{{ row.stock_code }} {{ row.stock_name }}</template>
            </el-table-column>
            <el-table-column label="回测区间" min-width="170">
              <template #header>
                <div class="header-filter">
                  <span>回测区间</span>
                  <el-input v-model="sessionFilters.range" placeholder="搜索" size="small" clearable />
                </div>
              </template>
              <template #default="{ row }">{{ row.start_date }} ~ {{ row.end_date }}</template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #header>
                <div class="header-filter">
                  <span>状态</span>
                  <el-input v-model="sessionFilters.status" placeholder="搜索" size="small" clearable />
                </div>
              </template>
              <template #default="{ row }">
                <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="总收益率" width="100">
              <template #header>
                <div class="header-filter">
                  <span>总收益率</span>
                  <el-input v-model="sessionFilters.total_return" placeholder="搜索" size="small" clearable />
                </div>
              </template>
              <template #default="{ row }">
                <span v-if="row.metric" :style="{ color: row.metric.total_return_rate >= 0 ? '#67c23a' : '#f56c6c' }">
                  {{ row.metric.total_return_rate }}%
                </span>
                <span v-else style="color:#c0c4cc">-</span>
              </template>
            </el-table-column>
            <el-table-column label="最大回撤" width="100">
              <template #header>
                <div class="header-filter">
                  <span>最大回撤</span>
                  <el-input v-model="sessionFilters.max_drawdown" placeholder="搜索" size="small" clearable />
                </div>
              </template>
              <template #default="{ row }">{{ row.metric ? row.metric.max_drawdown + '%' : '-' }}</template>
            </el-table-column>
            <el-table-column label="交易笔数" width="90">
              <template #header>
                <div class="header-filter">
                  <span>交易笔数</span>
                  <el-input v-model="sessionFilters.trade_count" placeholder="搜索" size="small" clearable />
                </div>
              </template>
              <template #default="{ row }">{{ row.metric?.total_trade_count ?? '-' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="goDetail(row)">详情</el-button>
                <el-button link type="danger" size="small" @click="confirmDeleteSession(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="table-footer">
            <el-pagination
              v-model:current-page="sessionPage"
              v-model:page-size="sessionPageSize"
              :total="filteredSessions.length"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              background
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑模拟策略' : '新建模拟策略'" width="640px">
      <el-form :model="form" label-width="100px" size="small">
        <el-form-item label="策略名称"><el-input v-model="form.name" placeholder="如：震荡向上-回测版" /></el-form-item>
        <el-form-item label="从正式策略">
          <el-select v-model="formalImportId" clearable placeholder="选择正式策略导入参数" style="width:100%" @change="importFormalStrategy">
            <el-option v-for="inst in formalInstances" :key="inst.id" :label="`${inst.name || '策略#'+inst.id}（${formalStockLabel(inst)}）`" :value="inst.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="回测标的">
          <el-select
            v-model="form.stock_code"
            filterable
            remote
            :remote-method="remoteSearchStock"
            :loading="stockSearching"
            clearable
            placeholder="输入代码或名称搜索 A股 / ETF"
            style="width:100%"
            @change="onStockSelected"
          >
            <el-option v-for="opt in stockOptions" :key="opt.code" :label="`${opt.code} ${opt.name}（${opt.type === 'etf' ? 'ETF' : '股票'}）`" :value="opt.code" />
            <template #empty>
              <div style="padding:8px;font-size:12px;color:#909399;text-align:left">
                <div v-if="stockSearching">搜索中…</div>
                <div v-else>输入代码或名称搜索，也可手工录入</div>
              </div>
            </template>
          </el-select>
          <div style="display:flex;gap:8px;margin-top:8px;align-items:center">
            <el-input v-model="manualCode" placeholder="代码，如 600519 / 510300" style="width:130px" />
            <el-input v-model="manualName" placeholder="名称（手工录入）" style="flex:1" />
            <el-button size="small" @click="manualSetStock">录入</el-button>
          </div>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="基准价">
              <el-input-number v-model="form.base_price" :min="0.01" :step="0.1" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="间距(%)">
              <el-input-number v-model="form.grid_spacing" :min="0.01" :step="0.1" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="层数">
              <el-input-number v-model="form.grid_layers" :min="1" :max="50" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="不对称比">
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
              <el-form-item label="底仓资金"><el-input v-model="form.position_funds" placeholder="0"><template #append>元</template></el-input></el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="网格资金"><el-input v-model="form.grid_funds" placeholder="100000"><template #append>元</template></el-input></el-form-item>
            </el-col>
          </el-row>
          <div style="font-size:12px;color:#909399;margin:-4px 0 12px 100px">总资金 = 网格资金 + 底仓资金，底仓不参与网格买卖</div>
          <el-form-item label="资金分配">
            <el-select v-model="form.fund_allocation" style="width:100%">
              <el-option label="等额均分" value="equal" />
              <el-option label="金字塔分配" value="pyramid" />
            </el-select>
          </el-form-item>
        </template>
        <template v-else>
          <el-row :gutter="12">
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
          <div style="font-size:12px;color:#909399;margin:-4px 0 12px 100px">份额模式：网格资金与总资金按各层份额自动计算</div>
        </template>
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
        <el-button @click="previewFromForm" :loading="previewing">生成网格价位</el-button>
        <el-button type="primary" @click="saveStrategy" :loading="saving">保存策略</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="previewDialog" :title="previewTitle" width="760px">
      <el-table :data="previewLayers" stripe size="small" style="width:100%" max-height="460">
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
        <el-table-column prop="trigger_price" label="触发价" width="110" />
        <el-table-column prop="quantity" label="数量" width="100" />
        <el-table-column prop="amount" label="金额" width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'holding' ? 'warning' : 'info'" size="small">{{ row.status === 'holding' ? '持仓' : '等待触发' }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="previewDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="runDialogVisible" title="发起模拟回测" width="560px">
      <el-descriptions :column="1" border size="small" style="margin-bottom:16px">
        <el-descriptions-item label="策略">{{ runStrategy?.name || `策略#${runStrategy?.id}` }}</el-descriptions-item>
        <el-descriptions-item label="标的">{{ runStrategy?.stock_code }} {{ runStrategy?.stock_name }}</el-descriptions-item>
        <el-descriptions-item label="初始资金">{{ runStrategy?.total_funds }} 元</el-descriptions-item>
      </el-descriptions>
      <el-form :model="runForm" label-width="110px" size="small">
        <el-form-item label="开始日期">
          <el-date-picker v-model="runForm.start_date" type="date" value-format="YYYY-MM-DD" placeholder="选择开始日期" style="width:100%" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="runForm.end_date" type="date" value-format="YYYY-MM-DD" placeholder="选择结束日期" style="width:100%" />
        </el-form-item>
        <el-divider content-position="left">费用参数（默认值）</el-divider>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="佣金率"><el-input-number v-model="runForm.fee.commission_rate" :min="0" :step="0.0001" :precision="5" style="width:100%" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最低佣金"><el-input-number v-model="runForm.fee.min_commission" :min="0" :step="0.5" style="width:100%" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="印花税率"><el-input-number v-model="runForm.fee.stamp_tax_rate" :min="0" :step="0.0001" :precision="4" style="width:100%" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="过户费率"><el-input-number v-model="runForm.fee.transfer_fee_rate" :min="0" :step="0.00001" :precision="6" style="width:100%" /></el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="滑点">
          <el-input-number v-model="runForm.fee.slippage" :min="0" :max="0.05" :step="0.001" :precision="3" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="runDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRun" :loading="running">开始回测</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="compareDialogVisible" title="回测结果对比" width="900px">
      <el-table :data="compareRows" border stripe size="small" style="width:100%">
        <el-table-column label="指标" min-width="120" fixed>
          <template #default="{ row }"><b>{{ row.label }}</b></template>
        </el-table-column>
        <el-table-column v-for="s in selectedSessions" :key="s.id" :label="`#${s.id} ${s.strategy_name || ''}`" min-width="130">
          <template #default="{ row }">
            <span v-if="s.metric">{{ formatMetric(row.key, s.metric) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getBacktestStrategies,
  createBacktestStrategy,
  updateBacktestStrategy,
  deleteBacktestStrategy,
  previewBacktestLayers,
  getBacktestSessions,
  createBacktestSession,
  deleteBacktestSession,
} from '../api/backtest.js'
import { getStrategyInstances, getStocks, searchStocks } from '../api/index.js'

const router = useRouter()
const activeTab = ref('strategies')
const strategies = ref([])
const sessions = ref([])
const strategyFilters = ref({
  id: '',
  name: '',
  stock: '',
  base_price: '',
  grid_spacing: '',
  grid_layers: '',
  asymmetry_ratio: '',
  funds: '',
  split_mode: '',
})
const strategyPage = ref(1)
const strategyPageSize = ref(10)
const sessionFilters = ref({
  id: '',
  strategy: '',
  stock: '',
  range: '',
  status: '',
  total_return: '',
  max_drawdown: '',
  trade_count: '',
})
const sessionPage = ref(1)
const sessionPageSize = ref(10)
const sessionsTableRef = ref(null)
const formalInstances = ref([])
const formalStocks = ref([])
const loadingStrategies = ref(false)
const loadingSessions = ref(false)
const saving = ref(false)
const previewing = ref(false)
const running = ref(false)

const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const formalImportId = ref(null)
const defaultForm = {
  name: '',
  template_id: null,
  stock_code: '',
  stock_name: '',
  stock_type: 'stock',
  grid_spacing: 1.0,
  grid_layers: 5,
  asymmetry_ratio: 1.0,
  base_price: null,
  stop_loss_strategy: 'none',
  fund_allocation: 'equal',
  total_funds: 100000,
  grid_funds: 100000,
  position_funds: 0,
  split_mode: 'amount',
  layer_shares: { buy: 100, sell: 100 },
  reset_cycle_days: 0,
}
const form = ref({ ...defaultForm })

const stockOptions = ref([])
const stockSearching = ref(false)
const manualCode = ref('')
const manualName = ref('')

const previewDialog = ref(false)
const previewTitle = ref('网格价位预览')
const previewLayers = ref([])

const runDialogVisible = ref(false)
const runStrategy = ref(null)
const runForm = ref({
  start_date: '',
  end_date: '',
  fee: {
    commission_rate: 0.00025,
    min_commission: 5,
    stamp_tax_rate: 0.001,
    transfer_fee_rate: 0.00001,
    slippage: 0,
  },
})

const selectedSessions = ref([])
const compareDialogVisible = ref(false)
const compareRows = ref([])

const round2 = (n) => Math.round((Number(n) || 0) * 100) / 100

const filteredStrategies = computed(() => {
  const f = strategyFilters.value
  const hasFilter = Object.values(f).some(v => (v || '').trim() !== '')
  if (!hasFilter) return strategies.value
  const match = (field, value) => !(field || '').trim() || String(value ?? '').includes((field || '').trim())
  return strategies.value.filter(row => (
    match(f.id, row.id)
    && match(f.name, row.name || `策略#${row.id}`)
    && match(f.stock, `${row.stock_code ?? ''} ${row.stock_name ?? ''}`)
    && match(f.base_price, row.base_price)
    && match(f.grid_spacing, row.grid_spacing)
    && match(f.grid_layers, row.grid_layers)
    && match(f.asymmetry_ratio, row.asymmetry_ratio)
    && match(f.funds, `${row.total_funds ?? ''} ${row.grid_funds ?? ''} ${row.position_funds ?? ''}`)
    && match(f.split_mode, row.split_mode === 'shares' ? '份额切分' : '金额切分')
  ))
})
const pagedStrategies = computed(() => {
  const start = (strategyPage.value - 1) * strategyPageSize.value
  return filteredStrategies.value.slice(start, start + strategyPageSize.value)
})
watch([filteredStrategies, strategyPageSize], () => {
  const maxPage = Math.max(1, Math.ceil(filteredStrategies.value.length / strategyPageSize.value))
  if (strategyPage.value > maxPage) strategyPage.value = maxPage
})
watch(strategyPageSize, () => { strategyPage.value = 1 })

const filteredSessions = computed(() => {
  const f = sessionFilters.value
  const hasFilter = Object.values(f).some(v => (v || '').trim() !== '')
  if (!hasFilter) return sessions.value
  const match = (field, value) => !(field || '').trim() || String(value ?? '').includes((field || '').trim())
  return sessions.value.filter(row => {
    const metric = row.metric
    return match(f.id, row.id)
      && match(f.strategy, row.strategy_name || `策略#${row.strategy_id}`)
      && match(f.stock, `${row.stock_code ?? ''} ${row.stock_name ?? ''}`)
      && match(f.range, `${row.start_date ?? ''} ${row.end_date ?? ''}`)
      && match(f.status, statusText(row.status))
      && match(f.total_return, metric?.total_return_rate)
      && match(f.max_drawdown, metric?.max_drawdown)
      && match(f.trade_count, metric?.total_trade_count)
  })
})
const pagedSessions = computed(() => {
  const start = (sessionPage.value - 1) * sessionPageSize.value
  return filteredSessions.value.slice(start, start + sessionPageSize.value)
})
watch([filteredSessions, sessionPageSize], () => {
  const maxPage = Math.max(1, Math.ceil(filteredSessions.value.length / sessionPageSize.value))
  if (sessionPage.value > maxPage) sessionPage.value = maxPage
})
watch(sessionPageSize, () => { sessionPage.value = 1 })

async function fetchStrategies() {
  loadingStrategies.value = true
  try {
    const r = await getBacktestStrategies()
    strategies.value = r.data
  } catch {
    ElMessage.error('模拟策略加载失败')
  } finally {
    loadingStrategies.value = false
  }
}

async function fetchSessions() {
  loadingSessions.value = true
  try {
    const r = await getBacktestSessions()
    sessions.value = r.data
    if (sessions.value.some(s => s.status === 'pending' || s.status === 'running')) {
      scheduleSessionPoll()
    }
  } catch {
    // 轮询失败静默，避免打断页面
  } finally {
    loadingSessions.value = false
  }
}

let sessionPollTimer = null
function scheduleSessionPoll() {
  clearTimeout(sessionPollTimer)
  sessionPollTimer = setTimeout(() => {
    if (activeTab.value === 'sessions' || sessions.value.some(s => s.status === 'pending' || s.status === 'running')) {
      fetchSessions()
    }
  }, 4000)
}

async function fetchFormalInstances() {
  try {
    const [r1, r2] = await Promise.all([getStrategyInstances(), getStocks()])
    formalInstances.value = r1.data
    formalStocks.value = r2.data
  } catch {}
}

function formalStockLabel(inst) {
  const s = formalStocks.value.find(x => x.id === inst.stock_id)
  return s ? `${s.code} ${s.name}` : '未绑定'
}

function openCreateDialog() {
  isEdit.value = false
  editingId.value = null
  form.value = { ...defaultForm, layer_shares: { buy: 100, sell: 100 } }
  formalImportId.value = null
  dialogVisible.value = true
}

function openEditDialog(row) {
  isEdit.value = true
  editingId.value = row.id
  form.value = {
    ...defaultForm,
    ...row,
    layer_shares: row.layer_shares || { buy: 100, sell: 100 },
  }
  formalImportId.value = null
  dialogVisible.value = true
}

function importFormalStrategy(id) {
  const inst = formalInstances.value.find(i => i.id === id)
  if (!inst) return
  const formalStock = formalStocks.value.find(s => s.id === inst.stock_id)
  form.value = {
    ...defaultForm,
    name: (inst.name || '策略') + '-回测版',
    template_id: inst.template_id,
    stock_code: formalStock?.code || '',
    stock_name: formalStock?.name || '',
    stock_type: formalStock?.type === 'etf' ? 'etf' : 'stock',
    grid_spacing: inst.grid_spacing,
    grid_layers: inst.grid_layers,
    asymmetry_ratio: inst.asymmetry_ratio,
    base_price: inst.base_price,
    stop_loss_strategy: inst.stop_loss_strategy || 'none',
    fund_allocation: inst.fund_allocation || 'equal',
    total_funds: inst.total_funds,
    grid_funds: inst.grid_funds ?? inst.total_funds,
    position_funds: inst.position_funds ?? 0,
    split_mode: inst.split_mode || 'amount',
    layer_shares: inst.layer_shares || { buy: 100, sell: 100 },
    reset_cycle_days: inst.reset_cycle_days || 0,
  }
  ElMessage.success(`已导入正式策略「${inst.name || inst.id}」参数`)
}

function remoteSearchStock(keyword) {
  const kw = (keyword || '').trim()
  if (!kw) {
    stockOptions.value = []
    return
  }
  doSearchStock(kw)
}

async function doSearchStock(kw) {
  stockSearching.value = true
  try {
    const r = await searchStocks(kw)
    stockOptions.value = r.data.filter(s => s.type === 'stock' || s.type === 'etf')
  } catch {
    ElMessage.warning('实时搜索暂不可用，可手工录入代码和名称')
    stockOptions.value = []
  } finally {
    stockSearching.value = false
  }
}

function onStockSelected(code) {
  const opt = stockOptions.value.find(o => o.code === code)
  if (!opt) return
  form.value.stock_code = opt.code
  form.value.stock_name = opt.name
  form.value.stock_type = opt.type === 'etf' ? 'etf' : 'stock'
}

function inferStockType(code) {
  if (/^5\d{5}$/.test(code)) return 'etf'
  if (/^1[5-8]\d{4}$/.test(code)) return 'etf'
  return 'stock'
}

function manualSetStock() {
  const code = (manualCode.value || '').trim()
  const name = (manualName.value || '').trim()
  if (!code || !name) {
    ElMessage.warning('请输入代码和名称')
    return
  }
  form.value.stock_code = code
  form.value.stock_name = name
  form.value.stock_type = inferStockType(code)
  manualCode.value = ''
  manualName.value = ''
  ElMessage.success(`已录入 ${code} ${name}`)
}

function buildPayload() {
  const base = Number(form.value.base_price)
  if (!form.value.stock_code || !form.value.stock_name) {
    ElMessage.warning('请先选择或录入回测标的')
    return null
  }
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
    const gridFunds = calcSharesGridFunds()
    return {
      ...form.value,
      total_funds: round2(gridFunds + p),
      grid_funds: round2(gridFunds),
      position_funds: round2(p),
    }
  }
  const g = Number(form.value.grid_funds) || 0
  return {
    ...form.value,
    total_funds: round2(g + p),
    grid_funds: round2(g),
    position_funds: round2(p),
    layer_shares: null,
  }
}

function calcSharesGridFunds() {
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
  return total
}

async function saveStrategy() {
  const payload = buildPayload()
  if (!payload) return
  saving.value = true
  try {
    if (isEdit.value) {
      await updateBacktestStrategy(editingId.value, payload)
      ElMessage.success('已更新')
    } else {
      await createBacktestStrategy(payload)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    await fetchStrategies()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function previewFromForm() {
  const payload = buildPayload()
  if (!payload) return
  previewing.value = true
  try {
    if (isEdit.value && editingId.value) {
      await updateBacktestStrategy(editingId.value, payload)
      const r = await previewBacktestLayers(editingId.value)
      previewLayers.value = r.data
    } else {
      const created = await createBacktestStrategy(payload)
      const r = await previewBacktestLayers(created.data.id)
      previewLayers.value = r.data
      isEdit.value = true
      editingId.value = created.data.id
    }
    previewTitle.value = `网格价位预览（${payload.stock_code} ${payload.stock_name}）`
    previewDialog.value = true
    await fetchStrategies()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '生成网格失败')
  } finally {
    previewing.value = false
  }
}

async function showPreview(row) {
  try {
    const r = await previewBacktestLayers(row.id)
    previewLayers.value = r.data
    previewTitle.value = `网格价位预览（${row.stock_code} ${row.stock_name}）`
    previewDialog.value = true
  } catch {
    ElMessage.error('网格预览失败')
  }
}

function openRunDialog(row) {
  runStrategy.value = row
  runForm.value = {
    start_date: '',
    end_date: '',
    fee: {
      commission_rate: 0.00025,
      min_commission: 5,
      stamp_tax_rate: 0.001,
      transfer_fee_rate: 0.00001,
      slippage: 0,
    },
  }
  runDialogVisible.value = true
}

async function submitRun() {
  if (!runForm.value.start_date || !runForm.value.end_date) {
    ElMessage.warning('请选择回测开始和结束日期')
    return
  }
  if (runForm.value.start_date > runForm.value.end_date) {
    ElMessage.warning('开始日期不能晚于结束日期')
    return
  }
  running.value = true
  try {
    const r = await createBacktestSession({
      strategy_id: runStrategy.value.id,
      start_date: runForm.value.start_date,
      end_date: runForm.value.end_date,
      fee_config: runForm.value.fee,
    })
    ElMessage.success('回测任务已创建，正在执行')
    runDialogVisible.value = false
    router.push(`/backtest/sessions/${r.data.id}`)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '创建回测失败')
  } finally {
    running.value = false
  }
}

async function confirmDeleteStrategy(row) {
  try {
    await ElMessageBox.confirm(`确定删除模拟策略「${row.name || row.id}」吗？其回测历史会一并删除`, '确认')
    await deleteBacktestStrategy(row.id)
    ElMessage.success('已删除')
    await fetchStrategies()
  } catch {}
}

async function confirmDeleteSession(row) {
  try {
    await ElMessageBox.confirm(`确定删除回测记录 #${row.id} 吗？`, '确认')
    await deleteBacktestSession(row.id)
    ElMessage.success('已删除')
    await fetchSessions()
  } catch {}
}

function goDetail(row) {
  router.push(`/backtest/sessions/${row.id}`)
}

function onSessionSelectionChange() {
  const rows = sessionsTableRef.value?.getSelectionRows() || []
  selectedSessions.value = rows.slice(0, 5)
}

function openCompare() {
  const rows = [
    { key: 'total_return_rate', label: '总收益率' },
    { key: 'annual_return_rate', label: '年化收益率' },
    { key: 'max_drawdown', label: '最大回撤' },
    { key: 'sharpe_ratio', label: '夏普比率' },
    { key: 'win_rate', label: '胜率' },
    { key: 'profit_loss_ratio', label: '盈亏比' },
    { key: 'total_trade_count', label: '成交笔数' },
    { key: 'total_fee', label: '累计手续费' },
    { key: 'benchmark_return_rate', label: '基准收益率' },
    { key: 'excess_return', label: '超额收益' },
  ]
  compareRows.value = rows
  compareDialogVisible.value = true
}

function formatMetric(key, metric) {
  if (metric == null) return '-'
  if (['total_return_rate', 'annual_return_rate', 'max_drawdown', 'win_rate', 'benchmark_return_rate', 'excess_return'].includes(key)) {
    return `${metric[key] ?? 0}%`
  }
  return metric[key] ?? 0
}

function statusText(status) {
  return { pending: '排队中', running: '回测中', success: '已完成', failed: '失败' }[status] || status
}

function statusType(status) {
  return { pending: 'info', running: 'warning', success: 'success', failed: 'danger' }[status] || 'info'
}

onMounted(() => {
  fetchStrategies()
  fetchSessions()
  fetchFormalInstances()
})

onUnmounted(() => clearTimeout(sessionPollTimer))
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
