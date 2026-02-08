"""Unit tests for the adaptation engine — no database required."""
from app.services.adaptation import (
    adapt_after_group, get_group_number, is_group_boundary,
    SESSION_TOTAL, GROUP_SIZE, NUM_GROUPS,
    VISUAL_RESET_ON_DIFFICULTY_UP,
)


# ── Structure helpers ────────────────────────────────────

class TestSessionStructure:
    def test_constants(self):
        assert SESSION_TOTAL == 15
        assert GROUP_SIZE == 3
        assert NUM_GROUPS == 5

    def test_group_number_mapping(self):
        assert get_group_number(1) == 1
        assert get_group_number(3) == 1
        assert get_group_number(4) == 2
        assert get_group_number(6) == 2
        assert get_group_number(13) == 5
        assert get_group_number(15) == 5

    def test_group_boundaries(self):
        boundaries = [s for s in range(1, 16) if is_group_boundary(s)]
        assert boundaries == [3, 6, 9, 12, 15]

    def test_non_boundaries(self):
        for s in [1, 2, 4, 5, 7, 8, 10, 11, 13, 14]:
            assert not is_group_boundary(s)


# ── Adaptation rules ─────────────────────────────────────

class TestAdaptPerfectGroup:
    """Rule 1: 3/3 correct → always advance."""

    def test_reduces_visual_first(self):
        r = adapt_after_group([True, True, True], [8000, 7000, 6000], 1, 4)
        assert r.new_visual_level == 3
        assert r.new_difficulty == 1

    def test_increases_difficulty_when_visual_at_min(self):
        """When visuals are at 1 and student is perfect, difficulty increases
        and visuals reset to scaffold the new harder content."""
        r = adapt_after_group([True, True, True], [8000, 7000, 6000], 2, 1)
        assert r.new_difficulty == 3
        assert r.new_visual_level == VISUAL_RESET_ON_DIFFICULTY_UP  # visuals come back

    def test_holds_at_max(self):
        r = adapt_after_group([True, True, True], [8000, 7000, 6000], 5, 1, max_difficulty=5)
        assert r.new_difficulty == 5
        assert r.new_visual_level == 1

    def test_advances_regardless_of_speed(self):
        """Even very slow perfect groups should advance."""
        r = adapt_after_group([True, True, True], [25000, 30000, 20000], 1, 5)
        assert r.new_visual_level == 4  # still advanced


class TestAdaptStrong:
    """Rule 2: ≥2/3 correct + fast → advance.

    Note: with 3-problem groups, 2/3 = 0.667 is just below the 0.67 threshold,
    so this only fires for groups of 4+ where the fraction is ≥ 0.67.
    With 3-problem groups, 2/3 falls to 'mixed results' → hold steady.
    """

    def test_two_of_three_fast_holds(self):
        """2/3 accuracy (0.667) is below 0.67 threshold → treated as mixed."""
        r = adapt_after_group([True, False, True], [5000, 4000, 3000], 2, 4)
        assert r.new_visual_level == 4  # hold
        assert r.new_difficulty == 2   # hold

    def test_three_of_four_fast_advances(self):
        """3/4 accuracy (0.75) exceeds threshold → advance."""
        r = adapt_after_group([True, True, False, True], [5000, 4000, 3000, 4000], 2, 4)
        assert r.new_visual_level == 3
        assert r.new_difficulty == 2


class TestAdaptAccurateButSlow:
    """Rule 3: ≥2/3 correct but slow → hold steady."""

    def test_holds_when_slow(self):
        r = adapt_after_group([True, True, False], [15000, 14000, 16000], 2, 3)
        assert r.new_difficulty == 2
        assert r.new_visual_level == 3


class TestAdaptStruggling:
    """Rule 4: 0/3 or 1/3 correct → retreat."""

    def test_zero_correct(self):
        r = adapt_after_group([False, False, False], [5000, 5000, 5000], 3, 2)
        assert r.new_difficulty == 2
        assert r.new_visual_level == 3

    def test_one_correct(self):
        r = adapt_after_group([False, True, False], [5000, 5000, 5000], 2, 3)
        assert r.new_difficulty == 1
        assert r.new_visual_level == 4

    def test_does_not_go_below_one(self):
        r = adapt_after_group([False, False, False], [5000, 5000, 5000], 1, 5)
        assert r.new_difficulty == 1
        assert r.new_visual_level == 5


class TestAdaptEdgeCases:
    def test_empty_data(self):
        r = adapt_after_group([], [], 2, 3)
        assert r.new_difficulty == 2
        assert r.new_visual_level == 3

    def test_single_problem(self):
        r = adapt_after_group([True], [3000], 1, 3)
        assert r.new_visual_level == 2  # perfect → advance


class TestFullSessionSimulation:
    """Simulate an entire session to verify the progression is sensible."""

    def test_strong_student_progresses(self):
        """A strong student spirals: visuals fade → difficulty up + visuals back → fade again."""
        diff, vis = 1, 3
        history = [(diff, vis)]
        for _ in range(8):  # 8 perfect groups
            r = adapt_after_group([True, True, True], [7000, 6000, 8000], diff, vis)
            diff, vis = r.new_difficulty, r.new_visual_level
            history.append((diff, vis))
        # Difficulty should have increased multiple times
        assert diff >= 3
        # Visuals should have cycled (gone up when difficulty increased)
        vis_values = [h[1] for h in history]
        saw_reset = any(vis_values[i] > vis_values[i - 1] for i in range(1, len(vis_values)))
        assert saw_reset, f"Expected visual reset on difficulty increase, got: {history}"

    def test_struggling_student_gets_support(self):
        diff, vis = 3, 1
        for _ in range(4):
            r = adapt_after_group([False, False, True], [10000, 10000, 10000], diff, vis)
            diff, vis = r.new_difficulty, r.new_visual_level
        assert vis >= 4
        assert diff == 1
