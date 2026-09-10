"""
EduIntegrity AI — Tests for Writing Style and Risk Scoring Services

Run with:
    cd backend
    venv\\Scripts\\pytest tests/test_analysis_services.py -v
"""

import pytest
from app.services.writing_style import (
    build_style_profile,
    calculate_style_deviation,
    _empty_profile,
)
from app.services.risk_scoring import calculate_risk_score


# ── Helpers ───────────────────────────────────────────────────────────────────

# A realistic paragraph with enough content to profile
_SAMPLE_TEXT = (
    "Academic integrity is the foundation of honest scholarship and learning. "
    "Students must submit their own original work and properly cite all sources. "
    "Plagiarism undermines the educational process for everyone involved. "
    "Instructors rely on honest submissions to accurately assess student understanding. "
    "When students circumvent this process, it devalues qualifications earned by others. "
    "Institutions have a responsibility to maintain rigorous academic standards. "
    "These standards protect both the integrity of credentials and the reputation of graduates."
)

_SHORT_TEXT = "Hi there."


# ─── Writing Style: build_style_profile ──────────────────────────────────────

class TestBuildStyleProfile:

    def test_returns_all_expected_keys(self):
        profile = build_style_profile(_SAMPLE_TEXT)
        expected = [
            "avg_sentence_length", "avg_word_length", "vocabulary_diversity",
            "punctuation_density", "avg_paragraph_length", "readability_score",
            "long_word_ratio", "sentence_length_std",
            "total_words", "total_sentences", "unique_words",
        ]
        for key in expected:
            assert key in profile, f"Missing key: {key}"

    def test_word_count_is_positive(self):
        profile = build_style_profile(_SAMPLE_TEXT)
        assert profile["total_words"] > 0

    def test_sentence_count_is_positive(self):
        profile = build_style_profile(_SAMPLE_TEXT)
        assert profile["total_sentences"] > 0

    def test_vocabulary_diversity_between_0_and_1(self):
        profile = build_style_profile(_SAMPLE_TEXT)
        assert 0.0 <= profile["vocabulary_diversity"] <= 1.0

    def test_readability_score_is_clamped(self):
        profile = build_style_profile(_SAMPLE_TEXT)
        assert 0.0 <= profile["readability_score"] <= 100.0

    def test_long_word_ratio_between_0_and_1(self):
        profile = build_style_profile(_SAMPLE_TEXT)
        assert 0.0 <= profile["long_word_ratio"] <= 1.0

    def test_avg_sentence_length_is_reasonable(self):
        # Sample text sentences average ~14-18 words
        profile = build_style_profile(_SAMPLE_TEXT)
        assert 5 < profile["avg_sentence_length"] < 40

    def test_short_text_returns_zeroed_profile(self):
        # Text too short to analyse should return zeros, not crash
        profile = build_style_profile(_SHORT_TEXT)
        assert profile["total_words"] == 0
        assert profile["avg_sentence_length"] == 0.0
        assert profile["readability_score"] == 0.0

    def test_different_texts_produce_different_profiles(self):
        text_a = _SAMPLE_TEXT
        text_b = (
            "The cat sat. Dogs run fast. Birds fly. Trees grow tall. Sun shines bright. "
            "Rain falls down. Wind blows hard. Snow comes cold. Ice forms slow. Fire burns hot."
        )
        profile_a = build_style_profile(text_a)
        profile_b = build_style_profile(text_b)
        # Academic text should have longer sentences than the short simple sentences
        assert profile_a["avg_sentence_length"] > profile_b["avg_sentence_length"]


# ─── Writing Style: calculate_style_deviation ────────────────────────────────

