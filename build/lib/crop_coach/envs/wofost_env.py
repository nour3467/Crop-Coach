import datetime
import os
from gym.utils import seeding
from gym import error, spaces, utils
import warnings
import shutup
from pprint import pprint
import time
import random
from datetime import date


# -- Importing dependencies :
import gym
from gym import spaces
import numpy as np

from crop_coach.envs.models import Wofost  #
from crop_coach.envs.actions import AgroActions
from crop_coach.envs.reward import calculate_reward

# import scienceplots
# plt.style.use("science")

# -- To add the external folders modules :
import sys

sys.path.append("..")

# -- Importing optional dependenciees :


shutup.please()




# -- To ignore deprecation warning

warnings.filterwarnings("ignore", category=DeprecationWarning)

# -- Gym Registration depending on the version :


# -------------- normalize and denormalize irrigation action (0.0, 20.0) -------------------
def normalize_irrigation_action(action):
    """Normalize the action from [low, high] to [-1, 1]"""
    low, high = 0.0, 20.0
    return 2.0 * ((action - low) / (high - low)) - 1.0


def denormalize_irrigation_action(action):
    """Denormalize the action from [-1, 1] to [low, high]"""
    low, high = 0.0, 20.0
    return low + (0.5 * (action + 1.0) * (high - low))


# -------------------------------------------------------------------------------------------

# -------------- normalize and denormalize fertilization actions (0.0, 200.0) -------------------
def normalize_fertilization_action(action):
    """Normalize the action from [low, high] to [-1, 1]"""
    low, high = 0.0, 200.0
    return 2.0 * ((action - low) / (high - low)) - 1.0


def denormalize_fertilization_action(action):
    """Denormalize the action from [-1, 1] to [low, high]"""
    low, high = 0.0, 200.0
    return low + (0.5 * (action + 1.0) * (high - low))


# -------------------------------------------------------------------------------------------

# -------------- normalize and denormalize frequencies  (0, 223) -------------------
def normalize_ferquencies_action(action, tot_days):
    """Normalize the action from [low, high] to [-1, 1]"""
    low, high = 0.0, tot_days
    return int(2.0 * ((action - low) / (high - low)) - 1.0)


def denormalize_frequencies_action(action, tot_days):
    """Denormalize the action from [-1, 1] to [low, high]"""
    low, high = 0.0, tot_days
    return int(low + (0.5 * (action + 1.0) * (high - low)))


# -------------------------------------------------------------------------------------------

# what region the following (latitude=51.97, longitude=5.67) corresponds to :
# https://www.latlong.net/place/arnhem-netherlands-103.html
# what region the following (latitude=33.0,longitude=9.0) corresponds to :
# https://www.latlong.net/place/tunisia-103.html


def demoralize_actions(actions_taken, tot_days):

    return np.array(
        [denormalize_irrigation_action(actions_taken[0])]
        + [
            denormalize_fertilization_action(actions_taken[index])
            for index in range(1, 4)
        ]
        + [
            denormalize_frequencies_action(actions_taken[index], tot_days)
            for index in range(4, 6)
        ]
    )



def calculate_days(start_date, end_date, year):
    # string to date :

    start_date = date(year, int(start_date.split("-")[1]), int(start_date.split("-")[2]))
    end_date = date(year, int(end_date.split("-")[1]), int(end_date.split("-")[2]))
    # print(f"\n---------------------- start_date :{start_date} ----------------------\n")
    # print(f"\n---------------------- end_date :{end_date} ----------------------\n")
    delta = end_date - start_date
    return delta.days


