# coding=utf-8
"""Unit tests for ``agents.base`` classes."""

import unittest

from base import BaseTestCase

from agents import base
from agents.base import (
    AvatarAgent,
    BaseAgent,
    MetadataAgent,
    PartialMetadataAgent,
    StudioAgent,
)
from agents.types import Metadata, Person, Resource


class TestBaseAgentEnabled(BaseTestCase):

    def test_enabled_when_pref_true(self):
        agent = BaseAgent(Prefs)
        agent.name = "sample"
        self.update_prefs(sample_enabled=True)
        self.assertTrue(agent.enabled)

    def test_enabled_when_pref_truthy_string(self):
        agent = BaseAgent(Prefs)
        agent.name = "sample"
        self.update_prefs(sample_enabled="true")
        self.assertTrue(agent.enabled)

    def test_disabled_when_pref_false(self):
        agent = BaseAgent(Prefs)
        agent.name = "sample"
        self.update_prefs(sample_enabled=False)
        self.assertFalse(agent.enabled)

    def test_enabled_by_default_when_no_pref(self):
        agent = BaseAgent(Prefs)
        agent.name = "nopref"
        # Prefs has no key for "nopref_enabled" → except branch → True
        self.assertTrue(agent.enabled)


class TestBaseAgentSession(BaseTestCase):

    _original_session_cache = None

    def setUp(self):
        super(TestBaseAgentSession, self).setUp()
        self._original_session_cache = base.flaresolverr_session_cache
        base.flaresolverr_session_cache = base.FlareSolverrSessionCache()

    def tearDown(self):
        base.flaresolverr_session_cache = self._original_session_cache
        super(TestBaseAgentSession, self).tearDown()

    def test_create_session_without_proxy(self):
        self.update_prefs(proxy="")
        agent = BaseAgent(Prefs)
        session = agent.session
        self.assertIsNotNone(session)
        self.assertFalse(session.proxies)

    def test_create_session_with_proxy(self):
        self.update_prefs(proxy="http://127.0.0.1:7890")
        agent = BaseAgent(Prefs)
        session = agent.session
        self.assertEqual(session.proxies["http"], "http://127.0.0.1:7890")
        self.assertEqual(session.proxies["https"], "http://127.0.0.1:7890")

    def test_session_reused(self):
        self.update_prefs(proxy="")
        agent = BaseAgent(Prefs)
        s1 = agent.session
        s2 = agent.session
        self.assertIs(s1, s2)

    def test_session_recreated_on_proxy_change(self):
        self.update_prefs(proxy="")
        agent = BaseAgent(Prefs)
        s1 = agent.session
        self.update_prefs(proxy="http://new-proxy:8080")
        s2 = agent.session
        self.assertIs(s1, s2)
        self.assertEqual(s2.proxies["http"], "http://new-proxy:8080")

    def test_session_user_agent(self):
        self.assertIsNone(BaseAgent(Prefs).session.headers.get("User-Agent"))

        agent = BaseAgent(Prefs)
        self.update_prefs(user_agent="TestAgent/1.0")
        session = agent.session
        self.assertEqual(session.headers.get("User-Agent"), "TestAgent/1.0")

        self.update_prefs(user_agent="TestAgent/2.0")
        session = agent.session
        self.assertEqual(session.headers.get("User-Agent"), "TestAgent/2.0")

        self.update_prefs(user_agent="")
        session = agent.session
        self.assertIsNone(session.headers.get("User-Agent"))

    def test_flaresolverr_session(self):
        agent = BaseAgent(Prefs)
        # flaresolverr session is None if flaresolverr_url is not set
        self.assertIsNone(agent.flaresolverr_session)

        # set flaresolverr_url to create a flaresolverr session
        self.update_prefs(flaresolverr_url="http://localhost:8191/v1")
        fss = agent.flaresolverr_session
        self.assertIsNotNone(fss)
        self.assertEqual(fss._rpc._flaresolverr_url, "http://localhost:8191/v1")

        # share flaresolverr session across agent instances
        agent2 = BaseAgent(Prefs)
        self.assertIs(fss, agent2.flaresolverr_session)

        # proxy change
        self.update_prefs(proxy="http://proxy.example.com:8080")
        self.assertEqual(agent.flaresolverr_session.proxies.get(
            "http"), "http://proxy.example.com:8080")
        self.assertIs(agent.flaresolverr_session, agent2.flaresolverr_session)

        # flaresolverr_url change should create a new session
        self.update_prefs(flaresolverr_url="http://otherhost:8191/v1")
        self.assertIsNot(agent.flaresolverr_session, fss)

        # reset flaresolverr_url should clear session
        self.update_prefs(flaresolverr_url="")
        self.assertIsNone(agent.flaresolverr_session)


