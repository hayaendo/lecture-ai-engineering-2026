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

def test_chat_loop_keeps_one_chat_session(monkeypatch, capsys):
    sent = []
    created =[]

    class FakeChat:
        def send_message(self, message):
            sent.append(message)
            return SimpleNamespace(
                text=f"reply to {message}",
                usage_metadata=SimpleNamespace(
                    prompt_token_count=10*len(sent), candidates_token_count=3
                ),
            )

    class FakeChats:
        def create(self, *, model):
            created.append(model)
            return FakeChat()

    class FakeClient:
        chats = FakeChats()

        def __init__(self, *, api_key):
            pass

    inputs = iter(["二つ目の質問", "exit"])
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

    ask_module.chat_loop("最初の質問")

    assert len(created) == 1
    assert sent == ["最初の質問", "二つ目の質問"]

    out = capsys.readouterr().out
    assert "reply to 最初の質問" in out
    assert "reply to 二つ目の質問" in out
    assert "input_tokens=20" in out