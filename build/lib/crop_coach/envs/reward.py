

from typing import List, Tuple, Dict, Union, Optional


def calculate_reward(
    Yield: float,
    Irr_amount: Union[float, int],
    N_amount: Union[float, int],
    P_amount: Union[float, int],
    K_amount: Union[float, int],
    Costs_dict: dict,
    Discount_factors_dict: dict,
) -> float:
    """
    calculate reward, on each step

    ---------------------------------------------------------------------
    :param Yield : the yield of the crop
    :type Yield : float
    :param Irr_amount: Irrigation amount
    :type Irr_amount: Union[float, int]
    :param N_amount: Nitrogen amount
    :type N_amount: Union[float, int]
    :param P_amount: Phosphorus amount
    :type P_amount: Union[float, int]
    :param K_amount: Potassium amount
    :type K_amount: Union[float, int]
    :param Costs_dict: Costs of each action
    :type Costs_dict: dict
    :param Discount_factors_dict: Discount factors of each action (how much strong we penalize the agent for each action)
    :type Discount_factors_dict: dict
    """

    # -- Initialize discount factors :
    Irr_disc_factor = Discount_factors_dict["Irrigation"]
    N_disc_factor = Discount_factors_dict["N"]
    P_disc_factor = Discount_factors_dict["P"]
    K_disc_factor = Discount_factors_dict["K"]

    # -- Calculate reward :
    reward = Yield * Costs_dict["Selling"] - (
        Irr_disc_factor * Irr_amount * Costs_dict["Irrigation"]
        + N_disc_factor * N_amount * Costs_dict["N"]
        + P_disc_factor * P_amount * Costs_dict["P"]
        + K_disc_factor * K_amount * Costs_dict["K"]
    )

    return reward
