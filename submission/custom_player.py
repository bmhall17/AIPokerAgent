from pypokerengine.players import BasePokerPlayer
import random as random
from sub.custom_player_helper import get_majority_action

class CustomPlayer(BasePokerPlayer):

  def declare_action(self, valid_actions, hole_card, round_state):
    """
    Leverages three individual agents as an ensemble. By calling each of the three agents independently,
    taking the action declared by each one and then taking the majority and breaking ties by random.

    Arguments:
        valid_actions: contains the possible actions the player can take in the given instance.
        hole_card: provides the pairings for the cards that our player holds
        round_state: provides information pertaining to the current round

    Returns:
        action: action ("fold", "call", or "raise") that received the most "votes" from the agents (ties broken at random)
    """

    return get_majority_action(valid_actions, hole_card, round_state)

  def receive_game_start_message(self, game_info):
    pass

  def receive_round_start_message(self, round_count, hole_card, seats):
    pass

  def receive_street_start_message(self, street, round_state):
    pass

  def receive_game_update_message(self, action, round_state):
    pass

  def receive_round_result_message(self, winners, hand_info, round_state):
    pass

def setup_ai():
  return CustomPlayer()