"""TEMPLATE tests/conftest.py - shared fixtures. Adapt imports to the real modules.

Rules: fixtures build FAKES at abstraction boundaries. Nothing here calls the network.
"""
import pytest

# from app.core.tenancy import TenantContext
# from tests.fakes import InMemoryVectorStore, FakeClock, FakeLLM


@pytest.fixture
def tenant_a():
    # return TenantContext(tenant_id="tenant-a")
    ...


@pytest.fixture
def tenant_b():
    # A SECOND tenant in every fixture set makes isolation bugs visible.
    # return TenantContext(tenant_id="tenant-b")
    ...


@pytest.fixture
def clock():
    # Freeze time; never let a test depend on the real clock.
    # return FakeClock("2026-01-01T00:00:00Z")
    ...


@pytest.fixture
def store():
    # return InMemoryVectorStore()   # must pass the SAME contract suite as the real store
    ...
