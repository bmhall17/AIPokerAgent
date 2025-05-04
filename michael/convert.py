import pickle

INTERNAL_ACTIONS_LEN = 3 

def create_default_node():
    return {'regret_sum': [0.0] * INTERNAL_ACTIONS_LEN,
            'strategy_sum': [0.0] * INTERNAL_ACTIONS_LEN}

INPUT_PICKLE_FILE = "mccfr_checkpoints_v2/mccfr_checkpoint_5000.pkl" 
OUTPUT_PICKLE_FILE = "mccfr_checkpoints_v2/mccfr_checkpoint_5000_converted.pkl"

with open(INPUT_PICKLE_FILE, 'rb') as f:
    loaded_data = pickle.load(f)
original_node_map = loaded_data['node_map']
iteration = loaded_data['iteration']
node_map_as_dict = dict(original_node_map)
data_to_save = {
    'iteration': iteration,
    'node_map': node_map_as_dict
}
with open(OUTPUT_PICKLE_FILE, 'wb') as f:
    pickle.dump(data_to_save, f)

