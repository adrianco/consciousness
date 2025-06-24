"""
Device discovery interview system package.

This package implements a conversational approach to discovering and configuring
smart home devices through natural language interactions, with automatic digital
twin creation and Home Assistant integration pattern matching.
"""

from .device_classifier import DeviceClassifier
from .integration_matcher import IntegrationMatcher
from .interview_controller import InterviewController
from .question_generator import QuestionGenerator

__all__ = [
    "InterviewController",
    "DeviceClassifier",
    "QuestionGenerator",
    "IntegrationMatcher",
]
