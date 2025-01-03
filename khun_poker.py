# This is a script taken from https://www.youtube.com/watch?v=NE7V8e77vg4&t=498s&ab_channel=JonathanGardner, and serves as a tutorial for CFR.

# I do not really like this implementation. He tried to replace tree structures with dictionaries, and it confuses me more than it helps.

from __future__ import annotations
import sys
from tabulate import tabulate
import matplotlib.pyplot as plt
import json


infoSets: dict[str, InfoSetData] = {}
sortedInfoSets = []

RANKS = ["K", "Q", "J"]
ACTIONS = ["b", "p"]

TERMINAL_ACTION_STR_MAP = {"pp", "bb", "bp", "pbb", "pbp"}

INFO_SET_ACTION_STRS = {"", "p", "b", "pb"}


def getDecidingPlayerForInfoSet(infoSetStr: str):
    return (len(infoSetStr) - 1) % 2


class InfoSetData:
    def __init__(self):
        self.actions: dict[str, InfoSetActionData] = {
            "b": InfoSetActionData(initStratVal=1 / len(ACTIONS)),
            "p": InfoSetActionData(initStratVal=1 / len(ACTIONS)),
        }

        self.beliefs: dict[str, float] = {}
        self.expectedUtil: float = None
        self.likelihood: float = None

    @staticmethod
    def printInfoSetDataTable(infoSets: dict[str, InfoSetData]):
        rows = []
        for infoSetStr in sortedInfoSets:
            infoSet = infoSets[infoSetStr]
            row = [
                infoSetStr,
                *infoSet.getStrategyTableData(),
                infoSetStr,
                *infoSet.getBeliefTableData(),
                infoSetStr,
                *infoSet.getUtilityTableData(),
                (
                    f"{infoSet.expectedUtil:.2f}"
                    if infoSet.expectedUtil != None
                    else "None"
                ),
            ]
            rows.append(row)

        headers = [
            "InfoSet",
            "Strat:Bet",
            "Strat:Pass",
            "---",
            "Belief:H",
            "Belief:L",
            "---",
            "Util:Bet",
            "Util:Pass",
            "ExpectedUtil",
            "Likelihood",
            "---",
            "TotalGain:Bet",
            "TotalGain:Pass",
        ]

        if "tabulate" in sys.modules:
            print(tabulate(rows, headers, tablefmt="pretty", stralign="left"))
        else:
            max_widths = [
                max(len(str(cell)) for cell in collumn)
                for collumn in zip(headers, *rows)
            ]

            header_line = "   ".join(
                header.ljust(width) for header, width in zip(headers, max_widths)
            )
            print(header_line)

            separator_line = "-" * (sum(max_widths) + 3 * len(headers))
            print(separator_line)

            for row in rows:
                row_line = "   ".join(
                    str(cell).ljust(width) for cell, width in zip(row, max_widths)
                )
                print(row_line)

    def getStrategyTableData(self):
        return [f"{self.actions[action].strategy:.2f}" for action in ACTIONS]

    def getUtilityTableData(self):
        return [f"{self.actions[action].util:.2f}" for action in ACTIONS]

    def getGainTableData(self):
        return [f"{self.actions[action].cumulativeGain:.2f}" for action in ACTIONS]

    def getBeliefTableData(self):
        return [f"{self.beliefs[oppPockets]:.2f}" for oppPockets in self.beliefs.keys()]


class InfoSetActionData:
    def __init__(self, initStratVal: float):
        self.strategy = initStratVal
        self.util = None
        self.cumulativeGain = initStratVal


def getPossibleOpponentPockets(pocket):
    return [rank for rank in RANKS if rank != pocket]


def getAncestralInfoSetStr(infoSetStr) -> list[InfoSetData]:
    if len(infoSetStr) == 1:
        raise ValueError(f"No ancestors for infoset={infoSetStr}")

    possibleOpponentPockets = getPossibleOpponentPockets(infoSetStr[0])
    return [oppPocket + infoSetStr[1:-1] for oppPocket in possibleOpponentPockets]


