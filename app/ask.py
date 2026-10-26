"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 対話モード（exit または quit で終了）

対話モードでは、終了するまで会話履歴を保つ。
ツールは持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai.chats import Chat
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の代表質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def create_chat(client: genai.Client) -> Chat:
    return client.chats.create(model=MODEL)


def ask(question: str) -> str:
    with genai.Client(api_key=get_api_key()) as client:
        return ask_with_chat(question, create_chat(client))


def ask_with_chat(question: str, chat: Chat) -> str:
    response = chat.send_message(question)

    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage else None
    output_tokens = usage.candidates_token_count if usage else None
    print(
        f"[トークン] 入力: {input_tokens if input_tokens is not None else '不明'} "
        f"/ 出力: {output_tokens if output_tokens is not None else '不明'}"
    )

    return response.text


def run_interactive() -> None:
    with genai.Client(api_key=get_api_key()) as client:
        chat = create_chat(client)
        print("質問を入力してください（終了するには exit または quit）")
        while True:
            try:
                question = input("あなた> ").strip()
            except EOFError:
                print()
                break
            if question.lower() in {"exit", "quit"}:
                break
            if not question:
                continue

            print(f"[質問] {question}\n")
            print(ask_with_chat(question, chat))


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", help="1回だけ質問する（省略すると対話モード）")
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        if args.question is None:
            run_interactive()
        else:
            print(f"[質問] {args.question}\n")
            print(ask(args.question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
