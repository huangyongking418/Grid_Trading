<template>
  <div class="login-page">
    <div class="grid-bg" aria-hidden="true"></div>
    <div class="horizon-line" aria-hidden="true"></div>
    <div class="meridian-line" aria-hidden="true"></div>
    <div class="scan-line" aria-hidden="true"></div>
    <header class="topbar">
      <div class="brand-lockup">
        <BrandLogo :size="26" />
        <span class="brand-name">网格策</span>
        <span class="brand-sub">GRID STRATEGY</span>
      </div>
    </header>
    <div class="login-card">
      <BrandLogo :size="58" class="login-logo" />
      <h1>网格策</h1>
      <p class="subtitle">GRID STRATEGY</p>
      <p class="slogan">专业网格策略构建、回测平台</p>
      <el-tabs v-model="tab" stretch>
        <el-tab-pane label="登录" name="login">
          <el-form :model="loginForm" label-width="0" size="large">
            <el-form-item>
              <el-input v-model="loginForm.username" placeholder="账号" prefix-icon="User" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="loginForm.password" type="password" placeholder="密码" prefix-icon="Lock"
                show-password @keyup.enter="doLogin" />
            </el-form-item>
            <el-form-item class="remember-row">
              <el-checkbox v-model="remember">记住密码</el-checkbox>
            </el-form-item>
            <el-button type="primary" size="large" style="width:100%" :loading="loading" @click="doLogin">
              登录
            </el-button>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="注册" name="register">
          <el-form :model="regForm" label-width="0" size="large">
            <el-form-item>
              <el-input v-model="regForm.username" placeholder="账号" prefix-icon="User" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="regForm.phone" placeholder="手机号" prefix-icon="Iphone" maxlength="11" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="regForm.password" type="password" placeholder="密码" prefix-icon="Lock"
                show-password @keyup.enter="doRegister" />
            </el-form-item>
            <el-button type="success" size="large" style="width:100%" :loading="loading" @click="doRegister">
              注册
            </el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
    <footer class="login-footer" v-if="footerItems.length">
      <div v-for="item in footerItems" :key="item.key" class="footer-item">
        <span class="footer-label">{{ item.label }}</span>
        <span class="footer-value">{{ item.value }}</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { login, register, getFooterConfig } from '../api/index.js'
import BrandLogo from '../components/BrandLogo.vue'

const tab = ref('login')
const loading = ref(false)
const remember = ref(false)
const footerItems = ref([])

const loginForm = ref({ username: '', password: '' })
const regForm = ref({ username: '', phone: '', password: '' })

onMounted(async () => {
  try {
    const saved = JSON.parse(localStorage.getItem('gts_saved_login') || 'null')
    if (saved) {
      loginForm.value.username = saved.username || ''
      loginForm.value.password = saved.password || ''
      remember.value = true
    }
  } catch {}
  try {
    const r = await getFooterConfig()
    footerItems.value = r.data.items || []
  } catch {}
})

function persistSavedLogin() {
  if (remember.value) {
    localStorage.setItem('gts_saved_login', JSON.stringify({
      username: loginForm.value.username,
      password: loginForm.value.password,
    }))
  } else {
    localStorage.removeItem('gts_saved_login')
  }
}

