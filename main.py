"""
Wildfire Simulation — Cellular Automaton
=========================================
A simple forest-fire model on a 2-D grid with three cell states:

    EMPTY (0) — bare ground
    TREE  (1) — living tree
    FIRE  (2) — burning tree

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
    python wildfire.py --growth 0.01 --lightning 0.0001 --init 0.6

Parameter sweep (all combinations, table + one plot window per combo):
    python wildfire.py --sweep-growth 0.005,0.01,0.02 \
                       --sweep-lightning 0.0001,0.0005 \
                       --init 0.6

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
TREE  = 1
FIRE  = 2

N    = 100   # grid size (N × N)
TICKS = 1000  # simulation duration

# Colour map: EMPTY = dark brown, TREE = forest green, FIRE = orange-red
CMAP = mcolors.ListedColormap(["#3b2a1a", "#2d6a2d", "#e84c0e"])
NORM = mcolors.BoundaryNorm([-0.5, 0.5, 1.5, 2.5], CMAP.N)


# ---------------------------------------------------------------------------
# Core model functions  (unchanged from previous version)
# ---------------------------------------------------------------------------

def init_grid(p_tree: float) -> np.ndarray:
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
    return np.random.choice(
        [EMPTY, TREE],
        size=(N, N),
        p=[1.0 - p_tree, p_tree],
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


def step(grid: np.ndarray, p_growth: float, p_lightning: float) -> np.ndarray:
    """
    Advance the simulation by one time step.

    Parameters
    ----------
    grid : np.ndarray, shape (N, N)
    p_growth : float
    p_lightning : float

    Returns
    -------
    np.ndarray, shape (N, N)
    """
    new_grid   = grid.copy()
    rnd        = np.random.random((N, N))
    fire_mask  = (grid == FIRE).astype(int)
    burning_nb = count_burning_neighbours(fire_mask)

    new_grid[grid == FIRE] = EMPTY                                         # FIRE  → EMPTY
    ignites = (grid == TREE) & ((burning_nb > 0) | (rnd < p_lightning))
    new_grid[ignites] = FIRE                                               # TREE  → FIRE
    grows   = (grid == EMPTY) & (rnd < p_growth)
    new_grid[grows] = TREE                                                 # EMPTY → TREE

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


def run_simulation(p_growth: float, p_lightning: float, p_init: float
                   ) -> tuple[list[float], list[float], list[float], list[int]]:
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
    grid               = init_grid(p_init)
    fire_sizes         = []
    tree_densities     = []
    mean_cluster_sizes = []
    num_clusters       = []

    for _ in range(TICKS):
        fire_sizes.append(float(np.sum(grid == FIRE)))
        tree_densities.append(float(np.sum(grid == TREE)) / N ** 2)
        mean_s, n_clust = cluster_stats(grid)
        mean_cluster_sizes.append(mean_s)
        num_clusters.append(n_clust)
        grid = step(grid, p_growth, p_lightning)

    return fire_sizes, tree_densities, mean_cluster_sizes, num_clusters


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_results(p_growth: float, p_lightning: float, p_init: float,
                 fire_sizes: list[float], tree_densities: list[float],
                 mean_cluster_sizes: list[float], num_clusters: list[int]) -> None:
    """
    Show a four-panel time-series plot for a single parameter combination.

    Panels
    ------
    1. Total burning cells per tick
    2. Tree density per tick
    3. Mean fire-cluster size per tick  (connected components)
    4. Number of fire clusters per tick (connected components)

    Parameters
    ----------
    p_growth, p_lightning, p_init : float
    fire_sizes, tree_densities, mean_cluster_sizes : list[float]
    num_clusters : list[int]
    """
    ticks = range(TICKS)
    fig, axes = plt.subplots(4, 1, figsize=(9, 10), sharex=True)
    fig.suptitle(
        f"growth={p_growth}  lightning={p_lightning}  init={p_init}",
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
    _panel(axes[1], tree_densities,     "#2d6a2d", "Tree density",      fmt=".3f")
    _panel(axes[2], mean_cluster_sizes, "#e08020", "Mean cluster size")
    _panel(axes[3], num_clusters,       "#8040c0", "# fire clusters")

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
    p.add_argument("--init",      type=float, default=0.6,
                   help="Initial tree density.")

    # Sweep overrides (comma-separated lists)
    p.add_argument("--sweep-growth",    type=parse_float_list, default=None,
                   metavar="v1,v2,...",
                   help="Sweep over these growth values.")
    p.add_argument("--sweep-lightning", type=parse_float_list, default=None,
                   metavar="v1,v2,...",
                   help="Sweep over these lightning values.")
    p.add_argument("--sweep-init",      type=parse_float_list, default=None,
                   metavar="v1,v2,...",
                   help="Sweep over these init-density values.")
    return p


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point: parse arguments, run simulation(s), print table, show plots."""
    args = build_parser().parse_args()

    # Build the list of (growth, lightning, init) combinations to run
    growth_values    = args.sweep_growth    or [args.growth]
    lightning_values = args.sweep_lightning or [args.lightning]
    init_values      = args.sweep_init      or [args.init]

    combos = list(itertools.product(growth_values, lightning_values, init_values))
    is_sweep = len(combos) > 1

    # Table header
    print(f"\n{'growth':>10} {'lightning':>12} {'init':>6} "
          f"{'mean_fire':>12} {'mean_tree':>10} {'mean_cluster':>14} {'mean_n_clusters':>16}")
    print("-" * 80)

    for p_growth, p_lightning, p_init in combos:
        fire_sizes, tree_densities, mean_cluster_sizes, num_clusters = \
            run_simulation(p_growth, p_lightning, p_init)

        mean_fire    = np.mean(fire_sizes)
        mean_tree    = np.mean(tree_densities)
        mean_cluster = np.mean(mean_cluster_sizes)
        mean_n_clust = np.mean(num_clusters)

        print(f"{p_growth:>10.4f} {p_lightning:>12.5f} {p_init:>6.2f} "
              f"{mean_fire:>12.2f} {mean_tree:>10.4f} "
              f"{mean_cluster:>14.2f} {mean_n_clust:>16.2f}")

        plot_results(p_growth, p_lightning, p_init,
                     fire_sizes, tree_densities, mean_cluster_sizes, num_clusters)

    print()
    plt.show()  # open all plot windows at once — blocks only here


if __name__ == "__main__":
    main()