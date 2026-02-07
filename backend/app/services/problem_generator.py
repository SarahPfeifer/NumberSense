"""
Problem generation engine for all three math domains.
Generates problems based on skill type and difficulty level.
All logic is transparent and rules-based (no black-box AI).
"""
import random
import math
from typing import Dict, Any, Tuple
from fractions import Fraction


def generate_problem(problem_type: str, difficulty: int, config: dict = None) -> Dict[str, Any]:
    """Main dispatcher: generate a problem based on type and difficulty."""
    generators = {
        "fraction_comparison": _fraction_comparison,
        "fraction_comparison_benchmark": _fraction_comparison_benchmark,
        "equivalent_fractions": _equivalent_fractions,
        "fraction_number_line": _fraction_number_line,
        "integer_addition": _integer_addition,
        "integer_subtraction": _integer_subtraction,
        "integer_magnitude": _integer_magnitude,
        "integer_number_line": _integer_number_line,
        "multiplication_facts": _multiplication_facts,
        "multiplication_related_facts": _multiplication_related_facts,
        "multiplication_scaling": _multiplication_scaling,
    }
    gen = generators.get(problem_type)
    if not gen:
        raise ValueError(f"Unknown problem type: {problem_type}")
    return gen(difficulty, config or {})


# ---------------------------------------------------------------------------
# FRACTIONS
# ---------------------------------------------------------------------------

def _pick_fraction(difficulty: int, exclude=None) -> Tuple[int, int]:
    """Generate a fraction (numerator, denominator) based on difficulty."""
    if difficulty <= 1:
        denoms = [2, 3, 4]
    elif difficulty <= 2:
        denoms = [2, 3, 4, 5, 6]
    elif difficulty <= 3:
        denoms = [2, 3, 4, 5, 6, 8, 10]
    elif difficulty <= 4:
        denoms = [3, 4, 5, 6, 7, 8, 9, 10, 12]
    else:
        denoms = [3, 5, 6, 7, 8, 9, 10, 11, 12]

    for _ in range(50):
        d = random.choice(denoms)
        n = random.randint(1, d - 1)
        if exclude and (n, d) == exclude:
            continue
        return (n, d)
    return (1, 2)


def _fraction_comparison(difficulty: int, config: dict) -> dict:
    n1, d1 = _pick_fraction(difficulty)
    n2, d2 = _pick_fraction(difficulty, exclude=(n1, d1))
    f1 = Fraction(n1, d1)
    f2 = Fraction(n2, d2)
    if f1 == f2:
        # Tweak to avoid equality at low difficulty
        n2 = min(n2 + 1, d2 - 1) if n2 < d2 - 1 else max(n2 - 1, 1)
        f2 = Fraction(n2, d2)

    if f1 > f2:
        correct = ">"
    elif f1 < f2:
        correct = "<"
    else:
        correct = "="

    return {
        "type": "fraction_comparison",
        "prompt": f"Compare: {n1}/{d1} ___ {n2}/{d2}",
        "left": {"numerator": n1, "denominator": d1},
        "right": {"numerator": n2, "denominator": d2},
        "choices": ["<", "=", ">"],
        "correct_answer": correct,
        "visual_hint": {
            "type": "fraction_bars",
            "left_value": float(f1),
            "right_value": float(f2),
            "left_numerator": n1,
            "left_denominator": d1,
            "right_numerator": n2,
            "right_denominator": d2,
        },
        "feedback_explanation": f"{n1}/{d1} = {float(f1):.3f} and {n2}/{d2} = {float(f2):.3f}",
    }


