# coding=utf-8
"""Base test class for agent testing"""

import os
import sys
import unittest
import locale

# Set up encoding for Python 2.7
reload(sys)
sys.setdefaultencoding('utf-8')

# Try to set locale but don't fail if it doesn't work
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except BaseException:
    pass

# Setup environment variables
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Setup paths to include bundled libraries and code
BUNDLE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE_PATH = os.path.join(BUNDLE_ROOT, 'Contents', 'Code')
LIBS_PATH = os.path.join(BUNDLE_ROOT, 'Contents', 'Libraries', 'Shared')

# Insert paths at the beginning so they take precedence
if LIBS_PATH not in sys.path:
    sys.path.insert(0, LIBS_PATH)
if CODE_PATH not in sys.path:
    sys.path.insert(0, CODE_PATH)

# Import requests from bundled libraries
import requests  # noqa: E402
import datetime  # noqa: E402

# Import mock Plex classes
from mock_plex import (Log, HTTP, Prefs, JSON, Locale, Agent, Media,  # noqa: E402
                       MetadataSearchResult, VideoClipObject)

# Inject into builtins so they're available globally
import __builtin__  # noqa: E402

# Inject into builtins so they're available globally
__builtin__.Log = Log
__builtin__.HTTP = HTTP
__builtin__.Prefs = Prefs()
__builtin__.JSON = JSON
__builtin__.Locale = Locale
__builtin__.Agent = Agent
__builtin__.Media = Media
__builtin__.MetadataSearchResult = MetadataSearchResult
__builtin__.VideoClipObject = VideoClipObject


class BaseAgentTest(unittest.TestCase):
    """Base class for agent tests"""

    agent_class = None

    def setUp(self):
        """Set up test fixtures"""
        if self.agent_class is None:
            self.skipTest("agent_class not set")
        self.agent = self.agent_class()

    def tearDown(self):
        """Tear down test fixtures"""
        self.agent = None

    def load_mock_html(self, filename):
        """Load mock HTML file from tests/mocks directory"""
        mock_path = os.path.join(os.path.dirname(__file__), 'mocks', filename)
        if not os.path.exists(mock_path):
            raise IOError("Mock HTML file not found: {0}".format(mock_path))
        with open(mock_path, 'r') as f:
            return f.read()

    def validate_url(
            self,
            url,
            expected_status=200,
            validate_content_type=None):
        try:
            resp = requests.head(url, timeout=10)
            if resp.status_code != expected_status:
                return False
            # Optionally check Content-Type header
            if validate_content_type:
                content_type = resp.headers.get('Content-Type', '')
                return content_type.startswith(validate_content_type)
            return True
        except Exception:
            return False


class QueryAgentTest(BaseAgentTest):
    """Base test class for QueryAgent tests"""

    test_cases = []
    # test_cases format: [(keyword, expected_properties), ...]
    # expected_properties: {'name': str, 'year': int, 'score_min': int}

    def test_query(self):
        """Test query method returns results"""
        if not self.test_cases:
            self.skipTest("No test cases defined")

        for keyword, expected in self.test_cases:
            try:
                results = self.agent.query(keyword)

                # Verify results are returned
                self.assertIsNotNone(
                    results, "Query should return results for keyword: {0}".format(keyword))
                self.assertGreater(
                    len(results),
                    0,
                    "Query should return at least one result for keyword: {0}".format(keyword))

                # Verify first result matches expected properties
                first_result = results[0]
                if 'name' in expected:
                    self.assertIn(
                        expected['name'],
                        first_result.name,
                        "Result name should contain expected string for keyword: {0}".format(keyword))
                if 'year' in expected:
                    self.assertEqual(
                        expected['year'],
                        first_result.year,
                        "Result year should match expected for keyword: {0}".format(keyword))
                if 'score_min' in expected:
                    self.assertGreaterEqual(
                        first_result.score,
                        expected['score_min'],
                        "Result score should be at least expected minimum for keyword: {0}".format(keyword))
            except Exception as e:
                self.fail(
                    "Test failed for keyword '{0}': {1}".format(
                        keyword, unicode(e)))


