import pickle
import copy
import time
import os
import re
import random
from collections import defaultdict
from monte_carlo import GameState, INTERNAL_ACTIONS, PLAYER_COUNT

def create_default_node():
    return {'regret_sum': [0.0] * len(INTERNAL_ACTIONS),
            'strategy_sum': [0.0] * len(INTERNAL_ACTIONS)}

CHECKPOINT_FILENAME = r"mccfr_checkpoint_(\d+)\.pkl"

class MCCFRTrainer:
    def __init__(self, checkpoint_dir="mccfr_checkpoints"):
        self.node_map = defaultdict(create_default_node)
        self.checkpoint_dir = checkpoint_dir
        self.start_iteration = 0

        if not os.path.exists(self.checkpoint_dir):
            os.makedirs(self.checkpoint_dir)
        self.load_checkpoint()

    # ------checkpointing stuff---------
    def get_checkpoint(self):
        latest_iter = -1
        latest_checkpoint_file = None
        for filename in os.listdir(self.checkpoint_dir):
            match = re.match(CHECKPOINT_FILENAME, filename)
            if match:
                iteration = int(match.group(1))
                if iteration > latest_iter:
                    latest_iter = iteration
                    latest_checkpoint_file = filename
        if latest_checkpoint_file:
            return os.path.join(self.checkpoint_dir, latest_checkpoint_file), latest_iter
        else:
            return None, -1

    def load_checkpoint(self):
        checkpoint_path, iteration = self.get_checkpoint()
        print(f"Latest checkpoint: {checkpoint_path} Iteration: {iteration}")
        if checkpoint_path and iteration >= 0:
            with open(checkpoint_path, 'rb') as f:
                checkpoint_data = pickle.load(f)
                loaded_iteration = checkpoint_data['iteration']
                new_node_map = defaultdict(create_default_node)
                loaded_map_data = checkpoint_data['node_map']
                for key, value in loaded_map_data.items():
                    new_node_map[key] = value
                self.node_map = new_node_map
                self.start_iteration = loaded_iteration
        else:
            print(f"No checkpoint, fresh run")
            self.start_iteration = 0
            self.node_map = defaultdict(create_default_node)

    def save_checkpoint(self, iteration):
        checkpoint_filename = f"mccfr_checkpoint_{iteration}.pkl"
        path = os.path.join(self.checkpoint_dir, checkpoint_filename)
        node_map = dict(self.node_map)

        checkpoint_data = {
            'iteration': iteration,
            'node_map': node_map
        }

        if not os.path.exists(self.checkpoint_dir):
            os.makedirs(self.checkpoint_dir)
        with open(path, 'wb') as f:
            pickle.dump(checkpoint_data, f)
  
    def save_final_strategy(self, total_iterations, f_name=None):
        if f_name is None:
            f_name = f"mccfr_strategy_avg_final_{total_iterations}.pkl"
        path = os.path.join(self.checkpoint_dir, f_name)
        out_strat = {}
        nodes_saved = 0
        for key, _ in self.node_map.items():
            avg_strat = self.get_average_strategy(key)
            out_strat[key] = avg_strat
            nodes_saved += 1
        if not os.path.exists(self.checkpoint_dir):
            os.makedirs(self.checkpoint_dir)
        with open(path, 'wb') as f:
            pickle.dump(out_strat, f)
        print(f"Saved {nodes_saved} strategies to {path}")

    # ------ mccfr stuff -------
    def get_strategy(self, infoset_key, valid_actions):
        node = self.node_map[infoset_key]
        strategy = {a: 0.0 for a in valid_actions}
        norm_sum = 0
        for i in valid_actions:
            if 0 <= i < len(node['regret_sum']):
                regret = node['regret_sum'][i]
                strategy[i] = max(0.0, regret)
                norm_sum += strategy[i]
        if norm_sum > 0:
            for i in valid_actions:
                 if i in strategy:
                    strategy[i] /= norm_sum
        else:
            num_valid = len(valid_actions)
            if num_valid > 0:
                for i in valid_actions:
                    strategy[i] = 1.0 / num_valid
        return strategy
    def get_average_strategy(self, infoset_key):
         node = self.node_map[infoset_key]
         avg_strat = list(node['strategy_sum'])
         norm_sum = sum(avg_strat)
         if norm_sum > 0:
            avg_strat = [s / norm_sum for s in avg_strat]
         else:
            avg_strat = [1.0 / len(INTERNAL_ACTIONS)] * len(INTERNAL_ACTIONS)
         while len(avg_strat) < len(INTERNAL_ACTIONS):
            avg_strat.append(0.0)
         return avg_strat[:len(INTERNAL_ACTIONS)]

    def mccfr(self, game_state, player_id, reach_probs):
        if game_state.is_terminal():
            return game_state.get_utility(player_id)
        if game_state.is_chance_node():
            next_game_state = game_state.advance_street()
            if next_game_state.is_terminal():
                return next_game_state.get_utility(player_id)
            return self.mccfr(next_game_state, player_id, reach_probs)
        current_player = game_state.get_current_player()
        infoset_key = game_state.get_infoset_key_for_player(current_player)
        valid_actions = game_state.get_valid_actions()
        if not valid_actions:
             if not game_state.is_terminal():
                game_state.is_terminal_state = True
             return game_state.get_utility(player_id)
        strategy = self.get_strategy(infoset_key, valid_actions)
        if not strategy and valid_actions:
            num_valid = len(valid_actions)
            strategy = {action: 1.0 / num_valid for action in valid_actions}
        node = self.node_map[infoset_key]
        if current_player == player_id:
            action_utils = {a: 0.0 for a in valid_actions}
            node_util = 0.0
            for action in valid_actions:
                next_gs = copy.deepcopy(game_state)
                next_gs.apply_action(action)
                action_rp = list(reach_probs)
                action_utils[action] = self.mccfr(next_gs, player_id, action_rp)
                prob = strategy.get(action, 0.0)
                node_util += prob * action_utils[action]
            opp_reach = reach_probs[1 - player_id]
            for action in valid_actions:
                if 0 <= action < len(node['regret_sum']):
                    node['regret_sum'][action] += opp_reach * (action_utils[action] - node_util)
            my_reach = reach_probs[player_id]
            for action in valid_actions:
                if 0 <= action < len(node['strategy_sum']):
                    node['strategy_sum'][action] += my_reach * strategy.get(action, 0.0)
            return node_util
        else:
            opp_strat = self.get_strategy(infoset_key, valid_actions)
            if not opp_strat:
                return 0.0
            sampled_action = random.choices(list(opp_strat.keys()), weights=list(opp_strat.values()), k=1)[0]
            my_reach = reach_probs[player_id]
            for action in valid_actions:
                if 0 <= action < len(node['strategy_sum']):
                    node['strategy_sum'][action] += my_reach * opp_strat.get(action, 0.0)
            next_gs = copy.deepcopy(game_state); next_gs.apply_action(sampled_action)
            next_rp = list(reach_probs); sampled_prob = opp_strat.get(sampled_action, 0.0)
            next_rp[current_player] *= sampled_prob if sampled_prob > 0 else 0
            return self.mccfr(next_gs, player_id, next_rp)

    def train(self, target_i, checkpoint_interval=1000, log_interval=10):
        start_time = time.time()
        if self.start_iteration >= target_i:
            self.save_checkpoint(curr_i)
            return
        for i in range(self.start_iteration, target_i):
            curr_i = i + 1
            for p_id in range(PLAYER_COUNT):
                game_state = GameState()
                if not game_state.is_terminal():
                    self.mccfr(game_state, player_id=p_id, reach_probs=[1.0] * PLAYER_COUNT)
            if curr_i % checkpoint_interval == 0:
                self.save_checkpoint(curr_i)
            if curr_i % log_interval == 0:
                print(f"Iteration {curr_i}/{target_i} | Nodes: {len(self.node_map)} | Time: {time.time() - start_time}")
        self.save_final_strategy(target_i)

if __name__ == "__main__":
    checkpoint_directory = "mccfr_checkpoints_10k"
    trainer = MCCFRTrainer(checkpoint_dir=checkpoint_directory)
    trainer.train(target_i=10000, checkpoint_interval=1000)