def _fraction_comparison_benchmark(difficulty: int, config: dict) -> dict:
    """Compare a fraction to a benchmark (0, 1/2, or 1)."""
    benchmarks = [(0, 1), (1, 2), (1, 1)]
    if difficulty <= 2:
        benchmark = (1, 2)  # always compare to 1/2 at low difficulty
    else:
        benchmark = random.choice(benchmarks)

    n, d = _pick_fraction(difficulty)
    frac = Fraction(n, d)
    bench = Fraction(benchmark[0], benchmark[1])

    if frac > bench:
        correct = ">"
    elif frac < bench:
        correct = "<"
    else:
        correct = "="

    bench_str = f"{benchmark[0]}/{benchmark[1]}" if benchmark != (0, 1) else "0"
    if benchmark == (1, 1):
        bench_str = "1"
    if benchmark == (1, 2):
        bench_str = "1/2"

    # Express benchmark using fraction's denominator for visual comparison
    bench_numer_common = round(float(bench) * d)

    return {
        "type": "fraction_comparison_benchmark",
        "prompt": f"Is {n}/{d} less than, equal to, or greater than {bench_str}?",
        "fraction": {"numerator": n, "denominator": d},
        "benchmark": {"numerator": benchmark[0], "denominator": benchmark[1], "display": bench_str},
        "left": {"numerator": n, "denominator": d},
        "right": {"numerator": benchmark[0], "denominator": benchmark[1]},
        "choices": ["<", "=", ">"],
        "correct_answer": correct,
        "visual_hint": {
            "type": "fraction_bars",
            "left_value": float(frac),
            "right_value": float(bench),
            "left_numerator": n,
            "left_denominator": d,
            "right_numerator": bench_numer_common,
            "right_denominator": d,
            "right_label": bench_str,
        },
        "feedback_explanation": f"{n}/{d} = {float(frac):.3f}, benchmark {bench_str} = {float(bench):.3f}",
    }


def _equivalent_fractions(difficulty: int, config: dict) -> dict:
    n, d = _pick_fraction(min(difficulty, 3))
    if difficulty <= 2:
        multipliers = [2, 3]
    elif difficulty <= 3:
        multipliers = [2, 3, 4]
    else:
        multipliers = [2, 3, 4, 5, 6]

    m = random.choice(multipliers)
    target_n, target_d = n * m, d * m

    # Decide what to ask: find numerator or denominator
    frac_val = float(Fraction(n, d))
    if random.random() < 0.5:
        return {
            "type": "equivalent_fractions",
            "prompt": f"Find the missing number: {n}/{d} = ?/{target_d}",
            "original": {"numerator": n, "denominator": d},
            "target_denominator": target_d,
            "missing": "numerator",
            "correct_answer": str(target_n),
            "visual_hint": {
                "type": "fraction_bars",
                "left_value": frac_val,
                "left_numerator": n,
                "left_denominator": d,
                "left_parts": d,
                "right_parts": target_d,
                "right_denominator": target_d,
                # right_numerator intentionally omitted — that's the answer
                "equiv_mode": True,
            },
            "feedback_explanation": f"{n}/{d} × {m}/{m} = {target_n}/{target_d}",
        }
    else:
        return {
            "type": "equivalent_fractions",
            "prompt": f"Find the missing number: {n}/{d} = {target_n}/?",
            "original": {"numerator": n, "denominator": d},
            "target_numerator": target_n,
            "missing": "denominator",
            "correct_answer": str(target_d),
            "visual_hint": {
                "type": "fraction_bars",
                "left_value": frac_val,
                "left_numerator": n,
                "left_denominator": d,
                "left_parts": d,
                "right_parts": target_d,
                "right_denominator": target_d,
                "right_numerator": target_n,
                "equiv_mode": True,
            },
            "feedback_explanation": f"{n}/{d} × {m}/{m} = {target_n}/{target_d}",
        }