class MetadataAgentTest(BaseAgentTest):
    """Base test class for MetadataAgent tests"""

    test_cases = []

    def test_get_metadata(self):
        """Test get_metadata method returns valid metadata"""
        if not self.test_cases:
            self.skipTest("No test cases defined")

        for agent_id, expected in self.test_cases:
            try:
                # Build metadata_id
                metadata_id = "{0},{1}".format(
                    agent_id, self.agent.build_metadata_id(agent_id))

                # Get metadata
                metadata = self.agent.get_metadata(metadata_id)

                # Verify metadata is returned
                self.assertIsNotNone(
                    metadata, "Metadata should be returned for agent_id: {0}".format(agent_id))
                self.assertIsInstance(
                    metadata,
                    dict,
                    "Metadata should be a dictionary for agent_id: {0}".format(agent_id))

                # Validate each expected field
                for key, value in expected.items():
                    self.validate_field(metadata, key, value, agent_id)

                # Validate poster URLs if present
                if 'posters' in metadata and metadata['posters']:
                    for poster_url in metadata['posters']:
                        self.assertTrue(
                            self.validate_url(
                                poster_url,
                                validate_content_type='image'),
                            "Poster URL should be accessible and return image content: {0}".format(poster_url))

                # Validate art/thumbs URLs if present
                if 'art' in metadata and metadata['art']:
                    for art_url in metadata['art']:
                        self.assertTrue(
                            self.validate_url(
                                art_url,
                                validate_content_type='image'),
                            "Art/thumb URL should be accessible and return image content: {0}".format(art_url))
            except Exception as e:
                self.fail(
                    "Test failed for agent_id '{0}': {1}".format(
                        agent_id, str(e)))

    def validate_field(self, metadata, key, expected, agent_id):
        """Route field validation to appropriate method"""
        self.assertIn(
            key,
            metadata,
            "Metadata should contain '{0}' for agent_id: {1}".format(
                key,
                agent_id))

        # Route to specific validation methods
        if key == 'summary':
            self.validate_summary(metadata, expected, agent_id)
        elif key == 'rating':
            self.validate_rating(metadata, expected, agent_id)
        elif key == 'studio':
            self.validate_studio(metadata, expected, agent_id)
        elif key == 'roles':
            self.validate_roles(metadata, expected, agent_id)
        elif key == 'genres':
            self.validate_genres(metadata, expected, agent_id)
        elif key == 'collections':
            self.validate_collections(metadata, expected, agent_id)
        elif key == 'duration':
            self.validate_duration(metadata, expected, agent_id)
        elif key == 'originally_available_at':
            self.validate_originally_available_at(metadata, expected, agent_id)
        elif key in ('movie_id', 'agent_id'):
            self.validate_exact_match(metadata, key, expected, agent_id)
        elif key in ('title', 'title_sort'):
            self.validate_string_match(metadata, key, expected, agent_id)
        elif isinstance(expected, list):
            self.validate_list_subset(metadata, key, expected, agent_id)
        elif expected is not None and expected is not True:
            # Generic validation for other fields
            actual = metadata[key]
            if isinstance(
                    expected,
                    basestring) and isinstance(
                    actual,
                    basestring):
                found = expected == actual or expected in actual
                self.assertTrue(
                    found,
                    "'{0}' should match or contain expected value for agent_id: {1}".format(
                        key,
                        agent_id))
            else:
                self.assertEqual(
                    actual,
                    expected,
                    "'{0}' should match expected value for agent_id: {1}".format(
                        key,
                        agent_id))

    def validate_summary(self, metadata, expected, agent_id):
        """Validate summary field"""
        if expected is True:
            self.assertTrue(
                metadata['summary'],
                "Summary should not be empty for agent_id: {0}".format(agent_id))
        elif expected:
            actual = metadata['summary']
            if isinstance(
                    expected,
                    basestring) and isinstance(
                    actual,
                    basestring):
                found = expected == actual or expected in actual
                self.assertTrue(
                    found,
                    "Summary should match or contain expected value for agent_id: {0}".format(agent_id))

    def validate_rating(self, metadata, expected, agent_id):
        """Validate rating field (0-10 range)"""
        if expected is True:
            self.assertIsNotNone(
                metadata['rating'],
                "Rating should not be None for agent_id: {0}".format(agent_id))
            self.assertGreaterEqual(
                metadata['rating'],
                0,
                "Rating should be >= 0 for agent_id: {0}".format(agent_id))
            self.assertLessEqual(
                metadata['rating'],
                10,
                "Rating should be <= 10 for agent_id: {0}".format(agent_id))
        elif expected is not None:
            self.assertEqual(
                metadata['rating'],
                expected,
                "Rating should match expected value for agent_id: {0}".format(agent_id))

    def validate_studio(self, metadata, expected, agent_id):
        """Validate studio field"""
        if expected:
            actual = metadata['studio']
            if isinstance(
                    expected,
                    basestring) and isinstance(
                    actual,
                    basestring):
                found = expected == actual or expected in actual
                self.assertTrue(
                    found,
                    "Studio should match or contain expected value for agent_id: {0}".format(agent_id))

    def validate_roles(self, metadata, expected, agent_id):
        """Validate roles field - match expected role names"""
        self.assertIsInstance(
            metadata['roles'],
            list,
            "Roles should be a list for agent_id: {0}".format(agent_id))

        # Extract actual role names
        actual_names = [
            role.get(
                'name',
                '') if isinstance(
                role,
                dict) else str(role) for role in metadata['roles']]

        # Validate all expected names are present
        for expected_name in expected:
            found = False
            for actual_name in actual_names:
                if expected_name == actual_name or expected_name in actual_name:
                    found = True
                    break
            self.assertTrue(
                found,
                "Expected role '{0}' not found in actual roles {1} for agent_id: {2}".format(
                    expected_name,
                    actual_names,
                    agent_id))

    def validate_genres(self, metadata, expected, agent_id):
        """Validate genres field - subset matching with partial match support"""
        self.assertIsInstance(
            metadata['genres'],
            list,
            "Genres should be a list for agent_id: {0}".format(agent_id))

        if expected is True:
            self.assertGreater(len(
                metadata['genres']), 0, "Genres should not be empty for agent_id: {0}".format(agent_id))
        elif isinstance(expected, list):
            actual_genres = metadata['genres']
            for expected_genre in expected:
                found = any(
                    expected_genre == actual or expected_genre in actual for actual in actual_genres)
                self.assertTrue(
                    found,
                    "Expected genre '{0}' not found in actual genres for agent_id: {1}".format(
                        expected_genre,
                        agent_id))

    def validate_collections(self, metadata, expected, agent_id):
        """Validate collections field - subset matching"""
        self.assertIsInstance(
            metadata['collections'],
            list,
            "Collections should be a list for agent_id: {0}".format(agent_id))

        if expected is True:
            self.assertGreater(
                len(
                    metadata['collections']),
                0,
                "Collections should not be empty for agent_id: {0}".format(agent_id))
        elif isinstance(expected, list):
            actual_collections = metadata['collections']
            for expected_collection in expected:
                found = any(
                    expected_collection == actual or expected_collection in actual for actual in actual_collections)
                self.assertTrue(
                    found,
                    "Expected collection '{0}' not found in actual collections for agent_id: {1}".format(
                        expected_collection,
                        agent_id))

    def validate_duration(self, metadata, expected, agent_id):
        """Validate duration field (positive integer)"""
        if expected is True:
            self.assertIsNotNone(
                metadata['duration'],
                "Duration should not be None for agent_id: {0}".format(agent_id))
            self.assertGreater(
                metadata['duration'],
                0,
                "Duration should be > 0 for agent_id: {0}".format(agent_id))
        elif expected is not None:
            self.assertEqual(
                metadata['duration'],
                expected,
                "Duration should match expected value for agent_id: {0}".format(agent_id))

    def validate_originally_available_at(self, metadata, expected, agent_id):
        """Validate originally_available_at field (datetime)"""
        if expected is True:
            self.assertIsNotNone(
                metadata['originally_available_at'],
                "Originally available at should not be None for agent_id: {0}".format(agent_id))
            self.assertIsInstance(
                metadata['originally_available_at'],
                datetime.datetime,
                "Originally available at should be datetime for agent_id: {0}".format(agent_id))
        elif isinstance(expected, datetime.datetime):
            self.assertEqual(
                metadata['originally_available_at'],
                expected,
                "Originally available at should match expected value for agent_id: {0}".format(agent_id))

    def validate_exact_match(self, metadata, key, expected, agent_id):
        """Validate fields that require exact match (movie_id, agent_id)"""
        if expected:
            self.assertEqual(
                metadata[key],
                expected,
                "'{0}' should match expected value for agent_id: {1}".format(
                    key,
                    agent_id))

    def validate_string_match(self, metadata, key, expected, agent_id):
        """Validate string fields with exact or substring matching"""
        if expected:
            actual = metadata[key]
            if isinstance(
                    expected,
                    basestring) and isinstance(
                    actual,
                    basestring):
                found = expected == actual or expected in actual
                self.assertTrue(
                    found,
                    "'{0}' should match or contain expected value for agent_id: {1}".format(
                        key,
                        agent_id))

    def validate_list_subset(self, metadata, key, expected, agent_id):
        """Validate list fields with subset matching"""
        self.assertIsInstance(
            metadata[key],
            list,
            "'{0}' should be a list for agent_id: {1}".format(
                key,
                agent_id))
        for item in expected:
            found = any(
                item == metadata_item or (
                    isinstance(
                        metadata_item,
                        basestring) and item in metadata_item) for metadata_item in metadata[key])
            self.assertTrue(
                found, "'{0}' should contain '{1}' for agent_id: {2}".format(
                    key, item, agent_id))


