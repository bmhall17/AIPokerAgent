class OpponentModel:
    def __init__(self, uuid):
        self.uuid = uuid
        self.reset_opponent()

    def reset_opponent(self):
        self.opponent_name = "Player2"
        self.history = []
        self.aggression_factor = 1.0
        self.tightness_factor = 1.0
        self.bluff_factor = 0.1
        self.learning_rate = 0.1
        self.last_action = None
        self.opponent_stats = {
            'raises': 0,
            'calls': 0,
            'folds': 0,
            'bluffs': 0,
            'total_hands': 0,
            'preflop_raises': 0,
            'postflop_raises': 0,
            'preflop_calls': 0,
            'postflop_calls': 0,
        }
        self.opp_counts = {'fold': 0, 'call': 0, 'raise': 0}

    def observe_action(self, stage, action, is_bluff=False):
        self.opponent_stats['total_hands'] += 1
        if action == "raise":
            self.opponent_stats['raises'] += 1
            if stage == "preflop":
                self.opponent_stats['preflop_raises'] += 1
            else:
                self.opponent_stats['postflop_raises'] += 1
        elif action == "call":
            self.opponent_stats['calls'] += 1
            if stage == "preflop":
                self.opponent_stats['preflop_calls'] += 1
            else:
                self.opponent_stats['postflop_calls'] += 1
        elif action == "fold":
            self.opponent_stats['folds'] += 1
        if is_bluff:
            self.opponent_stats['bluffs'] += 1

        self.history.append((stage, action, is_bluff))
        self.update_model()

    def update_model(self):
        raise_rate = self.opponent_stats['raises'] / max(1, self.opponent_stats['total_hands'])
        call_rate = self.opponent_stats['calls'] / max(1, self.opponent_stats['total_hands'])
        fold_rate = self.opponent_stats['folds'] / max(1, self.opponent_stats['total_hands'])
        bluff_rate = self.opponent_stats['bluffs'] / max(1, self.opponent_stats['total_hands'])

        self.aggression_factor = raise_rate / max(0.01, call_rate)
        self.tightness_factor = fold_rate
        self.bluff_factor = bluff_rate

    def estimate_opponent_action(self, stage, pot_odds):
        """
        Predict opponent's next action based on learned behavior.
        """
        if self.bluff_factor > 0.3 and pot_odds < 0.3:
            return "raise"
        if self.aggression_factor > 1.5:
            if pot_odds < 0.5:
                return "raise"
            else:
                return "call"
        elif self.tightness_factor > 0.5:
            if pot_odds > 0.7:
                return "fold"
            else:
                return "call"
        return "call"

    def decide_if_bluff(self, hand_strength):
        if hand_strength < 0.2 and self.opponent_stats['total_hands'] > 20:
            if self.aggression_factor < 1.0 and self.tightness_factor < 0.3:
                return True
        return False

    def get_opponent_profile(self):
        return {
            "aggression": self.aggression_factor,
            "tightness": self.tightness_factor,
            "bluff": self.bluff_factor
        }

    def simulate_learning_round(self, rounds):
        for _ in range(rounds):
            stage = "preflop" if _ % 2 == 0 else "postflop"
            action = self.simulate_opponent_action(stage)
            is_bluff = self.random_bluff_chance()
            self.observe_action(stage, action, is_bluff)

    def simulate_opponent_action(self, stage):
        import random
        chance = random.random()
        if self.aggression_factor > 1.5 and chance < 0.5:
            return "raise"
        elif chance < 0.8:
            return "call"
        else:
            return "fold"

    def random_bluff_chance(self):
        import random
        return random.random() < 0.1

    def reset_history(self):
        self.history = []

    def get_recent_history(self, n=5):
        return self.history[-n:]

    def update_after_hand(self, final_hand_strength):
        """
        Adjusts bluff detection and aggression learning based on showdown results.
        """
        if self.last_action == "raise" and final_hand_strength < 0.3:
            self.opponent_stats['bluffs'] += 1
        self.update_model()

    def update_opponent_actions(self, round_state):
        #track all opponent actions
        for street, acts in round_state.get('action_histories', {}).items():
            for act in acts:
                player_str = act.get('player', '')
                #skip our own actions
                if self.uuid in player_str:
                    continue
                a = act.get('action', '').lower()
                if a in self.opp_counts:
                    self.opp_counts[a] += 1

        #determine opponent's style based on actions wether its passive or agressibe 
        opp_style = 'aggressive' if self.opp_counts['raise'] > self.opp_counts['call'] else 'passive'
        return opp_style
