from types import SimpleNamespace

import app.ask as ask_module


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        text="answer",
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=4),
    )

    class FakeModels:
        def generate_content(self, *, model, contents):
            return response

    class FakeClient:
        models = FakeModels()

        def __init__(self, *, api_key):
            pass

    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)

    assert ask_module.ask("question") == "answer"
    assert capsys.readouterr().out == "[usage] input_tokens=12 output_tokens=4\n"