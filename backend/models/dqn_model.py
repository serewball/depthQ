import numpy as np
from collections import deque
import random
import tensorflow as tf

class DQNAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size  # 状态空间维度 (温度,湿度,降雨量,土壤养分等)
        self.action_size = action_size  # 动作空间大小 (灌溉量的不同级别)
        self.memory = deque(maxlen=2000)  # 经验回放缓冲区
        self.gamma = 0.95  # 折扣因子
        self.epsilon = 1.0  # 探索率
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.update_target_network()

    def _build_model(self):
        """构建神经网络模型"""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(24, input_dim=self.state_size, activation='relu'),
            tf.keras.layers.Dense(24, activation='relu'),
            tf.keras.layers.Dense(self.action_size, activation='linear')
        ])
        model.compile(loss='mse', optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate))
        return model

    def update_target_network(self):
        """更新目标网络"""
        self.target_model.set_weights(self.model.get_weights())

    def get_state(self, weather_data, crop_info):
        """构建状态向量"""
        return np.array([
            weather_data['main']['temp'],  # 当前温度
            weather_data['main']['humidity'],  # 当前湿度
            weather_data.get('rain', {}).get('1h', 0) * 24,  # 日降雨量
            abs(weather_data['main']['temp'] - crop_info['Temperature']),  # 与最佳温度的差距
            abs(weather_data['main']['humidity'] - crop_info['Humidity']),  # 与最佳湿度的差距
            abs(weather_data.get('rain', {}).get('1h', 0) * 24 - crop_info['Rainfall'] / 365)  # 与最佳日降水量的差距
        ])

    def get_action(self, state):
        """选择动作"""
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        state = np.reshape(state, [1, self.state_size])
        q_values = self.model.predict(state, verbose=0)
        return np.argmax(q_values[0])

    def remember(self, state, action, reward, next_state, done):
        """存储经验"""
        self.memory.append((state, action, reward, next_state, done))

    def train(self, batch_size=32):
        """训练模型"""
        if len(self.memory) < batch_size:
            return
        
        minibatch = random.sample(self.memory, batch_size)
        states = np.array([i[0] for i in minibatch])
        actions = np.array([i[1] for i in minibatch])
        rewards = np.array([i[2] for i in minibatch])
        next_states = np.array([i[3] for i in minibatch])
        dones = np.array([i[4] for i in minibatch])

        states = np.squeeze(states)
        next_states = np.squeeze(next_states)

        targets = self.model.predict(states, verbose=0)
        next_q_values = self.target_model.predict(next_states, verbose=0)

        for i in range(batch_size):
            if dones[i]:
                targets[i][actions[i]] = rewards[i]
            else:
                targets[i][actions[i]] = rewards[i] + self.gamma * np.amax(next_q_values[i])

        self.model.fit(states, targets, epochs=1, verbose=0)
        
        # 更新探索率
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay 