"""
課題1：発展
複数のモデル、質問で応答時間とトークン数を計測し、CSVファイル化する
"""

import argparse
import csv
import statistics
import time
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import errors

from app.ask import DEFAULT_QUESTION
from app.config import MODEL, get_api_key

QUESTIONS = {
    "fact": "日本の首都はどこですか？一言で答えてください。",
    "reasoning": (
        "りんごが3個入った箱が4つ、ミカンが5個入った袋が二つあります。"
        "リンゴはみかんより何個多いですか?"
    ),
    "course": DEFAULT_QUESTION,
}

FIELDS = [
    "timestamp", "model", "question", "repeat", "elapsed_s",
    "input_tokens", "output_tokens", "thoughts_tokens", "total_tokens",
    "retries", "waited_s", "error",
]

MAX_RETRIES = 3

def run_once(client, model: str, question: str) -> dict:
    retries = 0
    waited = 0
    while True:
        try:
            start = time.perf_counter()
            response = client.models.generate_content(model=model, contents=question)
            elapsed = time.perf_counter() - start
            break
        except errors.APIError as e:
            if e.code == 429 and retries < MAX_RETRIES:
                wait = 15 * 2**retries
                print(f" 429（レート制限）： {wait}秒待って再試行")
                time.sleep(wait)
                retries += 1
                waited += wait
                continue
            return {"retries": retries, "waited_s": waited, "error": f"{e.code} {e.message}"}

    usage = response.usage_metadata
    return {
        "elapsed_s": round(elapsed, 3),  # 成功した1回の API 呼び出しだけの時間
        "input_tokens": getattr(usage, "prompt_token_count", None),
        "output_tokens": getattr(usage, "candidates_token_count", None),
        "thoughts_tokens": getattr(usage, "thoughts_token_count", None),
        "total_tokens": getattr(usage, "total_token_count", None),
        "retries": retries,
        "waited_s": waited,
        "error": "",
    }

def _median(values):
    nums = [v for v in values if v  is not None]
    return statistics.median(nums) if nums else None

def _fmt(value) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}" if isinstance(value, float) else str(value)

def print_summary(rows: list[dict]) -> None:
    print("\n[中央値] model / question : time(s) input output thoughts total | 成功/試行 429回数")
    for model, qid in dict.fromkeys((r["model"], r["question"]) for r in rows):
        group = [r for r in rows if r["model"] == model and r["question"] == qid]
        ok = [r for r in group if not r["error"]]
        meds = [
            _median([r.get(f) for r in ok])
            for f in ("elapsed_s", "input_tokens", "output_tokens", "thoughts_tokens", "total_tokens")
        ]
        retries = sum(r["retries"] for r in group)
        print(
            f"{model} / {qid} : " + " ".join(_fmt(m) for m in meds)
            + f" | {len(ok)}/{len(group)} {retries}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="モデル・質問ごとの応答時間とトークン数を計測する")
    parser.add_argument("--models", nargs="+", default=[MODEL])
    parser.add_argument("--questions", nargs="+", choices=list(QUESTIONS), default=list(QUESTIONS))
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument(
        "--rpm", type=float, default=5,
        help="待機間隔の計算に使う1分あたりのリクエスト数（AI Studio の値より小さめに）",
    )
    args = parser.parse_args()

    interval = 60 / args.rpm
    total = len(args.models) * len(args.questions) * args.repeats
    print(f"[計画] {total}リクエスト / 間隔 {interval:.1f}秒 / 所要 約{total * interval / 60:.1f}分")

    client = genai.Client(api_key=get_api_key())
    out = Path("logs") / f"bench_{datetime.now():%Y%m%d_%H%M%S}.csv"
    out.parent.mkdir(exist_ok=True)

    rows = []
    n = 0
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        # 繰り返しを一番外側に回し、時間帯による偏りが特定のモデルに集中しないようにする
        for rep in range(1, args.repeats + 1):
            for model in args.models:
                for qid in args.questions:
                    n += 1
                    if n > 1:
                        time.sleep(interval)
                    print(f"[{n}/{total}] {model} / {qid} / {rep}回目")
                    row = {
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                        "model": model,
                        "question": qid,
                        "repeat": rep,
                        **run_once(client, model, QUESTIONS[qid]),
                    }
                    writer.writerow(row)
                    f.flush()  # 途中で止めてもそこまでの結果は残る
                    rows.append(row)

    print(f"\n[保存] {out}")
    print_summary(rows)


if __name__ == "__main__":
    main()