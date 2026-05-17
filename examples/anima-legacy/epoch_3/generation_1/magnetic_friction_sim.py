"""
Productive Friction Simulation
==============================

Core idea: in many systems, some resistance to change is beneficial.
  - Zero friction = chaos (agents whipsaw on every noisy observation)
  - Maximum friction = stasis (agents never update, drift from truth)
  - There is an optimum in between, and it depends on the environment.

Model:
  - 40x40 grid of agents, each holding a position value in [0, 1]
  - An external "truth" that drifts slowly with occasional sudden shifts
  - Each agent observes truth with Gaussian noise
  - Each agent has a friction parameter controlling resistance to change
  - Agents feel social pressure from neighbors (average neighbor position)

Three experiments:
  1. Uniform friction sweep
  2. Mixed friction populations
  3. Adaptive (self-tuning) friction
"""

import random
import math
import time

# --- Try numpy for speed, fall back to pure Python ---
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# =====================================================================
# Parameters
# =====================================================================
GRID = 40
N_AGENTS = GRID * GRID
STEPS = 200
OBSERVATION_NOISE = 0.15
SOCIAL_WEIGHT = 0.3       # how much neighbors influence vs own observation
SEED = 42

# =====================================================================
# Truth signal: slow drift + sudden shifts
# =====================================================================
def generate_truth(steps, seed=SEED):
    """Generate a truth signal: slow sine drift with sudden jumps."""
    rng = random.Random(seed)
    truth = []
    value = 0.5
    for t in range(steps):
        # Slow drift component
        value += 0.002 * math.sin(2 * math.pi * t / 80)
        # Sudden shift at t=60, t=130
        if t == 60:
            value += 0.25
        if t == 130:
            value -= 0.30
        # Keep in bounds
        value = max(0.0, min(1.0, value))
        truth.append(value)
    return truth


# =====================================================================
# Grid simulation (numpy path)
# =====================================================================
def run_sim_numpy(friction_grid, truth_signal, noise_std=OBSERVATION_NOISE,
                  social_w=SOCIAL_WEIGHT, seed=SEED):
    """Run simulation on a 40x40 grid. Returns list of per-step mean errors.

    Social influence is weighted by confidence (1 - friction): low-friction
    neighbors who update fast exert more social pull than high-friction ones.
    This creates an information flow asymmetry that lets mixed populations
    potentially outperform uniform ones.
    """
    rng = np.random.RandomState(seed)
    positions = np.full((GRID, GRID), 0.5)
    errors = []

    # Confidence weights (how much each agent influences neighbors)
    confidence = 1.0 - friction_grid  # low friction = high confidence

    for t, truth in enumerate(truth_signal):
        # Each agent observes truth + noise
        obs = truth + rng.normal(0, noise_std, (GRID, GRID))
        obs = np.clip(obs, 0, 1)

        # Confidence-weighted neighbor average
        # Each neighbor contributes position * confidence, then normalize
        pos_weighted = positions * confidence
        padded_pw = np.pad(pos_weighted, 1, mode='constant', constant_values=0)
        padded_cw = np.pad(confidence, 1, mode='constant', constant_values=0)

        sum_pw = (padded_pw[:-2, 1:-1] + padded_pw[2:, 1:-1] +
                  padded_pw[1:-1, :-2] + padded_pw[1:-1, 2:])
        sum_cw = (padded_cw[:-2, 1:-1] + padded_cw[2:, 1:-1] +
                  padded_cw[1:-1, :-2] + padded_cw[1:-1, 2:])
        sum_cw = np.maximum(sum_cw, 1e-10)  # avoid division by zero
        neighbor_avg = sum_pw / sum_cw

        # Target = blend of observation and social signal
        target = (1 - social_w) * obs + social_w * neighbor_avg

        # Update: move toward target, modulated by friction
        # friction=0 -> jump to target; friction=1 -> stay put
        positions = positions + (1 - friction_grid) * (target - positions)
        positions = np.clip(positions, 0, 1)

        # Error
        err = np.mean(np.abs(positions - truth))
        errors.append(err)

    return errors


