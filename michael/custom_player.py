import pickle
import random
from pypokerengine.players import BasePokerPlayer
from abstraction import get_infoset_key


DEFAULT_STRATEGY_FILE = "mccfr_checkpoint_4000_converted.pkl"
INTERNAL_ACTION_MAP = { 0: "fold", 1: "call", 2: "raise" }
ACTION_MAP = {
    "fold": 'f', "call": 'c', "check": 'c', "raise": 'r',
    "SMALLBLIND": None, "BIGBLIND": None
}

class CustomPlayer(BasePokerPlayer):
    def __init__(self, strategy_file=DEFAULT_STRATEGY_FILE):
        self.strategy_map = None
        with open(strategy_file, 'rb') as f:
            self.strategy_map = pickle.load(f)

    def format_card(self, card):
        suit_in = card[0].lower()
        rank_in = card[1].upper()
        return f"{rank_in}{suit_in}"

    def format_card_list(self, card_list):
        return [self.format_card(card) for card in card_list]

    def get_history(self, street_history):
        history = []
        raises = 0
        for actions in street_history:
            action = actions.get('action', '').upper()
            action = ACTION_MAP.get(action)
            if action:
                history.append(action)
                if action == 'r':
                    raises += 1
        return "".join(history), raises

    def declare_action(self, valid_actions, hole_card, round_state):
        street = round_state['street']
        community_cards = round_state['community_card']
        community_cards_abstraction = self.format_card_list(community_cards)
        hole_card_abstraction = self.format_card_list(hole_card)

        street_history = round_state['action_histories'].get(street, [])
        betting_history, num_raises = self.get_history(street_history)

        infoset_key = get_infoset_key(
            street=street,
            hole_card_str_list=hole_card_abstraction,
            community_card_str_list=community_cards_abstraction,
            betting_history=betting_history,
            num_raises_street=num_raises
        )

        action_probabilities = None
        if self.strategy_map is not None:
            action_probabilities = self.strategy_map.get(infoset_key)

        chosen_action = None

        if action_probabilities:
            valid_internal_actions = []
            actions_available = {a['action'] for a in valid_actions}

            if 'fold' in actions_available:
                valid_internal_actions.append(0)
            if 'call' in actions_available or 'check' in actions_available:
                valid_internal_actions.append(1)
            if 'raise' in actions_available:
                valid_internal_actions.append(2)

            filtered_probs = []
            for i in range(len(INTERNAL_ACTION_MAP)):
                if i in valid_internal_actions and 0 <= i < len(action_probabilities):
                    filtered_probs.append(action_probabilities[i])
                else:
                    filtered_probs.append(0.0)

            total_prob = sum(filtered_probs)

            final_probs = [p / total_prob for p in filtered_probs]
            action_indices = list(range(len(INTERNAL_ACTION_MAP)))
            chosen_action = random.choices(action_indices, weights=final_probs, k=1)[0]


        else:
            return self.fallback(valid_actions)

        if chosen_action is None:
             return self.fallback(valid_actions)

        chosen_action = INTERNAL_ACTION_MAP.get(chosen_action)

        if chosen_action == "fold":
            out = None
            for item in valid_actions:
                if item["action"] == "fold":
                    out = item
                    break
            if out:
                return out['action']#, out['amount']
        elif chosen_action == "call":
            out = None
            for item in valid_actions:
                if item["action"] == "call":
                    out = item
                    break
            if not out:
                for item in valid_actions:
                    if item["action"] == "check":
                        out = item
                        break
            if out:
                return out['action']#, out['amount']
        elif chosen_action == "raise":
            out = None
            for item in valid_actions:
                if item["action"] == "raise":
                    out = item
                    break
            if out:
                #amount = out['amount']['min']
                #amount = min(amount, out['amount']['max'])
                return out['action']#, amount

        return self.fallback(valid_actions)


    def fallback(self, valid_actions):
        check = None
        call = None
        fold = None

        for a in valid_actions:
            if a["action"] == "check":
                check = a
            elif a["action"] == "call":
                call = a
            elif a["action"] == "fold":
                fold = a

        if check:
            return check["action"]#, check["amount"]
        if call:
            return call["action"]#, call["amount"]
        if fold:
            return fold["action"]#, fold["amount"]

        return ("fold", 0)
      

    def receive_game_start_message(self, game_info): pass
    def receive_round_start_message(self, round_count, hole_card, seats): pass
    def receive_street_start_message(self, street, round_state): pass
    def receive_game_update_message(self, action, round_state): pass
    def receive_round_result_message(self, winners, hand_info, round_state): pass

def setup_ai():
    return CustomPlayer()