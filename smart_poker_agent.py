from pypokerengine.players import BasePokerPlayer
import random

class SmartPokerAgent(BasePokerPlayer):
    def declare_action(self, valid_actions, hole_card, round_state):
        """
        This method selects an action based on:
        1. **Mini-abstraction**: Recognizes pocket pairs and strong combos.
        2. **Opponent Modeling**: Tracks fold/call/raise actions and detects aggression.
        3. **Fallback**: Picks random valid action if nothing else triggers.
        """

        # --- 1. Mini-Abstraction (Pocket Pairs + High Card Combo) ---
        ranks = []
        for c in hole_card:
            if isinstance(c, str):
                ranks.append(c[1:])
            else:
                ranks.append(c.get('rank'))

        strong_ranks = {'A', 'K', 'Q'}
        is_pocket_pair = (ranks[0] == ranks[1])
        is_strong_combo = (ranks[0] in strong_ranks and ranks[1] in strong_ranks)

        if is_pocket_pair:
            # Always raise pocket pairs if allowed
            for act in valid_actions:
                if act['action'] == 'raise':
                    return 'raise', act['amount']
        
        # --- 2. Opponent Modeling: Track Actions ---
        if not hasattr(self, 'opp_counts'):
            self.opp_counts = {'fold': 0, 'call': 0, 'raise': 0}

        for street, actions in round_state.get('action_histories', {}).items():
            for action in actions:
                if action.get('player') == self.uuid:
                    continue  # Skip own actions
                opp_action = action.get('action', '').lower()
                if opp_action in self.opp_counts:
                    self.opp_counts[opp_action] += 1

        # Analyze opponent tendencies
        total = sum(self.opp_counts.values())
        raise_ratio = self.opp_counts['raise'] / total if total > 0 else 0

        # --- 3. Counter Hyper-Aggressive Opponent (Raise > 70%) ---
        if raise_ratio > 0.7:
            # Tighten play: fold weak hands
            if not (is_pocket_pair or is_strong_combo):
                for act in valid_actions:
                    if act['action'] == 'fold':
                        return 'fold', act['amount']
            else:
                # Trap: call with strong hands, don’t scare them off
                for act in valid_actions:
                    if act['action'] == 'call':
                        return 'call', act['amount']

        # --- 4. Random Fallback (when no rule triggers) ---
        return random.choice([(a['action'], a['amount']) for a in valid_actions])

    def receive_game_start_message(self, game_info): pass
    def receive_round_start_message(self, round_count, hole_card, seats): pass
    def receive_street_start_message(self, street, round_state): pass
    def receive_game_update_message(self, action, round_state): pass
    def receive_round_result_message(self, winners, hand_info, round_state): pass

def setup_ai():
    return SmartPokerAgent()
