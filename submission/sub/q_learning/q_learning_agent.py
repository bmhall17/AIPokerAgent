from pypokerengine.players import BasePokerPlayer
import random as random
from sub.q_learning.q_learning_helpers import extract_state, get_q_table

class QLearnPlayer(BasePokerPlayer):

  def declare_action(self, valid_actions, hole_card, round_state):
    """
    Identifies the current state, its possible actions, and the respective q_values for the pairing,
    before selecting the best action (maximal q_value). It breaks ties at random and then returns
    the player's action.

    Arguments:
        valid_actions: contains the possible actions the player can take in the given instance.
        hole_card: provides the pairings for the cards that our player holds
        round_state: provides information pertaining to the current round

    Returns:
        action: action ("fold", "call", or "raise") possessing the maximal q_value for the given
        state and action
    """
    # identify the state and action spaces and retrieve the q-value table
    state = extract_state(self, hole_card, round_state)
    possible_actions = [a["action"] for a in valid_actions]
    q_values = get_q_table()

    # isolate the q_values for each action and then randomly select one of the actions with the max q value
    q_vals = q_values.get(state, {})
    max_q_value = max(q_vals.get(action, 0.0) for action in possible_actions)
    best_actions = [a for a in possible_actions if q_vals.get(a, 0.0) == max_q_value]
    action = random.choice(best_actions)

    return action

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
  return QLearnPlayer()