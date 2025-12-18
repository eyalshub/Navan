from typing import Dict, List


class HallucinationGuard:
    """
    Validates that the agent output does not introduce unsupported factual claims.
    """

    def __init__(self, max_new_entities: int = 0):
        self.max_new_entities = max_new_entities

    def validate(
        self,
        raw_summary: str,
        agent_output: Dict,
    ) -> List[str]:
        """
        Returns a list of detected issues.
        Empty list = safe output.
        """

        issues = []

        explanation = agent_output.get("explanation", "")
        key_points = " ".join(agent_output.get("key_points", []))

        combined_output = explanation + " " + key_points

        # Very naive but effective first layer:
        # check for numbers not present in original summary
        summary_numbers = set(self._extract_numbers(raw_summary))
        output_numbers = set(self._extract_numbers(combined_output))

        if not output_numbers.issubset(summary_numbers):
            issues.append(
                "Output contains numeric details not present in the original summary."
            )

        # Detect overly specific phrasing
        suspicious_phrases = [
            "exactly",
            "specifically",
            "founded in",
            "opened in",
            "built in",
        ]

        for phrase in suspicious_phrases:
            if phrase in combined_output.lower():
                issues.append(
                    f"Suspiciously specific phrase detected: '{phrase}'"
                )

        return issues

    @staticmethod
    def _extract_numbers(text: str) -> List[str]:
        import re
        return re.findall(r"\b\d+\b", text)
