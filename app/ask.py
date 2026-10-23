"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import time

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
EXIT_WORDS = ("", "exit", "quit")

def print_usage(response) -> None:
    usage = response.usage_metadata
    if usage is not None:
        line = (
            f"[usage] input_tokens={usage.prompt_token_count} "
            f"output_tokens={usage.candidates_token_count}"
        )

        thoughts = getattr(usage, "thoughts_token_count", None)
        if thoughts is not None:
            line += f" thoughts_tokens={thoughts}"
        total = getattr(usage, "total_token_count", None)
        if total is not None:
            line += f" total_tokens={total}"
        print(line)

def print_elapsed(seconds: float) -> None:
    print(f"[time] {seconds:.2f}s")


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)
    print_usage(response)
    return response.text

def chat_loop(first_question: str | None = None) -> None:
    client = genai.Client(api_key = get_api_key())
    chat = client.chats.create(model=MODEL)

    print("会話モード（終了：exit/空行：Ctrl-D）\n")
    pending = first_question
    while True:
        if pending is not None:
            question, pending = pending, None
            print(f"> {question}")
        else:
            try:
                question = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
        if question.lower() in EXIT_WORDS:
            break

        try:
            start = time.perf_counter()
            response = chat.send_message(question)
            elapsed = time.perf_counter() - start
        except errors.APIError as e:
            print(api_error_message(e.code, e.message))
            continue

        print_elapsed(elapsed)
        print_usage(response)
        print(f"{response.text}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=None)
    parser.add_argument(
        "-c", "--chat", action="store_true", help="会話履歴を保ったまま続けて質問する"
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")

    if args.chat:
        chat_loop(args.question)
        return

    question = args.question or DEFAULT_QUESTION
    print(f"[質問] {question}\n")
    try:
        start = time.perf_counter()
        answer = ask(question)
        print_elapsed(time.perf_counter() - start)
        print(answer)
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
