"""
Rules-based adaptation logic.
All rules are transparent and explainable — no black-box AI.

Session structure:
  15 problems = 5 groups of 3
  After each group, we evaluate the group's accuracy + speed
  and adjust difficulty_level and visual_support_level for the next group.

Adaptation axes:
  1. difficulty_level (1–5): governs the complexity of generated problems
  2. visual_support_level (1–5): governs whether/how much visual scaffolding is shown
     5 = full static visuals (bars + shading shown)
     4 = full static visuals
     3 = interactive visuals (student builds the visual / places starting point)
     2 = interactive visuals
     1 = no visuals

Advance logic:
  Visual support is reduced first (5→4→…→1). Once visuals are at 1,
  difficulty increases AND visual support resets to 4 so that the new
  harder content is scaffolded again. This creates a spiral:
    visuals on → visuals off → harder content with visuals on → visuals off → …

Rules (evaluated per group of 3):
  1. Perfect group (3/3 correct) → ALWAYS advance (see above).
  2. Fast + accurate (≥2/3 correct, avg < 12s) → advance.
  3. Accurate but slow (≥2/3 correct, avg ≥ 12s) → hold steady.
  4. Struggling (0/3 or 1/3 correct) → increase support:
       increase visual support, decrease difficulty.
"""

from dataclasses import dataclass
from typing import List

# ── Thresholds ───────────────────────────────────────────
# These are intentionally generous. Interactive visuals (dragging,
# shading) take time, so speed thresholds account for that.
SPEED_FAST_MS = 12000   # under 12s per problem = "reasonably fast"
SPEED_SLOW_MS = 20000   # over 20s per problem = "slow" (for dashboard)

# ── Session structure ────────────────────────────────────
# Defaults (used by most skills)
SESSION_TOTAL = 15
GROUP_SIZE = 3
NUM_GROUPS = SESSION_TOTAL // GROUP_SIZE  # 5 groups

# Per-problem-type overrides.
# Multiplication facts need more reps to cover the fact space at each level.
_SESSION_CONFIGS = {
    "multiplication_facts": {"session_total": 25, "group_size": 5, "num_groups": 5},
}
_DEFAULT_SESSION_CONFIG = {"session_total": SESSION_TOTAL, "group_size": GROUP_SIZE, "num_groups": NUM_GROUPS}


def get_session_config(problem_type: str) -> dict:
    """Return (session_total, group_size, num_groups) for a given problem type."""
    return dict(_SESSION_CONFIGS.get(problem_type, _DEFAULT_SESSION_CONFIG))


@dataclass
class AdaptationResult:
    new_difficulty: int
    new_visual_level: int
    reason: str           # human-readable explanation


