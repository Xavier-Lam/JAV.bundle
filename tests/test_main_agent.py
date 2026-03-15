# coding=utf-8

from base import BaseTestCase

import datetime
import unittest

import mock

import Code as _main
from Code import JAVAgent
from agents.base import (
    BaseAgent,
    MetadataAgent,
    PartialMetadataAgent,
    SearchAgent,
)
from agents.types import Metadata, Person, Resource, SearchItem
from framework.containers import MediaContainer
from framework.media import Media, MediaItem, MediaPart
from framework.metadata import Movie


# ===================================================================
# Concrete mock agents
# ===================================================================

class _MockSearchAgent(SearchAgent):
    name = "mock_search"
    weight = 100

    keywords = None   # type: list | None
    results = None    # type: list | None

    def guess_keywords(self, name, filename, directory):
        if self.keywords is not None:
            return self.keywords
        return [name]

    def search(self, keywords, lang):
        return list(self.results or [])


class _MockMetadataAgent(MetadataAgent):
    name = "mock_meta"
    weight = 50

    metadata = None  # type: Metadata | None

    def get_metadata(self, agent_id, video_code, lang):
        return self.metadata


class _MockPartialAgent(PartialMetadataAgent):
    name = "mock_partial"
    weight = 30

    callback = None  # type: callable | None

    def partial_update(self, video_code, metadata, lang):
        if self.callback:
            self.callback(video_code, metadata, lang)


# ===================================================================
# Tests
# ===================================================================

class TestNormalizeLang(BaseTestCase):

    def test_japanese_unchanged(self):
        self.assertEqual(JAVAgent.normalize_lang("ja"), "ja")

    def test_english_unchanged(self):
        self.assertEqual(JAVAgent.normalize_lang("en"), "en")

    def test_chinese_unchanged(self):
        self.assertEqual(JAVAgent.normalize_lang("zh"), "zh")

    def test_no_language_falls_back(self):
        self.assertEqual(
            JAVAgent.normalize_lang(Locale.Language.NoLanguage), "ja",
        )

    def test_unsupported_falls_back(self):
        self.assertEqual(JAVAgent.normalize_lang("fr"), "ja")


class TestClearMetadata(BaseTestCase):

    def test_fields_are_reset(self):
        movie = Movie()
        movie.title = "Old Title"
        movie.year = 2020
        movie.studio = "Old Studio"
        movie.genres.add("Action")
        movie.posters["http://a.com/1.jpg"] = "data"

        agent = JAVAgent()
        agent.clear_metadata(movie)

        self.assertEqual(movie.title, "")
        self.assertIsNone(movie.year)
        self.assertIsNone(movie.duration)
        self.assertEqual(movie.studio, "")
        self.assertEqual(movie.summary, "")
        self.assertEqual(movie.original_title, "")
        self.assertEqual(movie.title_sort, "")
        self.assertIsNone(movie.rating)
        self.assertEqual(len(movie.genres), 0)
        self.assertEqual(len(movie.collections), 0)
        self.assertEqual(len(movie.similar), 0)
        self.assertEqual(len(movie.tags), 0)
        self.assertEqual(len(movie.roles), 0)
        self.assertEqual(len(movie.directors), 0)
        self.assertEqual(len(movie.posters), 0)
        self.assertEqual(len(movie.art), 0)