class TestCalculateStyleDeviation:

    def test_identical_profiles_give_zero_deviation(self):
        profile = build_style_profile(_SAMPLE_TEXT)
        deviation = calculate_style_deviation(profile, profile)
        assert deviation == 0.0

    def test_deviation_is_between_0_and_1(self):
        profile_a = build_style_profile(_SAMPLE_TEXT)
        simple = (
            "The cat sat. Dogs run fast. Birds fly. Trees grow tall. Sun shines bright. "
            "Rain falls down. Wind blows hard. Snow comes cold. Ice forms slow. Fire burns hot."
        )
        profile_b = build_style_profile(simple)
        deviation = calculate_style_deviation(profile_a, profile_b)
        assert 0.0 <= deviation <= 1.0

    def test_very_different_styles_give_high_deviation(self):
        academic = build_style_profile(_SAMPLE_TEXT)
        simple = build_style_profile(
            "The cat sat. Dogs run fast. Birds fly. Trees grow tall. Sun shines bright. "
            "Rain falls down. Wind blows hard. Snow comes cold. Ice forms slow. Fire hot. " * 3
        )
        deviation = calculate_style_deviation(academic, simple)
        # Significantly different texts should produce noticeable deviation
        assert deviation > 0.1

    def test_empty_historical_profile_returns_zero(self):
        profile = build_style_profile(_SAMPLE_TEXT)
        deviation = calculate_style_deviation(profile, _empty_profile())
        assert deviation == 0.0


# ─── Risk Scoring: calculate_risk_score ──────────────────────────────────────

class TestCalculateRiskScore:

    def test_returns_all_expected_keys(self):
        result = calculate_risk_score(lexical_similarity=0.5, semantic_similarity=0.5)
        for key in ["risk_score", "risk_level", "risk_band_description",
                    "risk_color", "contributions", "weights_used", "disclaimer"]:
            assert key in result

    def test_zero_inputs_give_zero_score(self):
        result = calculate_risk_score(lexical_similarity=0.0, semantic_similarity=0.0)
        assert result["risk_score"] == 0.0
        assert result["risk_level"] == "LOW"

    def test_max_inputs_give_high_score(self):
        result = calculate_risk_score(
            lexical_similarity=1.0,
            semantic_similarity=1.0,
            style_deviation=1.0,
            historical_anomaly=1.0,
            citation_anomaly=1.0,
            ai_indicator=1.0,
        )
        assert result["risk_score"] == 100.0
        assert result["risk_level"] == "VERY HIGH"

    def test_risk_score_is_between_0_and_100(self):
        result = calculate_risk_score(lexical_similarity=0.6, semantic_similarity=0.7)
        assert 0.0 <= result["risk_score"] <= 100.0

    def test_correct_risk_bands(self):
        # LOW: all zeros → 0 score
        assert calculate_risk_score(0.0, 0.0)["risk_level"] == "LOW"

        # MODERATE (31-60): sem=0.7→17.5, lex=0.5→10, style=0.5→10 = 37.5
        assert calculate_risk_score(0.5, 0.7, style_deviation=0.5)["risk_level"] == "MODERATE"

        # HIGH (61-80): need all 6 components. sem=1.0→25, lex=1.0→20,
        # style=1.0→20, hist=1.0→15 = 80 → exactly HIGH boundary
        result = calculate_risk_score(1.0, 1.0, style_deviation=1.0, historical_anomaly=1.0)
        assert result["risk_level"] in ("HIGH", "VERY HIGH")

        # VERY HIGH (81-100): all components maxed
        assert calculate_risk_score(
            1.0, 1.0, style_deviation=1.0,
            historical_anomaly=1.0, citation_anomaly=1.0, ai_indicator=1.0
        )["risk_level"] == "VERY HIGH"

    def test_contributions_sum_to_risk_score(self):
        result = calculate_risk_score(
            lexical_similarity=0.4,
            semantic_similarity=0.6,
            style_deviation=0.3,
        )
        total = sum(result["contributions"].values())
        assert abs(total - result["risk_score"]) < 0.01  # floating point tolerance

    def test_custom_weights_are_used(self):
        custom = {
            "semantic_similarity": 0.5,
            "lexical_similarity":  0.5,
            "style_deviation":     0.0,
            "historical_anomaly":  0.0,
            "citation_anomaly":    0.0,
            "ai_indicator":        0.0,
        }
        result = calculate_risk_score(
            lexical_similarity=1.0,
            semantic_similarity=1.0,
            weights=custom,
        )
        # With custom weights: 1.0×0.5×100 + 1.0×0.5×100 = 100
        assert result["risk_score"] == 100.0

    def test_disclaimer_always_present(self):
        result = calculate_risk_score(lexical_similarity=0.3, semantic_similarity=0.3)
        assert len(result["disclaimer"]) > 0
        # Must not contain accusatory language
        assert "plagiarized" not in result["disclaimer"].lower()
        assert "guilty" not in result["disclaimer"].lower()
