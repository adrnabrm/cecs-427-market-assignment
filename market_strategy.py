import networkx as nx
import argparse
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Set
import os

def build_preferred_graph(G: nx.Graph, prices: Dict[int, int]) -> nx.Graph:
    """
    Construct the preferred-seller graph based on current prices.
    
    Args:
        G: The original bipartite graph with valuations
        prices: Dictionary mapping seller node IDs to their current prices
        
    Returns:
        A bipartite graph P where edges represent preferred seller connections
    """
    P = nx.DiGraph()
    
    # Get buyers and sellers
    buyers = [n for n in G.nodes if G.nodes[n].get('bipartite') == 0]
    sellers = [n for n in G.nodes if G.nodes[n].get('bipartite') == 1]
    
    for buyer in buyers:
        max_payoff = float('-inf')
        preferred_sellers = []
        
        # Calculate payoff for each seller this buyer is connected to
        for seller in sellers:
            if G.has_edge(buyer, seller):
                valuation = G.edges[buyer, seller]['valuation']
                payoff = valuation - prices.get(seller, 0)
                
                if payoff > max_payoff:
                    max_payoff = payoff
                    preferred_sellers = [seller]
                elif payoff == max_payoff:
                    preferred_sellers.append(seller)
        
        # Only add edges if payoff is non-negative
        if max_payoff >= 0:
            for seller in preferred_sellers:
                P.add_edge(buyer, seller)
    
    return P


def find_constricted_set(P: nx.DiGraph) -> Tuple[Set[int], Set[int]]:
    """
    Find a constricted set using Hall's theorem.
    
    A set S of buyers is constricted if |N(S)| < |S| where N(S) is the 
    neighborhood of S (sellers connected to buyers in S).
    
    Args:
        P: The preferred-seller graph
        
    Returns:
        Tuple of (constricted_buyers, neighbors) where:
        - constricted_buyers: A set of buyer nodes that form a constricted set
        - neighbors: The sellers connected to these buyers
    """
    # Get all buyers and sellers in the preferred graph
    if not P.edges():
        return set(), set()
    
    buyers_in_P = set(source for source, _ in P.edges())
    sellers_in_P = set(target for _, target in P.edges())
    
    if not buyers_in_P:
        return set(), set()
    
    # Check all non-empty subsets of buyers
    from itertools import combinations
    
    for r in range(1, len(buyers_in_P) + 1):
        for subset in combinations(buyers_in_P, r):
            buyer_set = set(subset)
            neighbors = set()
            
            # Find all sellers connected to buyers in this set
            for buyer, seller in P.edges():
                if buyer in buyer_set:
                    neighbors.add(seller)
            
            # Check Hall's condition: |N(S)| < |S|
            if len(neighbors) < len(buyer_set):
                return buyer_set, neighbors
    
    return set(), set()


