from pypokerengine.players import BasePokerPlayer
import random as random
from sub.q_learning.q_learning_helpers import extract_state, get_q_table

class OurPlayer(BasePokerPlayer):

    
    # 1) Abstraction (Pocket-pair override)
  
    def declare_action(self, valid_actions, hole_card, round_state):
        """
        1) Mini‐abstraction: pocket pairs always raise
        2) Tiny opponent model: track fold/call/raise counts
           → penalize raises if opponent is very aggressive
        3) Fall back to Q‐table as before
        """

        # --- Pocket-pair override ---
        # Handle hole_card entries that may be strings like "H4" or dicts with 'rank'
        ranks = []
        for c in hole_card:
            if isinstance(c, str):
                # e.g. "H4" → rank = "4", or "DT" → rank = "T"
                ranks.append(c[1:])
            else:
                ranks.append(c.get('rank'))
        # If pocket pair, always raise if possible
        if len(ranks) == 2 and ranks[0] == ranks[1]:
            for opt in valid_actions:
                if opt['action'] == 'raise':
                    return 'raise'

        
        # 2) Opponent Modeling
        
        # Initialize opponent action counts (fold, call, raise) when first called
        if not hasattr(self, 'opp_counts'):
            self.opp_counts = {'fold': 0, 'call': 0, 'raise': 0}
        
        # Track all opponent actions so far
        for street, acts in round_state.get('action_histories', {}).items():
            for act in acts:
                player_str = act.get('player', '')
                # Skip our own actions
                if self.uuid in player_str:
                    continue
                a = act.get('action', '').lower()
                if a in self.opp_counts:
                    self.opp_counts[a] += 1
        
        # Determine opponent's style based on actions (aggressive or passive)
        opp_style = 'aggressive' if self.opp_counts['raise'] > self.opp_counts['call'] else 'passive'

        
        # 3) Q-Table Fallback
        # Get the state from the current round and hole cards
        state = extract_state(self, hole_card, round_state)
        possible_actions = [a["action"] for a in valid_actions]
        
        # Retrieve the Q-table and get the Q-values for the current state
        q_values = get_q_table()
        q_vals = q_values.get(state, {})

        # Adjust Q-values if the opponent is aggressive
        if opp_style == 'aggressive':
            q_vals = {
                act: (val - 0.05 if act == 'raise' else val)
                for act, val in q_vals.items()
            }

        # 4) Action Selection
        # Pick the highest-valued action (with random tie-breaking)
        max_q = max(q_vals.get(a, 0.0) for a in possible_actions)
        best = [a for a in possible_actions if q_vals.get(a, 0.0) == max_q]
        
        # Return the action with the highest Q-value (random tie-breaking)
        return random.choice(best)


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


# 5) Setup AI: Initialize and return the custom poker player

def setup_ai():
    return OurPlayer()
