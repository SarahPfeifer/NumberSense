"""Unit tests for the adaptation engine — no database required."""
from app.services.adaptation import (
    adapt_after_group, get_group_number, is_group_boundary,
    compute_fluency_status, get_session_config,
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


# ── Session config ──────────────────────────────────────

class TestSessionConfig:
    def test_default_config(self):
        cfg = get_session_config("integer_addition")
        assert cfg["session_total"] == 15
        assert cfg["group_size"] == 3
        assert cfg["num_groups"] == 5

    def test_multiplication_facts_longer(self):
        cfg = get_session_config("multiplication_facts")
        assert cfg["session_total"] == 25
        assert cfg["group_size"] == 5
        assert cfg["num_groups"] == 5

    def test_unknown_type_uses_default(self):
        cfg = get_session_config("some_future_type")
        assert cfg["session_total"] == 15


class TestParameterizedGroupHelpers:
    def test_group_number_with_custom_size(self):
        """With group_size=5: problems 1-5 → group 1, 6-10 → group 2, etc."""
        assert get_group_number(1, group_size=5, num_groups=5) == 1
        assert get_group_number(5, group_size=5, num_groups=5) == 1
        assert get_group_number(6, group_size=5, num_groups=5) == 2
        assert get_group_number(25, group_size=5, num_groups=5) == 5

    def test_group_boundary_with_custom_size(self):
        """With group_size=5: boundaries at 5, 10, 15, 20, 25."""
        assert is_group_boundary(5, group_size=5)
        assert is_group_boundary(10, group_size=5)
        assert not is_group_boundary(3, group_size=5)
        assert not is_group_boundary(7, group_size=5)


class TestAdaptGroupOfFive:
    """Verify adaptation rules work correctly with 5-problem groups."""

    def test_perfect_group_of_five_advances(self):
        r = adapt_after_group([True]*5, [6000]*5, 1, 4)
        assert r.new_visual_level == 3  # advanced

    def test_four_of_five_fast_advances(self):
        """4/5 = 0.80 ≥ 0.67, fast → advance."""
        r = adapt_after_group([True, True, True, True, False], [5000]*5, 2, 4)
        assert r.new_visual_level == 3

    def test_three_of_five_holds(self):
        """3/5 = 0.60 < 0.67 → mixed results → hold."""
        r = adapt_after_group([True, True, True, False, False], [5000]*5, 2, 4)
        assert r.new_difficulty == 2
        assert r.new_visual_level == 4

    def test_two_of_five_retreats(self):
        """2/5 = 0.40 < 0.45 → struggling → retreat."""
        r = adapt_after_group([True, False, True, False, False], [5000]*5, 3, 2)
        assert r.new_difficulty == 2
        assert r.new_visual_level == 3

    def test_one_of_five_retreats(self):
        """1/5 = 0.20 < 0.45 → struggling → retreat."""
        r = adapt_after_group([False, False, False, False, True], [5000]*5, 3, 2)
        assert r.new_difficulty == 2
        assert r.new_visual_level == 3


# ── Fluency status ──────────────────────────────────────

class TestFluencyStatus:
    """compute_fluency_status should require both accuracy AND full difficulty coverage."""

    def test_not_started(self):
        assert compute_fluency_status(0, 0, sessions_completed=0) == "not_started"

    def test_needs_data_one_session(self):
        assert compute_fluency_status(1.0, 5000, sessions_completed=1,
                                      max_difficulty_reached=1,
                                      skill_max_difficulty=5) == "needs_data"

    def test_needs_support_low_accuracy(self):
        assert compute_fluency_status(0.40, 10000, sessions_completed=5,
                                      max_difficulty_reached=3,
                                      skill_max_difficulty=5) == "needs_support"

    def test_developing_moderate_accuracy(self):
        assert compute_fluency_status(0.70, 10000, sessions_completed=4,
                                      max_difficulty_reached=3,
                                      skill_max_difficulty=5) == "developing"

    def test_developing_too_few_sessions(self):
        """Even high accuracy, fewer than 3 sessions → developing."""
        assert compute_fluency_status(0.90, 8000, sessions_completed=2,
                                      max_difficulty_reached=2,
                                      skill_max_difficulty=5) == "developing"

    def test_progressing_high_accuracy_low_difficulty(self):
        """85%+ accuracy but hasn't reached max difficulty → progressing."""
        assert compute_fluency_status(0.90, 8000, sessions_completed=5,
                                      max_difficulty_reached=3,
                                      skill_max_difficulty=5) == "progressing"

    def test_progressing_high_accuracy_max_difficulty_slow(self):
        """At max difficulty + accurate but too slow → progressing."""
        assert compute_fluency_status(0.90, 25000, sessions_completed=5,
                                      max_difficulty_reached=5,
                                      skill_max_difficulty=5) == "progressing"

    def test_fluent_requires_all_conditions(self):
        """Fluent = high accuracy + fast + max difficulty + enough sessions."""
        assert compute_fluency_status(0.90, 8000, sessions_completed=5,
                                      max_difficulty_reached=5,
                                      skill_max_difficulty=5) == "fluent"

    def test_not_fluent_without_max_difficulty(self):
        """Acing 0s/1s/2s is not fluency in 0-12 multiplication."""
        status = compute_fluency_status(0.95, 5000, sessions_completed=10,
                                        max_difficulty_reached=1,
                                        skill_max_difficulty=5)
        assert status == "progressing"

    def test_legacy_defaults_generous(self):
        """Without kwargs, defaults to legacy behavior (sessions=0 → not_started)."""
        assert compute_fluency_status(0.90, 5000) == "not_started"