class TestApplyMetadata(BaseTestCase):

    default_prefs = {"series_as_collection": ""}

    def _apply(self, metadata, movie=None):
        self.update_prefs(series_as_collection=Prefs._prefs.get(
            "series_as_collection", True))
        if movie is None:
            movie = Movie()
        agent = JAVAgent()
        agent.apply_metadata(movie, metadata, "ja")
        return movie

    def test_basic_fields(self):
        meta = Metadata()
        meta.title = "Test Title"
        meta.japanese_title = u"テストタイトル"
        meta.release_date = datetime.date(2022, 5, 15)
        meta.studio = "TestStudio"
        meta.duration = 7200000

        movie = self._apply(meta)

        self.assertEqual(movie.title, "Test Title")
        self.assertEqual(movie.original_title, u"テストタイトル")
        self.assertEqual(movie.originally_available_at,
                         datetime.date(2022, 5, 15))
        self.assertEqual(movie.year, 2022)
        self.assertEqual(movie.studio, "TestStudio")
        self.assertEqual(movie.duration, 7200000)
        self.assertEqual(movie.content_rating, "R")
        self.assertEqual(movie.content_rating_age, 18)
        self.assertIn("JP", movie.countries)

    def test_genres_applied(self):
        meta = Metadata()
        meta.title = "T"
        meta.genres = {"Action", "Drama"}
        movie = self._apply(meta)
        self.assertIn("Action", movie.genres)
        self.assertIn("Drama", movie.genres)

    def test_series_added_to_tags_and_similar(self):
        meta = Metadata()
        meta.title = "T"
        meta.series = "MySeries"
        movie = self._apply(meta)
        self.assertIn("MySeries", movie.tags)
        self.assertIn("MySeries", movie.similar)

    def test_series_as_collection_pref(self):
        self.update_prefs(series_as_collection="true")
        meta = Metadata()
        meta.title = "T"
        meta.series = "MySeries"
        movie = self._apply(meta)
        self.assertIn("MySeries", movie.collections)

    def test_series_not_in_collection_when_pref_empty(self):
        self.update_prefs(series_as_collection="")
        meta = Metadata()
        meta.title = "T"
        meta.series = "MySeries"
        movie = self._apply(meta)
        self.assertEqual(len(movie.collections), 0)

    def test_actresses_applied_as_roles(self):
        meta = Metadata()
        meta.title = "T"
        a = Person("Actress One")
        a.photo = "http://photo/1.jpg"
        meta.actresses = [a]
        movie = self._apply(meta)
        self.assertEqual(len(movie.roles), 1)
        self.assertEqual(movie.roles[0].name, "Actress One")
        self.assertEqual(movie.roles[0].photo, "http://photo/1.jpg")

    def test_directors_applied(self):
        meta = Metadata()
        meta.title = "T"
        d = Person("Director One")
        d.photo = "http://photo/d.jpg"
        meta.directors = [d]
        movie = self._apply(meta)
        self.assertEqual(len(movie.directors), 1)
        self.assertEqual(movie.directors[0].name, "Director One")

    def test_summary_applied(self):
        meta = Metadata()
        meta.title = "T"
        meta.summary = "A great movie."
        movie = self._apply(meta)
        self.assertEqual(movie.summary, "A great movie.")

    def test_rating_applied(self):
        meta = Metadata()
        meta.title = "T"
        meta.rating = 8.5
        movie = self._apply(meta)
        self.assertEqual(movie.rating, 8.5)

    def test_title_sort_defaults_to_title(self):
        meta = Metadata()
        meta.title = "My Title"
        movie = self._apply(meta)
        self.assertEqual(movie.title_sort, "My Title")

    def test_title_sort_explicit(self):
        meta = Metadata()
        meta.title = "My Title"
        meta.title_sort = "Title, My"
        movie = self._apply(meta)
        self.assertEqual(movie.title_sort, "Title, My")

    def test_labels_added_to_tags(self):
        meta = Metadata()
        meta.title = "T"
        meta.labels = {"LabelA", "LabelB"}
        movie = self._apply(meta)
        self.assertIn("LabelA", movie.tags)
        self.assertIn("LabelB", movie.tags)

    def test_studio_added_to_similar(self):
        meta = Metadata()
        meta.title = "T"
        meta.studio = "StudioX"
        movie = self._apply(meta)
        self.assertIn("StudioX", movie.similar)


