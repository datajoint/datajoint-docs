"""
Pytest configuration for notebook tests.

Configures DataJoint from environment variables before any tests run.
This separates configuration from workflow execution.

Usage:
    # MySQL (default)
    DJ_HOST=localhost DJ_USER=root DJ_PASS=tutorial pytest --nbmake ...

    # PostgreSQL
    DJ_HOST=localhost DJ_PORT=5432 DJ_USER=datajoint DJ_PASS=tutorial DJ_BACKEND=postgresql pytest --nbmake ...
"""

import os


def pytest_configure(config):
    """Configure DataJoint from environment variables before tests run."""
    import datajoint as dj

    # Database connection settings
    if os.getenv('DJ_HOST'):
        dj.config['database.host'] = os.getenv('DJ_HOST')
    if os.getenv('DJ_PORT'):
        dj.config['database.port'] = int(os.getenv('DJ_PORT'))
    if os.getenv('DJ_USER'):
        dj.config['database.user'] = os.getenv('DJ_USER')
    if os.getenv('DJ_PASS'):
        dj.config['database.password'] = os.getenv('DJ_PASS')
    if os.getenv('DJ_BACKEND'):
        dj.config['database.backend'] = os.getenv('DJ_BACKEND')

    # Display settings for notebooks
    dj.config['display.limit'] = 8
