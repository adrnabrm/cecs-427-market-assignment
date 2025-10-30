# CECS 427: Market and Strategic Interaction in Network

## Authors

Adrian Abraham   (030133153)
Matthew Fehr     (030014801)

## Overview

This project implements the **Market-Clearing Algorithm** for bipartite assignment markets. The algorithm finds market-clearing prices and a perfect matching between buyers and sellers that maximizes total market value.

## Files

- `market_strategy.py` - Main program implementing the market clearing algorithm
- `market.gml` - Sample market graph in Graph Modelling Language format
- `README.md` - This file

## Requirements

- Python 3.x
- NetworkX
- Matplotlib
- argparse (built-in)

Install dependencies:
```bash
pip install networkx matplotlib
```

## Usage

### Basic Execution

Run the program with a market graph file:

```bash
python ./market_strategy.py market.gml
```

### Interactive Mode

Show detailed output for each round of the algorithm:

```bash
python ./market_strategy.py market.gml --interactive
```

### Plot Mode

Visualize the final preferred-seller graph with the matching:

```bash
python ./market_strategy.py market.gml --plot
```

### Combined Modes

Use both plotting and interactive output:

```bash
python ./market_strategy.py market.gml --plot --interactive
```

## Market Graph Format (GML)

The `market.gml` file encodes a bipartite graph where:
- **Buyers** (set A): nodes with `bipartite=0` (0, 1, 2, ..., n-1)
- **Sellers** (set B): nodes with `bipartite=1` (n, n+1, ..., 2n-1)
- **Edges**: connections from buyers to sellers with `valuation` attribute

Example:
```gml
edge [
  source 0
  target 3
  valuation 12
]
```

## Output

The program outputs:
1. **Final Prices** - Market-clearing prices for each seller
2. **Perfect Matching** - Optimal buyer-seller pairs
3. **Total Market Value** - Sum of valuations in the matching
4. **Individual Payoffs** - Buyer payoffs (valuation - price)

In interactive mode, you also see:
- Current prices at each round
- Preferred-seller graph construction
- Matching computation results
- Constricted set identification
- Price updates

## Algorithm

The market-clearing algorithm:
1. Initializes all seller prices to 0
2. Constructs the preferred-seller graph based on current prices
3. Finds a maximum matching
4. If perfect matching achieved: return prices and matching
5. Otherwise: identifies a constricted set and raises prices
6. Repeats until perfect matching is found

## Examples

### Example 1: Basic Run
```bash
$ python ./market_strategy.py market.gml
Market Clearing Results:
Final Prices: {3: 0, 4: 2, 5: 0}
Perfect Matching: [(0, 3), (1, 5), (2, 4)]
Total Market Value: 23
```

### Example 2: Interactive Mode
```bash
$ python ./market_strategy.py market.gml --interactive
============================================================
ROUND 1
============================================================
Current Prices: {3: 0, 4: 0, 5: 0}
PREFERRED SELLER GRAPH:
  Buyer 0: Preferred sellers = [3], Payoff = 12
  Buyer 1: Preferred sellers = [4], Payoff = 7
  Buyer 2: Preferred sellers = [4], Payoff = 6
...
```

## Error Handling

The program handles:
- Missing or invalid GML files
- Malformed graph structures
- Convergence failures (with error messages)
- Edge cases such as empty graphs
