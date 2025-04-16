from pypokerengine.api.game import setup_config, start_poker
from pypokerengine.players import BasePokerPlayer
from ouragent_helpers import extract_state
from raise_player import RaisedPlayer
import random
import pickle


"""
Initial Declarations of q_values and pre-defined variables for q_learning.
"""
actions = ["fold", "call", "raise"]
streets = ["preflop", "flop", "turn", "river"]
strength_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
pot_buckets = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
states = [(street, strength, pot) for street in streets for strength in strength_values for pot in pot_buckets]
alpha = 0.1
gamma = 0.95
epsilon = 0.1
epsilon_min = 0.05
epsilon_decay = 0.995
q_values = {state: {action: 0.0 for action in actions} for state in states}

class TrainingPlayer(BasePokerPlayer):

    def __init__(self):
        """
        Initializes section of characteristics for the player for a round of play

        round_actions: list of actions in a round, leverage in q-value updating
        wallet_before: store the player's betting wallet amount for the computation of the reward

        """
        self.round_actions = []
        self.wallet_before = 0

    def declare_action(self, valid_actions, hole_card, round_state):
        """
        Identifies the current state, its possible actions, and the respective q_values for the pairing,
        before selecting the best action (maximal q_value). It breaks ties at random and then returns
        the player's action. Incorporates the epsilon element of randomly selecting an action to ensure coverage
        and value generation for all possible states and action pairings within the q_value dictionary.

        Arguments:
            valid_actions: contains the possible actions the player can take in the given instance.
            hole_card: provides the pairings for the cards that our player holds
            round_state: provides information pertaining to the current round

        Returns:
            action: action ("fold", "call", or "raise") possessing the maximal q_value for the given
            state and action
        """
        global epsilon
        global q_values
        state = extract_state(self, hole_card, round_state)
        possible_actions = [action["action"] for action in valid_actions]

        # epsilon greedy selection of action based on q_values, epsilon for exploration of random action
        if random.random() < epsilon:
            action = random.choice(possible_actions)
        else:
            q_vals = q_values.get(state, {})
            max_q = max(q_vals.get(action, 0.0) for action in possible_actions)
            best_actions = [a for a in possible_actions if q_vals.get(a, 0.0) == max_q]
            action = random.choice(best_actions)
        
        # add selected action to our list for q_value updating later
        self.round_actions.append((state, action))

        return action

    def receive_round_result_message(self, winners, hand_info, round_state):
        """
        Aimed at processing at the end of the round and updating the q_values. In this
        the player's reward for the round is computed (net gain/loss for the round) and then
        the q_value is updated using the standard formula:
            Q(s, a) = Q(s,a) + alpha * (reward + gamma * max(Q(s', a')) - Q(s, a))
        
        Arguments:
            winners: contains the winners for the respective round
            hand_info: contains the information pertaining each players hands and best hands
            round_state: contains the relevant round information
        """
        global q_values
        player_id = self.uuid
        wallet_after = None

        # identify the player's stack after the round and then compute the reward (net gain/loss)
        for player in round_state['seats']:
            if player['uuid'] == player_id:
                wallet_after = player['stack']
                break
        reward = wallet_after - self.wallet_before

        # perform q_learning value updates using specified formula
        for i, (state, action) in enumerate(self.round_actions):
            old_value = q_values[state][action]

            # last state in round doesn't have next states value to incorporate (set to 0)
            if i + 1 < len(self.round_actions):
                next_state, _ = self.round_actions[i + 1]
                next_q_vals = q_values.get(next_state, {})
                max_next_q = max(next_q_vals.values(), default=0.0)
            else:
                max_next_q = 0.0

            # update the curstate, action q_value
            new_value = old_value + alpha * (reward + gamma * max_next_q - old_value)
            q_values[state][action] = new_value
        
        #reset the round list
        self.round_actions = []

    def receive_game_start_message(self, game_info): pass

    def receive_round_start_message(self, round_count, hole_card, seats): 
        """
        Identify the Training Player's initial wallet at the beginning of the round for
        use in the reward computation.

        Arguments:
            round_count: identify the current round
            hole_card: information for the player's cards on hand
            seats: relevant player information
        """
        for player in seats:
            if player['uuid'] == self.uuid:
                self.wallet_before = player['stack']
                break
    
    def receive_street_start_message(self, street, round_state): pass

    def receive_game_update_message(self, action, round_state): pass

def run_training_game(num_rounds=500):
    """
    Run an instance of the game for the specified game conditions with our Training Player, and a
    chosen opponent (default of RaisedPlayer for time being). Obtain the games outcome for general
    observations. Also updates epsilon so that it is experiencing decay for the sake of improved
    learning and later rounds relying on learned information more.

    Arguments:
        num_rounds: number of rounds (specified as 500 for our project)

    Returns:
        final_wallets: each players respective final wallet value
    """
    global epsilon
    global q_values

    # configure the game with settings and players
    config = setup_config(
        max_round=num_rounds,
        initial_stack=1000,
        small_blind_amount=10
    )
    config.register_player(name="Training Player", algorithm=TrainingPlayer())
    config.register_player(name="FT2", algorithm=RaisedPlayer())

    # store the game result, perform epsilon decay, and store the final stacks at the end of the round
    game_result = start_poker(config, verbose=0)
    epsilon = max(epsilon_min, epsilon * epsilon_decay)
    final_wallets = [(p['name'], p['stack']) for p in game_result['players']]

    return final_wallets

def run_training(total_games=50000, rounds_per_game=500):
    """
    Training function that repetitively runs a specified number of games to allow for the agent to receive
    sufficient training. Identifies the winner for the current game, and provides status for ongoing training, before
    printing the final q-values generated during the training process.
    
    Arguments:
        total_games: the specified size of the training
        rounds_per_game: the specified number of rounds per game (default of 500)
    """
    for game in range(total_games):
        print(f"\nTraining Game {game + 1}/{total_games}")
        final_stacks = run_training_game(num_rounds=rounds_per_game)
        sorted_stacks = sorted(final_stacks, key=lambda x: x[1], reverse=True)
        winner = sorted_stacks[0]
        print(f"Winner: {winner[0]} with stack {winner[1]}")
        for name, stack in sorted_stacks:
            print(f" - {name}: {stack}")
    
    print("Q-table: ", q_values)


if __name__ == "__main__":
    """
    Call the training and then after performing the training, uses pickle to save the q_values.
    """
    run_training()

    with open("q_values.pkl", "wb") as f:
        pickle.dump(q_values, f)
