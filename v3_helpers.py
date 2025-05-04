import pickle
from collections import Counter
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate
import os


def extract_state(self, hole_card, round_state):
  """
  Extract the relevant information quantifying a given state (street, strength of player hand, pot, opponent aggressiveness).
  All these are normalized in some fashion before being returned. With the player hand reflecting
  both the hole cards and the communitee cards using pypoker engine functionality (Monte Carlo simulations),
  and pot being the relative size of the round pot relative to the player's current hand.
  
  Arguments:
    hole_card: player's current hand
    round_state: information pertaining to the round
    
  Returns:
    (street, round(strength, 1), pot_bucket, raise_ratio): tuple containing the street (flop, preflop, turn, river), 
    the strength of cards (hole and community) the player is holding, the size of the pot normalized, and the ratio of
    raise actions by opponent out of their total actions (aggressiveness).
  """
  card_ranks = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, 
           '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
  rank_vals = []

  # leverage the built-in functionality within pypoker engine to evaluate hand strength using monte carlo simulations
  hole_card_obj = gen_cards(hole_card)
  community_card_obj = gen_cards(round_state["community_card"])
  win_rate = estimate_hole_card_win_rate(
      nb_simulation=100,
      nb_player=2,
      hole_card=hole_card_obj,
      community_card=community_card_obj
  )

  # break the hand strength into buckets
  strength_bucket = round(win_rate, 1)

  # identify the current street, pot, and our player's id/seat
  street = round_state["street"]
  pot = round_state["pot"]["main"]["amount"]
  player_id = self.uuid
  players = round_state['seats']
  wallet = None

  # provide a normalization of the current pot with respect to the players wallet (stack),
  # first step identify our player's wallet
  for player in players:
    if player['uuid'] == player_id:
        wallet = player['stack']
        break
  
  # covering case where wallet = 0 and division will cause error and cap it at 1
  if wallet and wallet > 0:
    pot_bucket = min(round(pot / wallet, 1), 1)
  else:
    pot_bucket = 1.0
        
  # incorporate opponent modeling to identify aggressive behaviors
  opp_counts = {'fold': 0, 'call': 0, 'raise': 0}

  for street, acts in round_state.get('action_histories', {}).items():
      for act in acts:
          player_str = act.get('player', '')
          if self.uuid in player_str:
              continue
          a = act.get('action', '').lower()
          if a in opp_counts:
              opp_counts[a] += 1

  # compute the ratio of raise actions to determine aggressiveness
  total_actions = sum(opp_counts.values()) or 1
  raise_ratio = round(opp_counts["raise"] / total_actions, 1)
  
  return (street, strength_bucket, pot_bucket, raise_ratio)

def get_q_table():
  """
  Leverages pickle to obtain the q_values that were generated and then saved during the training process.
  Incorporate measure to allow for non-local runs to properly retrieve q-values.
  
  Returns:
    q_values: returns the dictionary containing the q_values
  """
  curr_dir = os.path.dirname(__file__)
  q_values_path = os.path.join(curr_dir, "q_values_v3.pkl")

  with open(q_values_path, "rb") as f:
    q_values = pickle.load(f)

  return q_values