class TestJAVAgentSearch(BaseTestCase):

    def _make_agent(self, mock_agents):
        agent = JAVAgent()
        agent.cached_agents = mock_agents
        return agent

    def _make_hints(self, name, filename):
        hints = Media.Movie()
        hints.name = name
        item = MediaItem()
        part = MediaPart()
        part.file = filename
        item.parts.append(part)
        hints.items.append(item)
        return hints

    def test_normalizes_language(self):
        searcher = _MockSearchAgent(Prefs)
        searcher.results = []
        searcher.keywords = ["kw"]

        with mock.patch.object(searcher, "search", wraps=searcher.search) as mock_search:
            agent = self._make_agent([searcher])
            hints = self._make_hints("ABC-123", "/movies/ABC-123.mp4")
            results = MediaContainer()
            agent.search(results, hints, "fr")

        mock_search.assert_called_once()
        self.assertEqual(mock_search.call_args[0][1], "ja")

    def test_chooses_only_search_agents(self):
        searcher = _MockSearchAgent(Prefs)
        si = SearchItem()
        si.id = "id1"
        si.video_code = "ABC-123"
        si.title = "Title"
        si.score = 100
        searcher.results = [si]

        meta_agent = _MockMetadataAgent(Prefs)
        meta_agent.metadata = Metadata()

        agent = self._make_agent([searcher, meta_agent])
        hints = self._make_hints("ABC-123", "/movies/ABC-123.mp4")
        results = MediaContainer()
        agent.search(results, hints, "ja")

        self.assertEqual(len(results._media), 1)

    def test_merged_results_from_multiple_sources(self):
        s1 = _MockSearchAgent(Prefs)
        s1.name = "source1"
        si1 = SearchItem()
        si1.id = "src1_id"
        si1.video_code = "ABC-123"
        si1.title = "Title from S1"
        si1.score = 90
        s1.results = [si1]

        s2 = _MockSearchAgent(Prefs)
        s2.name = "source2"
        si2 = SearchItem()
        si2.id = "src2_id"
        si2.video_code = "ABC-123"
        si2.title = "Title from S2"
        si2.score = 80
        s2.results = [si2]

        agent = self._make_agent([s1, s2])
        hints = self._make_hints("ABC-123", "/movies/ABC-123.mp4")
        results = MediaContainer()
        agent.search(results, hints, "ja")

        # Same video_code → merged into one result
        self.assertEqual(len(results._media), 1)
        # The merged result ID should contain both agents
        self.assertEqual(
            results._media[0].id, "ABC-123,source1.src1_id;source2.src2_id")

    def test_different_video_codes_not_merged(self):
        s1 = _MockSearchAgent(Prefs)
        s1.name = "s1"
        si1 = SearchItem()
        si1.id = "id1"
        si1.video_code = "ABC-123"
        si1.title = "T1"
        si1.score = 90
        s1.results = [si1]

        s2 = _MockSearchAgent(Prefs)
        s2.name = "s2"
        si2 = SearchItem()
        si2.id = "id2"
        si2.video_code = "XYZ-999"
        si2.title = "T2"
        si2.score = 80
        s2.results = [si2]

        agent = self._make_agent([s1, s2])
        hints = self._make_hints("test", "/movies/test.mp4")
        results = MediaContainer()
        agent.search(results, hints, "ja")

        self.assertEqual(len(results._media), 2)

    def test_results_sorted_by_score(self):
        s = _MockSearchAgent(Prefs)

        si1 = SearchItem()
        si1.id = "id1"
        si1.video_code = "LOW-001"
        si1.title = "Low"
        si1.score = 30

        si2 = SearchItem()
        si2.id = "id2"
        si2.video_code = "HIGH-002"
        si2.title = "High"
        si2.score = 95

        s.results = [si1, si2]
        agent = self._make_agent([s])
        hints = self._make_hints("test", "/movies/test.mp4")
        results = MediaContainer()
        agent.search(results, hints, "ja")

        self.assertEqual(len(results._media), 2)
        self.assertEqual(results._media[0].score, 95)
        self.assertEqual(results._media[1].score, 30)

    def test_search_results_converted_to_search_items(self):
        s = _MockSearchAgent(Prefs)
        si = SearchItem()
        si.id = "agent_id"
        si.video_code = "ABC-123"
        si.title = "My Title"
        si.year = "2022"
        si.score = 85
        si.thumb = "http://thumb.jpg"
        s.results = [si]

        agent = self._make_agent([s])
        hints = self._make_hints("ABC-123", "/movies/ABC-123.mp4")
        results = MediaContainer()
        agent.search(results, hints, "ja")

        self.assertEqual(len(results._media), 1)
        r = results._media[0]
        self.assertIn("ABC-123", r.id)
        self.assertEqual(r.name, "My Title")
        self.assertEqual(r.year, "2022")
        self.assertEqual(r.score, 85)
        self.assertEqual(r.thumb, "http://thumb.jpg")

    def test_agent_search_exception_skipped(self):
        class _FailingSearch(_MockSearchAgent):
            name = "failing"

            def search(self, keywords, lang):
                raise RuntimeError("boom")

        s = _FailingSearch(Prefs)
        s.keywords = ["kw"]

        agent = self._make_agent([s])
        hints = self._make_hints("ABC-123", "/movies/ABC-123.mp4")
        results = MediaContainer()

        # Should not raise
        agent.search(results, hints, "ja")
        self.assertEqual(len(results._media), 0)

    def test_empty_keywords_skipped(self):
        s = _MockSearchAgent(Prefs)
        s.keywords = []
        s.results = [SearchItem()]

        agent = self._make_agent([s])
        hints = self._make_hints("ABC-123", "/movies/ABC-123.mp4")
        results = MediaContainer()

        agent.search(results, hints, "ja")
        self.assertEqual(len(results._media), 0)


