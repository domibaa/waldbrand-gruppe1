

"""
Forest Fire Cellular Automaton
Based on the Drossel & Schwabl (1992) model.

Usage examples:
  python forest_fire.py
  python forest_fire.py --grid-size 150 --ticks 800 --lightning-prob 0.0005
  python forest_fire.py --sweep-param lightning_prob --sweep-values 0.0001 0.001 0.01
  python forest_fire.py --replicas 5 --no-animation
"""

import argparse
import random
from dataclasses import dataclass, field
from enum import IntEnum

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
GRID_SIZE: int = 100          # number of cells per side (GRID_SIZE x GRID_SIZE)
TICKS: int = 600              # total simulation steps
BURN_IN_TICKS: int = 100      # steps discarded before recording fire sizes
TREE_GROWTH_PROB: float = 0.4  # p: probability of empty cell growing a tree
LIGHTNING_PROB: float = 0.001  # f: probability of a tree being struck by lightning
INITIAL_TREE_DENSITY: float = 0.7  # fraction of cells initialised as trees
REPLICAS: int = 1             # number of independent runs per scenario
ANIMATION_INTERVAL_MS: int = 60  # milliseconds between animation frames

# Cell states
class CellState(IntEnum):
    EMPTY = 0
    TREE = 1
    FIRE = 2


# Colour map: empty=tan, tree=forest green, fire=red
CMAP = mcolors.ListedColormap(["#d4b896", "#2d6a2d", "#e63000"])
NORM = mcolors.BoundaryNorm([0, 1, 2, 3], CMAP.N)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class SimulationConfig:
    """All tuneable parameters for one simulation scenario."""
    grid_size: int = GRID_SIZE
    ticks: int = TICKS
    burn_in_ticks: int = BURN_IN_TICKS
    tree_growth_prob: float = TREE_GROWTH_PROB
    lightning_prob: float = LIGHTNING_PROB
    initial_tree_density: float = INITIAL_TREE_DENSITY
    replicas: int = REPLICAS
    animate: bool = True
    scenario_label: str = "default"


@dataclass
class FireEvent:
    """Records a single fire event (one connected burn cluster)."""
    tick: int
    size: int          # number of cells burned in this event
    scenario: str


