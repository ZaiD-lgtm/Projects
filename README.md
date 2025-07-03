Reinforcement Learning: In this project the goal is to train a tag-game model using reinforcement learning.
In this I have trained the chaser and the goal of the chaser  is to maximise the reward or to maximise the score in a round of 1000 steps.
The training is done in three phases- without obstacles, with obstacles by passing the coordinates of all the randomly generated obstacles, with obstacles but lidar is used to detect the obstacles without giving direct coordinates of obstacles to create a real life scenario. where it learned to maximize captures, achieving an average score of ~500 per 1000 steps without obstacles.The experience replay buffer of size 10000 steps is used.

