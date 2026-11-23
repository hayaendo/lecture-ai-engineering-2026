import json

import pytest

from app import retrieval
from scripts.build_rag_index import build_index

SEEDS = ["lec03-main-p039", "lec03-main-p040", "lec03-main-p038"]


def _fake_search(*args, **kwargs):
    pages = {p["page_id"]: p for p in retrieval.load_pages()}
    return [{**pages[page_id], "distance": 0.1} for page_id in SEEDS]


def test_graph_default_order_ignores_the_question(monkeypatch):
    monkeypatch.setattr(retrieval, "search", _fake_search)
    monkeypatch.setattr(retrieval, "GRAPH_RERANK", False)
    found = retrieval.search_graph("コンパクションとメモリの違い")
    assert found["rerank"] is False
    # 元の順では、共通用語「メモリ」経由の候補はページIDの順に選ばれ、第3回 p.13 は入らない
    assert "lec03-main-p013" not in [c["page_id"] for c in found["expanded"]]


def test_graph_rerank_picks_candidates_close_to_the_question(monkeypatch):
    monkeypatch.setattr(retrieval, "search", _fake_search)
    monkeypatch.setattr(retrieval, "GRAPH_RERANK", True)
    monkeypatch.setattr(retrieval, "embed_text", lambda *a: [1.0, 0.0])

    def distances(vector, page_ids):
        assert vector == [1.0, 0.0]  # 入口の検索と同じ質問ベクトルを使う
        return {page_id: (0.05 if page_id == "lec03-main-p013" else 0.5) for page_id in page_ids}

    monkeypatch.setattr(retrieval, "page_distances", distances)
    found = retrieval.search_graph("コンパクションとメモリの違い")
    assert found["rerank"] is True
    assert found["expanded"][0]["page_id"] == "lec03-main-p013"
    assert found["expanded"][0]["distance"] == pytest.approx(0.05)
    assert len(found["seeds"]) + len(found["expanded"]) <= retrieval.GRAPH_MAX_RESULTS


def test_page_distances_reads_the_index(tmp_path, monkeypatch):
    source = tmp_path / "lectures.json"
    source.write_text(json.dumps([
        {"id": "lec01-main", "title": "講義1", "content": [{"section": "章", "content": [
            {"id": "lec01-main-p001", "title": "近い", "page": 1, "content": "本文1"},
            {"id": "lec01-main-p002", "title": "遠い", "page": 2, "content": "本文2"}]}]}
    ], ensure_ascii=False), encoding="utf-8")
    database = tmp_path / "index.sqlite3"
    build_index(source, database, embedder=lambda text, _: [1, 0] if "本文1" in text else [0, 1])
    monkeypatch.setattr(retrieval, "RAG_DB", database)
    got = retrieval.page_distances([1, 0], ["lec01-main-p001", "lec01-main-p002"])
    assert got["lec01-main-p001"] == pytest.approx(0)
    assert got["lec01-main-p002"] == pytest.approx(1)