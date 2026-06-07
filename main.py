"""
Wildfire Simulation — Cellular Automaton
=========================================
A simple forest-fire model on a 2-D grid with three cell states:

    EMPTY  (0) — bare ground
    TREE_A (1) — living tree, species A (highly flammable)
    FIRE   (2) — burning tree
    TREE_B (3) — living tree, species B (fire resistant)

Transition rules (applied simultaneously each step):
    FIRE  → EMPTY  (burned-out cell)
    TREE  → FIRE   if at least one of the 8 Moore neighbours is on fire,
                   OR a lightning strike occurs (probability p_lightning)
    EMPTY → TREE   with probability p_growth

Boundary conditions: closed (fixed). Cells outside the grid are treated
as EMPTY, so fire cannot wrap around the edges.

Usage examples
--------------
Single run (shows animation + time-series plots):
    uv run main.py --growth 0.01 --lightning 0.0001 --init-a 0.6 --init-b 0.0

Only species B:
    uv run main.py --init-a 0.0 --init-b 0.6

Mixed forest:
    uv run main.py --init-a 0.3 --init-b 0.3 --spread-a 1.0 --spread-b 0.4

Parameter sweep:
    uv run main.py --sweep-growth 0.005,0.01,0.02 \
                       --sweep-lightning 0.0001,0.0005 \
                       --sweep-spread-b 0.2,0.4,0.6 \
                       --init-a 0.3 --init-b 0.3

Any mix of fixed and swept parameters is allowed.
"""

import argparse
import itertools

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import label as ndlabel
import matplotlib.colors as mcolors

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EMPTY = 0
TREE_A  = 1
FIRE  = 2
TREE_B = 3

N    = 100   # grid size (N × N)
TICKS = 1000  # simulation duration

# Colour map: EMPTY = dark brown, TREE = forest green, FIRE = orange-red
CMAP = mcolors.ListedColormap(["#3b2a1a", "#2d6a2d", "#e84c0e", "#a3c96e" ])
NORM = mcolors.BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], CMAP.N)


# ---------------------------------------------------------------------------
# Core model functions  (unchanged from previous version)
# ---------------------------------------------------------------------------

def init_grid(p_tree_a: float, p_tree_b: float) -> np.ndarray:
    """
    Create a new N×N grid with trees placed randomly.

    Parameters
    ----------
    p_tree : float
        Probability [0, 1] that any given cell starts as a TREE.

    Returns
    -------
    np.ndarray, shape (N, N), dtype int
    """
    p_empty = 1.0 - p_tree_a - p_tree_b
    return np.random.choice(
        [EMPTY, TREE_A, TREE_B],
        size=(N, N),
        p=[p_empty, p_tree_a, p_tree_b],
    )


def count_burning_neighbours(fire_mask: np.ndarray) -> np.ndarray:
    """
    Count how many of the 8 Moore neighbours of each cell are on fire.

    Boundary condition: closed — cells outside the grid count as EMPTY.

    Parameters
    ----------
    fire_mask : np.ndarray, shape (N, N), dtype int

    Returns
    -------
    np.ndarray, shape (N, N), dtype int
    """
    padded = np.pad(fire_mask, pad_width=1, mode="constant", constant_values=0)
    neighbours = np.zeros((N, N), dtype=int)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            neighbours += padded[1 + di : N + 1 + di, 1 + dj : N + 1 + dj]
    return neighbours


def step(grid: np.ndarray, p_growth: float, p_lightning: float,
         p_spread_a: float, p_spread_b: float,
         p_init_a: float, p_init_b: float) -> np.ndarray:
    """
    Advance the simulation by one time step.

    Parameters
    ----------
    grid : np.ndarray, shape (N, N)
    p_growth : float
    p_lightning : float
    p_spread_a : float
        Ignition probability for TREE_A when a burning neighbour is present.
    p_spread_b : float
        Ignition probability for TREE_B when a burning neighbour is present.
    p_init_a : float
        Initial density of TREE_A — used to determine regrowth ratio.
    p_init_b : float
        Initial density of TREE_B — used to determine regrowth ratio.

    Returns
    -------
    np.ndarray, shape (N, N)
    """
    new_grid   = grid.copy()
    rnd        = np.random.random((N, N))
    fire_mask  = (grid == FIRE).astype(int)
    burning_nb = count_burning_neighbours(fire_mask)

    # FIRE → EMPTY
    new_grid[grid == FIRE] = EMPTY

    # TREE_A → FIRE
    ignites_a = (grid == TREE_A) & (
        ((burning_nb > 0) & (rnd < p_spread_a)) | (rnd < p_lightning)
    )
    new_grid[ignites_a] = FIRE

    # TREE_B → FIRE
    ignites_b = (grid == TREE_B) & (
        ((burning_nb > 0) & (rnd < p_spread_b)) | (rnd < p_lightning)
    )
    new_grid[ignites_b] = FIRE

    # EMPTY → TREE_A or TREE_B (proportional to initial densities)
    total = p_init_a + p_init_b
    p_a   = p_init_a / total if total > 0 else 1.0
    p_b   = p_init_b / total if total > 0 else 0.0

    grows = (grid == EMPTY) & (rnd < p_growth)
    new_grid[grows] = np.random.choice(
        [TREE_A, TREE_B], size=(N, N), p=[p_a, p_b]
    )[grows]

    return new_grid