async function doLogin() {
  if (!loginForm.value.username || !loginForm.value.password) {
    ElMessage.warning('请输入账号和密码')
    return
  }
  loading.value = true
  try {
    const res = await login(loginForm.value)
    localStorage.setItem('gts_token', res.data.token)
    localStorage.setItem('gts_user', JSON.stringify(res.data.user))
    persistSavedLogin()
    ElMessage.success('登录成功')
    window.location.href = '/strategies'
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

async function doRegister() {
  if (!regForm.value.username || !regForm.value.phone || !regForm.value.password) {
    ElMessage.warning('请填写完整注册信息')
    return
  }
  loading.value = true
  try {
    const res = await register(regForm.value)
    localStorage.setItem('gts_token', res.data.token)
    localStorage.setItem('gts_user', JSON.stringify(res.data.user))
    ElMessage.success('注册成功，已自动登录')
    window.location.href = '/strategies'
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  overflow: hidden;
  background: #050b18;
  font-family: "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
}
.grid-bg {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(56, 139, 253, 0.09) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 139, 253, 0.09) 1px, transparent 1px);
  background-size: 44px 44px;
}
.kline-chart {
  position: absolute;
  left: 3%;
  top: 14%;
  z-index: 0;
  width: min(500px, 36vw);
  opacity: 0.92;
  pointer-events: none;
  filter: drop-shadow(0 0 14px rgba(56, 189, 248, 0.35));
}
.kline-chart .chart-grid {
  animation: fade-in 0.8s ease both;
}
.kline-chart .ma-line polyline {
  stroke-dasharray: 1000;
  stroke-dashoffset: 1000;
  animation: draw-line 2.4s ease forwards;
}
.kline-chart .ma-slow polyline {
  animation-delay: 0.4s;
}
.kline-chart .ma-fast polyline {
  filter: drop-shadow(0 0 4px rgba(34, 211, 238, 0.55));
}
.kline-chart .ma-slow polyline {
  filter: drop-shadow(0 0 4px rgba(167, 139, 250, 0.5));
}
.kline-chart .candle {
  transform-box: fill-box;
  transform-origin: center bottom;
  animation: candle-in 0.7s cubic-bezier(0.22, 1, 0.36, 1) both;
}
.kline-chart .price-mark {
  animation: fade-in 1.4s ease 1.5s both;
}
.kline-chart .axis-labels {
  animation: fade-in 1s ease 0.7s both;
}
.horizon-line,
.meridian-line {
  position: absolute;
  pointer-events: none;
}
.horizon-line {
  top: 20%;
  left: -10%;
  width: 70%;
  height: 1px;
  transform: rotate(-8deg);
  background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.45), transparent);
}
.meridian-line {
  top: -10%;
  right: 14%;
  width: 1px;
  height: 70%;
  transform: rotate(12deg);
  background: linear-gradient(180deg, transparent, rgba(99, 102, 241, 0.4), transparent);
}
.scan-line {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  opacity: 0;
  background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.9), transparent);
  animation: scan 7s linear infinite;
}
@keyframes scan {
  0% { transform: translateY(0); opacity: 0; }
  8% { opacity: 0.9; }
  92% { opacity: 0.9; }
  100% { transform: translateY(100vh); opacity: 0; }
}
@keyframes draw-line {
  to { stroke-dashoffset: 0; }
}
@keyframes candle-in {
  from { transform: scaleY(0); opacity: 0; }
  to { transform: scaleY(1); opacity: 1; }
}
@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}
.topbar {
  position: absolute;
  top: 26px;
  left: 32px;
  right: 32px;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 12px;
}
.brand-lockup {
  display: flex;
  align-items: center;
  gap: 10px;
}
.brand-name {
  color: #e0f2fe;
  font-size: 17px;
  font-weight: 700;
  text-shadow: 0 0 14px rgba(56, 189, 248, 0.6);
}
.brand-sub {
  color: rgba(148, 184, 255, 0.5);
  font-size: 10px;
  letter-spacing: 0;
}
.brand-sub::before {
  content: "/";
  margin-right: 10px;
  color: rgba(56, 189, 248, 0.45);
}
.login-card {
  position: relative;
  z-index: 1;
  width: 400px;
  max-width: 100%;
  padding: 38px 36px 30px;
  border-radius: 8px;
  border: 1px solid rgba(96, 165, 250, 0.3);
  background: rgba(13, 24, 46, 0.58);
  backdrop-filter: blur(22px) saturate(150%);
  -webkit-backdrop-filter: blur(22px) saturate(150%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    0 24px 70px rgba(0, 0, 0, 0.55);
}
.login-card::before {
  content: "";
  position: absolute;
  top: -1px;
  left: 26px;
  right: 26px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.9), rgba(99, 102, 241, 0.9), transparent);
}
.login-logo {
  display: block;
  margin: 0 auto 14px;
}
.login-card h1 {
  margin: 0 0 6px;
  font-size: 24px;
  font-weight: 600;
  color: #e6f1ff;
  text-align: center;
  text-shadow: 0 0 20px rgba(56, 189, 248, 0.45);
}
.subtitle {
  margin: 0 0 14px;
  color: rgba(148, 184, 255, 0.6);
  font-size: 11px;
  text-align: center;
}
.slogan {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin: 0 0 24px;
  color: rgba(186, 214, 255, 0.78);
  font-size: 13px;
  white-space: nowrap;
}
.slogan::before,
.slogan::after {
  content: "";
  width: 34px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.55));
}
.slogan::after {
  background: linear-gradient(90deg, rgba(99, 102, 241, 0.55), transparent);
}
.login-card :deep(.el-tabs__header) {
  margin-bottom: 24px;
}
.login-card :deep(.el-tabs__item) {
  color: rgba(180, 210, 255, 0.6);
  font-size: 15px;
}
.login-card :deep(.el-tabs__item.is-active) {
  color: #7dd3fc;
  text-shadow: 0 0 12px rgba(56, 189, 248, 0.6);
}
.login-card :deep(.el-tabs__active-bar) {
  height: 2px;
  background: linear-gradient(90deg, #38bdf8, #818cf8);
}
.login-card :deep(.el-input__wrapper) {
  background: rgba(6, 14, 30, 0.5);
  border-radius: 6px;
  box-shadow: 0 0 0 1px rgba(125, 170, 255, 0.22) inset;
  transition: box-shadow 0.2s ease, background 0.2s ease;
}
.login-card :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(125, 170, 255, 0.45) inset;
}
.login-card :deep(.el-input__wrapper.is-focus) {
  background: rgba(6, 14, 30, 0.72);
  box-shadow: 0 0 0 1px #38bdf8 inset, 0 0 18px rgba(56, 189, 248, 0.22);
}
.login-card :deep(.el-input__inner) {
  color: #dbeafe;
  caret-color: #7dd3fc;
}
.login-card :deep(.el-input__inner::placeholder) {
  color: rgba(160, 190, 255, 0.42);
}
.login-card :deep(.el-input__prefix),
.login-card :deep(.el-input__suffix) {
  color: rgba(125, 170, 255, 0.55);
}
.login-card :deep(.el-form-item) {
  margin-bottom: 18px;
}
.login-card :deep(.remember-row) {
  margin-bottom: 16px;
}
.login-card :deep(.remember-row .el-checkbox__label) {
  color: rgba(180, 210, 255, 0.78);
  font-size: 13px;
}
.login-card :deep(.remember-row .el-checkbox__inner) {
  background: rgba(6, 14, 30, 0.5);
  border-color: rgba(125, 170, 255, 0.45);
}
.login-card :deep(.remember-row .el-checkbox__input.is-checked .el-checkbox__inner) {
  background: #0ea5e9;
  border-color: #38bdf8;
}
.login-card :deep(.remember-row .el-checkbox__input.is-checked .el-checkbox__inner::after) {
  border-color: #fff;
}
.login-card :deep(.el-button) {
  height: 42px;
  border: none;
  font-weight: 600;
}
.login-card :deep(.el-button--primary) {
  background: linear-gradient(135deg, #0ea5e9, #6366f1);
  box-shadow: 0 0 24px rgba(56, 189, 248, 0.3);
}
.login-card :deep(.el-button--primary:hover),
.login-card :deep(.el-button--primary:focus) {
  background: linear-gradient(135deg, #38bdf8, #818cf8);
  box-shadow: 0 0 30px rgba(56, 189, 248, 0.45);
}
.login-card :deep(.el-button--success) {
  background: linear-gradient(135deg, #10b981, #0ea5e9);
  box-shadow: 0 0 24px rgba(16, 185, 129, 0.28);
}
.login-card :deep(.el-button--success:hover),
.login-card :deep(.el-button--success:focus) {
  background: linear-gradient(135deg, #34d399, #38bdf8);
  box-shadow: 0 0 30px rgba(52, 211, 153, 0.4);
}
.login-footer {
  position: absolute;
  left: 50%;
  bottom: 20px;
  transform: translateX(-50%);
  z-index: 2;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  gap: 8px 18px;
  max-width: min(720px, 92vw);
  padding: 10px 18px;
  border: 1px solid rgba(96, 165, 250, 0.22);
  border-radius: 8px;
  background: rgba(6, 14, 30, 0.55);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
}
.footer-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}
.footer-label {
  color: rgba(148, 184, 255, 0.55);
}
.footer-value {
  color: rgba(200, 220, 255, 0.85);
}
@media (max-width: 520px) {
  .login-card {
    padding: 30px 22px 24px;
  }
  .login-logo {
    margin-bottom: 12px;
  }
  .slogan {
    font-size: 12px;
  }
  .topbar {
    left: 20px;
    right: 20px;
  }
  .kline-chart {
    left: -110px;
    top: auto;
    bottom: 12px;
    width: 320px;
    opacity: 0.35;
  }
  .login-footer {
    bottom: 10px;
    padding: 8px 12px;
  }
}
</style>
