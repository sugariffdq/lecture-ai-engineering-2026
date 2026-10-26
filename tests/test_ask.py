from types import SimpleNamespace

from app import ask as ask_module


def test_ask_displays_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        text="回答",
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=7,
        ),
    )
    sent_messages = []
    client_open = []

    def send_message(message):
        assert client_open
        sent_messages.append(message)
        return response

    class FakeClient:
        chats = SimpleNamespace(
            create=lambda **_: SimpleNamespace(send_message=send_message)
        )

        def __init__(self, **_):
            pass

        def __enter__(self):
            client_open.append(True)
            return self

        def __exit__(self, *_):
            client_open.clear()

    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    assert ask_module.ask("質問") == "回答"
    assert sent_messages == ["質問"]
    assert not client_open
    assert "[トークン] 入力: 12 / 出力: 7" in capsys.readouterr().out


def test_main_reuses_chat_for_interactive_questions(monkeypatch, capsys):
    asked_questions = []
    client_status = []

    class FakeChat:
        def send_message(self, message):
            assert client_status == ["open"]
            return SimpleNamespace(text=f"回答: {message}", usage_metadata=None)

    class FakeClient:
        chats = SimpleNamespace(create=lambda **_: FakeChat())

        def __init__(self, **_):
            pass

        def __enter__(self):
            client_status.append("open")
            return self

        def __exit__(self, *_):
            client_status.clear()

    def fake_ask_with_chat(question, session):
        asked_questions.append(question)
        response = session.send_message(question)
        return response.text

    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module, "ask_with_chat", fake_ask_with_chat)
    monkeypatch.setattr("sys.argv", ["app.ask"])
    inputs = iter(["最初の質問", "その続きは？", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    ask_module.main()

    assert asked_questions == ["最初の質問", "その続きは？"]
    assert not client_status
    output = capsys.readouterr().out
    assert "回答: 最初の質問" in output
    assert "回答: その続きは？" in output