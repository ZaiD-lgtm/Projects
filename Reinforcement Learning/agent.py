import torch
import numpy as np
import pygame
import create_env
import math
import imageio

record_video = False
video_filename = "chaser_model_without_obs.mp4"

def max_possible_distance(env):
    return math.sqrt((env.screen_width)**2 + (env.screen_height)**2)

def state_to_array(state, env):
    array = [
        (state['target_x'] / env.screen_width),(state['target_y'] / env.screen_height),(state['chaser_x'] / env.screen_width),(state['chaser_y'] / env.screen_height),(state['target_dx'] / env.screen_width),(state['target_dy'] / env.screen_height),(state['distance'] / max_possible_distance(env)),(state['chaser_speed'] / env.max_chaser_speed),((state['chaser_x'] - state['target_x']) / env.screen_width),((state['chaser_y'] - state['target_y']) / env.screen_height)]
    return array

class deep_QN(torch.nn.Module):
    def __init__(self, state_size, action_size):
        super(deep_QN, self).__init__()
        self.fc1 = torch.nn.Linear(state_size, 128)
        self.fc2 = torch.nn.Linear(128, 64)
        self.fc3 = torch.nn.Linear(64, action_size)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)
env = create_env.ChaseEnvironment()
screen = env.render()
clock = pygame.time.Clock()
action_size = 6
state_size = 10

model = deep_QN(state_size, action_size)
# checkpoint = torch.load("chaser_model_ep2000.pth")
checkpoint = torch.load("chaser_model.pth")
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

num_episodes = 5
max_steps = 1000
ep_score = []

for episode in range(num_episodes):
    raw_state = env.reset()
    state = np.array(state_to_array(raw_state, env))
    done = False
    steps = 0
    frames = []  # To store frames for video

    while not done and steps < max_steps:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                pygame.quit()
                exit()

        state_tensor = torch.FloatTensor(state).unsqueeze(0)  # [1, state_size]
        with torch.no_grad():
            action = torch.argmax(model(state_tensor)).item()

        raw_next_state, reward, done = env.step(action)
        state = np.array(state_to_array(raw_next_state, env))

        env.update_screen(screen)
        pygame.display.flip()
        #recording only first episode
        if record_video and episode == 0:
            frame = pygame.surfarray.array3d(screen)
            frame = np.transpose(frame, (1, 0, 2))
            frames.append(frame)

        clock.tick(60)
        steps += 1

    ep_score.append(env.score)
    print(f"episode: {episode + 1} || Score: {env.score}")
    print()

    if record_video and episode == 0:
        imageio.mimsave(video_filename, frames, fps=30)
        print(f"Saved episode video to {video_filename}")

print(f"average score in {num_episodes} episodes: {sum(ep_score) / len(ep_score)}")
pygame.quit()



