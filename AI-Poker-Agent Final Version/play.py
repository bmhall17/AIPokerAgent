from pypokerengine.api.game import setup_config, start_poker
from custom_player import CustomPlayer
from raise_player import RaisedPlayer
import matplotlib.pyplot as plt
from mccfr.mccfr_agent import MCCFRPlayer
from randomplayer import RandomPlayer

NUM_GAMES = 1000
win_counts = {"Ensemble Player": 0, "Random Player": 0, "tie": 0}

for i in range(1, NUM_GAMES + 1):
    config = setup_config(max_round=500, initial_stack=1000, small_blind_amount=10)
    config.register_player(name="Ensemble Player", algorithm=CustomPlayer())
    config.register_player(name="Random Player", algorithm=RandomPlayer())
    game_result = start_poker(config, verbose=0)

    players = game_result["players"]
    stacks = {p["name"]: p["stack"] for p in players}

    if stacks["Ensemble Player"] > stacks["Random Player"]:
        winner = "Ensemble Player"
        win_counts["Ensemble Player"] += 1
    elif stacks["Random Player"] > stacks["Ensemble Player"]:
        winner = "Random Player"
        win_counts["Random Player"] += 1
    else:
        winner = "tie"
        win_counts["tie"] += 1

    print(f"Game {i}: Winner - {winner}")

# Final print
print("\nFinal Results after 1000 games:")
for player, count in win_counts.items():
    print(f"{player} Wins: {count}")

# Plotting bar graph
labels = list(win_counts.keys())
values = list(win_counts.values())

plt.figure(figsize=(8, 5))
bars = plt.bar(labels, values, color=["#4caf50", "#2196f3", "#ff9800"])
plt.title("Poker Win Counts after 1000 Games")
plt.xlabel("Player")
plt.ylabel("Number of Wins")
plt.ylim(0, max(values) + 50)

# Adding text on top of bars
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2.0, yval + 5, yval, ha='center', va='bottom')

plt.tight_layout()
plt.show()


