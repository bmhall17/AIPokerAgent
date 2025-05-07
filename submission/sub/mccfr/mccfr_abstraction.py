import collections

SUITS = "shdc"
RANKS = "23456789TJQKA"
RANK_MAP = {rank: i for i, rank in enumerate(RANKS)}
HIGH_CARD_THRESHOLD = RANK_MAP['T']


from collections import defaultdict
INTERNAL_ACTIONS_LEN = 3 

def create_default_node():
    """Creates the default dictionary structure for a new node."""
    return {'regret_sum': [0.0] * INTERNAL_ACTIONS_LEN,
            'strategy_sum': [0.0] * INTERNAL_ACTIONS_LEN}

# basic abstraction from own poker intuition
def get_preflop_bucket(hole_cards):
    card1, card2 = hole_cards

    rank1_char = card1[0].upper()
    suit1 = card1[1].lower()
    rank2_char = card2[0].upper()
    suit2 = card2[1].lower()

    rank1 = RANK_MAP[rank1_char]
    rank2 = RANK_MAP[rank2_char]

    is_pair = (rank1 == rank2)
    is_suited = (suit1 == suit2)
    high_rank = max(rank1, rank2)
    low_rank = min(rank1, rank2)

    if is_pair:
        if rank1 >= RANK_MAP['T']:
            return "P:HIGH"
        elif rank1 >= RANK_MAP['6']:
            return "P:MED"
        return "P:LOW"
    else:
        connector_gap = high_rank - low_rank
        is_ace_low_connector = (high_rank == RANK_MAP['A'] and low_rank <= RANK_MAP['5']) # ace default rank is too high to catch bottom end conn
        is_connected_broadly = (connector_gap <= 2 or is_ace_low_connector) # add value to 1 and 2 gappers

        if is_suited:
            if high_rank >= HIGH_CARD_THRESHOLD and is_connected_broadly:
                 return "S:HIGH_CONN"
            elif is_connected_broadly:
                 return "S:CONN"
            elif high_rank >= HIGH_CARD_THRESHOLD:
                 return "S:HIGH"
            return "S:LOW"
        else:
             if high_rank >= HIGH_CARD_THRESHOLD and is_connected_broadly:
                 return "U:HIGH_CONN"
             elif is_connected_broadly:
                 return "U:CONN"
             elif high_rank >= HIGH_CARD_THRESHOLD:
                 return "U:HIGH"
             return "U:LOW"

def get_postflop_bucket(hole_list, community_list):
    all_cards = hole_list + community_list
    ranks = [RANK_MAP[c[0].upper()] for c in all_cards]
    suits = [c[1].lower() for c in all_cards]


    # flush check
    suit_counts = collections.Counter(suits)
    flush_suit = None
    for s, count in suit_counts.items():
        if count >= 5:
            flush_suit = s
            break
    is_flush = (flush_suit is not None)

    # striaght check
    unique_ranks = sorted(list(set(ranks)))
    ranks_for_straight_check_set = set(unique_ranks)
    if RANK_MAP['A'] in ranks_for_straight_check_set:
        ranks_for_straight_check_set.add(-1) # bottom ace

    is_straight = False
    for low_rank in range(-1, 9): # A-5 (-1 to 3) up to T-A (8 to 12)
        potential_straight = set(range(low_rank, low_rank + 5))
        if potential_straight.issubset(ranks_for_straight_check_set):
            is_straight = True

 

    # pairs, trips, quads, FH
    rank_counts = collections.Counter(ranks)
    counts = sorted(rank_counts.values(), reverse=True)

    # if we already "made" a hand
    made_hand_rank = 0
    if counts and counts[0] >= 4:
        made_hand_rank = 7
    elif counts and counts[0] >= 3 and len(counts) >= 2 and counts[1] >= 2:
        made_hand_rank = 6
    elif counts and counts[0] >= 3:
        made_hand_rank = 3
    elif counts and len(counts) >= 2 and counts[0] >= 2 and counts[1] >= 2:
        made_hand_rank = 2
    elif counts and counts[0] >= 2:
        made_hand_rank = 1

    # bucketing
    strength_bucket = "St:HighCard"
    if made_hand_rank >= 6: # quads + FH 
        strength_bucket = "St:Monster"
    elif is_flush:
        # note striaght flushes get put here but too unlikely to occur to matter
        strength_bucket = "St:Flush"
    elif is_straight:
        strength_bucket = "St:Straight"
    elif made_hand_rank == 3:
        strength_bucket = "St:Trips"
    elif made_hand_rank == 2:
        strength_bucket = "St:TwoPair"
    elif made_hand_rank == 1:
        strength_bucket = "St:Pair"

    # draws
    flush_draw = False
    has_oesd = False
    has_gutshot = False

    if not is_flush and not is_straight and strength_bucket != "St:Monster":
        # flush draw
        for s, count in suit_counts.items():
            if count == 4:
                flush_draw = True
                break

        # straight draws 
        unique_ranks_for_draw = sorted(list(ranks_for_straight_check_set))
        # open ended straights
        if len(unique_ranks_for_draw) >= 4:
            for i in range(len(unique_ranks_for_draw) - 3):
                if all(unique_ranks_for_draw[i+j] == unique_ranks_for_draw[i] + j for j in range(4)):
                     has_oesd = True
                     break
                
        # gutshot straights
        if not has_oesd and len(unique_ranks_for_draw) >= 4:
             for low_rank in range(-1, 9):
                 window = set(range(low_rank, low_rank + 5))
                 ranks_in_window = ranks_for_straight_check_set.intersection(window)
                 if len(ranks_in_window) == 4:
                     has_gutshot = True
                     break

    draw_bucket = "D:None"
    if flush_draw:
        draw_bucket = "D:Flush"
    elif has_oesd:
        draw_bucket = "D:OESD"
    elif has_gutshot:
        draw_bucket = "D:Gutshot"

    return f"{strength_bucket}|{draw_bucket}"