# =====================================================================
# Grid simulation (pure Python path)
# =====================================================================
def run_sim_pure(friction_grid, truth_signal, noise_std=OBSERVATION_NOISE,
                 social_w=SOCIAL_WEIGHT, seed=SEED):
    """Pure-Python fallback. friction_grid is list-of-lists."""
    rng = random.Random(seed)
    positions = [[0.5] * GRID for _ in range(GRID)]
    errors = []

    def gauss():
        return rng.gauss(0, noise_std)

    def clamp(v):
        return max(0.0, min(1.0, v))

    for t, truth in enumerate(truth_signal):
        new_positions = [[0.0] * GRID for _ in range(GRID)]
        total_err = 0.0

        for r in range(GRID):
            for c in range(GRID):
                obs = clamp(truth + gauss())

                # Confidence-weighted neighbor average
                sum_pw = 0.0
                sum_cw = 0.0
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < GRID and 0 <= nc < GRID:
                        conf = 1.0 - friction_grid[nr][nc]
                        sum_pw += positions[nr][nc] * conf
                        sum_cw += conf
                n_avg = sum_pw / max(sum_cw, 1e-10)

                target = (1 - social_w) * obs + social_w * n_avg
                fric = friction_grid[r][c]
                new_positions[r][c] = clamp(
                    positions[r][c] + (1 - fric) * (target - positions[r][c])
                )
                total_err += abs(new_positions[r][c] - truth)

        positions = new_positions
        errors.append(total_err / N_AGENTS)

    return errors


# =====================================================================
# Adaptive friction simulation (numpy)
# =====================================================================
def run_adaptive_numpy(truth_signal, noise_std=OBSERVATION_NOISE,
                       social_w=SOCIAL_WEIGHT, seed=SEED):
    """Agents adjust their own friction based on recent performance."""
    rng = np.random.RandomState(seed)
    positions = np.full((GRID, GRID), 0.5)
    frictions = np.full((GRID, GRID), 0.5)  # start at middle friction
    prev_errors = np.full((GRID, GRID), 0.1)
    errors = []
    friction_history = []

    LEARN_RATE = 0.05
    WINDOW = 5
    error_buffer = []

    for t, truth in enumerate(truth_signal):
        obs = truth + rng.normal(0, noise_std, (GRID, GRID))
        obs = np.clip(obs, 0, 1)

        confidence = 1.0 - frictions
        pos_weighted = positions * confidence
        padded_pw = np.pad(pos_weighted, 1, mode='constant', constant_values=0)
        padded_cw = np.pad(confidence, 1, mode='constant', constant_values=0)
        sum_pw = (padded_pw[:-2, 1:-1] + padded_pw[2:, 1:-1] +
                  padded_pw[1:-1, :-2] + padded_pw[1:-1, 2:])
        sum_cw = (padded_cw[:-2, 1:-1] + padded_cw[2:, 1:-1] +
                  padded_cw[1:-1, :-2] + padded_cw[1:-1, 2:])
        neighbor_avg = sum_pw / np.maximum(sum_cw, 1e-10)

        target = (1 - social_w) * obs + social_w * neighbor_avg
        positions = positions + (1 - frictions) * (target - positions)
        positions = np.clip(positions, 0, 1)

        current_err = np.abs(positions - truth)
        err = np.mean(current_err)
        errors.append(err)
        error_buffer.append(current_err.copy())

        # Adaptive friction update every WINDOW steps
        if len(error_buffer) >= WINDOW:
            recent = np.mean(error_buffer[-WINDOW:], axis=0)
            # If error is high, try changing friction
            # Strategy: if error increased, nudge friction toward 0.5
            # If error is low, keep current friction
            # Simple gradient-free rule: decrease friction if position is far
            # from recent observations, increase if position is jittery
            if len(error_buffer) >= 2 * WINDOW:
                older = np.mean(error_buffer[-2*WINDOW:-WINDOW], axis=0)
                delta = recent - older  # positive = getting worse
                # If getting worse, flip direction of friction change
                frictions = frictions + LEARN_RATE * delta * 2
                # Also pull toward moderate values
                frictions = frictions + 0.01 * (0.5 - frictions)
                frictions = np.clip(frictions, 0.05, 0.95)

        friction_history.append(np.mean(frictions))

    return errors, friction_history