class AvatarAgentTest(BaseAgentTest):
    """Base test class for AvatarAgent tests"""

    test_cases = []
    # test_cases format: [(name, expected_properties), ...]
    # expected_properties: {'photo': str (URL or empty)}

    def test_get_roledata(self):
        """Test get_roledata method returns valid role data"""
        if not self.test_cases:
            self.skipTest("No test cases defined")

        for name, expected in self.test_cases:
            try:
                # Get role data
                roledata = self.agent.get_roledata(name)

                # Verify role data is returned
                self.assertIsNotNone(
                    roledata, "Role data should be returned for name: {0}".format(name))
                self.assertIsInstance(
                    roledata, dict, "Role data should be a dictionary for name: {0}".format(name))

                # Verify expected properties
                for key, value in expected.items():
                    self.assertIn(
                        key,
                        roledata,
                        "Role data should contain '{0}' for name: {1}".format(
                            key,
                            name))
                    if value and key == 'photo':
                        # Validate photo URL if non-empty
                        self.assertTrue(
                            roledata[key],
                            "Photo URL should not be empty for name: {0}".format(name))
                        if roledata[key]:
                            self.assertTrue(
                                self.validate_url(
                                    roledata[key],
                                    validate_content_type='image'),
                                "Photo URL should be accessible and return image content: {0}".format(
                                    roledata[key]))
            except Exception as e:
                self.fail(
                    "Test failed for name '{0}': {1}".format(
                        name, str(e)))
