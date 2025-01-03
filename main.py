import argparse
import sys
import random
from itertools import product
from functools import lru_cache

import json

import numpy as np
import matplotlib.pyplot as plt


# Historic will be a simple string of numbers, where the firs number is the number of coins choosen by the current player,
# and the following numbers are the guesses of the other players

class InfoSetData:
    def __init__(self, historic: str, num_coins: int, num_players: int):

        actions = [str(i) for i in range(0, pow(num_players, num_coins) + 1)]

        for j in range(len(actions), 0):
            if historic[1:].find(str(j)) != -1:
                actions.pop(j)

        self.actions: dict[int, InfoSetActionData] = {
            i: InfoSetActionData(initStratVal=1 / len(actions)) for i in actions
        }

        self.beliefs: dict[str, float] = {}
        self.expectedUtil: float = None
        self.likelihood: float = None


class InfoSetActionData:
    def __init__(self, initStratVal: float):
        self.strategy = initStratVal
        self.util = None
        self.cumulativeGain = initStratVal


class CFR:
    def __init__(self, number_coins, number_players):
        self.number_coins = number_coins
        self.number_players = number_players

        self.coins = [i for i in range(0, number_coins + 1)]

        self.infoSets: dict[str, InfoSetData] = {}
        self.sorted_infoSets: list = []

        self.coin_sum_prior : dict[str, list] = {}

    def init_info_sets(self):

        # Fist Player to act
        full_historics = []
        for i in range(0, self.number_coins + 1):
            full_historics.append(str(i))
            self.infoSets[str(i)] = InfoSetData(str(i), self.number_coins, self.number_players)
        
        # Other players

        historics = [str(i) for i in range(0, self.number_players * self.number_coins + 1)]

        for j in range(1, self.number_players - 1):
            for hist in historics:    
                if len(hist) == j:
                    for k in range(0, self.number_players * self.number_coins + 1):
                        if hist.find(str(k)) == -1:
                            historic = hist + str(k)
                            historics.append(historic)

        for hist in historics:
            for nc in range(0, self.number_coins + 1):
                full_hist = str(nc) + hist
                full_historics.append(full_hist)
                self.infoSets[full_hist] = InfoSetData(full_hist, self.number_coins, self.number_players)

        self.sorted_infoSets = sorted(full_historics, key=lambda x: len(x))
        
        for coin in range(0, self.number_coins + 1):
            all_combinations = product(range(self.number_coins + 1), repeat=self.number_players)
            sum_counter = {str(i) : 0 for i in range(0, self.number_players * self.number_coins + 1)}
            possible_sum = self.get_possible_coins_sum(coin)
            comb_tot = 0
            for comb in all_combinations:
                comb_sum = sum(comb)
                if str(comb_sum) not in possible_sum:
                    continue

                sum_counter[str(comb_sum)] += 1
                comb_tot += 1
            
            self.coin_sum_prior[str(coin)] = [sum_counter[str(i)] / comb_tot for i in range(0, self.number_players * self.number_coins + 1)]

    # This two functions change the state into the oponents prespective, changing the priviledge info and maintaining the public knowledge
    def get_prev_info_states_hist(self, historic : str):
        if len(historic) == 1:
            raise ValueError(f"No ancestors for infoset={historic}")
        return [str(i) + historic[-1:1] for i in range(0, self.number_coins)]

    def get_next_info_states_hist(self, historic, action):
        if len(historic) == 1:
            return [str(i) + action for i in range(0, self.number_coins)]
        
        return [str(i) + historic[-1:] + action for i in range(0, self.number_coins)]

    def get_possible_actions(self, historic):
        actions = [str(i) for i in range(0, self.number_players * self.number_coins + 1)]

        for j in reversed(range(0, len(actions))):
            if historic[1:].find(str(j)) != -1:
                actions.pop(j)

        return actions
 
    def get_possible_coins_sum(self, coin_choosen):
        return [str(i) for i in range(coin_choosen, (self.number_players - 1) * self.number_coins + 1 + coin_choosen)]

    def update_utilities_of_info_states(self, historic):
        playerIdx = len(historic) - 1
        infoSet = self.infoSets[historic]
        beliefs = infoSet.beliefs

        possible_actions = self.get_possible_actions(historic)

        for action in possible_actions:
            # full_action = historic + action
            # next_states = self.get_next_info_states_hist(historic, action)
            utils_info_states, utils_terminal_state = 0, 0

            prob_action = infoSet.actions[action].strategy

            for i in range(0, self.number_players * self.number_coins + 1):
                prob_state = beliefs[str(i)]

                if action == str(i):
                    utils_player = self.number_players - 1
                else:
                    utils_player = -1

                utils_terminal_state += prob_state * prob_action *utils_player
                
                # if len(full_action) == self.number_players + 1:
                #     utils = self.calc_util_terminal_node(full_action, str(i))
                #     utils_terminal_state += prob_state * utils[playerIdx]
                # else:
                #     for next_state in next_states:
                #         next_state_info_set = self.infoSets[next_state]
                #         utils_info_states += prob_state * prob_action * next_state_info_set.expectedUtil

            infoSet.actions[action].util = utils_terminal_state + utils_info_states

        infoSet.expectedUtil = 0
        for action in possible_actions:
            actionData = infoSet.actions[action]
            infoSet.expectedUtil += actionData.strategy * actionData.util                    
    
    def calc_util_terminal_node(self, historic, sum_coins):
        guesses = historic[1:]

        results = [-1] * self.number_players

        for i in range(0, self.number_players):
            if guesses[i] == sum_coins:
                results[i] = self.number_players - 1
                return results
            
        return [0] * self.number_players
    
    def calc_infoset_likelihoods(self):

        for historic in self.sorted_infoSets:
            state = self.infoSets[historic]
            state.likelihood = 0

            if len(historic) == 1:
                state.likelihood = 1 / (self.number_coins + 1)
            else:
                prev_states = self.get_prev_info_states_hist(historic)
                for prev_state in prev_states:
                    state.likelihood += self.infoSets[prev_state].likelihood * self.infoSets[prev_state].actions[prev_state[-1]].strategy

    def update_beliefs(self):
        for historic in self.sorted_infoSets:
            state = self.infoSets[historic]

            coin_choosen = int(historic[0])
            playerIdx = len(historic) - 1

            possible_sum_coins = self.get_possible_coins_sum(coin_choosen)

            probs_sum = {str(i) : 0 for i in range(0, self.number_players * self.number_coins + 1)}

            prob_state = 0
            for coin_sum in possible_sum_coins:
                coin_combs = get_coin_combinations(self.number_players - 1, int(coin_sum) - coin_choosen, self.number_coins)
                prob_sum = 0
                for comb in coin_combs:
                    prob_comb = 1 / (self.number_coins + 1)
                    for i in range(0, len(comb)):
                        opp_historic = str(comb[i]) + historic[1:i+1]
                        if i < playerIdx:
                            opp_action = historic[i+1]
                            prob_comb *= self.infoSets[opp_historic].actions[opp_action].strategy 
                        else:
                            possible_actions = self.get_possible_actions(historic)
                            prob_comb *= 1 / len(possible_actions)
                    
                    prob_sum += prob_comb
                    prob_state += prob_comb
                
                probs_sum[str(coin_sum)] = prob_sum
            
            for coin_sum in probs_sum.keys():
                state.beliefs[coin_sum] = (probs_sum[coin_sum] * self.coin_sum_prior[str(coin_choosen)][int(coin_sum)]) / prob_state

        return
    
    def calc_gains(self):
        totalGain = 0.0

        for historic in self.sorted_infoSets:
            state = self.infoSets[historic]
            possible_actions = self.get_possible_actions(historic)
            for action in possible_actions:
                util = state.actions[action].util
                gain = max(0, util - state.expectedUtil)
                totalGain += gain
                state.actions[action].cumulativeGain += gain * state.likelihood
        
        return totalGain
    
    def update_strat(self):
        for historic in self.sorted_infoSets:
            state = self.infoSets[historic]
            possible_actions = self.get_possible_actions(historic)
            gains = [state.actions[action].cumulativeGain for action in possible_actions]

            totGains = sum(gains)

            for action in possible_actions:
                gain = state.actions[action].cumulativeGain
                state.actions[action].strategy = gain / totGains

