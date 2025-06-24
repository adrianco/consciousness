"""Test setup and basic functionality."""


def test_python_version():
    """Test Python version compatibility."""
    import sys

    assert sys.version_info >= (3, 11)


def test_dependencies():
    """Test that all critical dependencies are importable."""
    import fastapi
    import pydantic
    import pytest
    import sqlalchemy

    assert True
