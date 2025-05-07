from collections import Counter
import random
from abstraction_opponent_modeling.abs_agent_modeling import AbsPlayer
from q_learning.q_learning_agent import QLearnPlayer
from mccfr.mccfr_agent import MCCFRPlayer
import time

# initialize each of the agents
agent1 = AbsPlayer()
agent1.set_uuid("Agent1")
agent2 = QLearnPlayer()
agent2.set_uuid("Agent2")
agent3 = MCCFRPlayer()
agent3.set_uuid("Agent1")
agents = [agent1, agent2, agent3]

def get_majority_action(valid_actions, hole_card, round_state):
    """
    Using the three agents, obtain their declared action and then return the majority recommended action

    Arguments:
        valid_actions: contains the possible actions the player can take in the given instance.
        hole_card: provides the pairings for the cards that our player holds
        round_state: provides information pertaining to the current round

    Returns:
        action: action ("fold", "call", or "raise") that received the most "votes" from the agents (ties when all disagree, take q-learning)
    """
    actions = []

    for agent in agents:
        start_time = time.time()
        action = agent.declare_action(valid_actions, hole_card, round_state)
        end_time = time.time()
        elapsed_ms = (end_time - start_time) * 1000
        #print(agent, " took ", elapsed_ms, "ms")
        actions.append(action)


    vote_counts = Counter(actions)
    top_votes = vote_counts.most_common()

    if len(top_votes) > 1 and top_votes[0][1] == top_votes[1][1]:
        return actions[1]
    else:
        return top_votes[0][0]