# =====================================================================
# Adaptive friction simulation (pure Python)
# =====================================================================
def run_adaptive_pure(truth_signal, noise_std=OBSERVATION_NOISE,
                      social_w=SOCIAL_WEIGHT, seed=SEED):
    """Pure-Python adaptive friction."""
    rng = random.Random(seed)
    positions = [[0.5] * GRID for _ in range(GRID)]
    frictions = [[0.5] * GRID for _ in range(GRID)]
    errors = []
    friction_history = []

    LEARN_RATE = 0.05
    WINDOW = 5
    # Store per-agent error history (ring buffer of last 2*WINDOW)
    error_buf = []

    def clamp(v):
        return max(0.0, min(1.0, v))

    def clamp_f(v):
        return max(0.05, min(0.95, v))

    for t, truth in enumerate(truth_signal):
        new_positions = [[0.0] * GRID for _ in range(GRID)]
        agent_errors = [[0.0] * GRID for _ in range(GRID)]
        total_err = 0.0

        for r in range(GRID):
            for c in range(GRID):
                obs = clamp(truth + rng.gauss(0, noise_std))
                neighbors = []
                if r > 0:       neighbors.append(positions[r-1][c])
                if r < GRID-1:  neighbors.append(positions[r+1][c])
                if c > 0:       neighbors.append(positions[r][c-1])
                if c < GRID-1:  neighbors.append(positions[r][c+1])
                n_avg = sum(neighbors) / len(neighbors)

                target = (1 - social_w) * obs + social_w * n_avg
                fric = frictions[r][c]
                new_positions[r][c] = clamp(
                    positions[r][c] + (1 - fric) * (target - positions[r][c])
                )
                ae = abs(new_positions[r][c] - truth)
                agent_errors[r][c] = ae
                total_err += ae

        positions = new_positions
        errors.append(total_err / N_AGENTS)
        error_buf.append(agent_errors)

        if len(error_buf) >= 2 * WINDOW:
            for r in range(GRID):
                for c in range(GRID):
                    recent = sum(error_buf[k][r][c]
                                 for k in range(-WINDOW, 0)) / WINDOW
                    older = sum(error_buf[k][r][c]
                                for k in range(-2*WINDOW, -WINDOW)) / WINDOW
                    delta = recent - older
                    frictions[r][c] = clamp_f(
                        frictions[r][c] + LEARN_RATE * delta * 2
                        + 0.01 * (0.5 - frictions[r][c])
                    )
            # Trim buffer
            if len(error_buf) > 3 * WINDOW:
                error_buf = error_buf[-2*WINDOW:]

        fric_sum = sum(frictions[r][c] for r in range(GRID) for c in range(GRID))
        friction_history.append(fric_sum / N_AGENTS)

    return errors, friction_history


# =====================================================================
# Dispatcher
# =====================================================================
def run_simulation(friction_grid, truth_signal, **kw):
    if HAS_NUMPY:
        if not isinstance(friction_grid, np.ndarray):
            friction_grid = np.array(friction_grid)
        return run_sim_numpy(friction_grid, truth_signal, **kw)
    else:
        if not isinstance(friction_grid[0], list):
            friction_grid = [[friction_grid[r][c] for c in range(GRID)]
                             for r in range(GRID)]
        return run_sim_pure(friction_grid, truth_signal, **kw)


