from collections import Counter
import random
from sub.abstraction_opponent_modeling.ouragent_modeling import OurPlayer
from sub.q_learning.q_learning_agent import QLearnPlayer
from sub.mccfr.mccfr_agent import MCCFRPlayer

# initialize each of the agents
agent1 = OurPlayer()
agent1.set_uuid("Agent1")
agent2 = QLearnPlayer()
agent2.set_uuid("Agent2")
agent3 = MCCFRPlayer()
agent3.set_uuid("Agent1")
agents = [agent1, agent2, agent3]

def get_majority_action(valid_actions, hole_card, round_state):
    """
    Using the three agents, obtain their declared action and then return the majority

    Arguments:
        valid_actions: contains the possible actions the player can take in the given instance.
        hole_card: provides the pairings for the cards that our player holds
        round_state: provides information pertaining to the current round

    Returns:
        action: action ("fold", "call", or "raise") that received the most "votes" from the agents (ties broken at random)
    """
    actions = []

    for agent in agents:
        action = agent.declare_action(valid_actions, hole_card, round_state)
        actions.append(action)

    vote_counts = Counter(actions)
    top_votes = vote_counts.most_common()

    if len(top_votes) > 1 and top_votes[0][1] == top_votes[1][1]:
        tied_actions = [action for action, count in top_votes if count == top_votes[0][1]]
        return random.choice(tied_actions)
    else:
        return top_votes[0][0]