def _fraction_number_line(difficulty: int, config: dict) -> dict:
    n, d = _pick_fraction(difficulty)
    frac_value = float(Fraction(n, d))

    # Generate some choices
    choices = [f"{n}/{d}"]
    while len(choices) < 4:
        cn, cd = _pick_fraction(difficulty)
        c_str = f"{cn}/{cd}"
        if c_str not in choices and abs(float(Fraction(cn, cd)) - frac_value) > 0.05:
            choices.append(c_str)
    random.shuffle(choices)

    return {
        "type": "fraction_number_line",
        "prompt": "Which fraction is shown on the number line?",
        "position": frac_value,
        "number_line": {"min": 0, "max": 1, "tick_count": d + 1},
        "choices": choices,
        "correct_answer": f"{n}/{d}",
        "visual_hint": {
            "type": "number_line",
            "marked_position": frac_value,
            "denominator": d,
        },
        "feedback_explanation": f"The point is at {n}/{d} = {frac_value:.3f}",
    }


# ---------------------------------------------------------------------------
# COMBINING INTEGERS
# ---------------------------------------------------------------------------

def _int_range(difficulty: int) -> Tuple[int, int]:
    if difficulty <= 1:
        return (-10, 10)
    elif difficulty <= 2:
        return (-20, 20)
    elif difficulty <= 3:
        return (-50, 50)
    elif difficulty <= 4:
        return (-100, 100)
    return (-200, 200)


def _pick_int_operands(difficulty: int) -> Tuple[int, int]:
    """Pick two integer operands with difficulty-appropriate sign variety.
    Difficulty 1: any combination (may be all positive for beginners)
    Difficulty 2: at least one operand is negative
    Difficulty 3+: guarantee mixed signs and larger magnitudes
    """
    lo, hi = _int_range(difficulty)

    if difficulty <= 1:
        a = random.randint(lo, hi)
        b = random.randint(lo, hi)
    elif difficulty == 2:
        # Guarantee at least one negative
        if random.random() < 0.5:
            a = random.randint(lo, -1)
            b = random.randint(lo, hi)
        else:
            a = random.randint(lo, hi)
            b = random.randint(lo, -1)
    else:
        # Difficulty 3+: force mixed signs most of the time
        pattern = random.choice(["pos_neg", "neg_pos", "neg_neg", "mixed"])
        if pattern == "pos_neg":
            a = random.randint(1, hi)
            b = random.randint(lo, -1)
        elif pattern == "neg_pos":
            a = random.randint(lo, -1)
            b = random.randint(1, hi)
        elif pattern == "neg_neg":
            a = random.randint(lo, -1)
            b = random.randint(lo, -1)
        else:
            a = random.randint(lo, hi)
            b = random.randint(lo, hi)

    return a, b


def _integer_addition(difficulty: int, config: dict) -> dict:
    a, b = _pick_int_operands(difficulty)
    correct = a + b

    prompt = f"{a} + ({b})" if b < 0 else f"{a} + {b}"

    return {
        "type": "integer_addition",
        "prompt": f"What is {prompt}?",
        "operands": [a, b],
        "operation": "+",
        "correct_answer": str(correct),
        "visual_hint": {
            "type": "number_line",
            "start": a,
            "move": b,
            "result": correct,
            "line_min": min(a, correct, 0) - 5,
            "line_max": max(a, correct, 0) + 5,
        },
        "feedback_explanation": f"Start at {a}, move {b} {'right' if b > 0 else 'left'} to reach {correct}",
    }


def _integer_subtraction(difficulty: int, config: dict) -> dict:
    a, b = _pick_int_operands(difficulty)
    correct = a - b

    prompt = f"{a} - ({b})" if b < 0 else f"{a} - {b}"

    return {
        "type": "integer_subtraction",
        "prompt": f"What is {prompt}?",
        "operands": [a, b],
        "operation": "-",
        "correct_answer": str(correct),
        "visual_hint": {
            "type": "number_line",
            "start": a,
            "move": -b,
            "result": correct,
            "line_min": min(a, correct, 0) - 5,
            "line_max": max(a, correct, 0) + 5,
        },
        "feedback_explanation": f"Start at {a}, subtract {b} to reach {correct}",
    }


