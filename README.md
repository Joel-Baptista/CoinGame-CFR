# CoinGame
This project solves the coin game utilizing the Counterfactual Regret Minimization (CFR) algorithm.

## Table of Contents
- [Coin Game](#game)
- [Counterfactual Regret Minization](#counterfactual-regret-minimization)
- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Game

The **coin game** is an imperfect information game where players must evaluate the choices of others to make better-informed decisions. The game can be played by $P$ players, each starting with $C$ coins. At the beginning of each turn, every player secretly chooses a number of coins to put into play. This choice remains hidden from the other players. Then, in a predefined order, each player attempts to guess the total sum of coins in play. Players cannot repeat guesses made by others. A player wins the turn if they guess the sum correctly.

In this game, the first player in the turn order has the advantage of freely choosing any possible sum, but with minimal information about other players’ choices. Conversely, the last player benefits from observing the earlier guesses, which may hint at the number of coins in play, but has fewer guessing options available.

The original game is played with three coins and more than two players. However, our implementation allows both parameters to be input variables. For testing, we used a simpler configuration with three players and one coin per player.

## Counterfactual Regret Minimization

**Counterfactual Regret Minimization** (CFR) is an iterative algorithm used to compute a Nash equilibrium for imperfect information games. CFR minimizes "regret" for each decision point (or information set) in the game by simulating gameplay and updating strategy weights based on observed regret. Over multiple iterations, the average strategy converges to a Nash equilibrium.

An information set represents all game states a player cannot distinguish between due to imperfect information.

In the coin game implementation, an information set is represented as a string where the first value indicates the player’s coin choice, and the rest represent the previous players’ guesses of the coin sum. This string is referred to as the "history."

The iterative script performs the following steps:

1. Belief Updates:
In CFR, beliefs represent probabilities over the game states associated with each information set. In our implementation, beliefs are maintained for each possible sum given the "history." For every information set, we calculate $B$ belief states, where $B = P \times C + 1$ 

2. Utility Updates:
This step computes the expected utility for each information set based on the current strategy $U(s) = \mathbb{E}_{a \sim \pi}[U(a, s_j)]$. Utilities guide the adjustments made to strategies during subsequent updates.

3. Likelihood Calculation:
This step computes the likelihood of encountering each information set during simulated games. This involves summing the probabilities of reaching prior states, multiplied by the probability of taking the action that leads to the current state. The information set tree is updated from top to bottom, ensuring that when a prior state's probability is used, it has already been updated.

4. Gain Calculation:
While the original algorithm focuses on regret, we calculate gain, which is the symmetric counterpart of regret. Gain GG is defined as the difference between the utility of an action in a given state and the expected utility of that state: $G(a_i, s_j) = U(a_i, s_j) - U(s)$. Here, $U(a_i, s_j)$ is the expected utility of taking action $a_i$​ in state $s_j$​. Gains are set to zero if negative. These calculations align with the [original CFR algorithm paper](https://www.ma.imperial.ac.uk/~dturaev/neller-lanctot.pdf).

5. Strategy Update:
The strategy for each information set is updated based on cumulative gains. Actions with higher cumulative gain are assigned higher probabilities, reducing the exploitability of the strategy and limiting the potential gains other players can achieve. Since all players follow the same strategy, this adjustment drives the potential gains down, and the strategy towards equilibrium. The algorithm converges to a Nash equilibrium when the total gain reaches zero. However, this equilibrium may only be reached asymptotically, so we might choose to stop the algorithm after a predefined number of iterations or when the total gain falls below a specified threshold (e.g. $0.1$).

## Installation

In the installation process, we strongly recommend to use [uv](https://docs.astral.sh/uv/) as a python package manager.

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/yourproject.git
   ```
2. Navigate to the project directory:
   ```bash
   cd yourproject
   ```
4. Initiate uv project:
   ```bash
   uv init
   ```

5. Install dependencies:
   ```bash
   uv sync
   ```

---

## Usage

You can find an optimal strategy for every version of the coin game and play against it following these steps:

1. Find strategy for $C$ coins and $P$ players:
   ```bash
   uv run main.py -nc [C] -p [P]
   ```
   
2. Play with against the same strategy:
   ```bash
   uv run play_coin_game.py -nc [C] -p [P]
   ```

> [!IMPORTANT]
> This implementation is single threaded for the moment and the search space grows exponentially given $C$ and $P$


During development, we implemented CFR in the Khun Poker game as a sanity check. You can also find the optimal strategy and play against it using the following steps:

1. Find strategy:
   ```bash
   uv run khun_poker.py
   ```
2. Find strategy:
   ```bash
   uv play_run khun_poker.py
   ```

## Sources

- https://www.youtube.com/watch?v=NE7V8e77vg4&t=2375s&ab_channel=JonathanGardner
- https://github.com/jonathangardnermd/counterfactualRegretMin

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