class WofostEnv(gym.Env):
    """Custom Environment that follows gym interface"""

    metadata = {"render.modes": ["human"]}


    @staticmethod
    def calculate_days(start_date, end_date, year):
        # string to date :

        start_date = date(year, int(start_date.split("-")[1]), int(start_date.split("-")[2]))
        end_date = date(year, int(end_date.split("-")[1]), int(end_date.split("-")[2]))
        # print(f"\n---------------------- start_date :{start_date} ----------------------\n")
        # print(f"\n---------------------- end_date :{end_date} ----------------------\n")
        delta = end_date - start_date
        return delta.days

    def __init__(
        self,
        files_paths=None,
        Agromanager_dict={
            "crop_name": "wheat","crop_variety": "Winter_wheat_101","campaign_start_date": "-01-01","crop_start_type":"emergence","emergence_date": "-04-11","crop_end_type": "harvest","harvest_date": "-08-11", "max_duration": 100
        },
        years_count=2,
        Costs_dict={"Irrigation": 150, "N": 8,
                    "P": 8.5, "K": 7, "Selling": 2.5},
        Discount_factors_dict={"Irrigation": 1, "N": 1, "P": 1, "K": 1},
        year=2019,
        sample_year=True,
        latitude: float = 51.97,
        longitude: float = 5.67,
        **kwargs
    ):
        """
        Initialization of the env : action and observation space

        """
        super(WofostEnv, self).__init__()

        self.info = {}

        self.files_paths = files_paths
        self.Agromanager_dict = Agromanager_dict



        self.sample_year = sample_year
        self.year = year
        self.years_count = years_count
        self.years_count_max = years_count
        self.Costs_dict = Costs_dict
        self.Discount_factors_dict = Discount_factors_dict
        self.seed = 0


        # -- Obsrevation space :
        # self.OUTPUT_VARS = [
        #     "DVS","LAI","TAGP", "TWSO", "TWLV", "TWST",
        #     "TWRT", "TRA", "RD", "SM", "WWLOW"
        # ]
        self.OUTPUT_VARS = [    'day',    'DVS',    'LAI',    'TAGP',    'TWSO',    'TWLV',    'TWST',    'TWRT',    'TRA',    'RD',    'SM',    'WWLOW',    'NNI',    'KNI',    'PNI',    'NPKI',    'NSOIL',    'PSOIL',    'KSOIL',    'NAVAIL',    'PAVAIL',    'KAVAIL',    'NDEMLV',    'NDEMRT',    'NDEMSO',    'NDEMST',    'PDEMLV',    'PDEMRT',    'PDEMSO',    'PDEMST',    'KDEMLV',    'KDEMRT',    'KDEMSO',    'KDEMST',    'RNUPTAKE',    'RPUPTAKE',    'RKUPTAKE',    'RNFIX',    'NTRANSLOCATABLE',    'PTRANSLOCATABLE',    'KTRANSLOCATABLE']


        # -- Mono-Action for now :
        self.n_actions = 6
        # -- Init the yield vector : state
        self.state = np.zeros(len(self.OUTPUT_VARS))

        self.crop_name = Agromanager_dict["crop_name"]
        self.crop_variety = Agromanager_dict["crop_variety"]

        # -- Init wofost and keep its parameters (for running wofost)
        params, wdp, config = Wofost.init_wofost(
            self.crop_name, self.crop_variety,files_paths, latitude, longitude, **kwargs
            )
        self.wofost_params = [params, wdp, config]

        # -- Irrigation amount :
        self.action_space = spaces.Box(
            low=np.array([-1, -1, -1, -1, -1, -1]),
            high=np.array([1, 1, 1, 1, 1, 1]),
            shape=(self.n_actions,),
            dtype="float32",
        )

        # -- yeild :
        self.observation_space = spaces.Box(
            low=0.0, high=np.inf, shape=self.state.shape, dtype="float32"
        )
        # -- avoid the problem with the monitor when the things are none :
        self.last_info = {}
        self.last_obs = None


    @staticmethod
    def sample_random_year():
        """
        Sample year from a non-stationary distribution
        """
        # get the current year :
        current_year = datetime.datetime.now().year
        random.seed(time.time())
        # list(range(1984, 2000)) + [2002] + list(range(2004, 2016)) +
        years_complete_weather = [2017, 2019] + list(range(2020, current_year-1))
        year = random.choice(years_complete_weather)

        # print(f"\n----------- year in sample_random year {year} ---------------\n")

        return year


    def step(self, action):
        """
        1. sample a year, and discount the years_count
        2. create action with the **action** irrigation amount, (fertilization_amount)
        # 3. run wofost and get the correspondent state variables (yield included),
        4. get the reward  (for now its the yield)
        """
        if self.sample_year :
            year = self.sample_random_year()
        else :
            year = self.year
        # -- sample a year with the full weather data :
        # year = self.sample_random_year()
        # year = self.year
        # print("years_count: ", self.years_count)

        # print(f"\n----------- year in step {year} ---------------\n")

        self.years_count -= 1

        # -- Create the action :
        irrigation_action = denormalize_irrigation_action(action[0])
        N_amount = denormalize_fertilization_action(action[1])
        P_amount = denormalize_fertilization_action(action[2])
        K_amount = denormalize_fertilization_action(action[3])
        irrigation_freq = denormalize_frequencies_action(action[4], self.calculate_days(self.Agromanager_dict["campaign_start_date"],self.Agromanager_dict["harvest_date"], self.year))
        fertilization_freq = denormalize_frequencies_action(action[5], self.calculate_days(self.Agromanager_dict["campaign_start_date"],self.Agromanager_dict["harvest_date"], self.year))

        # de_action = action
        # print(
        #     f"----------- de action in step : -------------\n{[irrigation_action, N_amount, P_amount, K_amount, irrigation_freq, fertilization_freq]}\n"
        # )
        # Add a parameter here that specifies the irrigation amount : our solo action for now
        # print(type(de_action[0]))
        self.actions, _ = AgroActions().create_actions(
            [irrigation_freq],
            [fertilization_freq],
            irrigation_amount=irrigation_action,
            N_amount=N_amount,
            P_amount=P_amount,
            K_amount=K_amount,
            year=year,
            Agromanager_dict=self.Agromanager_dict
        )

        # Run Wofost to obtain yield for each action : ** one action for now **
        # print(f"----------- action in run : {self.actions[0]} -------------\n")
        # print(f"----------- action in run : {demoralize_actions(self.actions[0])} -------------\n")
        # pprint(f"----------- len actions : {len(self.actions)} -------------\n")

        self.state, Yield = Wofost.run_wofost(
            self.actions[0], *self.wofost_params)

        # -- Modification Date and Hour : 30.08.2022 : 4.03
        # -- The Problem that needs a deep solution :
        self.reward = calculate_reward(
            Yield,
            irrigation_action,
            N_amount,
            P_amount,
            K_amount,
            Costs_dict=self.Costs_dict,
            Discount_factors_dict=self.Discount_factors_dict,
        )

        # pprint(f"----------- state in run : {self.state} -------------\n")

        info = {}

        # -- Implement done logic : Important :
        if self.years_count == 0:
            done = True
        else:
            done = False

        return self.state, self.reward, done, self.info

    def reset(self):
        """
        1. Reset the state,
        2. Reset the Simulation length
        """
        # -- Reset the state :
        self.state = np.zeros(len(self.OUTPUT_VARS))
        # -- Reset the years count :
        self.years_count = self.years_count_max

        return self.state  # reward, done, info can't be included

    def render(self, mode="human", close=False):
        """
        Implement a visualization
        """
        pass





    def close(self):
        """
        Close the env
        """
        pass


