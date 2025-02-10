require('dotenv').config();
const express = require('express');
const mysql = require('mysql2/promise');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const cors = require('cors');
const axios = require('axios');

const app = express();
app.use(express.json());
app.use(cors({
  origin: 'http://localhost:5173', // 前端地址
  credentials: true
}));

// 数据库配置
const pool = mysql.createPool({
  host: 'localhost',
  user: 'root',
  password: '010813',
  database: 'depthq',
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
});

// 登录接口
app.post('/api/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    
    // 查询用户
    const [rows] = await pool.query(
      'SELECT * FROM users WHERE username = ?', 
      [username]
    );
    
    if (rows.length === 0) {
      return res.status(401).json({ code: 401, message: '用户不存在' });
    }

    const user = rows[0];
    
    // 验证密码
    const valid = await bcrypt.compare(password, user.password);
    if (!valid) {
      return res.status(401).json({ code: 401, message: '密码错误' });
    }

    // 生成JWT
    const token = jwt.sign(
      { userId: user.id },
      process.env.JWT_SECRET || 'your_secret_key',
      { expiresIn: '2h' }
    );

    res.json({ 
      code: 200, 
      data: {
        token,
        username: user.username
      }
    });
    
  } catch (error) {
    console.error('登录错误:', error);
    res.status(500).json({ code: 500, message: '服务器错误' });
  }
});

// 注册接口
app.post('/api/register', async (req, res) => {
  try {
    const { username, password } = req.body;

    // 检查用户名是否已存在
    const [existingUsers] = await pool.query(
      'SELECT * FROM users WHERE username = ?',
      [username]
    );

    if (existingUsers.length > 0) {
      return res.status(400).json({ code: 400, message: '用户名已存在' });
    }

    // 密码加密
    const hashedPassword = await bcrypt.hash(password, 10);

    // 插入新用户
    await pool.query(
      'INSERT INTO users (username, password) VALUES (?, ?)',
      [username, hashedPassword]
    );

    res.json({ code: 200, message: '注册成功' });
    
  } catch (error) {
    console.error('注册错误:', error);
    res.status(500).json({ code: 500, message: '服务器错误' });
  }
});

// 退出登录接口
app.post('/api/logout', (req, res) => {
  try {
    // 由于使用的是JWT，服务器端不需要维护session
    // 只需要返回成功状态即可，前端会清除token
    res.json({ 
      code: 200, 
      message: '退出成功' 
    });
  } catch (error) {
    console.error('退出错误:', error);
    res.status(500).json({ code: 500, message: '服务器错误' });
  }
});

// 天气接口
app.get('/api/weather', async (req, res) => {
  try {
    const response = await axios.get(`https://api.openweathermap.org/data/2.5/weather`, {
      params: {
        q: 'Guangzhou',
        appid: '93625251f33ce2e39dea5a9f1e110c92',
        units: 'metric' // 使用摄氏度
      }
    });

    const weatherData = {
      temp: response.data.main.temp,
      humidity: response.data.main.humidity,
      windSpeed: response.data.wind.speed,
      rain: response.data.rain ? response.data.rain['1h'] || 0 : 0
    };

    res.json({
      code: 200,
      data: weatherData
    });
  } catch (error) {
    console.error('获取天气信息失败:', error);
    res.status(500).json({
      code: 500,
      message: '获取天气信息失败'
    });
  }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
}); 