# different types of community cards, consider how likely we can make soemthing vs opponent making something
def get_board_texture_bucket(community_card_str_list):
    board = community_card_str_list

    ranks = sorted([RANK_MAP[c[0].upper()] for c in board])
    suits = [c[1].lower() for c in board]

    # board is paired or has trips
    rank_counts = collections.Counter(ranks)
    counts = sorted(rank_counts.values(), reverse=True)
    is_paired = False
    is_trips = False
    if counts and counts[0] >= 3:
        is_trips = True
        is_paired = True
    if counts and counts[0] >= 2:
        is_paired = True

    # board can have a flush
    suit_counts = collections.Counter(suits)
    flush_possible = False
    if any(count >= 3 for count in suit_counts.values()):
         flush_possible = True

    # connectedness of board
    is_connected = False
    unique_ranks = sorted(list(set(ranks)))
    if len(unique_ranks) >= 3:
         for i in range(len(unique_ranks) - 2):
              if unique_ranks[i+2] - unique_ranks[i] <= 4:
                   is_connected = True
                   break
         if not is_connected:
            ace_low_ranks = {RANK_MAP['A'], RANK_MAP['2'], RANK_MAP['3'], RANK_MAP['4'], RANK_MAP['5']}
            present_ace_low = set(unique_ranks).intersection(ace_low_ranks)
            if RANK_MAP['A'] in present_ace_low and len(present_ace_low) >= 3:
                 low_cards = sorted([r for r in present_ace_low if r != RANK_MAP['A']])
                 if low_cards[-1] - low_cards[0] <= 3:
                      is_connected = True


    texture = ""
    if is_trips:
        texture += "Trips"
    elif is_paired:
        texture += "Paired"
    else:
        texture += "Unpaired"

    if flush_possible:
        texture += "_Flushy"
    else:
        texture += "_Rainbow"

    if is_connected:
        texture += "_Conn"
    else:
        texture += "_Uncon"

    return f"Board:{texture}"


def get_infoset_key(street, hole_card_str_list, community_card_str_list, betting_history, num_raises_street):
    hole_bucket = get_preflop_bucket(hole_card_str_list)

    if street == "preflop":
        board_bucket = "Board:None"
        hand_bucket = "Hand:Preflop"
    else:
        board_bucket = get_board_texture_bucket(community_card_str_list)
        hand_bucket = get_postflop_bucket(hole_card_str_list, community_card_str_list)

    history_str = "".join(betting_history)
    raise_info = f"R{num_raises_street}"

    key = f"{street}:{hole_bucket}:{hand_bucket}:{board_bucket}:{history_str}:{raise_info}"
    # reduce infoset sizes
    return key[:500]
