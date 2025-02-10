import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  withCredentials: true
});

// 登录请求
export const login = async (credentials) => {
  try {
    const response = await api.post('/login', credentials);
    return response.data;
  } catch (error) {
    throw error.response?.data || { message: '网络错误' };
  }
};

// 注册请求
export const register = async (userData) => {
  try {
    const response = await api.post('/register', userData);
    return response.data;
  } catch (error) {
    throw error.response?.data || { message: '网络错误' };
  }
};

// 退出登录请求
export const logout = async () => {
  try {
    const response = await api.post('/logout');
    return response.data;
  } catch (error) {
    throw error.response?.data || { message: '网络错误' };
  }
};

// 设置请求拦截器
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 获取天气信息
export const getWeather = async () => {
  try {
    const response = await api.get('/weather');
    return response.data;
  } catch (error) {
    throw error.response?.data || { message: '获取天气信息失败' };
  }
}; 