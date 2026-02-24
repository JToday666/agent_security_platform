<template>
    <Teleport to="body">
        <Transition name="fade" @after-leave="afterLeave">
            <div v-if="showLogin" class="dialog-overlay" @click.self="closeDialog">
                <Transition name="scale" appear>
                    <div class="dialog-card">
                        <!-- 关闭按钮 -->
                        <button class="close-btn" @click="closeDialog" aria-label="关闭">
                            <XMarkIcon class="w-5 h-5" />
                        </button>

                        <!-- 标题 & 装饰 -->
                        <div class="header">
                            <div class="logo-wrapper">
                                <ShieldCheckIcon class="logo-icon" />
                            </div>
                            <h3>{{ mode === 'login' ? '欢迎回来' : '创建账号' }}</h3>
                            <p class="subtitle">
                                {{ mode === 'login' ? '登录以继续使用智能体检测平台' : '注册后即可开始检测您的智能体' }}
                            </p>
                        </div>

                        <!-- 登录表单 -->
                        <form v-if="mode === 'login'" @submit.prevent="handleLogin" class="form">
                            <div class="form-group" :class="{ 'focused': focusedField === 'login-username' }">
                                <UserIcon class="input-icon" />
                                <input v-model="loginForm.username" type="text" placeholder="用户名" required
                                    @focus="focusedField = 'login-username'" @blur="focusedField = null" />
                            </div>
                            <div class="form-group" :class="{ 'focused': focusedField === 'login-password' }">
                                <LockClosedIcon class="input-icon" />
                                <input v-model="loginForm.password" type="password" placeholder="密码" required
                                    @focus="focusedField = 'login-password'" @blur="focusedField = null" />
                            </div>

                            <Transition name="shake">
                                <div v-if="loginError" class="error-message">
                                    <ExclamationCircleIcon class="w-4 h-4" />
                                    {{ loginError }}
                                </div>
                            </Transition>

                            <button type="submit" class="submit-btn" :disabled="!isLoginValid || loading">
                                <span v-if="!loading">登录</span>
                                <span v-else class="loader"></span>
                            </button>
                        </form>

                        <!-- 注册表单 -->
                        <form v-else @submit.prevent="handleRegister" class="form">
                            <div class="form-group" :class="{ 'focused': focusedField === 'reg-username' }">
                                <UserIcon class="input-icon" />
                                <input v-model="registerForm.username" type="text" placeholder="用户名" required
                                    @focus="focusedField = 'reg-username'" @blur="focusedField = null" />
                            </div>
                            <div class="form-group" :class="{ 'focused': focusedField === 'reg-email' }">
                                <EnvelopeIcon class="input-icon" />
                                <input v-model="registerForm.email" type="email" placeholder="邮箱" required
                                    @focus="focusedField = 'reg-email'" @blur="focusedField = null" />
                            </div>
                            <div class="form-group" :class="{ 'focused': focusedField === 'reg-password' }">
                                <LockClosedIcon class="input-icon" />
                                <input v-model="registerForm.password" type="password" placeholder="密码" required
                                    @focus="focusedField = 'reg-password'" @blur="focusedField = null" />
                            </div>
                            <div class="form-group" :class="{ 'focused': focusedField === 'reg-confirm' }">
                                <LockClosedIcon class="input-icon" />
                                <input v-model="registerForm.confirmPassword" type="password" placeholder="确认密码"
                                    required @focus="focusedField = 'reg-confirm'" @blur="focusedField = null" />
                            </div>

                            <Transition name="shake">
                                <div v-if="registerError" class="error-message">
                                    <ExclamationCircleIcon class="w-4 h-4" />
                                    {{ registerError }}
                                </div>
                            </Transition>
                            <Transition name="shake">
                                <div v-if="passwordMatchError" class="error-message">
                                    <ExclamationCircleIcon class="w-4 h-4" />
                                    {{ passwordMatchError }}
                                </div>
                            </Transition>

                            <button type="submit" class="submit-btn" :disabled="!isRegisterValid || loading">
                                <span v-if="!loading">注册</span>
                                <span v-else class="loader"></span>
                            </button>
                        </form>

                        <!-- 切换模式链接 -->
                        <div class="switch-mode">
                            <a href="#" @click.prevent="toggleMode">
                                <span v-if="mode === 'register'">← 已有账号？</span>
                                <span v-else>没有账号？</span>
                                <span class="highlight">{{ mode === 'register' ? '登录' : '立即注册' }}</span>
                                <span v-if="mode === 'login'"> →</span>
                            </a>
                        </div>
                    </div>
                </Transition>
            </div>
        </Transition>
    </Teleport>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useUserStore } from '@/store/user'
import { storeToRefs } from 'pinia'
import {
    XMarkIcon,
    ShieldCheckIcon,
    UserIcon,
    LockClosedIcon,
    EnvelopeIcon,
    ExclamationCircleIcon,
} from '@heroicons/vue/24/outline'

const userStore = useUserStore()
const { showLogin } = storeToRefs(userStore)

const mode = ref<'login' | 'register'>('login')
const loading = ref(false)
const focusedField = ref<string | null>(null)

const loginForm = reactive({
    username: '',
    password: '',
})
const loginError = ref('')

const registerForm = reactive({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
})
const registerError = ref('')

const afterLeave = () => {
    // 重置所有状态
    loginForm.username = ''
    loginForm.password = ''
    registerForm.username = ''
    registerForm.email = ''
    registerForm.password = ''
    registerForm.confirmPassword = ''
    loginError.value = ''
    registerError.value = ''
    mode.value = 'login'
    loading.value = false
}