def market_clearing(G: nx.Graph, interactive: bool = False) -> Tuple[List[Tuple[int, int]], Dict[int, int]]:
    """
    Market-clearing algorithm to find perfect matching and market-clearing prices.
    
    Args:
        G: Bipartite graph with buyers, sellers, and edge valuations
        interactive: If True, show detailed output for each round
        
    Returns:
        Tuple of (matching, prices) where:
        - matching: List of (buyer, seller) pairs
        - prices: Dictionary mapping seller IDs to final prices
    """
    # Get sellers
    sellers = [n for n in G.nodes if G.nodes[n].get('bipartite') == 1]
    
    # Initialize prices to 0 for all sellers
    prices = {seller: 0 for seller in sellers}
    
    max_iterations = 1000  # Safety limit
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # 1. Construct preferred-seller graph
        P = build_preferred_graph(G, prices)
        
        if interactive:
            print(f"\n{'='*60}")
            print(f"ROUND {iteration}")
            print(f"{'='*60}")
            print(f"\nCurrent Prices: {prices}")
        
        # Get buyers and sellers from original graph
        all_buyers = [n for n in G.nodes if G.nodes[n].get('bipartite') == 0]
        all_sellers = [n for n in G.nodes if G.nodes[n].get('bipartite') == 1]
        
        # Show preferred seller graph details
        if interactive:
            print(f"\nPREFERRED SELLER GRAPH:")
            buyers_in_P = set(source for source, _ in P.edges())
            for buyer in all_buyers:
                if buyer not in buyers_in_P:
                    print(f"  Buyer {buyer}: No preferred sellers (all payoffs negative)")
                else:
                    preferred = [s for b, s in P.edges() if b == buyer]
                    # Calculate payoffs for this buyer
                    payoffs = {}
                    for seller in preferred:
                        if G.has_edge(buyer, seller):
                            valuation = G.edges[buyer, seller]['valuation']
                            price = prices.get(seller, 0)
                            payoffs[seller] = valuation - price
                    if payoffs:
                        max_payoff = max(payoffs.values())
                        print(f"  Buyer {buyer}: Preferred sellers = {preferred}, Payoff = {max_payoff}")
            print(f"  Edges: {list(P.edges())}")
        
        # 2. Check if there exists a perfect matching
        # Try to find maximum bipartite matching
        buyers_in_P = set(source for source, _ in P.edges())
        sellers_in_P = set(target for _, target in P.edges())
        
        if not buyers_in_P:
            # No buyers have any preferred sellers (all payoffs negative)
            # This means prices are too high, but we can't find a matching
            # Try to lower prices or signal that no matching exists
            pass
        
        if buyers_in_P and sellers_in_P:
            # Find maximum matching
            matching = nx.bipartite.maximum_matching(P, top_nodes=buyers_in_P)
            
            # Check if it's perfect (all buyers matched)
            matched_buyers = [b for b in buyers_in_P if b in matching]
            
            if interactive:
                print(f"\nMATCHING COMPUTATION:")
                print(f"  Matching found: {matching}")
                print(f"  Matched buyers: {matched_buyers}")
                print(f"  Perfect matching? {len(all_buyers) == len(matched_buyers) and matched_buyers}")
            
            if len(all_buyers) == len(matched_buyers) and matched_buyers:
                # Convert matching dict to list of tuples
                matching_list = []
                for buyer in matched_buyers:
                    if buyer in matching:
                        matching_list.append((buyer, matching[buyer]))
                if interactive:
                    print(f"\n✓ PERFECT MATCHING ACHIEVED!")
                return matching_list, prices
        
        # 3. Find a constricted set
        constricted_buyers, constricted_neighbors = find_constricted_set(P)
        
        if not constricted_buyers:
            # No constriction found but no perfect matching either
            # This shouldn't happen, but raise an error
            raise RuntimeError("Unable to find constricted set or perfect matching")
        
        if interactive:
            print(f"\nCONSTRICTED SET COMPUTATION:")
            print(f"  Constricted buyers S: {constricted_buyers}")
            print(f"  Neighborhood N(S): {constricted_neighbors}")
            print(f"  Condition: |N(S)|={len(constricted_neighbors)} < |S|={len(constricted_buyers)}")
        
        # 4. According to the pseudocode:
        # S_constricted is the set of buyers (constricted_buyers)
        # N_constricted is the set of sellers (constricted_neighbors)
        # We raise prices for sellers in N_constricted
        old_prices = prices.copy()
        for seller in constricted_neighbors:
            prices[seller] += 1
        
        if interactive:
            print(f"\nPRICE UPDATE:")
            print(f"  Sellers to update: {constricted_neighbors}")
            for seller in constricted_neighbors:
                print(f"    p[{seller}]: {old_prices[seller]} → {prices[seller]}")
        else:
            print(f"Iteration {iteration}: Constricted buyers = {constricted_buyers}")
            print(f"  Their neighbor sellers = {constricted_neighbors}")
            print(f"  Raising prices for: {constricted_neighbors}")
            print(f"  Updated prices: {prices}")
    
    raise RuntimeError(f"Algorithm did not converge after {max_iterations} iterations")