# # -- Test the env & print all values in RL loop :
# if __name__ == "__main__":

#     # get the curent dir :
#     current_dir = os.path.dirname(os.path.realpath(__file__)).replace("\\","/")
#     # -- Define the env :
#     env = WofostEnv(
#         latitude=51.97,
#         longitude=5.67,
#         years_count=1,
#         Costs_dict={"Irrigation": 150, "N": 8,
#                     "P": 8.5, "K": 7, "Selling": 2.5},
#         Discount_factors_dict={"Irrigation": 1, "N": 1, "P": 1, "K": 1},
#         year=2019,
#         sample_year=False,
#         files_paths={"soil":current_dir+"/default_data/soil.cab", "site":current_dir+"/default_data/site.cab", "crop":current_dir+"/default_data/crop.cab"},
        # Agromanager_dict={
        #     "crop_name": "wheat","crop_variety": "Winter_wheat_101","campaign_start_date": "-01-01","crop_start_type":"emergence","emergence_date": "-03-31","crop_end_type": "harvest","harvest_date": "-08-11", "max_duration": 300
        # },
#     )

#     # -- Test the env : the rewarding mecanism
#     episodes = 10
#     for episode in range(1, episodes + 1):
#         state = env.reset()
#         done = False
#         score = 0

#         while not done:
#             # env.render()
#             action = env.action_space.sample()
#             # action = np.array([1000])
#             print(f"----------- action : {action} -------------\n")
#             print(f"----------- denormalized action : {demoralize_actions(action, calculate_days(env.Agromanager_dict['campaign_start_date'],env.Agromanager_dict['harvest_date'], env.year))} -------------\n")

#             n_state, reward, done, info = env.step(action)
#             print(f"----------- done : {done} -------------\n")
#             print(f"----------- state : {n_state} -------------\n")
#             print(f"----------- reward : {reward} -------------\n")
#             score += reward

#         print(f"Episode --:{episode} Score --:{score}")