# ---------------------------------------------------------------------------
# Simulation runner
# ---------------------------------------------------------------------------

def cluster_stats(grid: np.ndarray) -> tuple[float, int]:
    """
    Compute connected-component statistics for burning cells.

    Uses 8-connectivity (Moore neighbourhood) via scipy.ndimage.label so that
    diagonally adjacent fire cells belong to the same cluster — consistent with
    the rest of the simulation.

    Parameters
    ----------
    grid : np.ndarray, shape (N, N)

    Returns
    -------
    mean_size : float
        Mean cluster size in cells (0.0 if no fire).
    num_clusters : int
        Number of distinct fire clusters (0 if no fire).
    """
    fire_mask = (grid == FIRE).astype(int)
    # np.ones((3,3)) = 8-connectivity structure
    _, num_clusters = ndlabel(fire_mask, structure=np.ones((3, 3)))
    total_fire = int(fire_mask.sum())
    mean_size  = total_fire / num_clusters if num_clusters > 0 else 0.0
    return mean_size, num_clusters


def run_simulation(p_growth: float, p_lightning: float, p_init_a: float,
                   p_init_b: float, p_spread_a: float, p_spread_b: float
                   ) -> tuple[list[float], list[float], list[float], list[float], list[int]]:
    """
    Run the simulation for TICKS steps and record per-tick statistics.

    Parameters
    ----------
    p_growth : float
    p_lightning : float
    p_init : float

    Returns
    -------
    fire_sizes : list[float]
        Total number of burning cells at each tick.
    tree_densities : list[float]
        Fraction of cells that are trees at each tick.
    mean_cluster_sizes : list[float]
        Mean size of connected fire clusters at each tick.
    num_clusters : list[int]
        Number of distinct fire clusters at each tick.
    """
    grid               = init_grid(p_tree_a=p_init_a, p_tree_b=p_init_b)
    fire_sizes         = []
    tree_a_densities     = []
    tree_b_densities     = []
    mean_cluster_sizes = []
    num_clusters       = []

    for _ in range(TICKS):
        fire_sizes.append(float(np.sum(grid == FIRE)))
        tree_a_densities.append(float(np.sum(grid == TREE_A)) / N**2)
        tree_b_densities.append(float(np.sum(grid == TREE_B)) / N**2)
        mean_s, n_clust = cluster_stats(grid)
        mean_cluster_sizes.append(mean_s)
        num_clusters.append(n_clust)
        grid = step(grid, p_growth, p_lightning, p_spread_a, p_spread_b, p_init_a, p_init_b)

    return fire_sizes, tree_a_densities, tree_b_densities, mean_cluster_sizes, num_clusters


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_results(p_growth: float, p_lightning: float, p_init_a: float,
                 p_init_b: float, fire_sizes: list[float], tree_a_densities: list[float], 
                 tree_b_densities: list[float], mean_cluster_sizes: list[float],
                 num_clusters: list[int]) -> None:
    """
    Show a five-panel time-series plot for a single parameter combination.

    Panels
    ------
    1. Total burning cells per tick
    2. Tree A density per tick
    3. Tree B density per tick
    4. Mean fire-cluster size per tick  (connected components)
    5. Number of fire clusters per tick (connected components)

    Parameters
    ----------
    p_growth, p_lightning, p_init : float
    fire_sizes, tree_densities, mean_cluster_sizes : list[float]
    num_clusters : list[int]
    """
    ticks = range(TICKS)
    fig, axes = plt.subplots(5, 1, figsize=(9, 10), sharex=True)
    fig.suptitle(
        f"growth={p_growth}  lightning={p_lightning}  init_a={p_init_a}  init_b={p_init_b}",
        fontsize=11, fontweight="bold",
    )

    def _panel(ax, data, color, ylabel, fmt=".1f"):
        ax.plot(ticks, data, color=color, linewidth=0.9)
        ax.axhline(np.mean(data), color=color, linestyle="--",
                   linewidth=1.2, label=f"mean = {np.mean(data):{fmt}}")
        ax.set_ylabel(ylabel)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    _panel(axes[0], fire_sizes,         "#e84c0e", "Burning cells")
    _panel(axes[1], tree_a_densities, "#2d6a2d", "Tree A density", fmt=".3f")
    _panel(axes[2], tree_b_densities, "#a3c96e", "Tree B density", fmt=".3f")
    _panel(axes[3], mean_cluster_sizes, "#e08020", "Mean cluster size")
    _panel(axes[4], num_clusters,       "#8040c0", "# fire clusters")

    axes[-1].set_xlabel("Tick")
    plt.tight_layout()