def visualize_market(G: nx.Graph, matching: List[Tuple[int, int]], prices: Dict[int, int]):
    """
    Visualize the preferred-seller graph with matching and prices.
    
    Args:
        G: The original bipartite graph with valuations
        matching: List of (buyer, seller) pairs from the matching
        prices: Dictionary mapping seller IDs to final prices
    """
    # Build the preferred-seller graph
    P = build_preferred_graph(G, prices)
    
    # Create a directed graph for visualization
    plt.figure(figsize=(14, 8))
    
    # Get buyers and sellers
    buyers = [n for n in G.nodes if G.nodes[n].get('bipartite') == 0]
    sellers = [n for n in G.nodes if G.nodes[n].get('bipartite') == 1]
    
    # Position nodes in bipartite layout
    pos = {}
    # Buyers on the left
    for i, buyer in enumerate(sorted(buyers)):
        pos[buyer] = (0, i * 2)
    # Sellers on the right
    for i, seller in enumerate(sorted(sellers)):
        pos[seller] = (4, i * 2)
    
    # Create a matching set for quick lookup
    matching_set = set(matching)
    
    # Store edge info for labels
    edge_labels = {}
    offset_pos = {}
    
    # Draw only edges from the preferred-seller graph
    for buyer, seller in P.edges():
        # Check if this edge is in the matching
        is_matched = (buyer, seller) in matching_set
        color = 'green' if is_matched else 'blue'
        width = 4 if is_matched else 2
        G_draw = nx.DiGraph()
        G_draw.add_edge(buyer, seller)
        nx.draw_networkx_edges(G_draw, pos, edge_color=color, width=width, 
                               arrows=True, arrowsize=25, alpha=0.8)
        
        # Calculate payoff and store label position
        if G.has_edge(buyer, seller):
            valuation = G.edges[buyer, seller]['valuation']
            payoff = valuation - prices.get(seller, 0)
            # Position label to avoid overlaps - place above the seller node
            seller_x, seller_y = pos[seller]
            buyer_idx = sorted(buyers).index(buyer)
            seller_idx = sorted(sellers).index(seller)
            # Offset each label vertically based on which buyer is pointing to it
            label_y_offset = 0.8 + (buyer_idx - seller_idx) * 0.4
            offset_pos[(buyer, seller)] = (seller_x + 0.3, seller_y + label_y_offset)
            edge_labels[(buyer, seller)] = f'B{buyer}→p={payoff}'
    
    # Draw buyers (left side)
    matched_buyers = [buyer for buyer, _ in matching]
    buyer_colors = ['lightgreen' if buyer in matched_buyers else 'lightblue' 
                    for buyer in buyers]
    nx.draw_networkx_nodes(G, pos, nodelist=buyers, node_color=buyer_colors,
                           node_size=2500, node_shape='o')
    nx.draw_networkx_labels(G, pos, {b: f'B{b}' for b in buyers}, 
                           font_size=16, font_weight='bold')
    
    # Draw sellers (right side)
    matched_sellers = [seller for _, seller in matching]
    seller_colors = ['lightgreen' if seller in matched_sellers else 'lightcoral' 
                     for seller in sellers]
    nx.draw_networkx_nodes(G, pos, nodelist=sellers, node_color=seller_colors,
                           node_size=2500, node_shape='s')
    
    # Add seller labels with prices
    seller_labels = {s: f'S{s}\np={prices.get(s, 0)}' for s in sellers}
    nx.draw_networkx_labels(G, pos, seller_labels, font_size=14, font_weight='bold')
    
    # Add edge labels showing payoffs (positioned to the side)
    for (buyer, seller), label in edge_labels.items():
        label_pos = offset_pos[(buyer, seller)]
        plt.text(label_pos[0], label_pos[1], label, 
                fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8),
                ha='left', va='center')
    
    # Add title
    total_value = sum(G.edges[buyer, seller]['valuation'] 
                     for buyer, seller in matching)
    plt.title(f'Preferred-Seller Graph (Final Round)\n'
              f'Prices: {prices}, Matching (green edges): {matching}, Total Value = {total_value}', 
              fontsize=14, fontweight='bold')
    
    plt.axis('off')
    plt.tight_layout()
    plt.show()


def main():
    """
    Main function to run the market clearing algorithm on a GML file
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Market Clearing Algorithm')
    parser.add_argument('gml_file', help='Path to the GML file')
    parser.add_argument('--plot', action='store_true', 
                       help='Visualize the graph with matching and prices')
    parser.add_argument('--interactive', action='store_true',
                       help='Show detailed output for each round')
    args = parser.parse_args()

    # Handle non-existent file
    if not os.path.exists(args.gml_file):
        print(f"Error: File '{args.gml_file}' not found.")
        return
    
    # Load the graph from GML file
    try:
        G = nx.read_gml(args.gml_file, label='id')
    except Exception as e:
        print(f"Error reading '{args.gml_file}': {e}")
        return
    
    # Handle empty graph
    if len(G.nodes) == 0 or len(G.edges) == 0:
        print(f"Error: '{args.gml_file}' contains an empty graph.")
        return

    # Handle misising values
    for n, data in G.nodes(data=True):
        if 'bipartite' not in data:
            print(f"Error: Node {n} missing 'bipartite' attribute.")
            return

    for u, v, data in G.edges(data=True):
        if 'valuation' not in data:
            print(f"Error: Edge ({u}, {v}) missing 'valuation' attribute.")
            return
    
    if not args.interactive:
        print("Original Graph:")
        print(f"Nodes: {G.nodes(data=True)}")
        print(f"Edges: {G.edges(data=True)}")
        print()
    
    # Run market clearing algorithm
    matching, prices = market_clearing(G, interactive=args.interactive)
    
    if not args.interactive:
        print("\nMarket Clearing Results:")
    print(f"\n{'='*60}")
    print("FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Final Prices: {prices}")
    print(f"Perfect Matching: {matching}")
    
    # Calculate total value
    total_value = sum(G.edges[buyer, seller]['valuation'] for buyer, seller in matching)
    print(f"Total Market Value: {total_value}")
    
    # Calculate individual payoffs
    print("\nIndividual Payoffs:")
    for buyer, seller in matching:
        valuation = G.edges[buyer, seller]['valuation']
        price = prices[seller]
        payoff = valuation - price
        print(f"Buyer {buyer} -> Seller {seller}: "
              f"valuation={valuation}, price={price}, payoff={payoff}")
    
    # Plot if requested
    if args.plot:
        visualize_market(G, matching, prices)


if __name__ == "__main__":
    main()

