"""Shared pytest configuration and fixtures."""
import os
# Ensure test environment never accidentally hits production secrets
os.environ["JWT_SECRET_KEY"] = "test-only-secret-do-not-use-in-prod"
