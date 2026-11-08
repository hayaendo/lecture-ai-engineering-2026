# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
  - 素のLLM：
    - AIE2026が何を指しているのかが分からないため、AI活用の熟練度レベルやプログラミングやAI実装の難易度、生成AI（プロンプトエンジニアリング）の活用レベルなど、質問文から推測される一般的な回答を出力している。レベル別の説明もレベル1、レベル2、レベル3や初級、中級、上級と表示されており、AIE2026でのレベルとは異なる。
  - エージェント：
    - 素のLLMとは異なり、AIE2026の講座に基づいた回答を出力している。レベルも基礎、実装、発展と出力されている。また、3つのうち1つに取り組めば、その回の宿題が完了となり、提出では採点されないことも補足説明されている。
- `--trace` で見えたツール呼び出し（ツール名と引数）：
  - search_glossary({'query': 'LoRA'})
  - search_glossary({'query': 'QLoRA'})
- 1つの質問での LLM 呼び出し回数（`requests`）：２回
- 追加したツールと、docstring に書いた説明：
  - make_quiz()
    - 指定した回の用語から1つを選び、確認問題と答えを返す。「第2回の確認問題を出して」のように、講義内容の復習問題を求められた時に使う。

## 宿題

- 取り組んだレベル：基礎・実装・発展
- やったこと：
  - 基礎：同じ質問「LoRAとQLoRAの違いは？」を `--trace` 付きで、変更前・実験1・実験2 の3通り実行した。
    - 実験1：agent.pyのINSTRUCTIONSから「- 用語や講座に固有のことを答える前に、必ず search_glossary で用語集を確認する。」を削除
    - 実験2：tools.pyのsearch_glossaryのducsringを「query には調べたい用語を1つだけ入れる（例: "LoRA"）」から「query には調べたい用語をすべてまとめて入れる（例: "LoRA QLoRA"）」に変更
  - 実装：学習の記録を保存するツールsave_learning_logを作成し、保存する前に利用者の承認を挟んだ
    - tools.py：save_learning_log(content: str)を追加。learning_log/learning_log.mdに日時の見出しを付けて追記する（open("a")）。空の内容なら保存せずにメッセージを返す
    - agent.py：
      - agent.tool_plain(tools.save_learning_log, requires_approval=True)で登録
      - 承認待ちで止まったときの結果を受け取れるよう、output_type=[str, DeferredToolRequests]に
      - run_with_approvalを追加し、result.outputがDeferredToolRequestsの間、承認待ちの呼び出しごとにツール名と引数を表示して [y/N]を聞き、requests.build_results(approvals=...) とmessage_history=result.all_messages()を渡してrun_syncで再開する。usage=result.usageで承認前後の利用量を合算した
  - 発展（a）：
    - app/agent.pyのINSTRUCTIONSとapp/tools.pyのsearch_glossary・get_lecture_summary・make_quizをそのまま使い、エージェントを組み立てる部分だけを ADK で書いた（adk_agent/glossary_agent/agent.pyと __init__.py）。演習と同じ質問「LoRAとQLoRAの違いは？」を実行し、書き方と回答の違いを比べた

- 結果：
  - 基礎：

  | | 変更前 | 実験1 | 実験2 |
  | --- | --- | --- | --- |
  | `[tool call]` | `search_glossary({'query': 'LoRA'})`<br>`search_glossary({'query': 'QLoRA'})` | 変更前と同じ | `search_glossary({'query': 'LoRA QLoRA'})` |
  | `tool_calls` | 2 | 2 | 1 |
  | `requests` | 2 | 2 | 2 |
  | `input_tokens` | 1352 | 1304 | 1049 |
  | `output_tokens` | 181 | 185 | 219 |
  | 回答の書き出し | 「講座の用語集によると、」 | 「LoRAとQLoRAの違いは以下の通りです。」 | 「**LoRA**と**QLoRA**の違いは、...量子化してメモリを削減するかにあります。」と要約から |
  | 回答の最後 | 関係する回：第2回 | 関係する回：第2回 | 第2回（関係する回：第2回） |

  - agent.pyのINSTRUCTIONSから行を消しても、検索の仕方は変化しなかった
  - agent.pyのINSTRUCTIONSから行を消すと、回答の書き出しが変化した
    - 指示に、「用語や講座に固有のことを答える前に、必ず search_glossary で用語集を確認する」とあるため、その指示が答え方に影響していると考えられる
    - 実施したのが1回のみなので偶然の可能性もある
  - tools.pyのsearch_glossaryのdocstringをまとめてに変化させると検索が1回となった
  - 実験2ではinput_tokensが約300減った
    - 変更前は 'LoRA' の検索でもQLoRAが一緒に返り、LoRAとQLoRAの定義が2回ずつモデルに渡っていたため、input_tokensが多かったと考えられる
  - 実験2の回答には「Low-Rank Adaptation」「Quantized LoRA」という正式名が付いた。ツールの返り値（`term`・`lecture`・`definition`・`related`）には無い言葉なので、モデルが自分の知識で足したものであると考えられる

