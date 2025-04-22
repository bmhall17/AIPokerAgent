from pypokerengine.players import BasePokerPlayer

class OpponentModel:
    def __init__(self):
        self.stats = {"aggressive": 0, "passive": 0, "total": 0}

    def update(self, action):
        if action in ["raise", "bet"]:
            self.stats["aggressive"] += 1
        elif action in ["call", "check"]:
            self.stats["passive"] += 1
        self.stats["total"] += 1

    def get_style(self):
        if self.stats["total"] == 0:
            return "unknown"
        ratio = self.stats["aggressive"] / self.stats["total"]
        return "aggressive" if ratio > 0.6 else "passive"

def get_hand_bucket(strength):
    bucket = int(strength * 10)
    return min(bucket, 9)

class AbstractionAgent(BasePokerPlayer):
    def __init__(self):
        self.opp_model = OpponentModel()

    def declare_action(self, valid_actions, hole_card, round_state):
        # Simple estimation
        strength = self._estimate_strength(hole_card)
        bucket = get_hand_bucket(strength)

        opp_action = round_state['action_histories'][round_state['street']][-1]['action']
        self.opp_model.update(opp_action)
        opp_style = self.opp_model.get_style()

        if bucket >= 7:
            return "raise", valid_actions[2]['amount']
        elif opp_style == "passive":
            return "call", valid_actions[1]['amount']
        else:
            return "fold", valid_actions[0]['amount']

    def _estimate_strength(self, hole_card):
        ranks = {"2":2, "3":3, "4":4, "5":5, "6":6, "7":7,
                 "8":8, "9":9, "T":10, "J":11, "Q":12, "K":13, "A":14}
        r1 = ranks[hole_card[0][0]]
        r2 = ranks[hole_card[1][0]]
        return (r1 + r2) / 28.0  # normalize between 0 and 1

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
