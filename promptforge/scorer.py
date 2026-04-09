"""
Quality scoring for prompts — 0-100 across 4 dimensions.
No API calls, purely heuristic/structural analysis.
"""

import re
from dataclasses import dataclass

@dataclass
class QualityScore:
    clarity: int        # 0-25: Is the task unambiguous?
    specificity: int    # 0-25: Are constraints and format specified?
    structure: int      # 0-25: Is the prompt well-organized?
    grounding: int      # 0-25: Anti-hallucination / factual anchors?

    @property
    def total(self) -> int:
        return self.clarity + self.specificity + self.structure + self.grounding

    def breakdown(self) -> dict:
        return {
            "clarity":     self.clarity,
            "specificity": self.specificity,
            "structure":   self.structure,
            "grounding":   self.grounding,
            "total":       self.total,
        }


def score_prompt(prompt: str) -> QualityScore:
    text = prompt.strip()
    lower = text.lower()
    words = text.split()
    sentences = re.split(r'[.!?]+', text)

    # --- CLARITY (0-25) ---
    clarity = 10  # baseline

    # Has a clear verb/action
    action_verbs = ["write", "create", "generate", "explain", "summarize", "analyze",
                    "list", "compare", "describe", "translate", "classify", "extract",
                    "review", "evaluate", "suggest", "help", "build", "design"]
    if any(v in lower for v in action_verbs):
        clarity += 5

    # Not too short (vague)
    if len(words) >= 10:
        clarity += 5
    elif len(words) >= 5:
        clarity += 2

    # No ambiguous pronouns without antecedent at start
    if not re.match(r'^(it|this|that|they|them)\b', lower):
        clarity += 5

    clarity = min(25, clarity)

    # --- SPECIFICITY (0-25) ---
    specificity = 5  # baseline

    # Mentions output format
    format_words = ["format", "json", "markdown", "bullet", "list", "table",
                    "paragraph", "csv", "xml", "numbered", "code", "plain text"]
    if any(f in lower for f in format_words):
        specificity += 6

    # Mentions length/scope
    if any(w in lower for w in ["word", "sentence", "paragraph", "brief", "detailed",
                                  "concise", "comprehensive", "short", "long", "max", "limit"]):
        specificity += 5

    # Mentions audience or tone
    if any(w in lower for w in ["expert", "beginner", "technical", "casual", "formal",
                                  "audience", "professional", "simple", "tone", "style"]):
        specificity += 5

    # Has constraints (must, should, do not, avoid, only)
    if re.search(r'\b(must|should|avoid|do not|don\'t|only|always|never|ensure)\b', lower):
        specificity += 4

    specificity = min(25, specificity)

    # --- STRUCTURE (0-25) ---
    structure = 5  # baseline

    # Has multiple sentences (not a one-liner dump)
    non_empty = [s.strip() for s in sentences if s.strip()]
    if len(non_empty) >= 3:
        structure += 6
    elif len(non_empty) >= 2:
        structure += 3

    # Has context section (background/context words)
    if any(w in lower for w in ["context:", "background:", "given that", "the following",
                                  "here is", "below is", "<context>", "###"]):
        structure += 6

    # Has role assignment
    if re.search(r'\b(you are|act as|your role|as a|you\'re a)\b', lower):
        structure += 4

    # Has examples
    if any(w in lower for w in ["example:", "for example", "e.g.", "such as",
                                  "like this", "<example>", "input:", "output:"]):
        structure += 4

    structure = min(25, structure)

    # --- GROUNDING (0-25) anti-hallucination ---
    grounding = 5  # baseline

    # Asks for citations/sources
    if any(w in lower for w in ["cite", "source", "reference", "based on", "according to",
                                  "from the", "provided", "attached", "above"]):
        grounding += 7

    # Has confidence calibration
    if any(w in lower for w in ["if you're not sure", "if uncertain", "say so",
                                  "confidence", "don't make up", "only if you know",
                                  "acknowledge", "admit"]):
        grounding += 7

    # Scope limiting (reduces hallucination surface)
    if any(w in lower for w in ["only", "exclusively", "strictly", "limit", "restrict",
                                  "focus only", "do not include", "do not add"]):
        grounding += 4

    # Asks for reasoning
    if any(w in lower for w in ["explain", "reasoning", "step by step", "think",
                                  "why", "justify", "show your work"]):
        grounding += 4

    grounding = min(25, grounding)

    return QualityScore(clarity, specificity, structure, grounding)


def score_delta(before: QualityScore, after: QualityScore) -> str:
    """Human-readable quality improvement summary."""
    delta = after.total - before.total
    sign = "+" if delta >= 0 else ""
    lines = [f"Quality: {before.total} → {after.total} ({sign}{delta})"]
    dims = ["clarity", "specificity", "structure", "grounding"]
    for d in dims:
        b, a = getattr(before, d), getattr(after, d)
        if a != b:
            s = "+" if a > b else ""
            lines.append(f"  {d}: {b} → {a} ({s}{a-b})")
    return "\n".join(lines)