- 実装：「LoRAとQLoRAの違いを調べて、学習記録に保存して」を実行。1回目では返事をする前に終了してしまったため、修正して2回目を行った

  | | 1回目 | 2回目 |
  | --- | --- | --- |
  | docstring の最後の一文 | 「保存前に利用者の承認が必要。」 | 「保存してよいかの確認はプログラムが利用者に行うので、会話で確認を求めず、そのままこのツールを呼ぶこと。」 |
  | `[tool call]` | `search_glossary('LoRA')`、`search_glossary('QLoRA')` | 左の2つ＋`save_learning_log({'content': 'LoRAとQLoRAの違いについて学習しました。…（第2回）'})` |
  | 承認の確認（`[approval]` と `[y/N]`） | 出ない | 出た → `y` |
  | 保存 | されない | `learning_log/learning_log.md` に保存 |
  | `requests` / `tool_calls` | 2 / 2 | 3 / 3 |
  | `input_tokens` / `output_tokens` | 1524 / 266 | 2783 / 310 |

  - 1回目：save_learning_logは呼ばれず、モデルが回答の中で「保存するには、事前に…あなたの承認が必要です」「保存してもよろしければ、その旨をお知らせください」と会話で確認を求めた。この CLI は1回の質問で終わるので、返事をする方法がなく、保存されないまま終わった
  - 2回目：save_learning_logが呼ばれ、実行の前に止まって [y/N]を聞かれた。yで保存され、回答は「上記の学習内容を学習記録に保存しました」で終わった。保存した本文は、モデルが用語集の検索結果を要約して作った
  - 保存されたファイル（learning_log/learning_log.md）：

    ```
    ## 2026-11-07T06:08:50+00:00

    LoRAとQLoRAの違いについて学習しました。
    - LoRA: 事前学習済みの重みを固定し、更新分を低ランク行列で近似してそこだけを学習するPEFT手法。
    - QLoRA: ベースモデルの重みを4ビット等に量子化してさらにメモリを節約した状態で、LoRAによる学習を行う手法。
    （第2回）
    ```

  - 2回目の `requests=3` の内訳：1.検索を2つ呼ぶ 2.検索結果を見て save_learning_logを呼ぶ（ここで承認待ち）3.保存結果を見て回答を書く
  - 拒否（`n`）の場合は、保存されない