def run_adaptive(truth_signal, **kw):
    if HAS_NUMPY:
        return run_adaptive_numpy(truth_signal, **kw)
    else:
        return run_adaptive_pure(truth_signal, **kw)


# =====================================================================
# Visualization helpers
# =====================================================================
def spark_line(values, width=50):
    """Tiny text sparkline."""
    mn, mx = min(values), max(values)
    if mx - mn < 1e-12:
        return "-" * width
    blocks = " ▁▂▃▄▅▆▇█"
    out = []
    step = max(1, len(values) // width)
    for i in range(0, len(values), step):
        chunk = values[i:i+step]
        v = sum(chunk) / len(chunk)
        idx = int((v - mn) / (mx - mn) * (len(blocks) - 1))
        out.append(blocks[idx])
    return "".join(out[:width])


def bar(value, max_val, width=40, label=""):
    """Simple horizontal bar."""
    filled = int(width * value / max_val) if max_val > 0 else 0
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled) + f" {label}"


# =====================================================================
# EXPERIMENT 1: Uniform Friction Sweep
# =====================================================================
def experiment_1(truth_signal):
    print("=" * 70)
    print("  EXPERIMENT 1: Uniform Friction Sweep")
    print("=" * 70)
    print()
    print("  PREDICTION: Optimal friction will be moderate (around 0.3-0.5).")
    print("  Zero friction means agents chase every noisy observation.")
    print("  High friction means agents cannot track the truth at all.")
    print("  The sweet spot balances noise filtering with responsiveness.")
    print()

    friction_levels = [i * 0.05 for i in range(21)]  # 0.00 to 1.00
    results = {}

    for fric in friction_levels:
        if HAS_NUMPY:
            fg = np.full((GRID, GRID), fric)
        else:
            fg = [[fric] * GRID for _ in range(GRID)]
        errs = run_simulation(fg, truth_signal)
        avg_err = sum(errs) / len(errs)
        results[fric] = (avg_err, errs)

    # Find optimal
    best_fric = min(results, key=lambda f: results[f][0])
    worst_fric = max(results, key=lambda f: results[f][0])
    max_err = results[worst_fric][0]

    print(f"  {'Friction':>10} | {'Avg Error':>10} | {'Bar':40}")
    print("  " + "-" * 66)

    for fric in friction_levels:
        avg_err = results[fric][0]
        marker = " <-- BEST" if fric == best_fric else ""
        b = bar(avg_err, max_err, 40)
        print(f"  {fric:10.2f} | {avg_err:10.4f} | {b}{marker}")

    print()
    print(f"  Optimal uniform friction: {best_fric:.2f}")
    print(f"  Best average error:       {results[best_fric][0]:.4f}")
    print(f"  Error at friction=0.00:   {results[0.0][0]:.4f}")
    print(f"  Error at friction=1.00:   {results[1.0][0]:.4f}")
    print()

    # Show error over time for best, worst, and extremes
    print("  Error over time (sparklines, 200 steps):")
    for fric in [0.0, best_fric, 0.95, 1.0]:
        if fric in results:
            sl = spark_line(results[fric][1])
            print(f"    friction={fric:.2f}: {sl}  (avg={results[fric][0]:.4f})")

    print()
    return best_fric, results[best_fric][0]


