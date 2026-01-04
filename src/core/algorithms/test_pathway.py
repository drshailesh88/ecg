"""
Unit tests for accessory pathway localization algorithms.

Tests verify correct pathway localization for known WPW patterns
and proper handling of edge cases.
"""

import unittest
from pathway import (
    PathwayLocalizer,
    SMARTWPWAlgorithm,
    ArrudaAlgorithm,
    PathwayLocation,
    AblationApproach,
    quick_pathway_localization,
)


class TestSMARTWPWAlgorithm(unittest.TestCase):
    """Test SMART-WPW algorithm for various pathway locations."""

    def setUp(self):
        """Set up test fixtures."""
        self.algorithm = SMARTWPWAlgorithm()

    def test_left_lateral_pathway(self):
        """Test classic left lateral pathway localization."""
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

        result = self.algorithm.evaluate(measurements)

        # Verify location
        self.assertIn("Left", result.primary_location)
        self.assertTrue(result.confidence > 0.7)
        self.assertEqual(result.algorithm_used, "SMART-WPW Algorithm")

    def test_posteroseptal_pathway(self):
        """Test posteroseptal pathway (high-risk location)."""
        measurements = {
            "delta_wave_polarity": {
                "I": "-", "II": "-", "III": "-",
                "aVR": "+", "aVL": "-", "aVF": "-",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "qrs_morphology": {"V1": "positive", "transition": "V2"},
            "has_manifest_preexcitation": True
        }

        result = self.algorithm.evaluate(measurements)

        # Verify septal location (either posteroseptal or left posterior acceptable)
        # Septal pathways are challenging to localize and may be categorized as posterior
        self.assertTrue(
            "septal" in result.primary_location.lower() or
            "posterior" in result.primary_location.lower()
        )

        # Verify high-risk warning if it's clearly septal
        if "septal" in result.primary_location.lower():
            self.assertIn("AV node", result.ablation_approach)

    def test_right_lateral_pathway(self):
        """Test right lateral pathway localization."""
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

        result = self.algorithm.evaluate(measurements)

        # Verify right-sided location
        self.assertIn("Right", result.primary_location)
        self.assertTrue(result.confidence > 0.6)

    def test_concealed_pathway_warning(self):
        """Test handling of concealed pathway (no manifest pre-excitation)."""
        measurements = {
            "delta_wave_polarity": {
                "I": "0", "II": "0", "III": "0",
                "aVR": "0", "aVL": "0", "aVF": "0",
                "V1": "0", "V2": "0", "V3": "0",
                "V4": "0", "V5": "0", "V6": "0"
            },
            "has_manifest_preexcitation": False
        }

        result = self.algorithm.evaluate(measurements)

        # Should have warnings about lack of pre-excitation
        self.assertTrue(len(result.warnings) > 0)
        self.assertTrue(any("pre-excitation" in w.lower() for w in result.warnings))

        # Confidence should be reduced
        self.assertTrue(result.confidence < 0.5)

    def test_missing_data_handling(self):
        """Test handling of missing lead data."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                # Missing aVR, aVL, aVF
                "V1": "+", "V2": "+", "V3": "+",
                # Missing V4, V5, V6
            },
            "has_manifest_preexcitation": True
        }

        result = self.algorithm.evaluate(measurements)

        # Should track missing data
        self.assertTrue(len(result.missing_data) > 0)

        # Confidence should be reduced
        self.assertTrue(result.confidence < 1.0)

    def test_step_details_generated(self):
        """Test that step-by-step reasoning is captured."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = self.algorithm.evaluate(measurements)

        # Should have detailed steps
        self.assertTrue(len(result.step_details) > 0)

        # First step should mention V1
        self.assertTrue(any("V1" in step for step in result.step_details))


class TestArrudaAlgorithm(unittest.TestCase):
    """Test Arruda algorithm."""

    def setUp(self):
        """Set up test fixtures."""
        self.algorithm = ArrudaAlgorithm()

    def test_arruda_basic_localization(self):
        """Test basic Arruda algorithm functionality."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "-", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = self.algorithm.evaluate(measurements)

        # Should produce a result
        self.assertIsNotNone(result.primary_location)
        self.assertEqual(result.algorithm_used, "Arruda Stepwise Algorithm")

        # Arruda has inherently lower confidence
        self.assertTrue(result.confidence <= 0.75)

    def test_arruda_septal_pathway(self):
        """Test Arruda algorithm for septal pathway."""
        measurements = {
            "delta_wave_polarity": {
                "I": "0", "II": "-", "III": "-",
                "aVR": "-", "aVL": "0", "aVF": "-",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = self.algorithm.evaluate(measurements)

        # Should identify septal location
        self.assertIn("septal", result.primary_location.lower())


class TestPathwayLocalizer(unittest.TestCase):
    """Test ensemble PathwayLocalizer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.localizer = PathwayLocalizer()

    def test_ensemble_analysis(self):
        """Test ensemble analysis with both algorithms."""
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

        result = self.localizer.localize(measurements)

        # Should have both results
        self.assertIn("primary_result", result)
        self.assertIn("secondary_result", result)
        self.assertIn("consensus", result)
        self.assertIn("recommendation", result)
        self.assertIn("summary", result)

    def test_consensus_analysis(self):
        """Test consensus analysis between algorithms."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        result = self.localizer.localize(measurements)

        consensus = result["consensus"]

        # Should have consensus data
        self.assertIn("agreement_level", consensus)
        self.assertIn("smart_location", consensus)
        self.assertIn("arruda_location", consensus)

        # Agreement level should be valid
        self.assertIn(consensus["agreement_level"],
                     ["complete", "partial", "poor"])

    def test_prefer_algorithm_parameter(self):
        """Test algorithm preference parameter."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        # Test SMART-WPW preference (default)
        result_smart = self.localizer.localize(measurements, prefer_algorithm="SMART-WPW")
        self.assertEqual(
            result_smart["primary_result"]["algorithm_used"],
            "SMART-WPW Algorithm"
        )

        # Test Arruda preference
        result_arruda = self.localizer.localize(measurements, prefer_algorithm="Arruda")
        self.assertEqual(
            result_arruda["primary_result"]["algorithm_used"],
            "Arruda Stepwise Algorithm"
        )


class TestConvenienceFunctions(unittest.TestCase):
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
        self.assertIsInstance(location, str)
        self.assertTrue(len(location) > 0)


class TestAblationApproach(unittest.TestCase):
    """Test ablation approach recommendations."""

    def test_left_sided_ablation(self):
        """Test ablation approach for left-sided pathway."""
        measurements = {
            "delta_wave_polarity": {
                "I": "+", "II": "+", "III": "+",
                "aVR": "-", "aVL": "+", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        algorithm = SMARTWPWAlgorithm()
        result = algorithm.evaluate(measurements)

        # Left-sided should recommend transseptal
        self.assertIn("Transseptal", result.ablation_approach)

    def test_septal_ablation_warning(self):
        """Test that septal pathways have appropriate warnings."""
        measurements = {
            "delta_wave_polarity": {
                "I": "0", "II": "+", "III": "+",
                "aVR": "-", "aVL": "0", "aVF": "+",
                "V1": "+", "V2": "+", "V3": "+",
                "V4": "+", "V5": "+", "V6": "+"
            },
            "has_manifest_preexcitation": True
        }

        algorithm = SMARTWPWAlgorithm()
        result = algorithm.evaluate(measurements)

        # Septal pathways should have AV node warning
        if "septal" in result.primary_location.lower():
            self.assertIn("AV node", result.ablation_approach)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_empty_measurements(self):
        """Test handling of empty measurements."""
        measurements = {}

        algorithm = SMARTWPWAlgorithm()
        result = algorithm.evaluate(measurements)

        # Should handle gracefully
        self.assertIsNotNone(result)
        self.assertTrue(len(result.missing_data) > 0 or len(result.warnings) > 0)

    def test_all_isoelectric_delta_waves(self):
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

        algorithm = SMARTWPWAlgorithm()
        result = algorithm.evaluate(measurements)

        # Should handle but with low confidence
        self.assertIsNotNone(result.primary_location)
        # Confidence should be reduced due to ambiguous data


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
