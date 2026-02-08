"""Unit tests for problem generation — no database required."""
import pytest
from fractions import Fraction
from app.services.problem_generator import generate_problem


PROBLEM_TYPES = [
    "fraction_comparison",
    "fraction_comparison_benchmark",
    "equivalent_fractions",
    "fraction_number_line",
    "integer_addition",
    "integer_subtraction",
    "integer_number_line",
    "multiplication_facts",
    "multiplication_scaling",
]


class TestGeneratorBasics:
    """Every problem type must return the required fields."""

    @pytest.mark.parametrize("ptype", PROBLEM_TYPES)
    def test_has_required_keys(self, ptype):
        p = generate_problem(ptype, 2)
        assert "type" in p
        assert "prompt" in p
        assert "correct_answer" in p
        assert isinstance(p["correct_answer"], str)

    @pytest.mark.parametrize("ptype", PROBLEM_TYPES)
    def test_has_visual_hint(self, ptype):
        p = generate_problem(ptype, 2)
        assert "visual_hint" in p
        assert "type" in p["visual_hint"]

    @pytest.mark.parametrize("ptype", PROBLEM_TYPES)
    def test_has_feedback_explanation(self, ptype):
        p = generate_problem(ptype, 2)
        assert "feedback_explanation" in p

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Unknown problem type"):
            generate_problem("nonexistent_type", 1)


class TestDifficultyScaling:
    """Higher difficulty should produce larger numbers / harder problems."""

    @pytest.mark.parametrize("difficulty", [1, 2, 3, 4, 5])
    def test_integer_addition_valid(self, difficulty):
        p = generate_problem("integer_addition", difficulty)
        a, b = p["operands"]
        assert int(p["correct_answer"]) == a + b

    @pytest.mark.parametrize("difficulty", [1, 2, 3, 4, 5])
    def test_integer_subtraction_valid(self, difficulty):
        p = generate_problem("integer_subtraction", difficulty)
        a, b = p["operands"]
        assert int(p["correct_answer"]) == a - b

    @pytest.mark.parametrize("difficulty", [1, 2, 3, 4, 5])
    def test_multiplication_facts_valid(self, difficulty):
        p = generate_problem("multiplication_facts", difficulty)
        a, b = p["factors"]
        assert int(p["correct_answer"]) == a * b


class TestIntegerNegativeGuarantees:
    """Difficulty 2+ should guarantee negative operands."""

    def test_difficulty_2_has_negatives(self):
        has_neg_count = 0
        for _ in range(20):
            p = generate_problem("integer_addition", 2)
            if any(x < 0 for x in p["operands"]):
                has_neg_count += 1
        # At difficulty 2, the generator guarantees at least one negative.
        # Over 20 trials, all should have negatives.
        assert has_neg_count == 20

    def test_difficulty_3_subtraction_variety(self):
        """Difficulty 3 subtraction should produce 'minus a negative' sometimes."""
        saw_minus_negative = False
        for _ in range(50):
            p = generate_problem("integer_subtraction", 3)
            _, b = p["operands"]
            if b < 0:  # a - (negative) = a - (-|b|)
                saw_minus_negative = True
                break
        assert saw_minus_negative, "Never saw a 'minus a negative' at difficulty 3"


class TestFractionProblems:
    def test_comparison_has_fraction_data(self):
        p = generate_problem("fraction_comparison", 2)
        assert p["left"]["numerator"] > 0
        assert p["left"]["denominator"] > 0
        assert p["correct_answer"] in ("<", "=", ">")
        # Visual hint should have numerator/denominator
        vh = p["visual_hint"]
        assert vh["left_numerator"] == p["left"]["numerator"]
        assert vh["right_denominator"] == p["right"]["denominator"]

    def test_equivalent_fractions_correct(self):
        for _ in range(20):
            p = generate_problem("equivalent_fractions", 2)
            orig = p["original"]
            orig_val = Fraction(orig["numerator"], orig["denominator"])
            answer = int(p["correct_answer"])
            if p["missing"] == "numerator":
                target_d = p["target_denominator"]
                assert Fraction(answer, target_d) == orig_val
            else:
                target_n = p["target_numerator"]
                assert Fraction(target_n, answer) == orig_val

    def test_benchmark_uses_fraction_bars(self):
        p = generate_problem("fraction_comparison_benchmark", 2)
        assert p["visual_hint"]["type"] == "fraction_bars"
        assert "left_numerator" in p["visual_hint"]


class TestMultiplicationCoverage:
    """The coverage-aware picker should avoid repeating facts when unseen ones exist."""

    def test_avoids_repeats_when_possible(self):
        """With seen_facts passed in, the picker should prefer unseen facts."""
        # At difficulty 1, focus = [0,1,2], so all facts are from {0,1,2}×{0,1,2}
        # That's 6 unique normalised facts: (0,0),(0,1),(0,2),(1,1),(1,2),(2,2)
        seen = set()
        for _ in range(6):
            p = generate_problem("multiplication_facts", 1, {"seen_facts": seen})
            a, b = p["factors"]
            pair = (min(a, b), max(a, b))
            seen.add(pair)

        # After 6 draws, every unique fact at level 1 should have been seen
        assert len(seen) == 6

    def test_allows_repeats_after_full_coverage(self):
        """Once all facts are seen, the picker should still work (allow repeats)."""
        all_facts = {(0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (2, 2)}
        # This should not raise — repeats are allowed after full coverage
        p = generate_problem("multiplication_facts", 1, {"seen_facts": all_facts})
        assert "factors" in p

    def test_level_5_has_high_factors(self):
        """At difficulty 5, the picker should include 9-12."""
        saw_high = set()
        for _ in range(50):
            p = generate_problem("multiplication_facts", 5, {})
            a, b = p["factors"]
            for f in [a, b]:
                if f >= 9:
                    saw_high.add(f)
        assert 9 in saw_high, "Never saw factor 9 at difficulty 5"
        assert 12 in saw_high, "Never saw factor 12 at difficulty 5"
