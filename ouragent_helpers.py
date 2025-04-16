import pickle

def extract_state(self, hole_card, round_state):
  """
  Extract the relevant information quantifying a given state (street, strength of player hand, pot).
  All these are normalized in some fashion before being returned. With the player hand only reflecting the 
  two cards they hold currently, and pot being the relative size of the round pot relative to the player's
  current hand.
  
  Arguments:
    hole_card: player's current hand
    round_state: information pertaining to the round
    
  Returns:
    (street, round(strength, 1), pot_bucket): tuple containing the street (flop, preflop, turn, river), 
    the strength of the two cards the player is holding, and the size of the pot normalized.
  """
  card_ranks = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, 
           '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
  rank_vals = []

  # gather the ranks for the player's hole cards
  for card in hole_card:
    rank_vals.append(card_ranks[card[1]])
  
  # normalize the strength out of the maximal combined rank
  strength = sum(rank_vals) / 28 

  # provide a bonus for cards with the same value or the same suit
  if hole_card[0][1] == hole_card[1][1]:
    strength += 0.2
  if hole_card[0][0] == hole_card[1][0]:
    strength += 0.1
  
  # cap strength at 1
  strength = min(strength, 1.0)

  street = round_state["street"]
  pot = round_state["pot"]["main"]["amount"]
  player_id = self.uuid
  players = round_state['seats']
  wallet = None

  # provide a normalization of the current pot with respect to the players stack
  for player in players:
    if player['uuid'] == player_id:
        wallet = player['stack']
        break
  
  # covering case where wallet = 0 and division will cause error and cap it at 1
  if wallet and wallet > 0:
    pot_bucket = min(round(pot / wallet, 1), 1)
  else:
    pot_bucket = 1.0
  
  return (street, round(strength, 1), pot_bucket)

def get_q_table():
  """
  Leverages pickle to obtain the q_values that were generated and then saved during the training process.
  
  Returns:
    q_values: returns the dictionary containing the q_values
  """
  with open("q_values.pkl", "rb") as f:
    q_values = pickle.load(f)
  
  return q_values