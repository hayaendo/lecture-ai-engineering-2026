from app import retrieval

def _hit(page_id):
    page = next(p for p in retrieval.load_pages() if p["page_id"] == page_id)
    return {**page, "distance": 0.1}

def test_neighbors_are_previous_and_next_pages():
    [result] = retrieval.add_neighbors([_hit("lec03-main-p039")])
    assert [(n["position"], n["page_id"]) for n in result["neighbors"]] == [
        ("前", "lec03-main-p038"), ("後", "lec03-main-p040")]
    assert result["neighbors"][1]["content"]  # 本文も付く


def test_neighbors_are_not_duplicated():
    results = retrieval.add_neighbors([_hit("lec03-main-p039"), _hit("lec03-main-p040")])
    # p040 は検索結果そのものなので p039 には付けない。p041 は p040 にだけ付く
    assert [n["page_id"] for n in results[0]["neighbors"]] == ["lec03-main-p038"]
    assert [n["page_id"] for n in results[1]["neighbors"]] == ["lec03-main-p041"]


def test_neighbors_stay_in_the_same_document():
    [result] = retrieval.add_neighbors([_hit("lec02-main-p001")])
    assert [n["page_id"] for n in result["neighbors"]] == ["lec02-main-p002"]


def test_neighbors_are_off_by_default(monkeypatch):
    hits = [_hit("lec03-main-p039")]
    monkeypatch.setattr(retrieval, "search", lambda *a, **k: hits)
    monkeypatch.setattr(retrieval, "RAG_NEIGHBORS", 0)
    assert retrieval.search_with_neighbors("メモリ") == hits
    monkeypatch.setattr(retrieval, "RAG_NEIGHBORS", 1)
    assert len(retrieval.search_with_neighbors("メモリ")[0]["neighbors"]) == 2