const closeDialog = () => {
    userStore.showLogin = false
}

const toggleMode = () => {
    mode.value = mode.value === 'login' ? 'register' : 'login'
    loginError.value = ''
    registerError.value = ''
}

const isLoginValid = computed(() => {
    return loginForm.username.trim() !== '' && loginForm.password.trim() !== ''
})

const passwordMatchError = computed(() => {
    if (registerForm.password && registerForm.confirmPassword) {
        return registerForm.password !== registerForm.confirmPassword ? '两次密码不一致' : ''
    }
    return ''
})

const isRegisterValid = computed(() => {
    return (
        registerForm.username.trim() !== '' &&
        registerForm.email.trim() !== '' &&
        registerForm.password.trim() !== '' &&
        registerForm.confirmPassword.trim() !== '' &&
        registerForm.password === registerForm.confirmPassword &&
        /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerForm.email)
    )
})

const handleLogin = async () => {
    loading.value = true
    loginError.value = ''
    // 模拟异步请求
    setTimeout(() => {
        const success = userStore.login(loginForm.username, loginForm.password)
        if (success) {
            closeDialog()
        } else {
            loginError.value = '用户名或密码错误'
        }
        loading.value = false
    }, 100)
}

const handleRegister = async () => {
    if (registerForm.password !== registerForm.confirmPassword) {
        registerError.value = '密码不一致'
        return
    }
    loading.value = true
    registerError.value = ''
    // 模拟异步请求
    setTimeout(() => {
        const success = userStore.register({
            username: registerForm.username,
            email: registerForm.email,
            password: registerForm.password,
        })
        if (success) {
            closeDialog()
        } else {
            registerError.value = '用户名或邮箱已被注册'
        }
        loading.value = false
    }, 100)
}
</script>

<style scoped>
* {
    box-sizing: border-box;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}

.scale-enter-active {
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.scale-enter-from {
    transform: scale(0.9);
}

.shake-enter-active {
    animation: shake 0.3s ease;
}

@keyframes shake {

    0%,
    100% {
        transform: translateX(0);
    }

    20% {
        transform: translateX(-5px);
    }

    40% {
        transform: translateX(5px);
    }

    60% {
        transform: translateX(-3px);
    }

    80% {
        transform: translateX(3px);
    }
}

.dialog-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(8px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.dialog-card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 32px;
    padding: 2rem 2rem 2rem 2rem;
    width: 90%;
    max-width: 420px;
    box-shadow:
        0 25px 50px -12px rgba(0, 0, 0, 0.25),
        0 0 0 1px rgba(255, 255, 255, 0.5) inset;
    position: relative;
    color: #1e293b;
}

.close-btn {
    position: absolute;
    top: 1rem;
    right: 1rem;
    background: rgba(0, 0, 0, 0.05);
    border: none;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #64748b;
    cursor: pointer;
    transition: all 0.2s;
}

.close-btn:hover {
    background: rgba(0, 0, 0, 0.1);
    color: #0f172a;
    transform: rotate(90deg);
}

.header {
    text-align: center;
    margin-bottom: 2rem;
}

.logo-wrapper {
    display: inline-flex;
    padding: 12px;
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    border-radius: 24px;
    margin-bottom: 1rem;
    box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.2);
}

.logo-icon {
    width: 32px;
    height: 32px;
    color: white;
}

h3 {
    margin: 0;
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #1e293b, #0f172a);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.subtitle {
    margin: 0.5rem 0 0;
    color: #64748b;
    font-size: 0.9rem;
}

.form {
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
}

.form-group {
    position: relative;
    transition: all 0.2s;
}

.form-group.focused .input-icon {
    color: #3b82f6;
}

.input-icon {
    position: absolute;
    left: 14px;
    top: 50%;
    transform: translateY(-50%);
    width: 18px;
    height: 18px;
    color: #94a3b8;
    transition: color 0.2s;
    pointer-events: none;
}

.form-group input {
    width: 100%;
    padding: 0.9rem 1rem 0.9rem 2.8rem;
    border: 2px solid #e2e8f0;
    border-radius: 18px;
    font-size: 1rem;
    background: white;
    transition:
        border-color 0.2s,
        box-shadow 0.2s;
    outline: none;
}

.form-group.focused input {
    border-color: #3b82f6;
    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.15);
}

.submit-btn {
    position: relative;
    width: 100%;
    padding: 0.9rem;
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: white;
    border: none;
    border-radius: 18px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    overflow: hidden;
    transition: all 0.2s;
    margin-top: 0.5rem;
}

.submit-btn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px -10px #3b82f6;
}

.submit-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.loader {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    border-top-color: white;
    animation: spin 0.8s linear infinite;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

.error-message {
    display: flex;
    align-items: center;
    gap: 6px;
    justify-content: center;
    color: #dc2626;
    font-size: 0.85rem;
    background: #fee2e2;
    padding: 0.5rem 1rem;
    border-radius: 30px;
    margin-top: -0.5rem;
}

.switch-mode {
    margin-top: 1.5rem;
    text-align: center;
}

.switch-mode a {
    color: #64748b;
    text-decoration: none;
    font-size: 0.95rem;
    transition: color 0.2s;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.switch-mode a:hover {
    color: #3b82f6;
}

.highlight {
    color: #3b82f6;
    font-weight: 600;
}
</style>