def getDescendantInfoSetStrs(infoSetStr, action):
    oppPockets = getPossibleOpponentPockets(infoSetStr[0])
    actionStr = infoSetStr[1:] + action
    return [oppPocket + actionStr for oppPocket in oppPockets]


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


def initInfoSets():
    for actionStrs in sorted(INFO_SET_ACTION_STRS, key=lambda x: len(x)):
        for rank in RANKS:
            infoSetStr = rank + actionStrs
            infoSets[infoSetStr] = InfoSetData()
            sortedInfoSets.append(infoSetStr)


def updateBeliefs():
    for infoSetStr in sortedInfoSets:
        infoSet = infoSets[infoSetStr]
        if len(infoSetStr) == 1:
            possibleOpponentPockets = getPossibleOpponentPockets(infoSetStr[0])
            for oppPocket in possibleOpponentPockets:
                infoSet.beliefs[oppPocket] = 1 / len(possibleOpponentPockets)
        else:
            ancestralInfoSetStrs = getAncestralInfoSetStr(infoSetStr)
            lastAction = infoSetStr[-1]
            tot = 0
            for oppInfoSetStr in ancestralInfoSetStrs:
                oppInfoSet = infoSets[oppInfoSetStr]
                tot += oppInfoSet.actions[lastAction].strategy
            for oppInfoSetStr in ancestralInfoSetStrs:
                oppInfoSet = infoSets[oppInfoSetStr]
                oppPocket = oppInfoSetStr[0]
                infoSet.beliefs[oppPocket] = (
                    oppInfoSet.actions[lastAction].strategy / tot
                )

    return


def updateUtilitiesForInfoSetStr(infoSetStr):
    playerIdx = getDecidingPlayerForInfoSet(infoSetStr)
    infoSet = infoSets[infoSetStr]
    beliefs = infoSet.beliefs

    for action in ACTIONS:
        actionStr = infoSetStr[1:] + action
        descendantInfoSetStrs = getDescendantInfoSetStrs(infoSetStr, action)
        utilFromInfoSets, utilFromTerminalNodes = 0, 0

        for descendantInfoSetStr in descendantInfoSetStrs:
            probOfThisInfoSet = beliefs[descendantInfoSetStr[0]]
            pockets = [infoSetStr[0], descendantInfoSetStr[0]]

            if playerIdx == 1:
                pockets = list(reversed(pockets))
            if actionStr in TERMINAL_ACTION_STR_MAP:
                utils = calcUtilityAtTerminalNode(*pockets, actionStr)
                utilFromTerminalNodes += probOfThisInfoSet * utils[playerIdx]
            else:
                descendantInfoSet = infoSets[descendantInfoSetStr]
                for oppAction in ACTIONS:
                    probOfThisAction = descendantInfoSet.actions[oppAction].strategy
                    destinationInfoSetStr = infoSetStr + action + oppAction
                    destinationActionStr = destinationInfoSetStr[1:]


                    if destinationActionStr in TERMINAL_ACTION_STR_MAP:
                        utils = calcUtilityAtTerminalNode(
                            *pockets, destinationActionStr
                        )
                        utilFromTerminalNodes += (
                            probOfThisInfoSet * probOfThisAction * utils[playerIdx]
                        )
                    else:
                        destinationInfoSet = infoSets[destinationInfoSetStr]
                        utilFromInfoSets += (
                            probOfThisInfoSet
                            * probOfThisAction
                            * destinationInfoSet.expectedUtil
                        )

        infoSet.actions[action].util = utilFromInfoSets + utilFromTerminalNodes

    infoSet.expectedUtil = 0
    for actions in ACTIONS:
        actionData = infoSet.actions[actions]
        infoSet.expectedUtil += actionData.strategy * actionData.util