@dataclass
class ReplicaResult:
    """Aggregated results from one replica run."""
    replica_id: int
    scenario: str
    fire_events: list[FireEvent] = field(default_factory=list)
    tree_density_per_tick: list[float] = field(default_factory=list)

    @property
    def mean_fire_size(self) -> float:
        sizes = [e.size for e in self.fire_events]
        return float(np.mean(sizes)) if sizes else 0.0

    @property
    def max_fire_size(self) -> int:
        sizes = [e.size for e in self.fire_events]
        return int(np.max(sizes)) if sizes else 0


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------
class ForestFireModel:
    """
    Cellular automaton implementing the Drossel-Schwabl forest fire model.

    Rules (applied synchronously each tick):
      1. Empty cell → Tree with probability p
      2. Tree with a burning neighbour → Fire
      3. Tree with no burning neighbour → Fire with probability f (lightning)
      4. Fire → Empty
    """

    def __init__(self, cfg: SimulationConfig, rng: np.random.Generator):
        self.cfg = cfg
        self.rng = rng
        self.tick: int = 0
        self.grid: np.ndarray = self._init_grid()

    def _init_grid(self) -> np.ndarray:
        rand = self.rng.random((self.cfg.grid_size, self.cfg.grid_size))
        grid = np.where(rand < self.cfg.initial_tree_density,
                        CellState.TREE, CellState.EMPTY).astype(np.int8)
        return grid

    def _has_burning_neighbour(self, grid: np.ndarray) -> np.ndarray:
        """Returns boolean mask: True where at least one Moore neighbour is FIRE."""
        fire = (grid == CellState.FIRE).astype(np.int8)
        # Shift in all 8 directions and sum
        neighbour_fire = (
            np.roll(fire, 1, axis=0) + np.roll(fire, -1, axis=0) +
            np.roll(fire, 1, axis=1) + np.roll(fire, -1, axis=1) +
            np.roll(np.roll(fire, 1, axis=0), 1, axis=1) +
            np.roll(np.roll(fire, 1, axis=0), -1, axis=1) +
            np.roll(np.roll(fire, -1, axis=0), 1, axis=1) +
            np.roll(np.roll(fire, -1, axis=0), -1, axis=1)
        )
        return neighbour_fire > 0

    def step(self) -> list[FireEvent]:
        """
        Advance the grid by one tick.
        Returns a list of FireEvent objects for newly ignited clusters.
        """
        cfg = self.cfg
        grid = self.grid
        new_grid = np.copy(grid)

        is_tree = grid == CellState.TREE
        is_fire = grid == CellState.FIRE
        is_empty = grid == CellState.EMPTY

        # Rule 4: Fire → Empty
        new_grid[is_fire] = CellState.EMPTY

        # Rule 2: Tree with burning neighbour → Fire
        burning_neighbour = self._has_burning_neighbour(grid)
        spread_mask = is_tree & burning_neighbour
        new_grid[spread_mask] = CellState.FIRE

        # Rule 3: Lightning strike on tree (only if not already catching fire)
        lightning_candidates = is_tree & ~spread_mask
        lightning_strikes = self.rng.random((cfg.grid_size, cfg.grid_size)) < cfg.lightning_prob
        lightning_mask = lightning_candidates & lightning_strikes
        new_grid[lightning_mask] = CellState.FIRE

        # Rule 1: Empty → Tree
        grow_mask = is_empty & (self.rng.random((cfg.grid_size, cfg.grid_size)) < cfg.tree_growth_prob)
        new_grid[grow_mask] = CellState.TREE

        self.grid = new_grid
        self.tick += 1

        # Collect fire events (new ignitions this tick)
        fire_events: list[FireEvent] = []
        if self.tick > cfg.burn_in_ticks:
            newly_ignited = new_grid == CellState.FIRE
            total_burning = int(np.sum(newly_ignited))
            if total_burning > 0:
                fire_events.append(FireEvent(
                    tick=self.tick,
                    size=total_burning,
                    scenario=cfg.scenario_label
                ))
        return fire_events

    @property
    def tree_density(self) -> float:
        return float(np.mean(self.grid == CellState.TREE))


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def run_replica(cfg: SimulationConfig, replica_id: int,
                collect_frames: bool = False
                ) -> tuple[ReplicaResult, list[np.ndarray]]:
    """Run a single replica. Optionally collect grid frames for animation."""
    rng = np.random.default_rng(seed=replica_id * 1000 + hash(cfg.scenario_label) % 9999)
    model = ForestFireModel(cfg, rng)
    result = ReplicaResult(replica_id=replica_id, scenario=cfg.scenario_label)
    frames: list[np.ndarray] = []

    for _ in range(cfg.ticks):
        events = model.step()
        result.fire_events.extend(events)
        result.tree_density_per_tick.append(model.tree_density)
        if collect_frames:
            frames.append(model.grid.copy())

    return result, frames


# ---------------------------------------------------------------------------
# Animation
# ---------------------------------------------------------------------------
def show_animation(cfg: SimulationConfig, frames: list[np.ndarray]) -> None:
    """Display a matplotlib animation of the simulation grid."""
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor("#1a1a1a")
    ax.set_facecolor("#1a1a1a")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(
        f"Forest Fire  |  p={cfg.tree_growth_prob}  f={cfg.lightning_prob}",
        color="white", fontsize=11, pad=10
    )

    img = ax.imshow(frames[0], cmap=CMAP, norm=NORM, interpolation="nearest")
    tick_label = ax.text(0.02, 0.97, "Tick: 0", transform=ax.transAxes,
                         color="white", fontsize=9, va="top")

    def update(frame_idx: int):
        img.set_data(frames[frame_idx])
        tick_label.set_text(f"Tick: {frame_idx + 1}")
        return img, tick_label

    ani = animation.FuncAnimation(
        fig, update, frames=len(frames),
        interval=ANIMATION_INTERVAL_MS, blit=True, repeat=True
    )
    plt.tight_layout()
    plt.show()
    return ani  # keep reference so GC doesn't kill it