def get_group_number(sequence_number: int, group_size: int = GROUP_SIZE, num_groups: int = NUM_GROUPS) -> int:
    """Return 1-based group number for a given 1-based sequence number."""
    return min(num_groups, ((sequence_number - 1) // group_size) + 1)


def is_group_boundary(sequence_number: int, group_size: int = GROUP_SIZE) -> bool:
    """Return True if this sequence number is the last problem in a group."""
    return sequence_number % group_size == 0


VISUAL_RESET_ON_DIFFICULTY_UP = 4  # when difficulty increases, reset visuals here


def _advance(difficulty, visual_level, max_difficulty):
    """Reduce visual support first; once at minimum, increase difficulty.

    When difficulty increases, visual support resets to VISUAL_RESET_ON_DIFFICULTY_UP
    so that the new harder content gets scaffolding again. This creates a spiral:
      visuals on → visuals off → harder + visuals on → visuals off → …
    """
    if visual_level > 1:
        return difficulty, visual_level - 1
    elif difficulty < max_difficulty:
        return difficulty + 1, VISUAL_RESET_ON_DIFFICULTY_UP
    return difficulty, visual_level


def _retreat(difficulty, visual_level):
    """Increase visual support first; also lower difficulty if > 1."""
    new_vis = min(5, visual_level + 1)
    new_diff = max(1, difficulty - 1)
    return new_diff, new_vis


def adapt_after_group(
    group_correct: List[bool],
    group_times_ms: List[int],
    current_difficulty: int,
    current_visual_level: int,
    max_difficulty: int = 5,
) -> AdaptationResult:
    """
    Evaluate a completed group of problems and decide adjustments.
    Called after every GROUP_SIZE answers.
    """
    if len(group_correct) == 0:
        return AdaptationResult(current_difficulty, current_visual_level, "No data yet")

    num_correct = sum(group_correct)
    total = len(group_correct)
    accuracy = num_correct / total
    avg_time = sum(group_times_ms) / len(group_times_ms) if group_times_ms else 15000

    new_diff = current_difficulty
    new_vis = current_visual_level

    # ── Rule 1: Perfect group (3/3) → ALWAYS advance ──
    if num_correct == total:
        new_diff, new_vis = _advance(current_difficulty, current_visual_level, max_difficulty)
        if new_diff == current_difficulty and new_vis == current_visual_level:
            reason = (
                f"Perfect ({num_correct}/{total}, avg {avg_time/1000:.1f}s). "
                f"Already at max level (difficulty {current_difficulty}, visuals {current_visual_level})."
            )
        elif new_vis < current_visual_level:
            reason = (
                f"Perfect ({num_correct}/{total}, avg {avg_time/1000:.1f}s). "
                f"Reducing visual support {current_visual_level}→{new_vis}."
            )
        else:
            reason = (
                f"Perfect ({num_correct}/{total}, avg {avg_time/1000:.1f}s), visuals already minimal. "
                f"Increasing difficulty {current_difficulty}→{new_diff}."
            )

    # ── Rule 2: Strong (≥2/3 correct) + reasonably fast → advance ──
    elif accuracy >= 0.67 and avg_time <= SPEED_FAST_MS:
        new_diff, new_vis = _advance(current_difficulty, current_visual_level, max_difficulty)
        if new_vis < current_visual_level:
            reason = (
                f"Strong ({num_correct}/{total}, avg {avg_time/1000:.1f}s). "
                f"Reducing visual support {current_visual_level}→{new_vis}."
            )
        elif new_diff > current_difficulty:
            reason = (
                f"Strong ({num_correct}/{total}, avg {avg_time/1000:.1f}s), visuals minimal. "
                f"Increasing difficulty {current_difficulty}→{new_diff}."
            )
        else:
            reason = (
                f"Strong ({num_correct}/{total}, avg {avg_time/1000:.1f}s). "
                f"Holding at top level."
            )

    # ── Rule 3: Accurate but slow → hold steady ──
    elif accuracy >= 0.67:
        reason = (
            f"Accurate ({num_correct}/{total}) but working carefully (avg {avg_time/1000:.1f}s). "
            f"Holding difficulty {current_difficulty}, visuals {current_visual_level}."
        )

    # ── Rule 4: Struggling (< 45 % correct) → retreat ──
    # With 3-problem groups: 0/3 or 1/3 triggers retreat.
    # With 5-problem groups: 0/5, 1/5, or 2/5 triggers retreat.
    elif accuracy < 0.45:
        new_diff, new_vis = _retreat(current_difficulty, current_visual_level)
        reason = (
            f"Struggling ({num_correct}/{total}). "
            f"Adjusting to difficulty {new_diff}, visuals {new_vis}."
        )

    # ── Middle ground (e.g. 3/5 = 60 %) → hold steady ──
    else:
        reason = (
            f"Mixed results ({num_correct}/{total}, avg {avg_time/1000:.1f}s). "
            f"Holding at difficulty {current_difficulty}, visuals {current_visual_level}."
        )

    return AdaptationResult(new_diff, new_vis, reason)


def compute_fluency_status(
    accuracy: float,
    avg_time_ms: float,
    *,
    sessions_completed: int = 0,
    max_difficulty_reached: int = 0,
    skill_max_difficulty: int = 5,
    min_sessions_for_fluent: int = 3,
) -> str:
    """
    Return a fluency status for teacher dashboard.

    Statuses (in order of mastery):
      not_started  — 0 completed sessions
      needs_data   — fewer than 2 completed sessions
      needs_support — accuracy < 50 %
      developing   — accuracy 50-84 %, or < 3 sessions
      progressing  — accuracy >= 85 % but hasn't reached max difficulty
      fluent       — accuracy >= 85 %, fast enough, AND reached max difficulty

    For multiplication facts this means a student can't be "fluent"
    until they have successfully practiced 9–12 s (difficulty 5).
    """
    if sessions_completed == 0:
        return "not_started"

    if sessions_completed < 2:
        return "needs_data"

    if accuracy < 0.50:
        return "needs_support"

    if accuracy < 0.85 or sessions_completed < min_sessions_for_fluent:
        return "developing"

    # Accurate (>= 85 %) with enough sessions — check difficulty coverage
    if max_difficulty_reached < skill_max_difficulty:
        return "progressing"

    # Reached max difficulty + high accuracy — check speed
    if avg_time_ms <= SPEED_SLOW_MS:
        return "fluent"

    # Accurate at max difficulty but still slow
    return "progressing"


def compute_visual_trend(visual_levels: List[int]) -> str:
    """Determine if visual support usage is trending up or down."""
    if len(visual_levels) < 3:
        return "stable"
    recent = visual_levels[-3:]
    if recent[-1] < recent[0]:
        return "decreasing"
    elif recent[-1] > recent[0]:
        return "increasing"
    return "stable"