# =====================================================================
# EXPERIMENT 2: Mixed Friction Populations
# =====================================================================
def experiment_2(truth_signal, best_uniform_fric, best_uniform_err):
    print("=" * 70)
    print("  EXPERIMENT 2: Mixed Friction Populations")
    print("=" * 70)
    print()
    print("  PREDICTION: A mix of low-friction and high-friction agents")
    print("  will outperform uniform friction. Low-friction agents react fast")
    print("  to real changes; high-friction agents anchor the group during noise.")
    print("  The social pressure channel lets them complement each other.")
    print("  We test random mixes and also a structured checkerboard layout.")
    print()

    low_fric = 0.05
    high_fric = 0.90

    # Part A: Random mixes at various ratios
    ratios = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    results = {}
    for ratio_low in ratios:
        if HAS_NUMPY:
            rng = np.random.RandomState(SEED)
            mask = rng.random((GRID, GRID)) < ratio_low
            fg = np.where(mask, low_fric, high_fric)
        else:
            rng = random.Random(SEED)
            fg = [[low_fric if rng.random() < ratio_low else high_fric
                   for _ in range(GRID)] for _ in range(GRID)]
        errs = run_simulation(fg, truth_signal)
        avg_err = sum(errs) / len(errs)
        results[ratio_low] = avg_err

    # Part B: Structured checkerboard (every other cell is low-friction)
    if HAS_NUMPY:
        checker = np.fromfunction(lambda r, c: ((r + c) % 2 == 0),
                                  (GRID, GRID))
        fg_checker = np.where(checker, low_fric, high_fric)
    else:
        fg_checker = [[low_fric if (r + c) % 2 == 0 else high_fric
                        for c in range(GRID)] for r in range(GRID)]
    errs_checker = run_simulation(fg_checker, truth_signal)
    checker_err = sum(errs_checker) / len(errs_checker)

    best_ratio = min(results, key=lambda r: results[r])
    all_errs = list(results.values()) + [checker_err]
    max_err = max(all_errs)
    best_mix_err = min(min(results.values()), checker_err)

    print(f"  Low friction = {low_fric}, High friction = {high_fric}")
    print()
    print(f"  Part A: Random spatial mixes")
    print(f"  {'% Low':>8} | {'Avg Error':>10} | {'Bar':40}")
    print("  " + "-" * 64)

    for ratio in ratios:
        marker = " <-- BEST" if results[ratio] == min(results.values()) else ""
        b = bar(results[ratio], max_err, 40)
        print(f"  {ratio*100:7.0f}% | {results[ratio]:10.4f} | {b}{marker}")

    print()
    print(f"  Part B: Checkerboard layout (50% low, 50% high, structured)")
    b = bar(checker_err, max_err, 40)
    print(f"  {'checker':>8} | {checker_err:10.4f} | {b}")

    print()
    print(f"  Best random mix error:   {min(results.values()):.4f} ({best_ratio*100:.0f}% low)")
    print(f"  Checkerboard error:      {checker_err:.4f}")
    print(f"  Best uniform error:      {best_uniform_err:.4f} (at friction={best_uniform_fric:.2f})")

    improvement = (best_uniform_err - best_mix_err) / best_uniform_err * 100
    if best_mix_err < best_uniform_err:
        print(f"  Improvement over uniform: {improvement:.1f}%")
        print()
        print("  RESULT: Mixed friction OUTPERFORMS best uniform friction!")
    elif abs(improvement) < 2:
        print(f"  Difference: {improvement:.1f}%")
        print()
        print("  RESULT: Mixed friction is COMPARABLE to best uniform.")
        print("  The complementarity effect exists but is subtle.")
    else:
        print(f"  Difference: {improvement:.1f}%")
        print()
        print("  RESULT: Mixed friction does NOT outperform best uniform.")
        print("  Why? Each agent's update quality depends on ITS OWN friction.")
        print("  Low-friction agents are noisy; high-friction agents are slow.")
        print("  Social coupling transmits noise FROM low-friction agents,")
        print("  canceling the stability benefit of high-friction agents.")
        print("  Lesson: diversity helps only if the communication channel")
        print("  can filter signal from noise -- raw coupling is not enough.")

    print()
    return best_ratio, best_mix_err


