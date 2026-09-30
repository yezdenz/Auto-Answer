import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auto_answer.security import redact_secrets


class TestSecurityHelpers(unittest.TestCase):
    def test_redacts_google_keys_and_key_assignments(self):
        fake = "AIza" + "A" * 35
        text = redact_secrets(f"request failed api_key={fake} token {fake}")
        self.assertNotIn(fake, text)
        self.assertIn("[REDACTED]", text)

if __name__ == "__main__":
    unittest.main()