- 発展（a）：
  書き方の違い

  | | 演習 | ADK |
  | --- | --- | --- |
  | 指示の渡し方 | `Agent(instructions=INSTRUCTIONS)` | `Agent(instruction=INSTRUCTIONS)`（引数名が単数形） |
  | ツールの渡し方 | `agent.tool_plain(tools.search_glossary)` のように1つずつ登録 | `tools=[tools.search_glossary, ...]` とリストでまとめて渡す |
  | ツールの説明文 | 関数の docstring と型ヒントから作られる | 同じく docstring と型ヒントから作られる |
  | モデル | 実行するときに `run_sync(..., model=build_model())` で渡す | 組み立てるときに `model="gemini-3.5-flash-lite"` と文字列で書く |
  | 名前 | 不要 | `name="glossary_agent"` が必要 |
  | API キー | `GoogleProvider(api_key=get_api_key())` で自分で渡す | 環境変数 `GEMINI_API_KEY` を自動で読む |
  | 動かし方 | 自分で書いた CLI（`python -m app.agent`） | `adk run` が `root_agent` という名前の変数を探して動かす |
  | 会話 | 1回の質問で終わる | 対話を続けられる（会話の記録が `.adk/session.db` に保存される） |

  同じ質問への回答の違い

  それぞれ2回ずつの回答を比べた（演習の手順3と、基礎の変更前の2回。どちらも INSTRUCTIONS と docstring は変えていない）

  | | 演習 1回目 | 演習 2回目 | ADK 1回目 | ADK 2回目 |
  | --- | --- | --- | --- | --- |
  | 書き出し | 「講座の用語集によると、LoRAとQLoRAの違いは以下のとおりです。」 | 1回目と同じ文 | 「LoRAとQLoRAの違いは、ベースモデルの重みをそのまま扱うか、量子化してメモリを節約するかにあります。」と要約から | 1回目と同じ文 |
  | 説明の形 | LoRA・QLoRA を箇条書きで、定義に沿って説明 | 同じ | 同じ | 同じ。ただし短く、LoRA の説明から「PEFT」の語が抜けた |
  | 用語集の定義に無い言葉 | 「Parameter-Efficient Fine-Tuning」 | なし | 「Parameter-Efficient Fine-Tuning」「Quantization」 | 「Quantization」 |
  | 回答の最後 | 関係する回：第2回 | 関係する回：第2回 | 関係する回：第2回 | 関係する回：第2回 |

  - 回答の中身はどちらも用語集の定義に沿っていて、最後に関係する回を示すところも4回とも同じだった
  - 書き出しは、演習では、2回とも「講座の用語集によると、…以下のとおりです。」、ADK 版が2回とも同じ要約の一文で、道具ごとにそろっていた
  - 用語集に無い英語の正式名は、演習でも1回目に出ていて、ADK だけの特徴ではなかった（「Quantization」は ADK 版の2回だけに出た）
  - 2回ずつの実行なので、書き出しの違いが道具の違いによるものかは言い切れない。

- 気づき・疑問：
  - 基礎：
    - 実験1では必ず検索の文を消したのにも関わらず、検索していた
      - tools.pyのdocstringにも「答える前に使うこと」とあるため、これらの文が同じ役割をしていたため、あまり影響がなかったのではないかと考えられる
    - まとめての検索では、1回の検索で済み、トークン量も減少したため、こちらの方がよいのではないか
      - tools.pyの定義を確認すると「MAX_RESULTS = 3」といった定義があり、search_glossaryには1回の検索で最大3件しか返せないことが分かった
      - 用語が見つからなかった場合、if not hitsが何も検索にヒットしなかった場合は働くが、用語がヒットしたものとしていないもの混合であった場合、if notの部分が働かなくなってしまう。
      - 一方で一つずつ検索した場合は、問題なく働くためそもそもserch_glossaryがまとめて検索するように作られていないことが考えられた。
    - ツールの返り値にない正式名称が回答に混ざっていたことから、モデルが用語集にないことも混ぜて回答していることが分かった。
      - このことから、もしまとめての検索をserch_glossaryを変更させず、そのままに利用した場合、検索したい用語がヒットしたものとしていないもの混合であった場合、モデルは用語集にない用語であることを判別できないため、憶測で用語集にないものも回答してしまう恐れが考えられる。

  - 実装：
    - docstring に「承認が必要」と書いたら、モデルが自分で承認をもらおうとして、ツールを呼ばなくなってしまった
    - 承認は、プログラム（requires_approval=True）の側で持っていれば足りることで、モデルに伝えると逆効果になることがある
    - 基礎では INSTRUCTIONS の1行を消しても変わらなかったのに、実装ではdocstringの一文で大きく変わった
    - 条件（承認が必要）だけ伝えると、モデルが自分なりに解釈して動き方を変えてしまう。伝えるなら、どう動けばよいか（そのまま呼ぶ）まで書くとよい
    - 疑問：
      - INSTRUCTIONSとdocstringの両方に同じような指示があるとき、モデルはどちらを強く見ているのか

  - 発展（a）：
    - ツールを関数として定義しておけば、フレームワークを変えても使いまわすことができる
    - ADKでは会話の続きや保存、APIキーの読み込みを用意してくれる。演習で利用しているPydantic AIは自分で各部分が多いが、その分中身が見える
    - 疑問：
      - 回答の書き出しの違い
        - ADKがモデルに送る際にYou are agent.You internal name is ... といった文を足していることが分かった。ADK自体が複数のエージェントを組み合わせることを想定しているため、エージェント名を渡すための一文が追加される。この一文が影響している可能性がある。
      - 他にもフレームワークが足しているものはあるのか。