def calcInfoSetLikelihoods():
    for infoSetStr in sortedInfoSets:
        infoSet = infoSets[infoSetStr]
        infoSet.likelihood = 0

        possibleOppPockets = getPossibleOpponentPockets(infoSetStr[0])

        if len(infoSetStr) == 1:
            infoSet.likelihood = 1 / len(RANKS)
        elif len(infoSetStr) == 2:
            for oppPocket in possibleOppPockets:
                oppInfoSet = infoSets[oppPocket + infoSetStr[1:-1]]
                infoSet.likelihood += oppInfoSet.actions[infoSetStr[-1]].strategy / (
                    len(RANKS) * len(possibleOppPockets)
                )
        else:
            for oppPocket in possibleOppPockets:
                oppInfoSet = infoSets[oppPocket + infoSetStr[1:-1]]
                infoSetTwoLevelsAgo = infoSets[infoSetStr[:-2]]
                ancestorLikelihood = infoSetTwoLevelsAgo.likelihood / len(
                    possibleOppPockets
                )
                infoSet.likelihood += (
                    oppInfoSet.actions[infoSetStr[-1]].strategy * ancestorLikelihood
                )


def calcGains():
    totAddedGain = 0.0
    for infoSetStr in sortedInfoSets:
        infoSet = infoSets[infoSetStr]
        for action in ACTIONS:
            utilForActionPureStrat = infoSet.actions[action].util
            gain = max(0, utilForActionPureStrat - infoSet.expectedUtil)
            totAddedGain += gain
            infoSet.actions[action].cumulativeGain += gain * infoSet.likelihood
    return totAddedGain


def updateStrategies():
    for infoSetStr in sortedInfoSets:
        infoSet = infoSets[infoSetStr]
        gains = [infoSet.actions[action].cumulativeGain for action in ACTIONS]
        totGains = sum(gains)
        for action in ACTIONS:
            gain = infoSet.actions[action].cumulativeGain
            infoSet.actions[action].strategy = gain / totGains


def setInitialStrategiesToSpecificValues():

    # player 1
    infoSets["K"].actions["b"].strategy = 2 / 3
    infoSets["K"].actions["p"].strategy = 1 / 3

    infoSets["Q"].actions["b"].strategy = 1 / 2
    infoSets["Q"].actions["p"].strategy = 1 / 2

    infoSets["J"].actions["b"].strategy = 1 / 3
    infoSets["J"].actions["p"].strategy = 2 / 3

    infoSets["Kpb"].actions["b"].strategy = 1
    infoSets["Kpb"].actions["p"].strategy = 0

    infoSets["Qpb"].actions["b"].strategy = 1 / 2
    infoSets["Qpb"].actions["p"].strategy = 1 / 2

    infoSets["Jpb"].actions["b"].strategy = 0
    infoSets["Jpb"].actions["p"].strategy = 1

    # player 2
    infoSets["Kb"].actions["b"].strategy = 1
    infoSets["Kb"].actions["p"].strategy = 0
    infoSets["Kp"].actions["b"].strategy = 1
    infoSets["Kp"].actions["p"].strategy = 0

    infoSets["Qb"].actions["b"].strategy = 1 / 2
    infoSets["Qb"].actions["p"].strategy = 1 / 2
    infoSets["Qp"].actions["b"].strategy = 2 / 3
    infoSets["Qp"].actions["p"].strategy = 1 / 3

    infoSets["Jb"].actions["b"].strategy = 0
    infoSets["Jb"].actions["p"].strategy = 1
    infoSets["Jp"].actions["b"].strategy = 1 / 3
    infoSets["Jp"].actions["p"].strategy = 2 / 3

def save_strategy():
    with open('strategy.json', 'w') as f:
        json.dump({infoSetStr: {action: infoSet.actions[action].strategy for action in ACTIONS} for infoSetStr, infoSet in infoSets.items()}, f)


if __name__ == "__main__":
    initInfoSets()

    numIterations = 1_000_000
    totGains = []

    numGainsToPlot = 500_000
    gainGrpSize = numIterations // numGainsToPlot
    if gainGrpSize == 0:
        gainGrpSize = 1

    for i in range(numIterations):

        updateBeliefs()

        for infoSetStr in reversed(sortedInfoSets):
            updateUtilitiesForInfoSetStr(infoSetStr)

        calcInfoSetLikelihoods()

        totGain = calcGains()

        if i % gainGrpSize == 0:
            totGains.append(totGain)
            print(f"TOT GAIN={totGain:.3f}")

        updateStrategies()

    save_strategy()
    InfoSetData.printInfoSetDataTable(infoSets)

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
