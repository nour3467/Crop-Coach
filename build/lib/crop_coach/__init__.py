
from gym.envs.registration import register

register(
    id="CropCoach-v0",
    entry_point="crop_coach.envs:WofostEnv"
)