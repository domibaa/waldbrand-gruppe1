
# Wildfire Simulation — Cellular Automaton
=========================================
## Packages and Requirements 
This model requires the Python packages argparse, matplotlib, numpy, pandas and scipy. The necessary version can be found in the dependencies of the pyproject.toml. We used UV to manage the project if you are using UV the necessary packages will be added automatically to your environment. 

To able to save the animation as a .mp4 file the writer ffmpeg is required. 

## Basic description of the model 

The model was used to simulate a basic forest fire in a Cellular Automaton and study the influence of the tree growth probability and introducing a second tree species that is more fire resistent on the size and spread of thee fire. 

Each cell on the 2-D grid has four possible states:

    EMPTY  (0) — bare ground
    TREE_A (1) — living tree, species A (highly flammable)
    FIRE   (2) — burning tree
    TREE_B (3) — living tree, species B (fire resistant)

The transition rules (applied simultaneously each step) are:
    FIRE  → EMPTY  (burned-out cell)
    TREE  → FIRE   if at least one of the 8 Moore neighbours is on fire,
                   OR a lightning strike occurs (probability p_lightning)
    EMPTY → TREE   with probability p_growth

The boundary is closed (fixed), cells outside the grid are treated
as EMPTY, so fire cannot wrap around the edges.

## Description of the parameters 

Input parameters: 

    grid : np.ndarray, shape (N, N) 
        Size of the 2-D grid.
    p_growth : float
        Probability for the growth of TREE_A or TREE_B on an empty cell (EMPTY → TREE).
    p_lightning : float
        Probability for a tree been struck by lightning and igniting (TREE → FIRE). The default is set to p_lightning = 0.0001
    p_spread_a : float
        Ignition probability for TREE_A when a burning neighbour is present (TREE → FIRE). The default value is set to p_spread_a = 1.0
    p_spread_b : float
        Ignition probability for TREE_B when a burning neighbour is present (TREE → FIRE). The default value is set to p_spread_b = 0.6.
    p_init_a : float
        Initial density of TREE_A — used to determine regrowth ratio.
    p_init_b : float
        Initial density of TREE_B — used to determine regrowth ratio.

Output parameters of the model: 

    fire_sizes : list[float]
        Total number of burning cells at each tick.
    tree_densities : list[float]
        Fraction of cells that are trees at each tick.
    mean_cluster_sizes : list[float]
        Mean size of connected fire clusters at each tick.
    num_clusters : list[int]
        Number of distinct fire clusters at each tick.



## Usage examples

Here are some examples for running different scenarios of the simulation: 

Single run (shows animation + time-series plots):
    uv run main.py --growth 0.01 --lightning 0.0001 --init-a 0.6 --init-b 0.0

Only species B:
    uv run main.py --init-a 0.0 --init-b 0.6

Mixed forest:
    uv run main.py --init-a 0.3 --init-b 0.3 --spread-a 1.0 --spread-b 0.6

For Parameter sweeps skip the animation:
    uv run main.py --sweep-growth 0.005,0.01,0.02 \
                       --sweep-lightning 0.0001,0.0005 \
                       --sweep-spread-b 0.2,0.4,0.6 \
                       --init-a 0.3 --init-b 0.3 --no-anim

To save the animation (ffmpeg is required!): 
    uv run main.py --save-video wildfire_presentation.mp4

Any mix of fixed and swept parameters is allowed.