# ---------------------------------------------------------------------------
# Analysis plots
# ---------------------------------------------------------------------------
def plot_results(all_results: list[ReplicaResult], cfg: SimulationConfig) -> None:
    """Plot fire size distribution and tree density over time."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(f"Scenario: {cfg.scenario_label}  |  "
                 f"p={cfg.tree_growth_prob}, f={cfg.lightning_prob}, "
                 f"{cfg.replicas} replica(s)",
                 fontsize=12)

    # --- Fire size distribution (log-log) ---
    ax_dist = axes[0]
    all_sizes: list[int] = []
    for res in all_results:
        all_sizes.extend(e.size for e in res.fire_events)

    if all_sizes:
        bins = np.logspace(0, np.log10(max(all_sizes) + 1), 30)
        ax_dist.hist(all_sizes, bins=bins, color="#e63000", edgecolor="white",
                     linewidth=0.4, alpha=0.85)
        ax_dist.set_xscale("log")
        ax_dist.set_yscale("log")
        ax_dist.set_xlabel("Fire size (cells)", fontsize=11)
        ax_dist.set_ylabel("Frequency", fontsize=11)
        ax_dist.set_title("Fire Size Distribution (log-log)")
        mean_s = np.mean(all_sizes)
        ax_dist.axvline(mean_s, color="yellow", linestyle="--",
                        label=f"mean = {mean_s:.1f}")
        ax_dist.legend()

    # --- Tree density over time ---
    ax_dens = axes[1]
    ticks_axis = np.arange(1, cfg.ticks + 1)
    for res in all_results:
        ax_dens.plot(ticks_axis, res.tree_density_per_tick,
                     alpha=0.5, linewidth=0.8, color="#2d9a2d")
    if len(all_results) > 1:
        mean_density = np.mean(
            [res.tree_density_per_tick for res in all_results], axis=0
        )
        ax_dens.plot(ticks_axis, mean_density, color="white",
                     linewidth=1.5, label="mean across replicas")
        ax_dens.legend()
    ax_dens.axvline(cfg.burn_in_ticks, color="orange", linestyle=":",
                    label=f"burn-in end (t={cfg.burn_in_ticks})")
    ax_dens.set_xlabel("Tick", fontsize=11)
    ax_dens.set_ylabel("Tree density", fontsize=11)
    ax_dens.set_title("Tree Density Over Time")
    ax_dens.legend()

    plt.tight_layout()
    plt.show()


def plot_sweep_results(sweep_results: dict[str, list[ReplicaResult]],
                       sweep_param: str) -> None:
    """Summary plot for parameter sweep: mean fire size per parameter value."""
    labels, means, stds = [], [], []

    for label, results in sweep_results.items():
        all_sizes = [e.size for res in results for e in res.fire_events]
        labels.append(label)
        means.append(np.mean(all_sizes) if all_sizes else 0)
        stds.append(np.std(all_sizes) if all_sizes else 0)

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(labels))
    ax.bar(x, means, yerr=stds, color="#e63000", capsize=5,
           edgecolor="white", linewidth=0.5, alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_xlabel(f"Parameter: {sweep_param}", fontsize=11)
    ax.set_ylabel("Mean fire size (cells)", fontsize=11)
    ax.set_title(f"Parameter Sweep — {sweep_param}", fontsize=13)
    plt.tight_layout()
    plt.show()


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------
def export_csv(all_results: list[ReplicaResult], filename: str = "fire_events.csv") -> None:
    rows = [
        {"scenario": e.scenario, "replica": res.replica_id,
         "tick": e.tick, "fire_size": e.size}
        for res in all_results for e in res.fire_events
    ]
    df = pd.DataFrame(rows)
    df.to_csv(filename, index=False)
    print(f"Fire events saved to {filename}  ({len(df)} rows)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Forest Fire Cellular Automaton (Drossel & Schwabl 1992)"
    )
    parser.add_argument("--grid-size", type=int, default=GRID_SIZE,
                        help=f"Grid side length (default: {GRID_SIZE})")
    parser.add_argument("--ticks", type=int, default=TICKS,
                        help=f"Number of simulation steps (default: {TICKS})")
    parser.add_argument("--burn-in", type=int, default=BURN_IN_TICKS,
                        help=f"Steps before recording starts (default: {BURN_IN_TICKS})")
    parser.add_argument("--growth-prob", type=float, default=TREE_GROWTH_PROB,
                        help=f"Tree growth probability p (default: {TREE_GROWTH_PROB})")
    parser.add_argument("--lightning-prob", type=float, default=LIGHTNING_PROB,
                        help=f"Lightning probability f (default: {LIGHTNING_PROB})")
    parser.add_argument("--initial-density", type=float, default=INITIAL_TREE_DENSITY,
                        help=f"Initial tree density (default: {INITIAL_TREE_DENSITY})")
    parser.add_argument("--replicas", type=int, default=REPLICAS,
                        help=f"Number of independent replicas (default: {REPLICAS})")
    parser.add_argument("--no-animation", action="store_true",
                        help="Skip the grid animation")
    parser.add_argument("--export-csv", action="store_true",
                        help="Save fire events to fire_events.csv")

    # Parameter sweep
    sweep_group = parser.add_argument_group("Parameter sweep")
    sweep_group.add_argument("--sweep-param",
                             choices=["lightning_prob", "growth_prob", "initial_density"],
                             help="Parameter to sweep over")
    sweep_group.add_argument("--sweep-values", type=float, nargs="+",
                             help="Values to test in the sweep")

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    base_cfg = SimulationConfig(
        grid_size=args.grid_size,
        ticks=args.ticks,
        burn_in_ticks=args.burn_in,
        tree_growth_prob=args.growth_prob,
        lightning_prob=args.lightning_prob,
        initial_tree_density=args.initial_density,
        replicas=args.replicas,
        animate=not args.no_animation,
    )

    # ---- Parameter sweep mode ----
    if args.sweep_param and args.sweep_values:
        print(f"\nParameter sweep: {args.sweep_param} = {args.sweep_values}")
        sweep_results: dict[str, list[ReplicaResult]] = {}

        for val in args.sweep_values:
            label = f"{args.sweep_param}={val}"
            print(f"  Running scenario: {label} ...")

            cfg = SimulationConfig(
                grid_size=base_cfg.grid_size,
                ticks=base_cfg.ticks,
                burn_in_ticks=base_cfg.burn_in_ticks,
                tree_growth_prob=val if args.sweep_param == "growth_prob" else base_cfg.tree_growth_prob,
                lightning_prob=val if args.sweep_param == "lightning_prob" else base_cfg.lightning_prob,
                initial_tree_density=val if args.sweep_param == "initial_density" else base_cfg.initial_tree_density,
                replicas=base_cfg.replicas,
                animate=False,
                scenario_label=label,
            )
            replica_results = []
            for r in range(cfg.replicas):
                res, _ = run_replica(cfg, replica_id=r, collect_frames=False)
                replica_results.append(res)
                print(f"    Replica {r+1}/{cfg.replicas}  "
                      f"mean fire size: {res.mean_fire_size:.2f}  "
                      f"max fire size: {res.max_fire_size}")
            sweep_results[label] = replica_results

        if args.export_csv:
            all_flat = [res for results in sweep_results.values() for res in results]
            export_csv(all_flat, "fire_events_sweep.csv")

        plot_sweep_results(sweep_results, args.sweep_param)

    # ---- Single scenario mode ----
    else:
        base_cfg.scenario_label = (
            f"p={base_cfg.tree_growth_prob}_f={base_cfg.lightning_prob}"
        )
        all_results: list[ReplicaResult] = []
        frames: list[np.ndarray] = []

        for r in range(base_cfg.replicas):
            collect = base_cfg.animate and r == 0  # animate only first replica
            res, rep_frames = run_replica(base_cfg, replica_id=r,
                                          collect_frames=collect)
            all_results.append(res)
            if collect:
                frames = rep_frames
            print(f"Replica {r+1}/{base_cfg.replicas}  "
                  f"mean fire size: {res.mean_fire_size:.2f}  "
                  f"max fire size: {res.max_fire_size}  "
                  f"total events: {len(res.fire_events)}")

        if args.export_csv:
            export_csv(all_results)

        if base_cfg.animate and frames:
            _ani = show_animation(base_cfg, frames)  # noqa: F841 keep ref

        plot_results(all_results, base_cfg)


if __name__ == "__main__":
    main()