class Player:
    def __init__(self, id, number_coins, number_players):
        self.id = id
        self.number_coins = number_coins
        self.number_players = number_players
        self.guess = None

        self.policy = np.array([1] * (pow(number_players, number_coins) + 1))
        self.policy = self.policy / np.sum(self.policy)

    def choose_coins(self):
        return random.randint(0, self.number_coins)

    def guess_coins(self, legal_coins):
        p = self.policy * legal_coins
        p = p / np.sum(p)
        self.guess = np.random.choice(
            range(0, self.number_players * self.number_coins + 1), p=p
        )

@lru_cache(maxsize=None)
def get_coin_combinations(num_players, coin_sum, num_coins):
    all_combinations = product(range(num_coins + 1), repeat=num_players)
    valid_combinations = []
    for comb in all_combinations:
        if sum(comb) == coin_sum:
            valid_combinations.append(comb)
    
    return valid_combinations


def save_strategy(cfr : CFR, file_name : str):

    strategy = {}
    for historic in cfr.infoSets:
        infoset = cfr.infoSets[historic]
        actions = cfr.get_possible_actions(historic)

        strategy[historic] = {action : infoset.actions[action].strategy for action in actions}

    with open(f'{file_name}.json', 'w') as f:
        json.dump(strategy, f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-nc", "--number_coins", type=int, default=1, help="Number of coins"
    )
    parser.add_argument(
        "-p", "--number_players", type=int, default=3, help="Number of players"
    )

    arglist = [x for x in sys.argv[1:] if not x.startswith("__")]
    args = vars(parser.parse_args(args=arglist))

    cfr = CFR(args["number_coins"], args["number_players"])

    cfr.init_info_sets()

    numIterations = 10_000_000_000
    totGains = []

    numGainsToPlot = 1_000_000
    gainGrpSize = numIterations // numGainsToPlot
    if gainGrpSize == 0:
        gainGrpSize = 1

    i = 0
    while True:

        cfr.update_beliefs()

        for infoSetStr in reversed(cfr.sorted_infoSets):
            cfr.update_utilities_of_info_states(infoSetStr)

        cfr.calc_infoset_likelihoods()

        totGain = cfr.calc_gains()

        if i % gainGrpSize == 0:
            totGains.append(totGain)
            print(f"It {i} -> TOT GAIN={totGain:.3f}")

        cfr.update_strat()

        i += 1
        if i >= numIterations or totGain <= 0.1:
            break


    save_strategy(cfr, f'strategies/coin_game/coin_game_c{args["number_coins"]}p{args["number_players"]}')
    # InfoSetData.printInfoSetDataTable(infoSets)

    # The if statement is just meant to make the script easier to run if you don't want to install matplotlib
    if 'matplotlib' in sys.modules:
        print(f'Plotting {len(totGains)} totGains')
        # Generate random x, y coordinates
        x = [x*gainGrpSize for x in range(len(totGains))]
        y = totGains

        # Create scatter plot
        plt.scatter(x, y)

        # Set title and labels
        plt.title('Total Gain per iteration')
        plt.xlabel(f'Iteration # ')
        plt.ylabel('Total Gain In Round')

        # Display the plot
        plt.show()



if __name__ == "__main__":
    main()
