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
        "integer_number_line": _integer_number_line,
        "multiplication_facts": _multiplication_facts,
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


def _counter_data(a: int, b: int, operation: str) -> dict:
    """Build yellow/red counter model data for integer add/sub.

    Yellow counters = positive (+1 each)
    Red counters    = negative (-1 each)
    Zero pairs      = one yellow + one red that cancel out

    For addition:
        Show |a| yellows (if a>0) or |a| reds (if a<0),
        then add |b| yellows (if b>0) or |b| reds (if b<0),
        then cancel zero pairs.

    For subtraction a - b:
        Start with |a| yellows or reds.
        To subtract positives: remove yellow counters (add zero pairs if needed).
        To subtract negatives: remove red counters (add zero pairs if needed).
    """
    if operation == "+":
        start_yellow = max(a, 0)
        start_red = abs(min(a, 0))
        add_yellow = max(b, 0)
        add_red = abs(min(b, 0))
    else:  # subtraction a - b
        start_yellow = max(a, 0)
        start_red = abs(min(a, 0))
        # Subtracting b: we need to remove b-type counters.
        # If b > 0, remove yellow. If not enough, add zero pairs first.
        # If b < 0, remove red. If not enough, add zero pairs first.
        if b > 0:
            # Need to remove b yellow counters
            zero_pairs_needed = max(0, b - start_yellow)
            add_yellow = zero_pairs_needed  # zero pairs added
            add_red = zero_pairs_needed
            # "remove" is conceptual — the result handles it
        else:
            # b < 0: need to remove |b| red counters
            abs_b = abs(b)
            zero_pairs_needed = max(0, abs_b - start_red)
            add_yellow = zero_pairs_needed
            add_red = zero_pairs_needed

    result = a + b if operation == "+" else a - b
    result_yellow = max(result, 0)
    result_red = abs(min(result, 0))

    return {
        "start_yellow": start_yellow,
        "start_red": start_red,
        "add_yellow": add_yellow,
        "add_red": add_red,
        "zero_pairs_needed": max(0, (add_yellow if operation == "-" else 0)),
        "result_yellow": result_yellow,
        "result_red": result_red,
        "result": result,
        "operation": operation,
        "a": a,
        "b": b,
    }


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
            "line_min": min(a, correct, 0) - 3,
            "line_max": max(a, correct, 0) + 3,
            "counter_data": _counter_data(a, b, "+"),
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
            "line_min": min(a, correct, 0) - 3,
            "line_max": max(a, correct, 0) + 3,
            "counter_data": _counter_data(a, b, "-"),
        },
        "feedback_explanation": f"Start at {a}, subtract {b} to reach {correct}",
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
    """Range used by related-facts and scaling generators.

    Slightly wider than the strict facts progression because these
    problem types need at least two distinct non-trivial factors.
    """
    if difficulty <= 1:
        return (0, 5)
    elif difficulty <= 2:
        return (0, 5)
    elif difficulty <= 3:
        return (2, 8)
    elif difficulty <= 4:
        return (2, 10)
    return (2, 12)


# Multiplication facts use a structured progression where each difficulty
# level introduces a new set of factors while sprinkling in review of
# previously mastered facts.
_MULT_FACTS_LEVELS = {
    # difficulty: (focus_factors, review_factors)
    1: ([0, 1, 2], []),                       # 0s, 1s, 2s
    2: ([3], [0, 1, 2]),                       # 3s with 0-2 review
    3: ([4, 5], [0, 1, 2, 3]),                 # 4s, 5s with 0-3 review
    4: ([6, 7, 8], [0, 1, 2, 3, 4, 5]),       # 6-8s with 0-5 review
    5: ([9, 10, 11, 12], [0, 1, 2, 3, 4, 5, 6, 7, 8]),  # 9-12s with review
}


