<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <h1 class="login-title">📝 记事本</h1>
        <p class="login-subtitle">{{ isRegister ? '创建账号' : '欢迎回来' }}</p>
      </div>

      <form class="login-form" @submit.prevent="handleSubmit">
        <div class="form-field">
          <label class="field-label">用户名</label>
          <input
            v-model="username"
            type="text"
            class="field-input"
            placeholder="请输入用户名"
            autocomplete="username"
          />
        </div>

        <div class="form-field">
          <label class="field-label">密码</label>
          <input
            v-model="password"
            type="password"
            class="field-input"
            placeholder="请输入密码"
            :autocomplete="isRegister ? 'new-password' : 'current-password'"
          />
        </div>

        <div v-if="isRegister" class="form-field">
          <label class="field-label">确认密码</label>
          <input
            v-model="confirmPassword"
            type="password"
            class="field-input"
            placeholder="请再次输入密码"
            autocomplete="new-password"
          />
        </div>

        <!-- 邀请码输入框（仅注册模式 + 后端要求时显示） -->
        <div v-if="isRegister && needRegCode" class="form-field">
          <label class="field-label">邀请码</label>
          <input
            v-model="registrationCode"
            type="text"
            class="field-input"
            placeholder="请输入邀请码"
          />
        </div>

        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>

        <button type="submit" class="btn-submit" :disabled="loading">
          {{ loading ? '请稍候...' : (isRegister ? '注册' : '登录') }}
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

const router = useRouter()
const authStore = useAuthStore()

const isRegister = ref(false)
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const registrationCode = ref('')
const errorMsg = ref('')
const loading = ref(false)

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
  height: 100vh;
  background: linear-gradient(135deg, #2c3e50 0%, #1a252f 100%);
}

.login-card {
  width: 380px;
  max-width: 90vw;
  background: #fff;
  border-radius: 12px;
  padding: 40px 32px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-title {
  font-size: 28px;
  color: #2c3e50;
  margin-bottom: 8px;
}

.login-subtitle {
  font-size: 14px;
  color: #95a5a6;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 13px;
  color: #7f8c8d;
  font-weight: 500;
}

.field-input {
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.field-input:focus {
  outline: none;
  border-color: #42b983;
}

.error-msg {
  color: #e74c3c;
  font-size: 13px;
  text-align: center;
  padding: 4px 0;
}

.btn-submit {
  width: 100%;
  padding: 12px;
  background: #42b983;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
  margin-top: 8px;
}

.btn-submit:hover:not(:disabled) {
  background: #369870;
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.login-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 13px;
  color: #95a5a6;
}

.login-footer a {
  color: #42b983;
  font-weight: 500;
}

.login-footer a:hover {
  text-decoration: underline;
}

.reg-closed-hint {
  color: #e74c3c;
}
</style>