class TestUncensorTitle(BaseTestCase):

    def setUp(self):
        super(TestUncensorTitle, self).setUp()
        JAVAgent.censored_words_cache = None

    def _make_agent(self, mock_agents):
        agent = JAVAgent()
        agent.cached_agents = mock_agents
        return agent

    def _make_hints(self, name, filename):
        hints = Media.Movie()
        hints.name = name
        item = MediaItem()
        part = MediaPart()
        part.file = filename
        item.parts.append(part)
        hints.items.append(item)
        return hints

    def test_filled_circle_replaced(self):
        result = JAVAgent.uncensor_title(u"J\u25cfとのセックス")
        self.assertEqual(result, u"JKとのセックス")

    def test_white_circle_normalized(self):
        # ○ (U+25CB) is normalized to ● before lookup
        result = JAVAgent.uncensor_title(u"J\u25cbとのセックス")
        self.assertEqual(result, u"JKとのセックス")

    def test_large_white_circle_normalized(self):
        # ◯ (U+25EF) is normalized to ● before lookup
        result = JAVAgent.uncensor_title(u"J\u25efとのセックス")
        self.assertEqual(result, u"JKとのセックス")

    def test_ideographic_zero_normalized(self):
        # 〇 (U+3007) is normalized to ● before lookup
        result = JAVAgent.uncensor_title(u"J\u3007とのセックス")
        self.assertEqual(result, u"JKとのセックス")

    def test_fullwidth_variant_replaced(self):
        result = JAVAgent.uncensor_title(u"Ｊ●生レイプ")
        self.assertEqual(result, u"ＪＫ生レイプ")

    def test_multiple_censored_words(self):
        result = JAVAgent.uncensor_title(u"J●とJ●の物語")
        self.assertEqual(result, u"JKとJKの物語")

    def test_no_censored_words_unchanged(self):
        result = JAVAgent.uncensor_title(u"普通のタイトル ABP-123")
        self.assertEqual(result, u"普通のタイトル ABP-123")

    def test_empty_string_returned(self):
        result = JAVAgent.uncensor_title(u"")
        self.assertEqual(result, u"")

    def test_none_returned(self):
        result = JAVAgent.uncensor_title(None)
        self.assertIsNone(result)

    def test_cache_populated_after_first_call(self):
        self.assertIsNone(JAVAgent.censored_words_cache)
        JAVAgent.uncensor_title(u"J●")
        self.assertIsNotNone(JAVAgent.censored_words_cache)

    def test_search_result_title_uncensored(self):
        s = _MockSearchAgent(Prefs)
        si = SearchItem()
        si.id = "agent_id"
        si.video_code = "JK-001"
        si.title = u"J●女子校生コレクション"
        si.score = 85
        s.results = [si]

        agent = self._make_agent([s])
        hints = self._make_hints("JK-001", "/movies/JK-001.mp4")
        results = MediaContainer()
        agent.search(results, hints, "ja")

        self.assertEqual(len(results._media), 1)
        self.assertEqual(results._media[0].name, u"JK女子校生コレクション")

    def test_search_result_title_normalized_variant(self):
        # Title using ○ variant in search result is also uncensored
        s = _MockSearchAgent(Prefs)
        si = SearchItem()
        si.id = "agent_id"
        si.video_code = "JK-002"
        si.title = u"J○女子校生コレクション"
        si.score = 80
        s.results = [si]

        agent = self._make_agent([s])
        hints = self._make_hints("JK-002", "/movies/JK-002.mp4")
        results = MediaContainer()
        agent.search(results, hints, "ja")

        self.assertEqual(results._media[0].name, u"JK女子校生コレクション")

    def test_update_title_uncensored(self):
        meta = Metadata()
        meta.title = u"J〇女子校生コレクション"
        meta.japanese_title = u"Ｊ○女子校生コレクション"

        meta_agent = _MockMetadataAgent(Prefs)
        meta_agent.name = "ma"
        meta_agent.metadata = meta

        agent = self._make_agent([meta_agent])
        movie = Movie()
        movie.id = "JK-001,ma.id1"
        agent.update(movie, None, "ja")

        self.assertEqual(movie.title, u"JK女子校生コレクション")
        self.assertEqual(movie.original_title, u"ＪＫ女子校生コレクション")