def _integer_magnitude(difficulty: int, config: dict) -> dict:
    """Compare absolute values / reason about magnitude."""
    lo, hi = _int_range(difficulty)
    a = random.randint(lo, hi)
    b = random.randint(lo, hi)
    while a == b:
        b = random.randint(lo, hi)

    question_type = random.choice(["closer_to_zero", "farther_from_zero", "compare"])
    if question_type == "closer_to_zero":
        correct = str(a) if abs(a) < abs(b) else str(b)
        prompt = f"Which is closer to zero: {a} or {b}?"
    elif question_type == "farther_from_zero":
        correct = str(a) if abs(a) > abs(b) else str(b)
        prompt = f"Which is farther from zero: {a} or {b}?"
    else:
        if a > b:
            correct = ">"
        else:
            correct = "<"
        prompt = f"Compare: {a} ___ {b}"

    return {
        "type": "integer_magnitude",
        "prompt": prompt,
        "values": [a, b],
        "question_type": question_type,
        "choices": [str(a), str(b)] if question_type != "compare" else ["<", "=", ">"],
        "correct_answer": correct,
        "visual_hint": {
            "type": "number_line",
            "points": [a, b, 0],
            "line_min": min(a, b, 0) - 5,
            "line_max": max(a, b, 0) + 5,
        },
        "feedback_explanation": f"|{a}| = {abs(a)}, |{b}| = {abs(b)}",
    }


def _integer_number_line(difficulty: int, config: dict) -> dict:
    lo, hi = _int_range(difficulty)
    target = random.randint(lo, hi)

    choices = [target]
    while len(choices) < 4:
        c = random.randint(lo, hi)
        if c not in choices:
            choices.append(c)
    random.shuffle(choices)

    return {
        "type": "integer_number_line",
        "prompt": "Which integer is shown on the number line?",
        "position": target,
        "number_line": {"min": lo, "max": hi},
        "choices": [str(c) for c in choices],
        "correct_answer": str(target),
        "visual_hint": {
            "type": "number_line",
            "marked_position": target,
            "line_min": lo,
            "line_max": hi,
        },
        "feedback_explanation": f"The point is at {target}",
    }


# ---------------------------------------------------------------------------
# MULTIPLICATION FLUENCY
# ---------------------------------------------------------------------------

def _mult_range(difficulty: int) -> Tuple[int, int]:
    if difficulty <= 1:
        return (0, 5)
    elif difficulty <= 2:
        return (0, 7)
    elif difficulty <= 3:
        return (0, 10)
    elif difficulty <= 4:
        return (0, 12)
    return (2, 12)


def _multiplication_facts(difficulty: int, config: dict) -> dict:
    lo, hi = _mult_range(difficulty)
    a = random.randint(lo, hi)
    b = random.randint(lo, hi)
    correct = a * b

    return {
        "type": "multiplication_facts",
        "prompt": f"What is {a} × {b}?",
        "factors": [a, b],
        "correct_answer": str(correct),
        "visual_hint": {
            "type": "array_model",
            "rows": a,
            "cols": b,
        },
        "feedback_explanation": f"{a} × {b} = {correct}",
    }


