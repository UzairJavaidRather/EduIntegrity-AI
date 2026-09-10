"""
EduIntegrity AI — Writing Style Analysis Service

Analyses measurable writing characteristics of a text to build a
style profile. Used in two ways:

  1. Standalone — profile a single submission's writing style
  2. Comparative — compare a submission's style against a student's
     historical average to detect anomalous deviations

Metrics computed:
  - avg_sentence_length     : Average number of words per sentence
  - avg_word_length         : Average number of characters per word
  - vocabulary_diversity    : Unique words / total words (Type-Token Ratio)
  - punctuation_density     : Punctuation marks per 100 words
  - avg_paragraph_length    : Average sentences per paragraph
  - readability_score       : Flesch Reading Ease (0-100, higher = easier)
  - long_word_ratio         : Proportion of words with 7+ characters
  - sentence_length_std     : Standard deviation of sentence lengths
                              (high = inconsistent sentence structure)

IMPORTANT:
  Style deviation is one indicator among many. A change in writing style
  does not prove misconduct — students improve, use different sources,
  or write differently under different conditions.
  This is an advisory indicator only.
"""

import re
import math
from typing import Optional


# ─── Sentence tokenisation ────────────────────────────────────────────────────

def _split_sentences(text: str) -> list[str]:
    """
    Split text into sentences using punctuation boundaries.
    Simple regex approach — good enough for style metrics without
    requiring NLTK or spaCy as a dependency.
    """
    # Split on . ! ? followed by whitespace or end of string
    # Filter out empty strings and very short fragments
    raw = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in raw if len(s.strip().split()) >= 3]


def _split_words(text: str) -> list[str]:
    """Extract alphabetic words only (ignores numbers and punctuation)."""
    return re.findall(r'\b[a-zA-Z]+\b', text.lower())


def _split_paragraphs(text: str) -> list[str]:
    """Split on double newlines or single newlines between sentences."""
    # Since text has been cleaned (whitespace collapsed), paragraphs
    # are identified by sentence-ending punctuation patterns.
    # For cleaned single-line text, we treat every 5 sentences as a paragraph.
    sentences = _split_sentences(text)
    if not sentences:
        return [text]
    # Group into approximate paragraphs of ~5 sentences
    chunk_size = 5
    return [
        " ".join(sentences[i:i + chunk_size])
        for i in range(0, len(sentences), chunk_size)
    ]


# ─── Readability ──────────────────────────────────────────────────────────────

def _count_syllables(word: str) -> int:
    """
    Approximate syllable count for English words.
    Uses vowel-group counting — not perfect but sufficient for
    bulk readability estimation across a document.
    """
    word = word.lower()
    if len(word) <= 3:
        return 1
    # Remove silent trailing 'e'
    word = re.sub(r'e$', '', word)
    vowel_groups = re.findall(r'[aeiou]+', word)
    return max(1, len(vowel_groups))


def _flesch_reading_ease(sentences: list[str], words: list[str]) -> float:
    """
    Flesch Reading Ease score.
    Formula: 206.835 - 1.015*(words/sentences) - 84.6*(syllables/words)

    Interpretation:
      90-100 : Very easy (5th grade)
      60-70  : Standard (8th-9th grade)
      30-50  : Difficult (college level)
      0-30   : Very difficult (professional)

    Returns 0.0 if there is insufficient text to score.
    """
    if not sentences or not words:
        return 0.0

    num_sentences = len(sentences)
    num_words = len(words)
    num_syllables = sum(_count_syllables(w) for w in words)

    if num_sentences == 0 or num_words == 0:
        return 0.0

    score = (
        206.835
        - 1.015 * (num_words / num_sentences)
        - 84.6  * (num_syllables / num_words)
    )
    # Clamp to 0-100 range
    return round(max(0.0, min(100.0, score)), 2)


# ─── Standard deviation ───────────────────────────────────────────────────────