class TestJAVAgentUpdate(BaseTestCase):

    default_prefs = {"series_as_collection": ""}

    def _make_agent(self, mock_agents):
        agent = JAVAgent()
        agent.cached_agents = mock_agents
        return agent

    def test_normalizes_language(self):
        meta_agent = _MockMetadataAgent(Prefs)
        meta_agent.name = "testmeta"

        m = Metadata()
        m.title = "T"
        with mock.patch.object(meta_agent, "get_metadata", wraps=meta_agent.get_metadata) as mock_get:
            mock_get.return_value = m
            agent = self._make_agent([meta_agent])
            movie = Movie()
            movie.id = "CODE-1,testmeta.id1"
            agent.update(movie, None, "fr")

        mock_get.assert_called_once()
        self.assertEqual(mock_get.call_args[0][2], "ja")

    def test_metadata_from_single_agent(self):
        meta = Metadata()
        meta.title = "Test Title"
        meta.studio = "TestStudio"

        meta_agent = _MockMetadataAgent(Prefs)
        meta_agent.name = "ma"
        meta_agent.metadata = meta

        agent = self._make_agent([meta_agent])
        movie = Movie()
        movie.id = "ABC-123,ma.mid"
        agent.update(movie, None, "ja")

        self.assertEqual(movie.title, "Test Title")
        self.assertEqual(movie.studio, "TestStudio")

    def test_metadata_merge_first_wins_for_scalars(self):
        m1 = Metadata()
        m1.title = "First Title"
        m1.studio = "Studio1"

        m2 = Metadata()
        m2.title = "Second Title"
        m2.studio = "Studio2"

        a1 = _MockMetadataAgent(Prefs)
        a1.name = "a1"
        a1.weight = 100
        a1.metadata = m1

        a2 = _MockMetadataAgent(Prefs)
        a2.name = "a2"
        a2.weight = 50
        a2.metadata = m2

        agent = self._make_agent([a1, a2])
        movie = Movie()
        movie.id = "X,a1.id1;a2.id2"
        agent.update(movie, None, "ja")

        # First non-None wins for scalars (should_contribute_to returns
        # False for simple scalars by default).
        self.assertEqual(movie.title, "First Title")
        self.assertEqual(movie.studio, "Studio1")

    def test_metadata_merge_posters_combined(self):
        r1 = Resource("http://a.com/1.jpg")
        r1.score = 90
        m1 = Metadata()
        m1.title = "T"
        m1.posters = [r1]

        r2 = Resource("http://b.com/2.jpg")
        r2.score = 80
        m2 = Metadata()
        m2.posters = [r2]

        a1 = _MockMetadataAgent(Prefs)
        a1.name = "a1"
        a1.weight = 100
        a1.metadata = m1

        a2 = _MockMetadataAgent(Prefs)
        a2.name = "a2"
        a2.weight = 50
        a2.metadata = m2

        agent = self._make_agent([a1, a2])
        movie = Movie()
        movie.id = "X,a1.id1;a2.id2"

        # apply_metadata downloads images; mock requests in the Code module
        mock_resp = mock.MagicMock()
        mock_resp.content = b"fake_image_data"
        with mock.patch.object(_main, "requests") as mock_requests:
            mock_requests.get.return_value = mock_resp
            agent.update(movie, None, "ja")

        # apply_metadata only uses the first valid image per container,
        # but the merge preserved both poster resources.
        self.assertEqual(len(movie.posters), 1)

    def test_partial_agent_called(self):
        captured = {}

        def cb(video_code, metadata, lang):
            captured["video_code"] = video_code
            captured["called"] = True

        partial = _MockPartialAgent(Prefs)
        partial.callback = cb

        agent = self._make_agent([partial])
        movie = Movie()
        movie.id = "CODE-1,"
        agent.update(movie, None, "ja")

        self.assertTrue(captured.get("called"))
        self.assertEqual(captured["video_code"], "CODE-1")

    def test_partial_agent_exception_skipped(self):
        class _FailPartial(_MockPartialAgent):
            name = "fail_partial"

            def partial_update(self, video_code, metadata, lang):
                raise RuntimeError("boom")

        agent = self._make_agent([_FailPartial(Prefs)])
        movie = Movie()
        movie.id = "CODE-1,"

        # Should not raise
        agent.update(movie, None, "ja")

    def test_metadata_agent_exception_skipped(self):
        class _FailMeta(_MockMetadataAgent):
            name = "fail_meta"

            def get_metadata(self, agent_id, video_code, lang):
                raise RuntimeError("boom")

        agent = self._make_agent([_FailMeta(Prefs)])
        movie = Movie()
        movie.id = "CODE-1,fail_meta.id1"

        # Should not raise
        agent.update(movie, None, "ja")

    def test_agent_without_id_skipped(self):
        meta_agent = _MockMetadataAgent(Prefs)
        meta_agent.name = "ma"
        meta_agent.metadata = Metadata()
        meta_agent.metadata.title = "Should Not Appear"

        agent = self._make_agent([meta_agent])
        # No agent id for "ma" in the metadata_id
        movie = Movie()
        movie.id = "CODE-1,other.id1"
        agent.update(movie, None, "ja")

        self.assertNotEqual(movie.title, "Should Not Appear")

    def test_force_calls_clear_metadata(self):
        meta = Metadata()
        meta.title = "New T"
        meta_agent = _MockMetadataAgent(Prefs)
        meta_agent.name = "ma"
        meta_agent.metadata = meta

        agent = self._make_agent([meta_agent])
        movie = Movie()
        movie.id = "X,ma.id1"
        movie.genres.add("OldGenre")
        movie.studio = "OldStudio"

        agent.update(movie, None, "ja", force=True)

        # clear_metadata should have cleared genres
        self.assertNotIn("OldGenre", movie.genres)

    def test_none_values_not_applied(self):
        meta = Metadata()
        # Only title set, everything else is None
        meta.title = "Title Only"

        meta_agent = _MockMetadataAgent(Prefs)
        meta_agent.name = "ma"
        meta_agent.metadata = meta

        agent = self._make_agent([meta_agent])
        movie = Movie()
        movie.id = "X,ma.id1"
        agent.update(movie, None, "ja")

        self.assertEqual(movie.title, "Title Only")
        self.assertIsNone(movie.rating)


class TestJAVAgentAgentsProperty(BaseTestCase):

    def test_disabled_agents_excluded(self):
        class _DisabledAgent(SearchAgent):
            name = "disabled"
            weight = 100

            @property
            def enabled(self):
                return False

        agent = JAVAgent()
        agent.cached_agents = [_DisabledAgent(Prefs)]
        self.assertEqual(len(agent.agents), 0)

    def test_agents_sorted_by_weight(self):
        class _LowWeight(SearchAgent):
            name = "low"
            weight = 10

        class _HighWeight(SearchAgent):
            name = "high"
            weight = 100

        agent = JAVAgent()
        agent.cached_agents = [_LowWeight(Prefs), _HighWeight(Prefs)]
        result = agent.agents
        self.assertEqual(result[0].name, "high")
        self.assertEqual(result[1].name, "low")


if __name__ == "__main__":
    unittest.main()