class TestMetadataAgentShouldContributeTo(BaseTestCase):

    def setUp(self):
        super(TestMetadataAgentShouldContributeTo, self).setUp()
        self.agent = MetadataAgent(Prefs)

    @staticmethod
    def _meta(**attrs):
        m = Metadata()
        for k, v in attrs.items():
            setattr(m, k, v)
        return m

    def test_returns_false_when_new_value_is_none(self):
        meta = self._meta(title="Existing")
        self.assertFalse(self.agent.should_contribute_to(meta, "title", None))

    def test_returns_true_when_current_value_is_none(self):
        meta = self._meta(title=None)
        self.assertTrue(self.agent.should_contribute_to(meta, "title", "New"))

    def test_media_containers_always_contribute(self):
        meta = self._meta(posters=["existing"], art=["existing"],
                          themes=["existing"], trailers=["existing"])
        for attr in ("posters", "art", "themes", "trailers"):
            self.assertTrue(
                self.agent.should_contribute_to(meta, attr, ["new"]),
                msg="Expected contribution for attribute: " + attr,
            )

    def test_scalar_does_not_contribute_when_already_set(self):
        meta = self._meta(title="Already Set")
        self.assertFalse(self.agent.should_contribute_to(meta, "title", "New"))


class TestMetadataAgentGetContributionValue(BaseTestCase):

    def setUp(self):
        super(TestMetadataAgentGetContributionValue, self).setUp()
        self.agent = MetadataAgent(Prefs)

    def test_resource_merge_sorted_by_score(self):
        r1 = Resource("http://a.com/1.jpg")
        r1.score = 80
        r2 = Resource("http://b.com/2.jpg")
        r2.score = 90
        r3 = Resource("http://c.com/3.jpg")
        r3.score = 70

        result = self.agent.get_contribution_value(
            [r3], "posters", [r1, r2],
        )
        scores = [r.score for r in result]
        self.assertEqual(scores, [90, 80, 70])

    def test_resource_merge_preserves_all(self):
        current = [Resource("http://a.com")]
        new = [Resource("http://b.com")]
        result = self.agent.get_contribution_value(new, "art", current)
        self.assertEqual(len(result), 2)

    def test_scalar_returns_new_value(self):
        result = self.agent.get_contribution_value("New Title", "title", "Old")
        self.assertEqual(result, "New Title")


class TestStudioAgentShouldContributeTo(BaseTestCase):

    def setUp(self):
        super(TestStudioAgentShouldContributeTo, self).setUp()
        self.agent = StudioAgent(Prefs)

    @staticmethod
    def _meta(**attrs):
        m = Metadata()
        for k, v in attrs.items():
            setattr(m, k, v)
        return m

    def test_studio_fields_contribute_even_when_already_set(self):
        studio_fields = [
            ("japanese_title", "new title"),
            ("release_date", "2022-01-01"),
            ("studio", "New Studio"),
            ("series", "New Series"),
            ("duration", 120),
        ]
        for attr, value in studio_fields:
            meta = self._meta(**{attr: "already set"})
            self.assertTrue(
                self.agent.should_contribute_to(meta, attr, value),
                msg="Expected contribution for studio field: " + attr,
            )

    def test_studio_fields_do_not_contribute_when_new_value_is_none(self):
        studio_fields = ["japanese_title", "release_date",
                         "studio", "series", "duration"]
        for attr in studio_fields:
            meta = self._meta(**{attr: "already set"})
            self.assertFalse(
                self.agent.should_contribute_to(meta, attr, None),
                msg="Expected no contribution for None value on field: " + attr,
            )

    def test_media_containers_contribute_via_parent(self):
        meta = self._meta(posters=["existing"], art=["existing"])
        for attr in ("posters", "art"):
            self.assertTrue(
                self.agent.should_contribute_to(meta, attr, ["new"]),
                msg="Expected contribution for media container: " + attr,
            )

    def test_non_studio_scalar_does_not_contribute_when_set(self):
        meta = self._meta(title="Already Set")
        self.assertFalse(self.agent.should_contribute_to(meta, "title", "New"))


