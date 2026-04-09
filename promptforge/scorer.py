"""
Quality scoring for prompts — 0-100 across 4 dimensions.
No API calls, purely heuristic/structural analysis.

Scores are earned, not given as baselines. Each dimension measures
contextual signal, not mere keyword presence.
"""

import re
from dataclasses import dataclass
from typing import List

# Imperative action verbs that indicate a real task instruction
_ACTION_VERBS = {
    "write", "create", "generate", "explain", "summarize", "analyze",
    "list", "compare", "describe", "translate", "classify", "extract",
    "review", "evaluate", "suggest", "build", "design", "find", "identify",
    "calculate", "convert", "format", "fix", "debug", "refactor", "improve",
    "predict", "estimate", "rank", "filter", "parse", "validate", "test",
    "document", "outline", "draft", "rewrite", "annotate", "assess",
}

# Vague quantifiers that reduce clarity
_VAGUE_QUANTIFIERS = re.compile(
    r'\b(some|various|several|many|few|a\s+lot|certain|appropriate|relevant|suitable|proper)\b',
    re.I
)

# Dangling pronouns at the start of a prompt (no antecedent)
_DANGLING_PRONOUN = re.compile(r'^(it|this|that|they|them|these|those)\b', re.I)

# Output-format keywords in the context of an output specification
_OUTPUT_FORMAT_CTX = re.compile(
    r'(output|return|format|provide|give me|respond)\s+(?:it\s+)?(?:as|in|with|using)?\s*'
    r'(json|markdown|bullet|list|table|csv|xml|numbered|plain\s*text|code|html)',
    re.I
)

# Length/scope that are genuinely constraining (not just "detailed" in passing)
_LENGTH_SCOPE = re.compile(
    r'\b(\d+\s*(word|sentence|paragraph|line|bullet|item|point)s?'
    r'|under\s+\d+|max\s+\d+|no\s+more\s+than\s+\d+'
    r'|brief(ly)?|concise(ly)?|comprehensive(ly)?|in\s+detail)\b',
    re.I
)

# Genuine grounding phrases — not just the word "source" in any context
_GROUNDING_PHRASES = re.compile(
    r'\b(cite\s+(your\s+)?sources?'
    r'|based\s+on\s+the\s+(provided|following|above|given)'
    r'|according\s+to\s+(the\s+)?(provided|following|document|text|data)'
    r'|from\s+the\s+(provided|following|above|given)'
    r'|don\'?t\s+(make\s+up|fabricate|invent|hallucinate)'
    r'|if\s+you\s+(are|\'re)\s+(not\s+sure|uncertain|unsure)'
    r'|only\s+(if\s+you\s+know|include\s+facts\s+you\'re\s+confident)'
    r'|say\s+so\s+if\s+(you\'re\s+not\s+sure|uncertain))\b',
    re.I
)


def _count_distinct_instructions(text: str) -> int:
    """Count distinct imperative action verbs (deduplicated)."""
    lower = text.lower()
    found = {v for v in _ACTION_VERBS if re.search(r'\b' + v + r'\b', lower)}
    return len(found)


def _ambiguity_score(text: str) -> int:
    """
    Returns an ambiguity penalty 0–10.
    Higher = more ambiguous = lower clarity.
    """
    penalty = 0
    lower = text.lower()
    words = text.split()

    # Very short prompts are ambiguous by nature
    if len(words) < 5:
        penalty += 8
    elif len(words) < 10:
        penalty += 4

    # Dangling pronoun at start
    if _DANGLING_PRONOUN.match(lower.strip()):
        penalty += 4

    # Vague quantifiers
    vague_hits = len(_VAGUE_QUANTIFIERS.findall(text))
    penalty += min(4, vague_hits * 2)

    return min(10, penalty)


@dataclass
class QualityScore:
    clarity: int        # 0-25: Is the task unambiguous?
    specificity: int    # 0-25: Are constraints and format specified?
    structure: int      # 0-25: Is the prompt well-organized?
    grounding: int      # 0-25: Anti-hallucination / factual anchors?

    @property
    def total(self) -> int:
        return self.clarity + self.specificity + self.structure + self.grounding

    def grade(self) -> str:
        """Letter grade for the total score."""
        t = self.total
        if t >= 85: return "A"
        if t >= 70: return "B"
        if t >= 55: return "C"
        if t >= 40: return "D"
        return "F"

    def breakdown(self) -> dict:
        return {
            "clarity":     self.clarity,
            "specificity": self.specificity,
            "structure":   self.structure,
            "grounding":   self.grounding,
            "total":       self.total,
            "grade":       self.grade(),
        }


