<template>
  <div class="login-container">
    <div class="login-box">
      <h2>智慧灌溉系统</h2>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="登录" name="login">
          <el-form :model="loginForm" @submit.prevent="handleLogin">
            <el-form-item>
              <el-input 
                v-model="loginForm.username" 
                placeholder="用户名"
                prefix-icon="User">
              </el-input>
            </el-form-item>
            <el-form-item>
              <el-input 
                v-model="loginForm.password" 
                type="password" 
                placeholder="密码"
                prefix-icon="Lock"
                show-password>
              </el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleLogin" style="width: 100%">登录</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="注册" name="register">
          <el-form 
            :model="registerForm" 
            :rules="rules"
            ref="registerFormRef"
            @submit.prevent="handleRegister">
            <el-form-item prop="username">
              <el-input 
                v-model="registerForm.username" 
                placeholder="用户名"
                prefix-icon="User">
              </el-input>
            </el-form-item>
            <el-form-item prop="password">
              <el-input 
                v-model="registerForm.password" 
                type="password" 
                placeholder="密码"
                prefix-icon="Lock"
                show-password>
              </el-input>
            </el-form-item>
            <el-form-item prop="confirmPassword">
              <el-input 
                v-model="registerForm.confirmPassword" 
                type="password" 
                placeholder="确认密码"
                prefix-icon="Lock"
                show-password>
              </el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleRegister" style="width: 100%">注册</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { login, register } from '../api';

const router = useRouter();
const activeTab = ref('login');
const registerFormRef = ref(null);

// 登录表单
const loginForm = ref({
  username: '',
  password: ''
});

// 注册表单
const registerForm = ref({
  username: '',
  password: '',
  confirmPassword: ''
});

// 表单验证规则
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在3到20个字符之间', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在6到20个字符之间', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.value.password) {
          callback(new Error('两次输入的密码不一致'));
        } else {
          callback();
        }
      },
      trigger: 'blur'
    }
  ]
};

// 登录处理
const handleLogin = async () => {
  try {
    const { username, password } = loginForm.value;
    if (!username || !password) {
      return ElMessage.warning('请输入用户名和密码');
    }
    
    const res = await login({ username, password });
    if (res.code === 200) {
      localStorage.setItem('token', res.data.token);
      localStorage.setItem('username', res.data.username);
      ElMessage.success('登录成功');
      router.push('/dashboard');
    }
  } catch (error) {
    ElMessage.error(error.message || '登录失败');
  }
};

// 注册处理
const handleRegister = async () => {
  if (!registerFormRef.value) return;
  
  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const { username, password } = registerForm.value;
        const res = await register({ username, password });
        if (res.code === 200) {
          ElMessage.success('注册成功，请登录');
          activeTab.value = 'login';
          registerForm.value = {
            username: '',
            password: '',
            confirmPassword: ''
          };
        }
      } catch (error) {
        ElMessage.error(error.message || '注册失败');
      }
    }
  });
};
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f5f5;
}

.login-box {
  width: 350px;
  padding: 30px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
}
</style> 