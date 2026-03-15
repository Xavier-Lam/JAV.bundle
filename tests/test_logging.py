# coding=utf-8
"""Tests that agents' loggers bridge correctly to Plex's builtin Log API."""

import mock

from base import BaseTestCase
from Code import Start
from agents.base import BaseAgent


class TestAgentLogger(BaseTestCase):

    agent = None  # type: BaseAgent

    def setUp(self):
        super(TestAgentLogger, self).setUp()
        Start()
        self.agent = BaseAgent(Prefs)
        self.agent.name = "sample"

    def test_agent_logger_is_child_of_agents(self):
        self.assertEqual(self.agent.logger.name, "agents.sample")

    def test_agent_debug_calls_log_debug(self):
        with mock.patch.object(Log, "Debug") as mock_debug:
            self.agent.logger.debug("agent debug %s", "msg")
        mock_debug.assert_called_once_with("[sample] agent debug msg")

    def test_agent_info_calls_log_info(self):
        with mock.patch.object(Log, "Info") as mock_info:
            self.agent.logger.info("agent info")
        mock_info.assert_called_once_with("[sample] agent info")

    def test_agent_warning_calls_log_warn(self):
        with mock.patch.object(Log, "Warn") as mock_warn:
            self.agent.logger.warning("agent warning")
        mock_warn.assert_called_once_with("[sample] agent warning")

    def test_agent_error_calls_log_error(self):
        with mock.patch.object(Log, "Error") as mock_error:
            self.agent.logger.error("agent error")
        mock_error.assert_called_once_with("[sample] agent error")

    def test_agent_exception_calls_log_exception(self):
        with mock.patch.object(Log, "Exception") as mock_exception:
            try:
                raise RuntimeError("boom")
            except RuntimeError:
                self.agent.logger.exception("error occurred")
        mock_exception.assert_called_once_with("[sample] error occurred")