def _all_facts_for_level(difficulty: int):
    """Return (focus_facts, review_facts) as sets of normalised (min,max) tuples."""
    level = max(1, min(5, difficulty))
    focus, review = _MULT_FACTS_LEVELS[level]
    full_pool = focus + review

    # Focus facts: at least one factor from the focus set, paired with anything in the pool
    focus_facts = set()
    for f in focus:
        for p in full_pool:
            focus_facts.add((min(f, p), max(f, p)))

    # Review facts: both factors from the review set
    review_facts = set()
    for r1 in review:
        for r2 in review:
            review_facts.add((min(r1, r2), max(r1, r2)))

    return focus_facts, review_facts


def _pick_mult_factors(difficulty: int, seen_facts: set = None) -> Tuple[int, int]:
    """Coverage-aware picker for multiplication facts.

    Tracks which (normalised) facts the student has already seen in this
    session and prefers unseen facts so every session explores new ground.

    ~70 % of problems feature a *focus* factor (the new fact family).
    ~30 % are pure review of previously mastered facts.
    Within each category, unseen facts are chosen first; once all have
    been shown at least once, repeats are allowed.
    """
    focus_facts, review_facts = _all_facts_for_level(difficulty)
    seen = seen_facts or set()

    unseen_focus = focus_facts - seen
    unseen_review = review_facts - seen

    # Decide category: review (30 %) or focus (70 %)
    do_review = bool(review_facts) and random.random() < 0.30

    if do_review:
        pool = list(unseen_review) if unseen_review else list(review_facts)
    else:
        pool = list(unseen_focus) if unseen_focus else list(focus_facts)

    a, b = random.choice(pool)

    # Randomly swap so the focus number isn't always first
    if random.random() < 0.5:
        a, b = b, a
    return a, b


def _distributive_split(n: int):
    """Split n into two 'friendly' addends for the distributive property.

    Returns (left_cols, right_cols) where left_cols + right_cols == n,
    chosen so each part is easy to multiply mentally:
      - n >= 11 → (10, n-10)        e.g. 11→(10,1), 12→(10,2)
      - n in {6..10} → (5, n-5)     e.g. 7→(5,2), 10→(5,5)
      - n == 5 → (3, 2)             "I know ×3 and ×2"
      - n == 4 → (2, 2)             doubles
      - n == 3 → (2, 1)             "doubles + 1 more"
      - n <= 2 → None               too small to benefit
    """
    if n >= 11:
        return (10, n - 10)
    if 6 <= n <= 10:
        return (5, n - 5)
    if n == 5:
        return (3, 2)
    if n == 4:
        return (2, 2)
    if n == 3:
        return (2, 1)
    return None


def _multiplication_facts(difficulty: int, config: dict) -> dict:
    seen_raw = config.get("seen_facts")
    seen = set()
    if seen_raw:
        seen = {(min(a, b), max(a, b)) for a, b in seen_raw}
    a, b = _pick_mult_factors(difficulty, seen)
    correct = a * b

    # Build the array model with the smaller factor as rows so the
    # visual reads naturally (e.g. 3 rows × 7 columns for 3×7).
    rows, cols = (a, b) if a <= b else (b, a)

    hint: dict = {
        "type": "array_model",
        "rows": rows,
        "cols": cols,
    }

    # Distributive-property highlight: split the *columns* (the larger
    # factor) into two friendly parts so students see, for example:
    #   6 × 11  →  6 rows × 10 cols (purple)  +  6 rows × 1 col (gold)
    #   3 × 7   →  3 rows × 5 cols (purple)   +  3 rows × 2 cols (gold)
    # Only applied when the column count is large enough to benefit.
    split = _distributive_split(cols)
    if split and rows >= 2:
        left_cols, right_cols = split
        hint["highlight"] = {
            "type": "distributive",
            "leftCols": left_cols,
            "rightCols": right_cols,
            "rows": rows,
        }

    return {
        "type": "multiplication_facts",
        "prompt": f"What is {a} × {b}?",
        "factors": [a, b],
        "correct_answer": str(correct),
        "visual_hint": hint,
        "feedback_explanation": f"{a} × {b} = {correct}",
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
