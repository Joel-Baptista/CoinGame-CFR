import argparse
import json
import sys
import random

def load_strategy(filename):
    with open(f"{filename}.json", 'r') as file:
        strategy = json.load(file)
    return strategy

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-nc", "--number_coins", type=int, default=1, help="Number of coins"
    )
    parser.add_argument(
        "-p", "--number_players", type=int, default=3, help="Number of players"
    )
    parser.add_argument(
        "-ng", "--number_games", type=int, default=1, help="Number of games"
    )

    arglist = [x for x in sys.argv[1:] if not x.startswith("__")]
    args = vars(parser.parse_args(args=arglist))

    strategy = load_strategy(f'strategies/coin_game/coin_game_c{args["number_coins"]}p{args["number_players"]}')

    num_p = args["number_players"]
    num_c = args["number_coins"]

    for i in range(0, args["number_games"]):
        historic = ''
        human_player_idx = i % args["number_players"]

        while True:
            player_coin = input(f'Choose number of coins (0 - {num_c}): ')
            if int(player_coin) <= num_c and int(player_coin) >= 0:
                break
            print("Input a valid number!")

        historic += player_coin
        bot_coins = [random.randint(0, num_c) for _ in range(0, num_p - 1)]
        bot_count = 0
        
        for j in range(0, num_p):
            if j == human_player_idx:
                human_guess = input(f"The historic is: {historic}\nWhat is your guess: ")
                historic += human_guess
            else:
                bot_coin = bot_coins[bot_count]
                bot_historic = str(bot_coin) + historic[1:]

                bot_strategy = strategy[bot_historic]
                bot_guesses = [guess for guess in bot_strategy]
                bot_probs = [bot_strategy[guess] for guess in bot_strategy]
                bot_guess = random.choices(bot_guesses, weights=bot_probs)[0]
                historic += bot_guess
                bot_count += 1

        sum_coins = int(player_coin) + sum(bot_coins)
        print(f"Sum of coins: {sum_coins} - historic: {historic}")
        if sum_coins == int(human_guess):
            print(f"Human player wins")
        else:
            print(f"Human player loses")


if __name__ == "__main__":
    main()