def _multiplication_related_facts(difficulty: int, config: dict) -> dict:
    """Given a known fact, derive a related fact."""
    lo, hi = _mult_range(difficulty)
    a = random.randint(max(lo, 2), hi)
    b = random.randint(max(lo, 2), hi)
    known_product = a * b

    # Related fact variations
    variation = random.choice(["double", "half", "plus_one", "commutative"])
    if variation == "double":
        prompt = f"If {a} × {b} = {known_product}, what is {a*2} × {b}?"
        correct = str(a * 2 * b)
        explanation = f"{a*2} × {b} = 2 × ({a} × {b}) = 2 × {known_product} = {a*2*b}"
    elif variation == "half" and a % 2 == 0:
        prompt = f"If {a} × {b} = {known_product}, what is {a//2} × {b}?"
        correct = str(a // 2 * b)
        explanation = f"{a//2} × {b} = half of ({a} × {b}) = {known_product} ÷ 2 = {a//2*b}"
    elif variation == "plus_one":
        prompt = f"If {a} × {b} = {known_product}, what is {a+1} × {b}?"
        correct = str((a + 1) * b)
        explanation = f"{a+1} × {b} = {a} × {b} + {b} = {known_product} + {b} = {(a+1)*b}"
    else:  # commutative
        prompt = f"If {a} × {b} = {known_product}, what is {b} × {a}?"
        correct = str(known_product)
        explanation = f"{b} × {a} = {a} × {b} = {known_product} (commutative property)"

    return {
        "type": "multiplication_related_facts",
        "prompt": prompt,
        "known_fact": {"a": a, "b": b, "product": known_product},
        "variation": variation,
        "correct_answer": correct,
        "visual_hint": {
            "type": "array_model",
            "rows": a,
            "cols": b,
            "highlight_variation": variation,
        },
        "feedback_explanation": explanation,
    }


def _multiplication_scaling(difficulty: int, config: dict) -> dict:
    """Multiplication as scaling — number sense focus."""
    lo, hi = _mult_range(difficulty)
    base = random.randint(max(lo, 2), hi)

    # Scaling questions
    scale_type = random.choice(["bigger_smaller", "estimate", "compare_products"])
    if scale_type == "bigger_smaller":
        multiplier = random.choice([0, 1, random.randint(2, 5)])
        if multiplier == 0:
            correct = "zero"
            explanation = f"Any number × 0 = 0"
        elif multiplier == 1:
            correct = "same"
            explanation = f"Any number × 1 = the same number"
        else:
            correct = "bigger"
            explanation = f"{base} × {multiplier} = {base * multiplier}, which is bigger than {base}"

        return {
            "type": "multiplication_scaling",
            "prompt": f"Is {base} × {multiplier} bigger than, smaller than, or equal to {base}?",
            "base": base,
            "multiplier": multiplier,
            "choices": ["bigger", "same", "zero", "smaller"],
            "correct_answer": correct,
            "visual_hint": {
                "type": "scaling_bar",
                "base_value": base,
                "multiplier": multiplier,
            },
            "feedback_explanation": explanation,
        }
    elif scale_type == "estimate":
        a = random.randint(max(lo, 2), hi)
        b = random.randint(max(lo, 2), hi)
        product = a * b
        # Generate close options
        options = sorted(set([
            product,
            product + random.randint(1, 10),
            product - random.randint(1, min(10, product - 1)) if product > 1 else product + 5,
            product + random.randint(10, 20),
        ]))
        random.shuffle(options)
        return {
            "type": "multiplication_scaling",
            "prompt": f"Which is closest to {a} × {b}?",
            "factors": [a, b],
            "choices": [str(o) for o in options],
            "correct_answer": str(product),
            "visual_hint": {
                "type": "array_model",
                "rows": a,
                "cols": b,
            },
            "feedback_explanation": f"{a} × {b} = {product}",
        }
    else:  # compare_products
        a1 = random.randint(max(lo, 2), hi)
        b1 = random.randint(max(lo, 2), hi)
        a2 = random.randint(max(lo, 2), hi)
        b2 = random.randint(max(lo, 2), hi)
        p1, p2 = a1 * b1, a2 * b2
        if p1 > p2:
            correct = ">"
        elif p1 < p2:
            correct = "<"
        else:
            correct = "="
        return {
            "type": "multiplication_scaling",
            "prompt": f"Without calculating exactly: {a1} × {b1} ___ {a2} × {b2}",
            "left": {"a": a1, "b": b1},
            "right": {"a": a2, "b": b2},
            "choices": ["<", "=", ">"],
            "correct_answer": correct,
            "visual_hint": {
                "type": "double_array",
                "left": {"rows": a1, "cols": b1},
                "right": {"rows": a2, "cols": b2},
            },
            "feedback_explanation": f"{a1}×{b1}={p1}, {a2}×{b2}={p2}",
        }
