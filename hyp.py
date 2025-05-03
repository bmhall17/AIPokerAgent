from pypokerengine.players import BasePokerPlayer
import random
import copy

class HybridPlayer(BasePokerPlayer):
    def __init__(self, num_simulations=100, depth=3, use_mcts=True):
        self.num_simulations = num_simulations
        self.depth = depth
        self.use_mcts = use_mcts

    def declare_action(self, valid_actions, hole_card, round_state):
        if self.use_mcts:
            return self.mcts_declare_action(valid_actions, hole_card, round_state)
        else:
            return self.minimax_declare_action(valid_actions, hole_card, round_state)

    def mcts_declare_action(self, valid_actions, hole_card, round_state):
        best_score = -float('inf')
        best_action = valid_actions[0]["action"]

        for action_info in valid_actions:
            total_score = 0
            for _ in range(self.num_simulations):
                sim_round_state = copy.deepcopy(round_state)
                sim_hole_card = list(hole_card)

                reward = self.simulate_game(sim_round_state, sim_hole_card, action_info["action"])
                total_score += reward

            avg_score = total_score / self.num_simulations

            if avg_score > best_score:
                best_score = avg_score
                best_action = action_info["action"]

        return best_action

    def simulate_game(self, round_state, hole_card, chosen_action):
        # Use a more accurate simulation logic here
        win_chance = self.simulate_hand(round_state, hole_card)
        return win_chance

    def simulate_hand(self, round_state, hole_card):
        # A simplified hand evaluation based on known poker odds (this could be refined)
        hand_strength = random.uniform(0, 1)
        return hand_strength

    def minimax_declare_action(self, valid_actions, hole_card, round_state):
        best_action = None
        best_score = -float('inf')

        for valid_action in valid_actions:
            action = valid_action.get("action")
            if action:
                score = self.minimax(round_state, hole_card, action, self.depth, True)
                if score > best_score:
                    best_score = score
                    best_action = action

        if best_action is None:
            best_action = "fold"
        return best_action

    def minimax(self, round_state, hole_card, valid_action, depth, maximizing_player):
        if depth == 0:
            return self.evaluate_state(round_state, hole_card, valid_action)

        sim_round_state = self.simulate_round(round_state, valid_action)
        score = None

        if maximizing_player:
            score = -float('inf')
            for valid_action in self.get_valid_actions(sim_round_state):
                score = max(score, self.minimax(sim_round_state, hole_card, valid_action["action"], depth - 1, False))
        else:
            score = float('inf')
            for valid_action in self.get_valid_actions(sim_round_state):
                score = min(score, self.minimax(sim_round_state, hole_card, valid_action["action"], depth - 1, True))

        return score

    def evaluate_state(self, round_state, hole_card, valid_action):
        # Add more detailed debugging
        print(f"Evaluating state for action: {valid_action}")
        print(f"Hand strength: {self.evaluate_hand_strength(hole_card)}")
        print(f"Pot odds: {self.calculate_pot_odds(round_state)}")

        # Enhanced logic based on pot odds, hand strength, etc.
        hand_strength = self.evaluate_hand_strength(hole_card)
        pot_odds = self.calculate_pot_odds(round_state)

        if hand_strength > 0.8 and pot_odds < 2:
            return 1  # Strong hand, favorable pot odds
        elif hand_strength < 0.2 and pot_odds > 3:
            return -1  # Weak hand, unfavorable pot odds
        return 0  # Neutral outcome

    def evaluate_hand_strength(self, hole_card):
        # Placeholder for more sophisticated hand strength evaluation
        return random.uniform(0, 1)

    def calculate_pot_odds(self, round_state):
        # Calculate pot odds based on current bet and pot size (simplified version)
        pot_size = round_state["pot"]["main"]["amount"]
        current_bet = round_state["betting"]["current"]["amount"]
        return current_bet / pot_size if pot_size else 0

    def simulate_round(self, round_state, valid_action):
        sim_round_state = copy.deepcopy(round_state)
        sim_round_state["pot"]["main"]["amount"] += 10  # Simulate action, such as raise
        return sim_round_state

    def get_valid_actions(self, round_state):
        if "valid_actions" in round_state:
            return round_state["valid_actions"]
        else:
            return []

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
    return HybridPlayer(num_simulations=100, depth=3, use_mcts=True)  # Set 'use_mcts' to False for Minimax only