# ---------------------------------------------------------------------------
# Argument parsing helpers
# ---------------------------------------------------------------------------

def parse_float_list(value: str) -> list[float]:
    """Parse a comma-separated string of floats, e.g. '0.01,0.02,0.05'."""
    return [float(v) for v in value.split(",")]


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    p = argparse.ArgumentParser(
        description="Wildfire cellular automaton simulation.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # Single-value parameters
    p.add_argument("--growth",    type=float, default=0.01,
                   help="Tree growth probability (EMPTY → TREE).")
    p.add_argument("--lightning", type=float, default=0.0001,
                   help="Lightning probability (TREE → FIRE).")
    p.add_argument("--init-a",      type=float, default=0.6,
                   help="Initial tree density for species A.")
    p.add_argument("--init-b",    type=float, default=0.0, 
                    help="Initial tree density for species B.")
    p.add_argument("--spread-a",  type=float, default=1.0,  
                help="Probability of ignation for tree species A.")
    p.add_argument("--spread-b",  type=float, default=0.4,  
                help="Probability of ignation for tree species B.")

    # Sweep overrides (comma-separated lists)
    p.add_argument("--sweep-growth",    type=parse_float_list, default=None,
                   metavar="v1,v2,...",
                   help="Sweep over these growth values.")
    p.add_argument("--sweep-lightning", type=parse_float_list, default=None,
                   metavar="v1,v2,...",
                   help="Sweep over these lightning values.")
    p.add_argument("--sweep-init-a",      type=parse_float_list, default=None,
                   metavar="v1,v2,...",
                   help="Sweep over these init-density values for species A.")
    p.add_argument("--sweep-init-b",   type=parse_float_list, default=None,
                   metavar="v1,v2,...",
                   help="Sweep over these init-density values for species B.")
    p.add_argument("--sweep-spread-a", type=parse_float_list, default=None,
                   metavar="v1,v2,...",
                   help="Sweep over these spread-a values (for species A).")
    p.add_argument("--sweep-spread-b", type=parse_float_list, default=None,
                   metavar="v1,v2,...",
                   help="Sweep over these spread-b values (for species B).")
    return p


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point: parse arguments, run simulation(s), print table, show plots."""
    args = build_parser().parse_args()
    np.random.seed(42) 

    # Build the list of (growth, lightning, init) combinations to run
    growth_values    = args.sweep_growth    or [args.growth]
    lightning_values = args.sweep_lightning or [args.lightning]
    init_a_values   = args.sweep_init_a   or [args.init_a]
    init_b_values   = args.sweep_init_b   or [args.init_b]
    spread_a_values = args.sweep_spread_a or [args.spread_a]
    spread_b_values = args.sweep_spread_b or [args.spread_b]

    combos = list(itertools.product(
        growth_values, lightning_values, init_a_values,
        init_b_values, spread_a_values, spread_b_values
    ))
    is_sweep = len(combos) > 1

    # Table header
    print(f"\n{'growth':>10} {'lightning':>12} {'init_a':>7} {'init_b':>7} "
          f"{'spread_a':>9} {'spread_b':>9} {'mean_fire':>12}"
          f"{'mean_tree_a':>12} {'mean_tree_b':>12} {'mean_cluster':>14} {'mean_n_clusters':>16}")
    print("-" * 80)

    for p_growth, p_lightning, p_init_a, p_init_b, p_spread_a, p_spread_b in combos:
        fire_sizes, tree_a_densities, tree_b_densities, mean_cluster_sizes, num_clusters = \
            run_simulation(p_growth, p_lightning, p_init_a, p_init_b, p_spread_a, p_spread_b)

        mean_fire    = np.mean(fire_sizes)
        mean_tree_a = np.mean(tree_a_densities)
        mean_tree_b = np.mean(tree_b_densities)
        mean_cluster = np.mean(mean_cluster_sizes)
        mean_n_clust = np.mean(num_clusters)

        print(f"{p_growth:>10.4f} {p_lightning:>12.5f} {p_init_a:>7.2f} {p_init_b:>7.2f} "
              f"{p_spread_a:>9.2f} {p_spread_b:>9.2f} {mean_fire:>12.2f} "
              f"{p_spread_a:>9.2f} {p_spread_b:>9.2f} {mean_fire:>12.2f} {mean_cluster:>14.2f} {mean_n_clust:>16.2f}")

        plot_results(p_growth, p_lightning, p_init_a, p_init_b,
                     fire_sizes, tree_a_densities, tree_b_densities, mean_cluster_sizes, num_clusters)

    print()
    plt.show()  # open all plot windows at once — blocks only here


if __name__ == "__main__":
    main()