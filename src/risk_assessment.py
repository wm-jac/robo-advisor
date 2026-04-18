"""
risk_assessment.py
Risk questionnaire and mapping from score to risk aversion coefficient A.
"""

QUESTIONS: list[dict] = [
    {
        "id": 1,
        "text": "What is your primary investment time horizon?",
        "options": [
            "Less than 1 year",
            "1 – 3 years",
            "3 – 5 years",
            "5 – 10 years",
            "More than 10 years",
        ],
        "scores": [1, 2, 3, 4, 5],
    },
    {
        "id": 2,
        "text": (
            "Imagine your portfolio drops 20% in value over three months. "
            "What would you most likely do?"
        ),
        "options": [
            "Sell everything to prevent further losses",
            "Sell some investments to reduce risk",
            "Do nothing and wait for recovery",
            "Buy more to take advantage of lower prices",
        ],
        "scores": [1, 2, 4, 6],
    },
    {
        "id": 3,
        "text": "What is the maximum loss you could accept in a single year without losing sleep?",
        "options": [
            "I cannot tolerate any loss",
            "Up to 5%",
            "Up to 10%",
            "Up to 20%",
            "More than 20%",
        ],
        "scores": [1, 2, 3, 5, 6],
    },
    {
        "id": 4,
        "text": "What is your primary investment goal?",
        "options": [
            "Preserve my capital at all costs",
            "Generate steady income with minimal risk",
            "Balance between growth and income",
            "Achieve long-term capital growth",
            "Maximise returns, accepting high risk",
        ],
        "scores": [1, 2, 3, 4, 5],
    },
    {
        "id": 5,
        "text": "How stable is your current income?",
        "options": [
            "Very unstable – I rely on investments for daily expenses",
            "Somewhat unstable – irregular income",
            "Moderate – my income covers needs but little savings",
            "Stable – salaried with regular savings",
            "Very stable – high income with substantial savings",
        ],
        "scores": [1, 2, 3, 4, 5],
    },
    {
        "id": 6,
        "text": "How would you describe your investment experience?",
        "options": [
            "None – this is my first investment",
            "Beginner – I have bought a few funds or ETFs",
            "Intermediate – I actively manage a diversified portfolio",
            "Experienced – I trade individual stocks and use derivatives",
            "Expert – I have professional investment experience",
        ],
        "scores": [1, 2, 3, 4, 5],
    },
    {
        "id": 7,
        "text": "How many months of living expenses do you have set aside as an emergency fund?",
        "options": [
            "Less than 1 month",
            "1 – 3 months",
            "3 – 6 months",
            "More than 6 months",
        ],
        "scores": [1, 2, 3, 4],
    },
    {
        "id": 8,
        "text": (
            "If your portfolio gained 25% in one year but then lost 20% the following year, "
            "how would you feel?"
        ),
        "options": [
            "Very stressed — I would exit the market immediately",
            "Uncomfortable — I would reduce my risk exposure",
            "Disappointed but patient — I would stay invested",
            "Unbothered — volatility is part of long-term investing",
        ],
        "scores": [1, 2, 4, 6],
    },
    {
        "id": 9,
        "text": "What percentage of your total savings are you planning to invest?",
        "options": [
            "Less than 10%",
            "10% – 25%",
            "25% – 50%",
            "50% – 75%",
            "More than 75%",
        ],
        "scores": [5, 4, 3, 2, 1],
    },
    {
        "id": 10,
        "text": "Which statement best describes your attitude toward investment returns?",
        "options": [
            "I prefer guaranteed low returns over uncertain higher returns",
            "I accept slightly higher risk for modestly better returns",
            "I am willing to accept moderate swings for solid long-term growth",
            "I seek high returns and accept the possibility of large losses",
            "I want maximum possible returns regardless of risk",
        ],
        "scores": [1, 2, 3, 4, 5],
    },
]

# Score boundaries
_MIN_SCORE = sum(q["scores"][0] for q in QUESTIONS)   # 7
_MAX_SCORE = sum(q["scores"][-1] for q in QUESTIONS)  # 36

# A-value range: higher score (more risk tolerant) → lower A
_A_MIN = 1.0   # most aggressive
_A_MAX = 8.0   # most conservative


def score_to_A(total_score: int) -> float:
    """
    Continuously map total questionnaire score to risk aversion coefficient A.
    Higher score = more risk tolerant = lower A.
    """
    score_clamped = max(_MIN_SCORE, min(_MAX_SCORE, total_score))
    normalised = (score_clamped - _MIN_SCORE) / (_MAX_SCORE - _MIN_SCORE)
    A = _A_MAX - normalised * (_A_MAX - _A_MIN)
    return round(A, 2)


def describe_profile(A: float) -> dict:
    """Return a human-readable investor profile for a given A value."""
    if A >= 7.0:
        return {
            "label": "Very Conservative",
            "description": (
                "You prioritise capital preservation above all else. "
                "Your portfolio will focus heavily on low-volatility assets."
            ),
            "color": "#e74c3c",
            "emoji": "🛡️",
        }
    elif A >= 5.5:
        return {
            "label": "Conservative",
            "description": (
                "You are cautious about risk and prefer stable, income-generating investments "
                "over high-growth opportunities."
            ),
            "color": "#e67e22",
            "emoji": "⚖️",
        }
    elif A >= 4.0:
        return {
            "label": "Moderate",
            "description": (
                "You seek a balance between growth and stability, "
                "accepting some volatility in exchange for reasonable returns."
            ),
            "color": "#f1c40f",
            "emoji": "📊",
        }
    elif A >= 2.5:
        return {
            "label": "Aggressive",
            "description": (
                "You are comfortable with significant market swings "
                "in pursuit of strong long-term capital growth."
            ),
            "color": "#2ecc71",
            "emoji": "📈",
        }
    else:
        return {
            "label": "Very Aggressive",
            "description": (
                "You pursue maximum returns and can tolerate large drawdowns. "
                "Your portfolio will be concentrated in high-growth assets."
            ),
            "color": "#27ae60",
            "emoji": "🚀",
        }


def calculate_utility(ret: float, var: float, A: float) -> float:
    """U = r - (A * sigma^2) / 2"""
    return ret - (A * var) / 2


def get_score_range() -> tuple[int, int]:
    return _MIN_SCORE, _MAX_SCORE
