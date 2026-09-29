"""TEMPLATE contract test: the SAME assertions run against every implementation.

Why: type checkers cannot see behavioural differences. If the in-memory fake ignores
tenant scoping, every test that uses it passes while production leaks data.
"""
import pytest

# from app.modules.retrieval import Candidate
# from app.modules.retrieval.adapters import QdrantStore   # needs a container in CI
# from tests.fakes import InMemoryVectorStore


@pytest.fixture(params=["in_memory"])  # add "qdrant" when the container fixture exists
def store(request):
    # return {"in_memory": InMemoryVectorStore, "qdrant": make_qdrant_store}[request.param]()
    ...


@pytest.mark.contract
def test_search__never_returns_other_tenants_content(store, tenant_a, tenant_b):
    # store.upsert(tenant_b, [chunk("secret pricing for B")])
    # results = store.search(tenant_a, query="secret pricing for B", limit=5)
    # assert results == []
    pytest.fail("TODO: fill in")


@pytest.mark.contract
def test_search__respects_limit_and_sorts_by_descending_score(store, tenant_a):
    # ingest 10 chunks, search limit=3
    # assert len(results) <= 3 and scores == sorted(scores, reverse=True)
    pytest.fail("TODO: fill in")
