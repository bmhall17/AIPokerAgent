import pickle
import os
from collections import defaultdict

INTERNAL_ACTIONS_LEN = 3 
def create_default_node():
    return {'regret_sum': [0.0] * INTERNAL_ACTIONS_LEN,
            'strategy_sum': [0.0] * INTERNAL_ACTIONS_LEN}


CHECKPOINT_FILE_PATH = "mccfr_checkpoints_v2/mccfr_checkpoint_5000_converted.pkl"
AVERAGE_STRATEGY_OUTPUT_PATH = "mccfr_checkpoints_v2/mccfr_checkpoint_5000_converted_avg.pkl"

def avg(node_data, num_actions):
    if not isinstance(node_data, dict) or 'strategy_sum' not in node_data:
        return [1.0 / num_actions] * num_actions

    avg_strategy = list(node_data['strategy_sum'])
    normalizing_sum = sum(avg_strategy)

    if normalizing_sum > 0:
        try:
            avg_strategy = [s / normalizing_sum for s in avg_strategy]
        except ZeroDivisionError:
             avg_strategy = [1.0 / num_actions] * num_actions
    else:
        avg_strategy = [1.0 / num_actions] * num_actions

    while len(avg_strategy) < num_actions:
        avg_strategy.append(0.0)
    return avg_strategy[:num_actions]


def main():
    with open(CHECKPOINT_FILE_PATH, 'rb') as f:
        checkpoint_data = pickle.load(f)
        node_map = checkpoint_data['node_map']

        output_strategy_map = {}
        num_nodes = 0

        for infoset_key, node_data in node_map.items():
            num_nodes += 1
            avg_strategy = avg(node_data, INTERNAL_ACTIONS_LEN)

            # sometimes did not sum to 1
            if abs(sum(avg_strategy) - 1.0) < 1e-5:
                output_strategy_map[infoset_key] = avg_strategy

        print(f"Num nodes: {num_nodes}")

        output_dir = os.path.dirname(AVERAGE_STRATEGY_OUTPUT_PATH)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        with open(AVERAGE_STRATEGY_OUTPUT_PATH, 'wb') as f:
            pickle.dump(output_strategy_map, f)

if __name__ == "__main__":
    main()