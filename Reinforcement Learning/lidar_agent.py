from collections import deque
import numpy as np
import pygame
import time
import random
# import torch.nn as nn
# import torch.optim as optim
import math
# import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.optim as optim
import cv2  # for video saving
import lidar_env

def max_possible_distance(env):
    return math.sqrt((env.screen_width)**2 + (env.screen_height)**2)

def state_to_array(state, env):
    array = [
        (state['target_x'] / env.screen_width),(state['target_y'] / env.screen_height),(state['chaser_x'] / env.screen_width),(state['chaser_y'] / env.screen_height),(state['target_dx'] / env.screen_width),(state['target_dy'] / env.screen_height),(state['distance'] / max_possible_distance(env)),(state['chaser_speed'] / env.max_chaser_speed),((state['chaser_x'] - state['target_x']) / env.screen_width),((state['chaser_y'] - state['target_y']) / env.screen_height)
    ]
    lidar_readings = state['lidar_readings']
    return array+lidar_readings  # state_size = 10 + 8 = 18
class deep_QN(nn.Module):
    def __init__(self, state_size, action_size):
        super(deep_QN, self).__init__()
        self.fc1 = nn.Linear(state_size, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, action_size)
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)
class DQN_Chaser:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=10000)  ##from python-collection (type of list) used for fast append and popping
        self.epsilon = 1.0
        self.epsilon_min = 0.05
        self.epsilon_decay = 0.995
        self.discount = 0.95
        self.batch_size = 64
        self.learning_rate = 0.001
        self.update_frequency = 4
        self.target_update_frequency = 50
        self.steps = 0
        self.model = deep_QN(state_size, action_size)
        self.target_model = deep_QN(state_size, action_size)
        self.target_model.load_state_dict(self.model.state_dict())
        self.criterion = nn.MSELoss()

        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)

    def update_target_model(self):
        self.target_model.load_state_dict(self.model.state_dict())

    def epsilon_greedy(self, state):
        if np.random.rand() < self.epsilon:
            return random.randint(0, self.action_size - 1)
        else:
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            with torch.no_grad():
                act_values = self.model(state_tensor)
            return torch.argmax(act_values[0]).item()

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def replay(self, batch_size=64):
        if len(self.memory) < batch_size:
            return 0  # Return 0 if no training happened

        minibatch = random.sample(self.memory, batch_size)
        states = []
        targets = []

        for state, action, reward, next_state, done in minibatch:
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0)

            with torch.no_grad():
                if not done:
                    next_q_values = self.target_model(next_state_tensor)
                    target = reward + self.discount * torch.max(next_q_values).item()
                else:
                    target = reward

            current_q_values = self.model(state_tensor)
            target_f = current_q_values.clone()
            target_f[0][action] = target

            states.append(state)
            targets.append(target_f.squeeze().detach().numpy())

        states_tensor = torch.FloatTensor(np.array(states))
        targets_tensor = torch.FloatTensor(np.array(targets))

        self.optimizer.zero_grad()
        outputs = self.model(states_tensor)
        loss = self.criterion(outputs, targets_tensor)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)

        self.optimizer.step()


        # epsilon decay
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        return loss.item()

    def update_learning_rate(self, episode, total_episodes):
        if episode == int(total_episodes * 0.5):
            self.learning_rate *= 0.5
            self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
            print(f"reduced new learning rate: {self.learning_rate}")

    def save(self, file_path):
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'loss_history': self.loss_history
        }, file_path)
        print(f"saved to: {file_path}")
def train_agent(env, episodes=1500, max_steps_per_episode=1000, frequency=50, save_video=False):
    screen = env.render()
    clock = pygame.time.Clock()

    state_size = 18  # 10 + 8 lidar
    action_size = 6
    agent = DQN_Chaser(state_size, action_size)

    episode_rewards = []
    avg_rewards = []
    scores = []

    for i in range(episodes):
        raw_state = env.reset()
        state = np.array(state_to_array(raw_state, env))
        done = False
        total_reward = 0
        episode_loss = []
        print(f"episodes: {i + 1}/{episodes}, epsilon: {agent.epsilon}")
        pygame.event.get()
        steps = 0
        render_this_episode = (i % frequency == 0)
        if i == 0:
            print("State vector example:", state)
            print("State size:", len(state))
        while not done and steps < max_steps_per_episode:
            action = agent.epsilon_greedy(state)

            raw_next_state, reward, done = env.step(action)
            next_state = np.array(state_to_array(raw_next_state, env))

            agent.remember(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward
            steps += 1
            agent.steps += 1

            if agent.steps % agent.update_frequency == 0:
                loss = agent.replay(agent.batch_size)
                if loss:
                    episode_loss.append(loss)

            if agent.steps % agent.target_update_frequency == 0:
                agent.update_target_model()

            if render_this_episode or i >= episodes - 5:
                if steps % 2 == 0:
                    env.update_screen(screen)
                    clock.tick(60)
        agent.update_learning_rate(i, episodes)
        if (i + 1) % 1000 == 0:
            agent.save(f"chaser_model_ep.pth")
        episode_rewards.append(total_reward)
        scores.append(env.score)

        if len(episode_rewards) > 10:
            avg_rewards.append(np.mean(episode_rewards[-10:]))
            print(
                f"episode {i + 1}: score={env.score}, reward={total_reward}, avg reward (10ep)={avg_rewards[-1]}, steps={steps}")
        else:
            print(f"episode {i + 1}: score={env.score}, reward={total_reward}, steps={steps}")

        if episode_loss:
            avg_loss = np.mean(episode_loss)
            print(f"average loss: {avg_loss}")

env = lidar_env.ChaseEnvironment()
agent = train_agent(env, episodes=20000, frequency=50)