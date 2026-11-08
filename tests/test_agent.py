"""エージェントの配線テスト。

TestModel は実際のLLMを呼ばない偽モデルで、登録されたツールを全部呼んでから
ダミーの回答を返す。APIキーも利用枠も使わずに、
「ツールが登録され、呼ばれ、結果がモデルに戻るか」を確かめられる。
"""

from pydantic_ai.messages import DeferredToolRequests, ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app.agent import agent, run_with_approval

BASE_TOOLS = {"search_glossary", "get_lecture_summary"}


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_base_tools_are_registered_and_called():
    model = TestModel()
    with agent.override(model=model):
        result = agent.run_sync("LoRAとは？")

    offered = {t.name for t in model.last_model_request_parameters.function_tools}
    assert BASE_TOOLS <= offered  # 演習でツールを足しても壊れないよう「含む」で判定

    called = {p.tool_name for p in _parts(result, ToolCallPart)}
    assert BASE_TOOLS <= called
    assert isinstance(result.output, DeferredToolRequests)
    assert len(_parts(result, ToolReturnPart)) + len(result.output.approvals) == len(
        _parts(result, ToolCallPart)
    )


def test_glossary_result_reaches_the_model():
    model = TestModel(call_tools=["search_glossary"])
    with agent.override(model=model):
        result = agent.run_sync("RAGとは？")
    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == "search_glossary"


def test_learning_log_is_not_saved_until_approved(tmp_path, monkeypatch, capsys):
    from app import tools

    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", tmp_path)
    models = iter(
        [TestModel(call_tools=["save_learning_log"]), TestModel(call_tools=[])]
    )
    monkeypatch.setattr("app.agent.build_model", lambda: next(models))

    def approve_after_checking(prompt):
        assert prompt.startswith("実行を許可しますか？")
        assert not (tmp_path / "learning_log.md").exists()
        return "y"

    monkeypatch.setattr("builtins.input", approve_after_checking)
    completed = run_with_approval(agent, "学習記録を保存して")

    assert isinstance(completed.output, str)
    assert "保存しました" in completed.output
    assert "save_learning_log" in capsys.readouterr().out
    assert (tmp_path / "learning_log.md").exists()