class _StubAvatarAgent(AvatarAgent):
    """Concrete AvatarAgent for testing."""

    name = "stub_avatar"
    avatars = {}  # type: dict

    def get_avatar(self, actress, lang):
        url = self.avatars.get(str(actress))
        if url:
            url = Resource(url)
        return url


class TestAvatarAgentPartialUpdate(BaseTestCase):

    @staticmethod
    def _make_person(name, photo=None):
        p = Person(name)
        p.photo = photo
        return p

    def test_sets_photo_for_actress_without_one(self):
        agent = _StubAvatarAgent(Prefs)
        agent.avatars = {"Actress A": "http://avatar/a.jpg"}

        actress = self._make_person("Actress A")
        meta = Metadata()
        meta.actresses = [actress]

        agent.partial_update("CODE-1", meta, "ja")

        self.assertEqual(actress.photo, "http://avatar/a.jpg")
        self.assertIsInstance(actress.photo, Resource)
        self.assertEqual(actress.photo.score, 50)

    def test_skips_actress_when_photo_score_is_high(self):
        agent = _StubAvatarAgent(Prefs)
        agent.avatars = {"Actress A": "http://avatar/new.jpg"}

        old_photo = Resource("http://avatar/old.jpg")
        old_photo.score = 80
        actress = self._make_person("Actress A", photo=old_photo)
        meta = Metadata()
        meta.actresses = [actress]

        agent.partial_update("CODE-1", meta, "ja")

        self.assertEqual(actress.photo, "http://avatar/old.jpg")
        self.assertEqual(actress.photo.score, 80)

    def test_skips_actress_when_photo_score_at_threshold(self):
        agent = _StubAvatarAgent(Prefs)
        agent.avatars = {"Actress A": "http://avatar/new.jpg"}

        old_photo = Resource("http://avatar/old.jpg")
        old_photo.score = 50
        actress = self._make_person("Actress A", photo=old_photo)
        meta = Metadata()
        meta.actresses = [actress]

        agent.partial_update("CODE-1", meta, "ja")

        self.assertEqual(actress.photo, "http://avatar/old.jpg")

    def test_overwrites_photo_with_low_score(self):
        agent = _StubAvatarAgent(Prefs)
        agent.avatars = {"Actress A": "http://avatar/new.jpg"}

        old_photo = Resource("http://avatar/old.jpg")
        old_photo.score = 20
        actress = self._make_person("Actress A", photo=old_photo)
        meta = Metadata()
        meta.actresses = [actress]

        agent.partial_update("CODE-1", meta, "ja")

        self.assertEqual(actress.photo, "http://avatar/new.jpg")

    def test_skips_actress_with_no_match(self):
        agent = _StubAvatarAgent(Prefs)
        agent.avatars = {}

        actress = self._make_person("Unknown")
        meta = Metadata()
        meta.actresses = [actress]

        agent.partial_update("CODE-1", meta, "ja")

        self.assertIsNone(actress.photo)

    def test_handles_get_avatar_exception(self):
        class _FailingAvatar(AvatarAgent):
            name = "failing"

            def get_avatar(self, actress, lang):
                raise RuntimeError("network error")

        agent = _FailingAvatar(Prefs)
        actress = self._make_person("Actress A")
        meta = Metadata()
        meta.actresses = [actress]

        # Should not raise.
        agent.partial_update("CODE-1", meta, "ja")
        self.assertIsNone(actress.photo)


if __name__ == "__main__":
    unittest.main()