def score_prompt(prompt: str) -> QualityScore:
    text = prompt.strip()
    lower = text.lower()
    words = text.split()
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]

    # --- CLARITY (0-25) ---
    # Earned by: having a real action verb, sufficient length, low ambiguity
    clarity = 0

    instruction_count = _count_distinct_instructions(text)
    if instruction_count >= 2:
        clarity += 12
    elif instruction_count == 1:
        clarity += 8

    ambiguity = _ambiguity_score(text)
    clarity += max(0, 13 - ambiguity)   # up to 13 pts for low ambiguity

    clarity = min(25, clarity)

    # --- SPECIFICITY (0-25) ---
    # Earned by: output format in context, constraining length, audience/tone, hard constraints
    specificity = 0

    # Output format must appear in context of an output spec, not in passing
    if _OUTPUT_FORMAT_CTX.search(text):
        specificity += 8
    elif re.search(r'\b(json|markdown|csv|xml|html)\b', lower):
        specificity += 4  # format mentioned but not as explicit output spec

    # Length/scope that actually constrains the response
    if _LENGTH_SCOPE.search(text):
        specificity += 6

    # Audience or tone (contextually — "technical" in passing gets partial)
    if re.search(
        r'\b(for\s+(a\s+)?(beginner|expert|technical|non-technical|junior|senior|manager|developer)'
        r'|tone[:\s]+(formal|casual|professional|friendly)'
        r'|audience[:\s]|write\s+for\s+a)',
        lower
    ):
        specificity += 6
    elif re.search(r'\b(beginner|expert|technical|casual|formal|professional)\b', lower):
        specificity += 2  # mentioned but not contextually tied to output

    # Hard constraints (must/should/avoid with content after them)
    if re.search(r'\b(must|should|avoid|do\s+not|don\'t|never|ensure|always)\b\s+\w', lower):
        specificity += 5

    specificity = min(25, specificity)

    # --- STRUCTURE (0-25) ---
    # Earned by: multiple sentences, explicit sections, role, examples
    structure = 0

    if len(sentences) >= 4:
        structure += 8
    elif len(sentences) >= 2:
        structure += 4

    # Explicit section labels
    if re.search(
        r'(context:|background:|given\s+that|the\s+following|here\s+is|below\s+is'
        r'|<context>|###|\*\*task\b|\*\*context\b)',
        lower
    ):
        structure += 7

    # Role assignment
    if re.search(r'\b(you\s+are|act\s+as|your\s+role|as\s+a|you\'re\s+a)\b', lower):
        structure += 5

    # Examples (strong structural signal)
    if re.search(
        r'(example:|for\s+example|e\.g\.|such\s+as|like\s+this|<example>|input:|output:)',
        lower
    ):
        structure += 5

    structure = min(25, structure)

    # --- GROUNDING (0-25) anti-hallucination ---
    # Earned by: meaningful grounding phrases, confidence calibration, scope limiting
    grounding = 0

    # Genuine grounding phrases (contextual, not just word presence)
    grounding_hits = len(_GROUNDING_PHRASES.findall(text))
    grounding += min(12, grounding_hits * 6)

    # Explicit scope limiting that reduces hallucination surface
    if re.search(
        r'\b(only\s+(use|include|refer\s+to|base|draw\s+from)'
        r'|do\s+not\s+(include|add|make\s+up|invent|assume)'
        r'|strictly\s+(based|limit|use)'
        r'|focus\s+only\s+on)\b',
        lower
    ):
        grounding += 6

    # Asks for reasoning / shows-work (reduces confident-but-wrong outputs)
    if re.search(
        r'\b(step\s+by\s+step|show\s+your\s+(work|reasoning)'
        r'|explain\s+(why|your\s+reasoning|how\s+you)'
        r'|think\s+through|walk\s+(me\s+)?through)\b',
        lower
    ):
        grounding += 7

    grounding = min(25, grounding)

    return QualityScore(clarity, specificity, structure, grounding)


def score_delta(before: QualityScore, after: QualityScore) -> str:
    """Human-readable quality improvement summary."""
    delta = after.total - before.total
    sign = "+" if delta >= 0 else ""
    lines = [f"Quality: {before.total} → {after.total} ({sign}{delta})  [{before.grade()} → {after.grade()}]"]
    dims = ["clarity", "specificity", "structure", "grounding"]
    for d in dims:
        b, a = getattr(before, d), getattr(after, d)
        if a != b:
            s = "+" if a > b else ""
            lines.append(f"  {d}: {b} → {a} ({s}{a-b})")
    return "\n".join(lines)
