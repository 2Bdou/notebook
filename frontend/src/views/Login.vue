<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <Icon name="notebook" :size="36" :stroke-width="1.5" class="login-logo" />
        <h1 class="login-title">记事本</h1>
        <p class="login-subtitle">{{ isRegister ? '创建账号' : '欢迎回来' }}</p>
      </div>

      <form class="login-form" @submit.prevent="handleSubmit">
        <div class="form-field">
          <label class="field-label" for="username">用户名</label>
          <input
            id="username"
            v-model="username"
            type="text"
            class="field-input"
            placeholder="请输入用户名"
            autocomplete="username"
          />
        </div>

        <div class="form-field">
          <label class="field-label" for="password">密码</label>
          <div class="password-wrapper">
            <input
              id="password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              class="field-input"
              placeholder="请输入密码"
              :autocomplete="isRegister ? 'new-password' : 'current-password'"
            />
            <button
              type="button"
              class="password-toggle"
              :aria-label="showPassword ? '隐藏密码' : '显示密码'"
              @click="showPassword = !showPassword"
            >
              <Icon :name="showPassword ? 'eye-off' : 'eye'" :size="18" />
            </button>
          </div>
        </div>

        <div v-if="isRegister" class="form-field">
          <label class="field-label" for="confirm-password">确认密码</label>
          <input
            id="confirm-password"
            v-model="confirmPassword"
            type="password"
            class="field-input"
            placeholder="请再次输入密码"
            autocomplete="new-password"
          />
        </div>

        <!-- 邀请码输入框（仅注册模式 + 后端要求时显示） -->
        <div v-if="isRegister && needRegCode" class="form-field">
          <label class="field-label" for="reg-code">邀请码</label>
          <input
            id="reg-code"
            v-model="registrationCode"
            type="text"
            class="field-input"
            placeholder="请输入邀请码"
          />
        </div>

        <div v-if="errorMsg" class="error-msg" role="alert">{{ errorMsg }}</div>

        <button type="submit" class="btn-submit" :disabled="loading">
          <Icon v-if="loading" name="loader" :size="18" class="spin" />
          <span>{{ loading ? '请稍候...' : (isRegister ? '注册' : '登录') }}</span>
        </button>
      </form>

      <div class="login-footer">
        <span v-if="isRegister">
          已有账号？
          <a href="#" @click.prevent="toggleMode">去登录</a>
        </span>
        <span v-else-if="allowRegistration">
          还没有账号？
          <a href="#" @click.prevent="toggleMode">去注册</a>
        </span>
        <span v-else class="reg-closed-hint">注册已关闭，请联系管理员</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'
import Icon from '@/components/Icon.vue'

const router = useRouter()
const authStore = useAuthStore()

const isRegister = ref(false)
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const registrationCode = ref('')
const errorMsg = ref('')
const loading = ref(false)
const showPassword = ref(false)

// 后端认证配置
const allowRegistration = ref(true)
const needRegCode = ref(false)

/** 页面加载时获取后端认证配置 */
onMounted(async () => {
  try {
    const config = await authApi.config()
    allowRegistration.value = config.allow_registration
    needRegCode.value = config.need_registration_code
  } catch {
    // 获取配置失败时保持默认值（允许注册、不需要邀请码）
  }
})

/** 切换登录/注册模式 */
function toggleMode() {
  if (!allowRegistration.value && !isRegister.value) return
  isRegister.value = !isRegister.value
  errorMsg.value = ''
  confirmPassword.value = ''
  registrationCode.value = ''
}

/** 提交表单 */
async function handleSubmit() {
  errorMsg.value = ''

  // 前端校验
  if (!username.value.trim()) {
    errorMsg.value = '请输入用户名'
    return
  }
  if (username.value.trim().length < 2) {
    errorMsg.value = '用户名至少 2 个字符'
    return
  }
  if (!password.value) {
    errorMsg.value = '请输入密码'
    return
  }
  if (password.value.length < 6) {
    errorMsg.value = '密码至少 6 个字符'
    return
  }
  if (isRegister.value && password.value !== confirmPassword.value) {
    errorMsg.value = '两次输入的密码不一致'
    return
  }
  if (isRegister.value && needRegCode.value && !registrationCode.value.trim()) {
    errorMsg.value = '请输入邀请码'
    return
  }

  loading.value = true
  try {
    if (isRegister.value) {
      await authStore.register(
        username.value.trim(),
        password.value,
        registrationCode.value.trim()
      )
    } else {
      await authStore.login(username.value.trim(), password.value)
    }
    // 登录/注册成功，跳转首页
    router.push({ name: 'home' })
  } catch (err: any) {
    // 从错误信息中提取提示
    const msg = err?.response?.data?.detail || err?.message || '操作失败'
    errorMsg.value = msg
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100dvh;
  background: linear-gradient(135deg, #1e2937 0%, #0f172a 100%);
  padding: var(--space-4);
}

.login-card {
  width: 400px;
  max-width: 100%;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  padding: var(--space-8) var(--space-6);
  box-shadow: var(--shadow-lg);
}

.login-header {
  text-align: center;
  margin-bottom: var(--space-8);
}

.login-logo {
  color: var(--color-primary);
  margin-bottom: var(--space-3);
}

.login-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.login-subtitle {
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 13px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.field-input {
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 14px;
  transition: border-color var(--transition-fast);
  background: var(--color-bg-card);
  color: var(--color-text-primary);
}

.field-input:focus {
  border-color: var(--color-primary);
  outline: none;
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.15);
}

/* 密码显示/隐藏切换 */
.password-wrapper {
  position: relative;
}

.password-toggle {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  transition: color var(--transition-fast);
}

.password-toggle:hover {
  color: var(--color-text-secondary);
}

.error-msg {
  color: var(--color-danger);
  font-size: 13px;
  text-align: center;
  padding: var(--space-1) 0;
  background: var(--color-danger-light);
  border-radius: var(--radius-sm);
}

.btn-submit {
  width: 100%;
  padding: 12px;
  background: var(--color-primary);
  color: #fff;
  border-radius: var(--radius-md);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition-fast);
  margin-top: var(--space-2);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  min-height: 44px;
}

.btn-submit:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.btn-submit:active:not(:disabled) {
  transform: scale(0.98);
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.login-footer {
  text-align: center;
  margin-top: var(--space-6);
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.login-footer a {
  color: var(--color-primary);
  font-weight: 500;
}

.login-footer a:hover {
  text-decoration: underline;
}

.reg-closed-hint {
  color: var(--color-danger);
}

/* 加载动画 */
.spin {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