# =====================================================================
# EXPERIMENT 3: Adaptive Friction
# =====================================================================
def experiment_3(truth_signal, best_uniform_err, best_mix_err):
    print("=" * 70)
    print("  EXPERIMENT 3: Adaptive (Self-Tuning) Friction")
    print("=" * 70)
    print()
    print("  PREDICTION: Adaptive friction should approach the best uniform")
    print("  performance, possibly better. Agents that self-tune can increase")
    print("  friction during noise and decrease it during real shifts.")
    print("  However, the adaptation has lag, so it may not beat a well-chosen")
    print("  static friction on a short run (200 steps).")
    print()

    errors, fric_hist = run_adaptive(truth_signal)
    avg_err = sum(errors) / len(errors)

    print("  Error over time:")
    print(f"    {spark_line(errors)}")
    print()
    print("  Average friction over time:")
    print(f"    {spark_line(fric_hist)}")
    print()
    print(f"  Final average friction:    {fric_hist[-1]:.4f}")
    print(f"  Adaptive average error:    {avg_err:.4f}")
    print(f"  Best uniform error:        {best_uniform_err:.4f}")
    print(f"  Best mixed error:          {best_mix_err:.4f}")
    print()

    if avg_err < best_uniform_err:
        print("  RESULT: Adaptive friction BEATS best uniform!")
    elif avg_err < best_uniform_err * 1.05:
        print("  RESULT: Adaptive friction is COMPARABLE to best uniform.")
    else:
        print("  RESULT: Adaptive friction UNDERPERFORMS best uniform.")
        print("  This is expected with short runs -- adaptation needs time.")

    if avg_err < best_mix_err:
        print("  Adaptive also beats the best mixed-friction configuration.")
    print()

    return avg_err


# =====================================================================
# Main
# =====================================================================
def main():
    print()
    print("*" * 70)
    print("  PRODUCTIVE FRICTION SIMULATION")
    print("  How much resistance to change is optimal?")
    print("*" * 70)
    print()
    print(f"  Grid: {GRID}x{GRID} = {N_AGENTS} agents")
    print(f"  Steps: {STEPS}")
    print(f"  Observation noise: {OBSERVATION_NOISE}")
    print(f"  Social weight: {SOCIAL_WEIGHT}")
    print(f"  Backend: {'numpy' if HAS_NUMPY else 'pure Python (slower)'}")
    print()

    # Generate truth signal
    truth = generate_truth(STEPS)
    print("  Truth signal over time:")
    print(f"    {spark_line(truth)}")
    print(f"    (range: {min(truth):.3f} to {max(truth):.3f})")
    print(f"    Sudden shift up at t=60, sudden shift down at t=130")
    print()

    t0 = time.time()

    # Experiment 1
    best_fric, best_uniform_err = experiment_1(truth)

    # Experiment 2
    best_ratio, best_mix_err = experiment_2(truth, best_fric, best_uniform_err)

    # Experiment 3
    adaptive_err = experiment_3(truth, best_uniform_err, best_mix_err)

    elapsed = time.time() - t0

    # Summary
    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print()
    print(f"  {'Method':<30} | {'Avg Error':>10}")
    print("  " + "-" * 45)
    print(f"  {'Zero friction (f=0.00)':<30} | {'--':>10}")
    print(f"  {'Best uniform (f=' + f'{best_fric:.2f}' + ')':<30} | {best_uniform_err:10.4f}")
    print(f"  {'Best mixed (' + f'{best_ratio*100:.0f}' + '% low)':<30} | {best_mix_err:10.4f}")
    print(f"  {'Adaptive (self-tuning)':<30} | {adaptive_err:10.4f}")
    print()

    print("  KEY INSIGHT:")
    print("  Friction is not waste -- it is a filtering mechanism.")
    print("  Too little friction and agents amplify noise.")
    print("  Too much friction and agents miss real changes.")
    print("  The optimum depends on the signal-to-noise ratio")
    print("  and the frequency of genuine shifts in truth.")
    print()
    print(f"  Completed in {elapsed:.1f}s")
    print()


if __name__ == "__main__":
    main()
