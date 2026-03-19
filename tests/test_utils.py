# coding=utf-8

from base import BaseTestCase
from agents.utils import guess_video_code
from Code import parse_metadata_id, update_metadata_id, is_legacy_metadata_id


class TestParseMetadataId(BaseTestCase):

    def test_full_format(self):
        uid, agents = parse_metadata_id("ABC-123|agent1.id1;agent2.id2")
        self.assertEqual(uid, "ABC-123")
        self.assertEqual(agents, {"agent1": "id1", "agent2": "id2"})

    def test_single_agent(self):
        uid, agents = parse_metadata_id("ABC-123|lib.abc123")
        self.assertEqual(uid, "ABC-123")
        self.assertEqual(agents, {"lib": "abc123"})

    def test_no_agents_trailing_pipe(self):
        uid, agents = parse_metadata_id("ABC-123|")
        self.assertEqual(uid, "ABC-123")
        self.assertEqual(agents, {})

    def test_no_separator(self):
        uid, agents = parse_metadata_id("ABC-123")
        self.assertEqual(uid, "ABC-123")
        self.assertEqual(agents, {})

    def test_dotted_agent_id(self):
        uid, agents = parse_metadata_id("ABC-123|agent.com.example.path")
        self.assertEqual(uid, "ABC-123")
        self.assertEqual(agents, {"agent": "com.example.path"})

    def test_empty_string(self):
        uid, agents = parse_metadata_id("")
        self.assertEqual(uid, "")
        self.assertEqual(agents, {})

    def test_legacy_comma_format_compat(self):
        uid, agents = parse_metadata_id("ABC-123,agent1.id1;agent2.id2")
        self.assertEqual(uid, "ABC-123")
        self.assertEqual(agents, {"agent1": "id1", "agent2": "id2"})

    def test_legacy_comma_no_agents(self):
        uid, agents = parse_metadata_id("ABC-123,")
        self.assertEqual(uid, "ABC-123")
        self.assertEqual(agents, {})


class TestUpdateMetadataId(BaseTestCase):

    def test_appends_agent(self):
        result = update_metadata_id("ABC-123|a1.id1", "a2", "id2")
        self.assertEqual(result, "ABC-123|a1.id1;a2.id2")

    def test_appends_to_bare_id(self):
        result = update_metadata_id("ABC-123", "a1", "id1")
        self.assertEqual(result, "ABC-123|a1.id1")

    def test_updates_existing_agent(self):
        result = update_metadata_id("ABC-123|a1.old_id", "a1", "new_id")
        self.assertEqual(result, "ABC-123|a1.new_id")
    
    def test_legacy_metadata_id(self):
        self.assertFalse(is_legacy_metadata_id("ABC-123"))
        self.assertFalse(is_legacy_metadata_id(""))
        self.assertTrue(is_legacy_metadata_id("ABC-123,agent.id1"))
        self.assertTrue(is_legacy_metadata_id("ABC-123,"))
        self.assertFalse(is_legacy_metadata_id("ABC-123|agent.id1"))
        self.assertFalse(is_legacy_metadata_id("ABC-123|a1.id1;a2.id2"))


class TestGuessVideoCodePositive(BaseTestCase):

    CASES = [
        ("some text ABC-123 more text", "ABC-123"),
        ("[JBD-226] title", "JBD-226"),
        ("(ABP-001).mp4", "ABP-001"),
        ("/movies/MIDE-100/MIDE-100.mp4", "MIDE-100"),
        ("stars.STARS-999.mp4", "STARS-999"),
        ("ADV-R0630", "ADV-R0630"),
    ]

    def test_positive_cases(self):
        for text, expected in self.CASES:
            result = guess_video_code(text)
            self.assertEqual(
                result, expected,
                "guess_video_code(%r) should return %r, got %r" % (
                    text, expected, result),
            )


class TestGuessVideoCodeNegative(BaseTestCase):

    CASES = [
        "no id here",
        "1234567",
        "",
    ]

    def test_negative_cases(self):
        for text in self.CASES:
            result = guess_video_code(text)
            self.assertIsNone(
                result,
                "guess_video_code(%r) should return None, got %r" % (
                    text, result),
            )


if __name__ == "__main__":
    unittest.main()
