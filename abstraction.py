
RANKS = "23456789TJQKA"
SUITS = "cdhs"  

RANK_VALUES = {
    '2': 2, '3': 3, '4': 4, '5': 5,
    '6': 6, '7': 7, '8': 8, '9': 9,
    'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
}

HAND_RANKS = {
    "high_card": 0,
    "pair": 1,
    "two_pair": 2,
    "three_of_a_kind": 3,
    "straight": 4,
    "flush": 5,
    "full_house": 6,
    "four_of_a_kind": 7,
    "straight_flush": 8,
    "royal_flush": 9
}

def get_rank(card):
    return card[0]

def get_suit(card):
    return card[1]

def card_value(card):
    return RANK_VALUES.get(card[0], 0)

def sort_cards(cards):
    return sorted(cards, key=lambda x: RANK_VALUES[x[0]], reverse=True)

def group_by_rank(cards):
    rank_counts = {}
    for card in cards:
        rank = get_rank(card)
        if rank not in rank_counts:
            rank_counts[rank] = []
        rank_counts[rank].append(card)
    return rank_counts

def group_by_suit(cards):
    suit_counts = {}
    for card in cards:
        suit = get_suit(card)
        if suit not in suit_counts:
            suit_counts[suit] = []
        suit_counts[suit].append(card)
    return suit_counts

def is_straight(ranks):
    unique_ranks = sorted(set(ranks), reverse=True)
    for i in range(len(unique_ranks) - 4):
        slice_ = unique_ranks[i:i+5]
        if slice_[0] - slice_[-1] == 4:
            return True, slice_[0]
    # Check wheel (A-2-3-4-5)
    if set([14, 2, 3, 4, 5]).issubset(set(ranks)):
        return True, 5
    return False, 0

def is_flush(cards):
    suits = group_by_suit(cards)
    for suit, suited_cards in suits.items():
        if len(suited_cards) >= 5:
            return True, sort_cards(suited_cards)[:5]
    return False, []

def get_hand_rank(hole_cards, community_cards):
    all_cards = hole_cards + community_cards
    all_cards = sort_cards(all_cards)
    rank_groups = group_by_rank(all_cards)
    suit_groups = group_by_suit(all_cards)
    rank_list = [RANK_VALUES[card[0]] for card in all_cards]

    
    flush, flush_cards = is_flush(all_cards)#checks for flush
    flush_ranks = [RANK_VALUES[card[0]] for card in flush_cards]

    
    straight, high_straight = is_straight(rank_list)#check for straight

    #check straight flush
    if flush:
        flush_ranks_only = [RANK_VALUES[card[0]] for card in flush_cards]
        straight_flush, high_sf = is_straight(flush_ranks_only)
        if straight_flush:
            if high_sf == 14:
                return HAND_RANKS["royal_flush"], high_sf
            return HAND_RANKS["straight_flush"], high_sf

    
    for rank, cards in rank_groups.items():
        if len(cards) == 4:
            kicker = max([card_value(c) for c in all_cards if get_rank(c) != rank])
            return HAND_RANKS["four_of_a_kind"], RANK_VALUES[rank]

    # Full house
    trips = []
    pairs = []
    for rank, cards in rank_groups.items():
        if len(cards) == 3:
            trips.append(RANK_VALUES[rank])
        elif len(cards) == 2:
            pairs.append(RANK_VALUES[rank])
    if trips and (pairs or len(trips) > 1):
        return HAND_RANKS["full_house"], trips[0]

    #flush
    if flush:
        return HAND_RANKS["flush"], flush_ranks[0]

    #straight
    if straight:
        return HAND_RANKS["straight"], high_straight

    #three of a kind
    if trips:
        return HAND_RANKS["three_of_a_kind"], trips[0]

    #two pair
    if len(pairs) >= 2:
        pairs.sort(reverse=True)
        return HAND_RANKS["two_pair"], pairs[0]

    #one pair
    if pairs:
        return HAND_RANKS["pair"], pairs[0]

    #high card
    return HAND_RANKS["high_card"], rank_list[0]

def bucket_hand_rank(rank_score):
    return rank_score  

def bucket_high_card(high_card):
    if high_card >= 14:
        return 4
    elif high_card >= 11:
        return 3
    elif high_card >= 8:
        return 2
    elif high_card >= 5:
        return 1
    else:
        return 0

def abstract_state(hole_cards, community_cards, position, stack_ratio, pot_odds, street):
    rank_score, high_card = get_hand_rank(hole_cards, community_cards)
    hand_bucket = bucket_hand_rank(rank_score)
    high_bucket = bucket_high_card(high_card)

    position_map = {'early': 0, 'middle': 1, 'late': 2, 'blind': 3}
    pos_bucket = position_map.get(position, 3)

    if stack_ratio > 50:
        stack_bucket = 0
    elif stack_ratio > 20:
        stack_bucket = 1
    elif stack_ratio > 10:
        stack_bucket = 2
    else:
        stack_bucket = 3

    pot_bucket = min(int(pot_odds * 10), 9)

    street_map = {'preflop': 0, 'flop': 1, 'turn': 2, 'river': 3}
    street_bucket = street_map.get(street, 0)

    return (hand_bucket, high_bucket, pos_bucket, stack_bucket, pot_bucket, street_bucket)
