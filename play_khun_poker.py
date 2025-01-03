import json
import random

CARD_MAP = ["J", "Q", "K"]
TERMINAL_ACTION_STR_MAP = {"pp", "bb", "bp", "pbb", "pbp"}

def playerOnePocketIsHigher(pocket1, pocket2):
    if pocket1 == "K":
        return True
    if pocket1 == "J":
        return False
    if pocket2 == "K":
        return False
    if pocket2 == "J":
        return True
    raise ValueError("This should not occur bc one player must have K or J")

def calcUtilityAtTerminalNode(pocket1, pocket2, actionStr: str):
    if actionStr == "pp":
        if playerOnePocketIsHigher(pocket1, pocket2):
            return 1, -1
        return -1, 1
    elif actionStr == "pbp":
        return -1, 1
    elif actionStr == "bp":
        return 1, -1
    elif actionStr == "bb" or actionStr == "pbb":
        if playerOnePocketIsHigher(pocket1, pocket2):
            return 2, -2
        return -2, 2
    else:
        raise ValueError(f"Invalid actionStr={actionStr}")


def load_strategy(filename):
    with open(filename, 'r') as file:
        strategy = json.load(file)
    return strategy

def get_computer_action(strategy, history):
    if history in strategy.keys():
        return random.choices(['b', 'p'], weights=[strategy[history][actions] for actions in strategy[history].keys()])[0]
    
    raise ValueError(f"Invalid history: {history}")

def get_human_action():
    while True:
        action = input("Bet or Pass (b/p): ").strip().lower()
        if action in ['b', 'p']:
            return action
        print("Invalid action. Please enter 'bet' or 'check'.")

def play_round(strategy, scores):
    deck = [0, 1, 2]
    random.shuffle(deck)
    human_card = deck.pop()
    computer_card = deck.pop()

    player_initiative = random.choice([0, 1])
    print("Player with initiative: ", "Human" if player_initiative % 2 == 0 else "Computer")

    action_str = ""

    while True:

        if action_str in TERMINAL_ACTION_STR_MAP:
            human_utility, computer_utility = calcUtilityAtTerminalNode(CARD_MAP[human_card], CARD_MAP[computer_card], action_str)
            scores['human'] += human_utility
            scores['computer'] += computer_utility
            print(f"Human's card: {CARD_MAP[human_card]}")
            print(f"Computer's card: {CARD_MAP[computer_card]}")
            print(f"Winner is {'human' if human_utility > computer_utility else 'computer'}")   
            print("--------------------------------------------")
            input("Press Enter to continue...")
            break
 
        if player_initiative % 2 == 0:
            print(f"Your card: {CARD_MAP[human_card]}")
            history = CARD_MAP[computer_card]
            # Human's turn
            human_action = get_human_action()
            action_str += human_action
        else:
            # Computer's turn
            history = CARD_MAP[computer_card] + action_str
            computer_action = get_computer_action(strategy, history)
            action_str += computer_action
            print(f"Computer's action: {computer_action}")

        player_initiative += 1




    return scores

def main():
    strategy = load_strategy('strategy.json')

    scores = {'human': 0, 'computer': 0}

    for _ in range(50):
        scores = play_round(strategy, scores)
        # again = input("Play another round? (y/n): ").strip().lower()
        # if again != 'y':
        #     break

    print(scores)

if __name__ == "__main__":
    main()