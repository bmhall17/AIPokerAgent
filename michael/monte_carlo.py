import random
# basic library to see who wins a poker hand
from pokereval.card import Card
from pokereval.hand_evaluator import HandEvaluator
from abstraction import get_infoset_key

SMALL_BLIND = 5
BIG_BLIND = 10
RAISE_AMOUNT = 10
MAX_RAISES_PER_STREET = 4
PLAYER_COUNT = 2
INITIAL_STACK = 200 # reduced to speed up monte carlo sims
ACTIONS = ["fold", "call", "raise"] # 0, 1, 2
INTERNAL_ACTIONS = [0, 1, 2]
FULL_DECK_INTS = list(range(52))
RANKS_STR = "23456789TJQKA"
SUITS_STR = "shdc"
STREETS = ["preflop", "flop", "turn", "river"]

# modified and simplified poker engine to allow for mccfr, track histories
class GameState:
    def __init__(self):
        self.stacks = [INITIAL_STACK] * PLAYER_COUNT
        self.hole_cards = [[] for _ in range(PLAYER_COUNT)]
        self.hole_cards_str = [[] for _ in range(PLAYER_COUNT)]
        self.street_bets = [0] * PLAYER_COUNT
        self.round_bets = [0] * PLAYER_COUNT
        self.pot = 0
        self.current_deck = []
        self.community_cards = []
        self.community_cards_str = []
        self.street = "preflop"
        self.history = {s: [] for s in STREETS}
        self.num_street_raises = 0
        self.last_raiser = -1
        self.player_to_act = 0
        self.is_terminal_state = False
        self.winner = -1
        self.street_ended = False
        self.new_hand()

    def card_int_to_str(self, card_int):
        rank_index = card_int // 4
        suit_index = card_int % 4
        return f"{RANKS_STR[rank_index]}{SUITS_STR[suit_index]}"

    # pokereval specific thing
    def ints_to_cards(self, card_int_list):
        card_objects = []
        for card_int in card_int_list:
            rank_index_0_12 = card_int // 4
            suit_index_0_3 = card_int % 4
            pokereval_rank = rank_index_0_12 + 2
            pokereval_suit = suit_index_0_3 + 1
            card_objects.append(Card(pokereval_rank, pokereval_suit))
        return card_objects

    def deal(self, num_cards):
        return [self.current_deck.pop() for _ in range(num_cards)]

    def new_hand(self):
        # Reset everything
        self.stacks = [INITIAL_STACK] * PLAYER_COUNT
        self.pot = 0
        self.current_deck = list(FULL_DECK_INTS)
        random.shuffle(self.current_deck)
        self.hole_cards = [[] for _ in range(PLAYER_COUNT)]
        self.hole_cards_str = [[] for _ in range(PLAYER_COUNT)]
        self.community_cards = []
        self.community_cards_str = []
        self.street = "preflop"
        self.history = {s: [] for s in STREETS}
        self.street_bets = [0] * PLAYER_COUNT
        self.round_bets = [0] * PLAYER_COUNT
        self.num_street_raises = 0
        self.last_raiser = -1
        self.is_terminal_state = False
        self.winner = -1
        self.street_ended = False


        for i in range(PLAYER_COUNT):
            dealt_ints = self.deal(2)
            self.hole_cards[i] = dealt_ints
            self.hole_cards_str[i] = [self.card_int_to_str(c) for c in dealt_ints]
       
        # post blinds (in this case player0 is always small blind, so slightly innacurate)
        sb_player, bb_player = 0, 1
        sb_amount = min(SMALL_BLIND, self.stacks[sb_player])
        bb_amount = min(BIG_BLIND, self.stacks[bb_player])
        self.apply_bet(sb_player, sb_amount)
        self.apply_bet(bb_player, bb_amount)
        self.player_to_act = sb_player
        self.last_raiser = bb_player

    def apply_bet(self, player_id, amount):
         amount = min(amount, self.stacks[player_id])
         self.stacks[player_id] -= amount
         self.street_bets[player_id] += amount
         self.round_bets[player_id] += amount
         self.pot += amount
         return amount

    def get_current_player(self): return self.player_to_act
    def is_terminal(self): return self.is_terminal_state
    def is_chance_node(self): return self.street_ended and not self.is_terminal_state

    def get_utility(self, player_id):
        if self.winner == -1:
            active_players_with_bets = [i for i, bet in enumerate(self.round_bets) if bet > 0 or self.stacks[i] > 0]
            if len(active_players_with_bets) == 1: # folded out
                self.winner = active_players_with_bets[0]
            else: # showdown
                self.winner = self.eval_win()

        # Calculate utility
        if self.winner == -2: # Split pot
            return (self.pot / PLAYER_COUNT) - self.round_bets[player_id]
        elif self.winner == player_id: # Player won
            return self.pot - self.round_bets[player_id]
        else: # Player lost
            return -self.round_bets[player_id]

    def eval_win(self):
        p0, p1 = 0, 1

        p0_cards = self.ints_to_cards(self.hole_cards[p0])
        p1_cards = self.ints_to_cards(self.hole_cards[p1])
        board_cards = self.ints_to_cards(self.community_cards)

        p0_score = HandEvaluator.evaluate_hand(p0_cards, board_cards)
        p1_score = HandEvaluator.evaluate_hand(p1_cards, board_cards)

        if p0_score > p1_score:
            return p0
        elif p1_score > p0_score:
            return p1
        else: # split
            return -2

    def advance_street(self):
        num_cards = 0
        next_street = None
        if self.street == "preflop":
            num_cards = 3
            next_street = "flop"
        elif self.street == "flop":
            num_cards = 1
            next_street = "turn"
        elif self.street == "turn":
            num_cards = 1
            next_street = "river"
        else: # in river, terminal
            self.is_terminal_state = True
            self.street_ended = False
            return self

        new_cards_ints = self.deal(num_cards)
        self.community_cards.extend(new_cards_ints)
        self.community_cards_str = [self.card_int_to_str(c) for c in self.community_cards]

        self.street = next_street
        self.street_bets = [0] * PLAYER_COUNT
        self.num_street_raises = 0
        self.last_raiser = -1
        self.street_ended = False
        self.player_to_act = 0

        return self

    def get_valid_actions(self):
            valid = []
            player = self.player_to_act
            opponent = 1 - player
            player_stack = self.stacks[player]
            player_bet_this_street = self.street_bets[player]
            max_bet_this_street = max(self.street_bets) if self.street_bets else 0
            amount_to_call = max_bet_this_street - player_bet_this_street

            # all in check
            if player_stack <= 0 and player_bet_this_street >= max_bet_this_street:
                return [1]

            # avoid folding if checked around
            if amount_to_call > 0:
                valid.append(0)

            # check / call always possible
            valid.append(1)

            # raising
            can_raise = self.num_street_raises < MAX_RAISES_PER_STREET and player_stack > amount_to_call
            opp_stack = self.stacks[opponent]
            opp_bet = self.street_bets[opponent]
            opp_allin = opp_stack <= 0 and opp_bet == max_bet_this_street
            if can_raise and not opp_allin:
                valid.append(2)

            return sorted(list(set(valid)))

    def apply_action(self, internal_action):
        player = self.player_to_act
        opponent = 1 - player
        player_bet_this_street = self.street_bets[player]
        max_bet_this_street = max(self.street_bets) if self.street_bets else 0
        amount_to_call = max_bet_this_street - player_bet_this_street

        action_char = '' 
        # all in (bet to stack size 0)
        if self.stacks[player] <= 0 and player_bet_this_street >= max_bet_this_street:
             self.check_street_end()
             if not self.street_ended:
                  if not (self.stacks[opponent] <= 0 and self.street_bets[opponent] >= max(self.street_bets)):
                       self.player_to_act = opponent
             return self

        if internal_action == 0: # Fold
            action_char = 'f'
            self.is_terminal_state = True
            self.winner = opponent
            self.street_ended = True

        elif internal_action == 1: # Call / Check
            is_check = (amount_to_call <= 0)
            action_char = 'c'
            if not is_check: 
                 bet_amount = self.apply_bet(player, amount_to_call)
            self.last_raiser = self.last_raiser

        elif internal_action == 2: # Raise
            action_char = 'r'
            min_raise_total_bet = max_bet_this_street + RAISE_AMOUNT
            amount_to_add = min_raise_total_bet - player_bet_this_street
            bet_amount = self.apply_bet(player, amount_to_add)
            self.num_street_raises += 1
            self.last_raiser = player


        self.history[self.street].append(action_char)

        if not self.is_terminal_state:
             self.check_street_end()
             if not self.street_ended:
                  self.player_to_act = opponent

        if self.street_ended and self.street == "river" and not self.is_terminal_state:
            self.is_terminal_state = True

        if self.is_terminal_state:
             self.player_to_act = -1

        return self

    def check_street_end(self):
         if self.is_terminal_state:
              self.street_ended = True
              return

         num_actions = len(self.history[self.street])
         min_actions = 2 if self.street != 'preflop' else 1
         if num_actions < min_actions:
              self.street_ended = False
              return

         
         last_player = self.player_to_act 
         last_action = self.history[self.street][-1] if self.history[self.street] else None

         is_closed = False

         bets_equal = self.street_bets[0] == self.street_bets[1]
         if bets_equal:
              if last_action in ['c']: # check/call ends if equal
                   is_closed = True
              # Preflop specific: BB checks after SB completes BB
              if self.street == 'preflop' and last_player == 1 and last_action == 'c' and self.street_bets[1] == BIG_BLIND and num_actions >= 1:
                    is_closed = True

              # checked around
              if self.street != 'preflop' and self.num_street_raises == 0 and last_action == 'c':
                  is_closed = True

         # allins
         p0_all_in = self.stacks[0] <= 0
         p1_all_in = self.stacks[1] <= 0
         if p0_all_in and p1_all_in:
            is_closed = True
         if (p0_all_in or p1_all_in) and bets_equal and last_action == 'c':
             is_closed = True 

         self.street_ended = is_closed

    # for our infosets, we only use the street, our hole cards, community cards, the number of bets, and number of raises previously
    def get_infoset_key_for_player(self, player_id):
        hole_cards_for_key = self.hole_cards_str[player_id] 
        current_street_history = self.history[self.street]
        return get_infoset_key(
            street=self.street,
            hole_card_str_list=hole_cards_for_key,
            community_card_str_list=self.community_cards_str,
            betting_history=current_street_history,
            num_raises_street=self.num_street_raises
        )

