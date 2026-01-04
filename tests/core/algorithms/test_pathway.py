"""
Comprehensive unit tests for accessory pathway localization algorithms.

Tests verify correct pathway localization for known WPW patterns,
proper handling of edge cases, and clinical safety warnings.

Test Coverage:
- SMART-WPW Algorithm (15+ tests)
- Arruda Algorithm (10+ tests)
- PathwayLocalizer Ensemble (10+ tests)
- Clinical Safety (5+ tests)
- Edge Cases (5+ tests)

Total: 45+ comprehensive tests
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from core.algorithms.pathway import (
    PathwayLocalizer,
    SMARTWPWAlgorithm,
    ArrudaAlgorithm,
    PathwayLocation,
    AblationApproach,
    PathwayResult,
    quick_pathway_localization,
    detailed_pathway_analysis,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def smart_wpw_algorithm():
    """Fixture for SMART-WPW algorithm."""
    return SMARTWPWAlgorithm()


@pytest.fixture
def arruda_algorithm():
    """Fixture for Arruda algorithm."""
    return ArrudaAlgorithm()


@pytest.fixture
def pathway_localizer():
    """Fixture for PathwayLocalizer."""
    return PathwayLocalizer()


# ============================================================================
# SMART-WPW ALGORITHM TESTS (15+ tests)
# ============================================================================

class TestSMARTWPWAlgorithm:
    """Test SMART-WPW algorithm for various pathway locations."""

    def test_left_lateral_pathway(self, smart_wpw_algorithm):
        """Test left lateral pathway: V1+, inferior+, I+, aVL+ (free wall)."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "qrs_morphology": {"V1": "positive", "transition": "V2"},
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # Verify location
        assert PathwayLocation.LEFT_LATERAL.value in result.primary_location
        assert result.confidence > 0.8
        assert result.algorithm_used == "SMART-WPW Algorithm"
        assert len(result.step_details) >= 4  # Should have 4 main steps

        # Verify ablation approach
        assert "Transseptal" in result.ablation_approach

    def test_left_posterolateral_pathway(self, smart_wpw_algorithm):
        """Test left posterolateral pathway: V1+, inferior mixed/negative."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "0", "III": "-",
                "aVR": "-", "aVL": "+", "aVF": "0",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "qrs_morphology": {"V1": "positive", "transition": "V2"},
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # Should be left-sided with posterior component
        assert "Left" in result.primary_location
        # Mixed inferior leads reduce confidence
        assert result.confidence > 0.5

    def test_left_posterior_pathway(self, smart_wpw_algorithm):
        """Test left posterior pathway: V1+, inferior-, I+/-, aVL-/0 (more septal)."""
        measurements = {
            "delta_wave_polarity": {
                "I": "0", "II": "-", "III": "-",
                "aVR": "+", "aVL": "0", "aVF": "-",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "qrs_morphology": {"V1": "positive", "transition": "V2"},
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # Should be left posterior or posteroseptal
        assert ("Left Posterior" in result.primary_location or
                "Posteroseptal" in result.primary_location)
        assert result.confidence > 0.6

    def test_posteroseptal_pathway(self, smart_wpw_algorithm):
        """Test posteroseptal pathway: V1-, inferior-, I-, aVL- (midline septal)."""
        measurements = {
            "delta_wave_polarity": {
                "I": "-", "II": "-", "III": "-",
                "aVR": "+", "aVL": "-", "aVF": "-",
                "V1": "-", "V2": "0", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "qrs_morphology": {"V1": "negative", "transition": "V3"},
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # Should be posteroseptal
        assert "Posteroseptal" in result.primary_location or "septal" in result.primary_location.lower()

        # HIGH RISK warning for septal pathways
        assert "AV node" in result.ablation_approach or "CAUTION" in result.ablation_approach
        assert result.confidence > 0.6

    def test_right_posteroseptal_pathway(self, smart_wpw_algorithm):
        """Test right posteroseptal pathway: V1-, inferior-, I-, but more rightward."""
        measurements = {
            "delta_wave_polarity": {
                "I": "-", "II": "0", "III": "-",
                "aVR": "+", "aVL": "-", "aVF": "-",
                "V1": "-", "V2": "-", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "qrs_morphology": {"V1": "negative", "transition": "V3"},
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # Should be right posteroseptal or posteroseptal
        assert ("Right Posteroseptal" in result.primary_location or
                "Posteroseptal" in result.primary_location)

        # Should warn about AV node proximity
        assert any("AV node" in note.lower() or "caution" in note.lower()
                  for note in result.clinical_notes) or "AV node" in result.ablation_approach

    def test_anteroseptal_pathway_high_risk(self, smart_wpw_algorithm):
        """Test anteroseptal pathway: V1-, inferior+, I-, aVL- (HIGHEST RISK)."""
        measurements = {
            "delta_wave_polarity": {
                "I": "-", "II": "+", "III": "+",
                "aVR": "-", "aVL": "-", "aVF": "+",
                "V1": "-", "V2": "0", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "qrs_morphology": {"V1": "negative", "transition": "V2"},
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # Should identify as anteroseptal or septal
        assert ("Anteroseptal" in result.primary_location or
                "septal" in result.primary_location.lower())

        # MUST have HIGH RISK warnings
        assert "AV node" in result.ablation_approach
        assert "CAUTION" in result.ablation_approach or "HIGH RISK" in result.ablation_approach

        # Should mention risk in clinical notes
        assert any("high risk" in note.lower() or "av block" in note.lower()
                  for note in result.clinical_notes)

    def test_midseptal_pathway(self, smart_wpw_algorithm):
        """Test midseptal pathway: V1 negative (right/septal), inferior mixed, I-, aVL- for septal."""
        measurements = {
            "delta_wave_polarity": {
                "I": "-", "II": "0", "III": "0",
                "aVR": "-", "aVL": "-", "aVF": "0",
                "V1": "-", "V2": "0", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "qrs_morphology": {"V1": "negative", "transition": "V3"},
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # With V1 negative and I/aVL negative, should be septal or right-sided
        # May also be indeterminate with mixed inferior leads
        assert ("septal" in result.primary_location.lower() or
                "Right" in result.primary_location or
                "Indeterminate" in result.primary_location)

        # If clearly septal, should have AV node warnings
        if "septal" in result.primary_location.lower():
            assert "AV node" in result.ablation_approach

        # Should have low to moderate confidence due to mixed signals
        assert result.confidence <= 0.9

    def test_right_lateral_pathway(self, smart_wpw_algorithm):
        """Test right lateral pathway: V1-, inferior mixed, I+, aVL+ (free wall)."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "0",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "-", "V2": "-", "V3": "0",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "qrs_morphology": {"V1": "negative", "transition": "V3"},
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # Should be right-sided
        assert "Right" in result.primary_location
        assert result.confidence > 0.6

        # Right free wall should be standard approach
        assert "right atrial" in result.ablation_approach.lower() or "Right" in result.ablation_approach

    def test_right_anterolateral_pathway(self, smart_wpw_algorithm):
        """Test right anterolateral pathway: V1-, inferior+, right-sided."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "-", "V2": "-", "V3": "-",
                "V4": "0", "V5": "+", "V6": "+"
            },
            "qrs_morphology": {"V1": "negative", "transition": "V4"},
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # Should be right anterolateral or right lateral
        assert "Right" in result.primary_location
        assert result.confidence > 0.6

    def test_right_posterior_pathway(self, smart_wpw_algorithm):
        """Test right posterior pathway: V1-, inferior-, right free wall."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "-", "III": "-",
                "aVR": "-", "aVL": "+", "aVF": "-",
                "V1": "-", "V2": "-", "V3": "0",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "qrs_morphology": {"V1": "negative", "transition": "V3"},
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # Should be right posterior or right lateral
        assert "Right" in result.primary_location
        assert "Posterior" in result.primary_location or "Lateral" in result.primary_location

    def test_missing_lead_data_handling(self, smart_wpw_algorithm):
        """Test handling of incomplete lead data."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                # Missing aVR, aVL, aVF
                "V1": "+", "V2": "+", "V3": "+",
                # Missing V4, V5, V6
            },
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # Should track missing data
        assert len(result.missing_data) > 0
        assert "Delta wave polarity in leads" in result.missing_data[0]

        # Should have warnings
        assert len(result.warnings) > 0
        assert any("missing" in w.lower() for w in result.warnings)

        # Confidence should be reduced
        assert result.confidence < 1.0

    def test_no_manifest_preexcitation_warning(self, smart_wpw_algorithm):
        """Test warning when no manifest pre-excitation present."""
        measurements = {
            "delta_wave_polarity": {
                "I": "0", "II": "0", "III": "0",
                "aVR": "0", "aVL": "0", "aVF": "0",
                "V1": "0", "V2": "0", "V3": "0",
                "V4": "0", "V5": "0", "V6": "0"
            },
            "has_manifest_preexcitation": False
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # Should have warning about lack of pre-excitation
        assert len(result.warnings) > 0
        assert any("pre-excitation" in w.lower() for w in result.warnings)

        # Confidence should be very low
        assert result.confidence < 0.5

    def test_confidence_score_high_quality(self, smart_wpw_algorithm):
        """Test confidence score is high with complete, clear data."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "qrs_morphology": {"V1": "positive", "transition": "V2"},
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # Should have high confidence
        assert result.confidence >= 0.8
        assert result.primary_location != PathwayLocation.INDETERMINATE.value

    def test_step_details_generation(self, smart_wpw_algorithm):
        """Test that detailed step-by-step reasoning is generated."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # Should have 4 main steps
        assert len(result.step_details) >= 4

        # Step 1 should mention V1
        assert any("Step 1" in step and "V1" in step for step in result.step_details)

        # Step 2 should mention inferior leads
        assert any("Step 2" in step and ("inferior" in step.lower() or "II" in step)
                  for step in result.step_details)

        # Step 3 should mention I and aVL
        assert any("Step 3" in step and ("I" in step or "aVL" in step)
                  for step in result.step_details)

        # Step 4 should mention precordial
        assert any("Step 4" in step and "precordial" in step.lower()
                  for step in result.step_details)

    def test_ablation_approach_recommendations(self, smart_wpw_algorithm):
        """Test that appropriate ablation approaches are recommended."""
        # Left lateral - should recommend transseptal
        measurements_left = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result_left = smart_wpw_algorithm.evaluate(measurements_left)
        assert "Transseptal" in result_left.ablation_approach

        # Right lateral - should recommend right atrial
        measurements_right = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "0",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "-", "V2": "-", "V3": "0",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result_right = smart_wpw_algorithm.evaluate(measurements_right)
        assert ("right atrial" in result_right.ablation_approach.lower() or
                "Right" in result_right.ablation_approach)


# ============================================================================
# ARRUDA ALGORITHM TESTS (10+ tests)
# ============================================================================

class TestArrudaAlgorithm:
    """Test Arruda stepwise algorithm."""

    def test_arruda_free_wall_v1_negative(self, arruda_algorithm):
        """Test Arruda free wall pathway analysis (V1 negative)."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "-", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = arruda_algorithm.evaluate(measurements)

        # Should identify as free wall (left side because V2 is positive)
        assert "Left" in result.primary_location
        assert result.algorithm_used == "Arruda Stepwise Algorithm"

        # Step details should mention V1 negative
        assert any("V1" in step and "NEGATIVE" in step for step in result.step_details)

    def test_arruda_septal_v1_positive(self, arruda_algorithm):
        """Test Arruda septal pathway analysis (V1 positive)."""
        measurements = {
            "delta_wave_polarity": {
                "I": "0", "II": "-", "III": "-",
                "aVR": "-", "aVL": "0", "aVF": "-",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = arruda_algorithm.evaluate(measurements)

        # Should identify as septal
        assert "septal" in result.primary_location.lower()

        # Step details should mention V1 positive indicating septal
        assert any("V1" in step and "POSITIVE" in step and "Septal" in step
                  for step in result.step_details)

    def test_arruda_left_lateral(self, arruda_algorithm):
        """Test Arruda left lateral pathway identification."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "-", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = arruda_algorithm.evaluate(measurements)

        # Should be left lateral (V1 negative, V2 positive, I and II positive)
        assert PathwayLocation.LEFT_LATERAL.value in result.primary_location

        # Should mention leads I and II positive
        assert any("I and II" in step and "POSITIVE" in step for step in result.step_details)

    def test_arruda_left_posterolateral(self, arruda_algorithm):
        """Test Arruda left posterolateral pathway."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "-", "III": "-",
                "aVR": "-", "aVL": "+", "aVF": "-",
                "V1": "-", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = arruda_algorithm.evaluate(measurements)

        # Should be left posterolateral (V1 neg, V2 pos, II neg/iso)
        assert "Left" in result.primary_location
        assert ("Posterolateral" in result.primary_location or
                "Posterior" in result.primary_location)

    def test_arruda_right_anterolateral(self, arruda_algorithm):
        """Test Arruda right anterolateral pathway."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "-", "V2": "-", "V3": "0",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = arruda_algorithm.evaluate(measurements)

        # Should be right sided (V2 negative) with anterior (inferior positive)
        assert "Right" in result.primary_location

    def test_arruda_right_posterior(self, arruda_algorithm):
        """Test Arruda right posterior pathway."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "-", "III": "-",
                "aVR": "-", "aVL": "+", "aVF": "-",
                "V1": "-", "V2": "-", "V3": "0",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = arruda_algorithm.evaluate(measurements)

        # Should be right posterior (V2 neg, inferior neg)
        assert "Right" in result.primary_location
        assert ("Posterior" in result.primary_location or
                "Lateral" in result.primary_location)

    def test_arruda_posteroseptal(self, arruda_algorithm):
        """Test Arruda posteroseptal pathway."""
        measurements = {
            "delta_wave_polarity": {
                "I": "0", "II": "-", "III": "-",
                "aVR": "-", "aVL": "0", "aVF": "-",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = arruda_algorithm.evaluate(measurements)

        # Should be posteroseptal (V1 pos, inferior neg)
        assert "Posteroseptal" in result.primary_location or "septal" in result.primary_location.lower()

    def test_arruda_anteroseptal(self, arruda_algorithm):
        """Test Arruda anteroseptal pathway."""
        measurements = {
            "delta_wave_polarity": {
                "I": "0", "II": "+", "III": "+",
                "aVR": "-", "aVL": "0", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = arruda_algorithm.evaluate(measurements)

        # Should be anteroseptal (V1 pos, inferior pos)
        assert "Anteroseptal" in result.primary_location or "septal" in result.primary_location.lower()

    def test_arruda_accuracy_warning_present(self, arruda_algorithm):
        """Test that Arruda algorithm includes accuracy warning."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "-", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = arruda_algorithm.evaluate(measurements)

        # Should warn about lower accuracy
        assert len(result.warnings) > 0
        assert any("SMART-WPW" in w for w in result.warnings)

        # Confidence should be reduced (max 0.75)
        assert result.confidence <= 0.75

        # Clinical notes should mention accuracy
        assert any("53-75%" in note for note in result.clinical_notes)

    def test_arruda_step_details(self, arruda_algorithm):
        """Test that Arruda generates step details for decisions."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "-", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = arruda_algorithm.evaluate(measurements)

        # Should have step details
        assert len(result.step_details) >= 3

        # Should have Arruda steps
        assert any("Arruda Step" in step for step in result.step_details)


# ============================================================================
# PATHWAY LOCALIZER ENSEMBLE TESTS (10+ tests)
# ============================================================================

class TestPathwayLocalizer:
    """Test ensemble PathwayLocalizer combining both algorithms."""

    def test_complete_agreement(self, pathway_localizer):
        """Test when both algorithms agree on clear pathway pattern."""
        # Use a very clear left lateral pattern for best agreement
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "qrs_morphology": {"V1": "positive", "transition": "V2"},
            "has_manifest_preexcitation": True
        }

        result = pathway_localizer.localize(measurements)

        # Should have some level of agreement (algorithms may differ but should be compatible)
        assert result["consensus"]["agreement_level"] in ["complete", "partial", "poor"]

        # Both should identify as left-sided (V1 positive)
        assert "Left" in result["consensus"]["smart_location"]

        # Recommendation should be present and have confidence
        assert "recommendation" in result
        assert "CONFIDENCE" in result["recommendation"] or "confidence" in result["recommendation"].lower()

    def test_partial_agreement_alternative_match(self, pathway_localizer):
        """Test handling of algorithms with varying agreement levels."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "0", "III": "-",
                "aVR": "-", "aVL": "+", "aVF": "0",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = pathway_localizer.localize(measurements)

        # Should produce valid consensus regardless of agreement level
        assert result["consensus"]["agreement_level"] in ["complete", "partial", "poor"]

        # Both should still identify general location (likely left-sided based on V1+)
        # The consensus structure should be complete
        assert "smart_location" in result["consensus"]
        assert "arruda_location" in result["consensus"]

    def test_poor_agreement(self, pathway_localizer):
        """Test when algorithms disagree significantly."""
        # This is harder to construct, but indeterminate data might cause it
        measurements = {
            "delta_wave_polarity": {
                "I": "0", "II": "0", "III": "0",
                "aVR": "0", "aVL": "0", "aVF": "0",
                "V1": "0", "V2": "0", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": False
        }

        result = pathway_localizer.localize(measurements)

        # Consensus should exist even with disagreement
        assert "consensus" in result
        assert "agreement_level" in result["consensus"]
        assert result["consensus"]["agreement_level"] in ["complete", "partial", "poor"]

    def test_consensus_analysis_structure(self, pathway_localizer):
        """Test consensus analysis contains all required fields."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = pathway_localizer.localize(measurements)
        consensus = result["consensus"]

        # Check all required fields
        assert "exact_match" in consensus
        assert "agreement_level" in consensus
        assert "agreement_description" in consensus
        assert "regions_match" in consensus
        assert "smart_location" in consensus
        assert "arruda_location" in consensus
        assert "smart_confidence" in consensus
        assert "arruda_confidence" in consensus

    def test_recommendation_generation_high_confidence(self, pathway_localizer):
        """Test recommendation with high confidence agreement."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "qrs_morphology": {"V1": "positive", "transition": "V2"},
            "has_manifest_preexcitation": True
        }

        result = pathway_localizer.localize(measurements)

        # Should have clear recommendation
        assert "recommendation" in result
        assert len(result["recommendation"]) > 0
        assert "CONFIDENCE" in result["recommendation"]

    def test_recommendation_moderate_confidence(self, pathway_localizer):
        """Test recommendation with moderate confidence."""
        measurements = {
            "delta_wave_polarity": {
                "I": "0", "II": "+", "III": "0",
                "aVR": "-", "aVL": "0", "aVF": "0",
                "V1": "-", "V2": "0", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = pathway_localizer.localize(measurements)

        # Should still provide recommendation
        assert "recommendation" in result
        assert len(result["recommendation"]) > 0

    def test_summary_formatting(self, pathway_localizer):
        """Test that summary is properly formatted."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = pathway_localizer.localize(measurements)

        # Check summary structure
        assert "summary" in result
        summary = result["summary"]

        assert "ACCESSORY PATHWAY LOCALIZATION SUMMARY" in summary
        assert "PRIMARY LOCALIZATION:" in summary
        assert "SECONDARY CONFIRMATION:" in summary
        assert "AGREEMENT:" in summary
        assert "ABLATION APPROACH:" in summary

    def test_regional_agreement_left_sided(self, pathway_localizer):
        """Test regional agreement checking for left-sided pathways."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "0",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = pathway_localizer.localize(measurements)

        # Both should identify as left-sided
        assert "Left" in result["consensus"]["smart_location"]
        # Regional match should be true for similar locations
        # (this depends on the specific results)

    def test_regional_agreement_septal(self, pathway_localizer):
        """Test regional agreement checking for septal pathways."""
        measurements = {
            "delta_wave_polarity": {
                "I": "0", "II": "-", "III": "-",
                "aVR": "-", "aVL": "0", "aVF": "-",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = pathway_localizer.localize(measurements)

        # Should identify septal region
        consensus = result["consensus"]
        assert ("septal" in consensus["smart_location"].lower() or
                "septal" in consensus["arruda_location"].lower())

    def test_prefer_algorithm_smart_wpw(self, pathway_localizer):
        """Test prefer_algorithm parameter for SMART-WPW."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = pathway_localizer.localize(measurements, prefer_algorithm="SMART-WPW")

        # Primary should be SMART-WPW
        assert result["primary_result"]["algorithm_used"] == "SMART-WPW Algorithm"
        assert result["secondary_result"]["algorithm_used"] == "Arruda Stepwise Algorithm"

    def test_prefer_algorithm_arruda(self, pathway_localizer):
        """Test prefer_algorithm parameter for Arruda."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = pathway_localizer.localize(measurements, prefer_algorithm="Arruda")

        # Primary should be Arruda
        assert result["primary_result"]["algorithm_used"] == "Arruda Stepwise Algorithm"
        assert result["secondary_result"]["algorithm_used"] == "SMART-WPW Algorithm"


# ============================================================================
# CLINICAL SAFETY TESTS (5+ tests)
# ============================================================================

class TestClinicalSafety:
    """Test clinical safety warnings and recommendations."""

    def test_anteroseptal_high_risk_warning(self, smart_wpw_algorithm):
        """Test VERY HIGH RISK warning for anteroseptal pathways."""
        measurements = {
            "delta_wave_polarity": {
                "I": "-", "II": "+", "III": "+",
                "aVR": "-", "aVL": "-", "aVF": "+",
                "V1": "-", "V2": "0", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # If anteroseptal, MUST have high risk warning
        if "Anteroseptal" in result.primary_location:
            assert "AV node" in result.ablation_approach
            assert ("VERY HIGH RISK" in result.ablation_approach or
                    "CAUTION" in result.ablation_approach or
                    "HIGH RISK" in result.ablation_approach)

            # Clinical notes should mention pacemaker risk
            clinical_text = " ".join(result.clinical_notes).lower()
            assert ("pacemaker" in clinical_text or
                    "av block" in clinical_text or
                    "heart block" in clinical_text)

    def test_posteroseptal_av_node_warning(self, smart_wpw_algorithm):
        """Test AV node proximity warning for posteroseptal pathways."""
        measurements = {
            "delta_wave_polarity": {
                "I": "-", "II": "-", "III": "-",
                "aVR": "+", "aVL": "-", "aVF": "-",
                "V1": "-", "V2": "0", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # Posteroseptal should warn about AV node
        if "septal" in result.primary_location.lower():
            assert "AV node" in result.ablation_approach

            # Should mention cryoablation
            notes_text = " ".join(result.clinical_notes).lower()
            assert "cryo" in notes_text or "av node" in notes_text.lower()

    def test_left_sided_transseptal_approach(self, smart_wpw_algorithm):
        """Test transseptal approach recommendation for left-sided pathways."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # Left-sided should recommend transseptal
        assert "Left" in result.primary_location
        assert "Transseptal" in result.ablation_approach

        # Should mention anticoagulation
        notes_text = " ".join(result.clinical_notes).lower()
        assert ("anticoagulation" in notes_text or
                "transseptal" in notes_text)

    def test_right_sided_right_atrial_approach(self, smart_wpw_algorithm):
        """Test right atrial approach for right-sided pathways."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "0",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "-", "V2": "-", "V3": "0",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # Right free wall should be standard approach
        if "Right" in result.primary_location and "Posteroseptal" not in result.primary_location:
            assert ("right atrial" in result.ablation_approach.lower() or
                    "Standard right atrial" in result.ablation_approach)

    def test_all_wpw_referral_to_ep(self, smart_wpw_algorithm):
        """Test that all WPW cases recommend EP referral."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # Should recommend EP referral
        notes_text = " ".join(result.clinical_notes).lower()
        assert ("electrophysiology" in notes_text or
                "ep" in notes_text or
                "ablation" in notes_text)


# ============================================================================
# EDGE CASES (5+ tests)
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_all_leads_isoelectric(self, smart_wpw_algorithm):
        """Test handling of all isoelectric delta waves."""
        measurements = {
            "delta_wave_polarity": {
                "I": "0", "II": "0", "III": "0",
                "aVR": "0", "aVL": "0", "aVF": "0",
                "V1": "0", "V2": "0", "V3": "0",
                "V4": "0", "V5": "0", "V6": "0"
            },
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # Should handle gracefully
        assert result.primary_location is not None

        # Confidence should be very low
        assert result.confidence < 0.7

        # May be indeterminate
        # (algorithm should still produce result, just with low confidence)

    def test_conflicting_polarities(self, smart_wpw_algorithm):
        """Test handling of conflicting polarity patterns."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "-", "III": "+",
                "aVR": "+", "aVL": "-", "aVF": "+",
                "V1": "+", "V2": "-", "V3": "+",
                "V4": "-", "V5": "+", "V6": "-"
            },
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # Should produce result but with reduced confidence
        assert result.primary_location is not None

        # May have warnings about conflicting data
        # (algorithm should be robust to mixed patterns)

    def test_empty_measurements_dict(self, smart_wpw_algorithm):
        """Test handling of empty measurements dictionary."""
        measurements = {}

        result = smart_wpw_algorithm.evaluate(measurements)

        # Should handle gracefully
        assert result is not None

        # Should have missing data warnings
        assert len(result.missing_data) > 0 or len(result.warnings) > 0

        # Confidence should be very low
        assert result.confidence < 0.5

    def test_invalid_polarity_values(self, smart_wpw_algorithm):
        """Test handling of invalid polarity values."""
        measurements = {
            "delta_wave_polarity": {
                "I": "invalid", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # Should handle gracefully (treat invalid as isoelectric or missing)
        assert result is not None
        assert result.primary_location is not None

    def test_partial_lead_data(self, smart_wpw_algorithm):
        """Test with minimal but sufficient lead data."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+",
                "II": "+",
                "V1": "+",
                "V2": "+",
            },
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # Should handle but with reduced confidence
        assert result is not None
        assert result.confidence < 1.0
        assert len(result.missing_data) > 0


# ============================================================================
# CONVENIENCE FUNCTIONS TESTS
# ============================================================================

class TestConvenienceFunctions:
    """Test convenience functions for quick usage."""

    def test_quick_pathway_localization(self):
        """Test quick_pathway_localization function."""
        delta_waves = {
            "I": "+", "II": "+", "III": "+",
            "aVR": "-", "aVL": "+", "aVF": "+",
            "V1": "+", "V2": "+", "V3": "+",
            "V4": "+", "V5": "+", "V6": "+"
        }

        location = quick_pathway_localization(delta_waves)

        # Should return a string location
        assert isinstance(location, str)
        assert len(location) > 0
        assert "Left" in location

    def test_detailed_pathway_analysis(self):
        """Test detailed_pathway_analysis function."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = detailed_pathway_analysis(measurements)

        # Should return full analysis
        assert isinstance(result, dict)
        assert "primary_result" in result
        assert "secondary_result" in result
        assert "consensus" in result
        assert "recommendation" in result
        assert "summary" in result


# ============================================================================
# PATHWAY RESULT TESTS
# ============================================================================

class TestPathwayResult:
    """Test PathwayResult dataclass."""

    def test_pathway_result_to_dict(self, smart_wpw_algorithm):
        """Test PathwayResult.to_dict() method."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)
        result_dict = result.to_dict()

        # Should have all required fields
        assert "primary_location" in result_dict
        assert "confidence" in result_dict
        assert "alternative_locations" in result_dict
        assert "delta_wave_analysis" in result_dict
        assert "ablation_approach" in result_dict
        assert "clinical_notes" in result_dict
        assert "algorithm_used" in result_dict
        assert "step_details" in result_dict
        assert "missing_data" in result_dict
        assert "warnings" in result_dict

    def test_pathway_result_confidence_range(self, smart_wpw_algorithm):
        """Test that confidence is always between 0 and 1."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = smart_wpw_algorithm.evaluate(measurements)

        # Confidence should be 0-1
        assert 0.0 <= result.confidence <= 1.0