def _std_dev(values: list[float]) -> float:
    """Population standard deviation."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return round(math.sqrt(variance), 2)


# ─── Main profile function ────────────────────────────────────────────────────

def build_style_profile(text: str) -> dict:
    """
    Compute a writing style profile from a text string.

    Args:
        text: Cleaned extracted text from a submission.

    Returns:
        A dict of style metrics. All values are floats rounded to 2dp.
        Returns a zeroed profile if the text is too short to analyse.
    """
    sentences = _split_sentences(text)
    words = _split_words(text)

    # Guard against very short texts
    if len(words) < 20 or len(sentences) < 2:
        return _empty_profile()

    # Sentence lengths in words
    sentence_lengths = [len(_split_words(s)) for s in sentences]

    # Word lengths in characters
    word_lengths = [len(w) for w in words]

    # Vocabulary diversity (Type-Token Ratio)
    unique_words = set(words)
    vocab_diversity = round(len(unique_words) / len(words), 4)

    # Punctuation density (marks per 100 words)
    punct_count = len(re.findall(r'[.,;:!?"\'\(\)\-]', text))
    punct_density = round((punct_count / len(words)) * 100, 2)

    # Paragraph statistics
    paragraphs = _split_paragraphs(text)
    para_sentence_counts = []
    for para in paragraphs:
        para_sents = _split_sentences(para)
        if para_sents:
            para_sentence_counts.append(len(para_sents))
    avg_para_length = round(
        sum(para_sentence_counts) / len(para_sentence_counts), 2
    ) if para_sentence_counts else 0.0

    # Long word ratio (words of 7+ characters)
    long_words = [w for w in words if len(w) >= 7]
    long_word_ratio = round(len(long_words) / len(words), 4)

    return {
        "avg_sentence_length":  round(sum(sentence_lengths) / len(sentence_lengths), 2),
        "avg_word_length":      round(sum(word_lengths) / len(word_lengths), 2),
        "vocabulary_diversity": vocab_diversity,
        "punctuation_density":  punct_density,
        "avg_paragraph_length": avg_para_length,
        "readability_score":    _flesch_reading_ease(sentences, words),
        "long_word_ratio":      long_word_ratio,
        "sentence_length_std":  _std_dev([float(l) for l in sentence_lengths]),
        "total_words":          len(words),
        "total_sentences":      len(sentences),
        "unique_words":         len(unique_words),
    }


def _empty_profile() -> dict:
    """Returns a zeroed profile for texts that are too short to analyse."""
    return {
        "avg_sentence_length":  0.0,
        "avg_word_length":      0.0,
        "vocabulary_diversity": 0.0,
        "punctuation_density":  0.0,
        "avg_paragraph_length": 0.0,
        "readability_score":    0.0,
        "long_word_ratio":      0.0,
        "sentence_length_std":  0.0,
        "total_words":          0,
        "total_sentences":      0,
        "unique_words":         0,
    }


# ─── Style deviation ──────────────────────────────────────────────────────────

def calculate_style_deviation(
    current_profile: dict,
    historical_profile: dict,
) -> float:
    """
    Compare a submission's style profile against a student's historical
    average profile and return a deviation score between 0.0 and 1.0.

    0.0 = writing style is identical to historical baseline
    1.0 = writing style is maximally different from historical baseline

    This is used to populate the `style_deviation` component in the
    risk score calculation.

    Args:
        current_profile    : Profile from the current submission.
        historical_profile : Average profile from previous submissions.

    Returns:
        Float between 0.0 and 1.0 representing style deviation magnitude.
        Returns 0.0 if either profile is empty/zeroed (no historical data).
    """
    # Metrics to compare and their maximum expected deviation ranges
    # (used to normalise each metric's contribution to 0-1)
    comparisons = [
        ("avg_sentence_length",  20.0),   # expect variation up to 20 words
        ("avg_word_length",       1.5),   # expect variation up to 1.5 chars
        ("vocabulary_diversity",  0.4),   # expect variation up to 0.4 TTR
        ("readability_score",    40.0),   # expect variation up to 40 points
        ("long_word_ratio",       0.3),   # expect variation up to 0.3
        ("sentence_length_std",  10.0),   # expect variation up to 10 words
    ]

    deviations = []
    for metric, max_range in comparisons:
        hist_val = historical_profile.get(metric, 0.0)
        curr_val = current_profile.get(metric, 0.0)

        # Skip if no historical baseline
        if hist_val == 0.0:
            continue

        raw_diff = abs(curr_val - hist_val)
        normalised = min(1.0, raw_diff / max_range)
        deviations.append(normalised)

    if not deviations:
        return 0.0

    return round(sum(deviations) / len(deviations), 4)


# ─── Manual test ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sample = (
        "Academic integrity is the foundation of honest scholarship. "
        "Students must submit original work and properly cite all sources used. "
        "Plagiarism undermines the educational process for everyone involved. "
        "Instructors rely on submitted work to accurately assess student understanding. "
        "When students circumvent this process, it devalues the qualifications earned. "
        "Institutions have a responsibility to maintain rigorous academic standards. "
        "These standards protect both the integrity of qualifications and the reputation of graduates."
    )

    profile = build_style_profile(sample)
    print("Style Profile:")
    for k, v in profile.items():
        print(f"  {k:<25} : {v}")

    # Simulate historical comparison
    historical = {
        "avg_sentence_length":  12.0,
        "avg_word_length":       4.8,
        "vocabulary_diversity":  0.72,
        "readability_score":    55.0,
        "long_word_ratio":       0.18,
        "sentence_length_std":   3.5,
    }
    deviation = calculate_style_deviation(profile, historical)
    print(f"\nStyle Deviation vs Historical: {deviation:.4f}")
