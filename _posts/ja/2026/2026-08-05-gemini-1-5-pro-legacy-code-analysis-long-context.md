---
layout: post
title: '長いコンテキストでレガシー解析時間を短縮する（Gemini 1.5 Pro ワークフロー）'
slug: gemini-1-5-pro-legacy-code-analysis-long-context
lang: ja
translation_key: gemini-1-5-pro-legacy-code-analysis-long-context
post_type: deep-dive
date: 2026-08-05 11:36:38 +0900
updated: 2026-08-11 12:00:00 +0900
categories:
- AI
tags:
- Gemini
- LLM
- Legacy Code
description: 複数ファイルに散らばったレガシー依存を長いコンテキストで一度に読む実務手順。丸ごとダンプの失敗例、トークン見積もり、検証ループまでまとめます。
image: /uploads/gemini-1-5-pro-legacy-code-analysis-long-context/thumbnail.webp
ai_generated: true
permalink: /ja/posts/gemini-1-5-pro-legacy-code-analysis-long-context/
---
古いサービスに修正依頼が来ました。担当はすでに退職し、Wiki にはデプロイ順だけが残っています。決済ロジックがコントローラ・サービス・モデル・外部クライアントに分かれ、関数名検索だけでは本物のコールスタックが分かりません。ファイル単位で LLM に貼ると、ファイル B を聞いた頃には A の文脈が消え、過去回答の再貼り付けが解析より重くなります。

長いコンテキスト窓は、**関連モジュールを一度に読ませる**ことでこの問題を和らげます。Gemini 1.5 Pro が百万トークン級を一般化し、以降のモデルも同じ型のワークフローを引き継ぎます。本稿では **何を入れ何を捨てるか**、**答えが誤ったときにどこを検証するか**に焦点を当てます。Tool Use（関数呼び出し）自体は[別記事](/ja/posts/gemini-1-5-pro-tool-use-connecting-llms/)で扱います。

<!--more-->
![長いコンテキストでレガシー解析時間を短縮する（Gemini 1.5 Pro ワークフロー）](/uploads/gemini-1-5-pro-legacy-code-analysis-long-context/thumbnail.webp "長いコンテキストでレガシー解析時間を短縮する（Gemini 1.5 Pro ワークフロー）")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## 問題定義：断片化したコンテキスト

レガシー解析が遅い主因は「1 ファイルが難しい」ことより、**文脈がファイル境界で割れている**ことです。決済 1 件がおおよそ次のように散らばっているとします。

* `controllers/payment_controller.rb` — HTTP 入口、パラメータ検証
* `services/payment_service.rb` — ビジネスルール、複数モデル呼び出し
* `models/order.rb` / `models/user.rb` — 状態・権限
* `lib/external_api_client.rb` — PG 連携

`payment_service.rb` だけ渡して「バグを探せ」と聞くと、注文状態遷移や外部クライアントのタイムアウト方針を知らないため、**半分の情報でそれらしい推測**になります。短いコンテキストでは[会話中に文脈が失われる](/ja/posts/antigravity-cli-context-loss-mistakes/)問題も重なります。長いコンテキストは関連ファイルを **1 プロンプトに固定**して両方を減らす試みです。

## 長いコンテキストが変えるもの／変えないもの

百万トークンは中小モジュールのソースを一度に入れるのに十分な規模です。ただし窓が広いだけでは次は自動では解けません。

| 助けになる側 | 代替できない側 |
| --- | --- |
| 複数ファイルにまたがる呼び出し流れの初稿 | 存在しないメソッド・設定キーの幻覚 |
| 「どのファイルが関係するか」の地図 | `vendor` / `node_modules` まで入れたノイズ |
| リファクタ候補リスト | 本番障害の実再現 |

つまり長いコンテキストは **地図を描く道具**であり、**デプロイ前検証の代わりにはなりません。**

## 実務ワークフロー：範囲 → 梱包 → 質問 → 検証

### 1. モノレポ全体ではなくモジュール境界から

最初の失敗パターンは「リポジトリルートで `find` 一発」です。フィクスチャ・生成コード・依存ディレクトリまで入るとトークンだけ消費し信号が薄くなります。まずドメインを狭めます。

1. 入口ファイルを 1〜2 個確定（例: `PaymentController#create`）
2. import/require と呼び出しで 1-hop、2-hop だけ収集
3. まだ足りないときだけ同ドメインディレクトリを拡張

### 2. 除外リスト付きの梱包スクリプト

```bash
cd path/to/legacy/project

# 目安: ASCII 主体なら 文字数/4 前後がトークン概算
# 1 回目の目標例: 8万〜20万トークン（製品上限と料金を確認）

OUT=combined_payment.txt
rm -f "$OUT"

{
  echo "Project structure (payment-related):"
  find app/controllers app/services app/models lib \
    -type f -name '*payment*' -o -name '*order*' 2>/dev/null | head -200
  echo
  echo "--- End of structure ---"
  echo
} > "$OUT"

find app lib \
  \( -path '*/node_modules/*' -o -path '*/vendor/*' -o -path '*/tmp/*' \
     -o -path '*/.git/*' -o -name '*.min.js' \) -prune -o \
  -type f \( -name '*.rb' -o -name '*.rake' \) -print0 \
| while IFS= read -r -d '' file; do
    case "$file" in
      *payment*|*order*|*checkout*) ;;
      *) continue ;;
    esac
    echo "--- File: $file ---" >> "$OUT"
    cat "$file" >> "$OUT"
    echo >> "$OUT"
  done

wc -c "$OUT"
```

失敗例: 無関係な `app/admin` 全体と spec フィクスチャを一緒に入れたところ、モデルが **存在しない `PaymentService#settle_async!`** を「核心パス」と要約しました（ダブル/モック名と本番メソッドの混線に見えた）。以降 **回答中の全シンボルを `rg` で再検索**する手順を固定しました。

### 3. プロンプト：実行フローと根拠の強制

```text
あなたはレガシー決済モジュールを引き継いだバックエンドエンジニアです。
下記コードだけを根拠に答えてください。コードにないクラス・メソッド・設定キーは
捏造せず「提供コードでは確認不可」と書いてください。

[目標]
1. PaymentController#create から外部 PG 呼び出しまでの実行フローを番号付きで。
   各段: ファイルパス / クラス#メソッド / 一行の役割。
2. PaymentService の中核責任を 1〜2 文。根拠となるメソッド名を括弧で。
3. バグ・性能リスク候補は最大 3。各項目に根拠ファイル近傍のシンボル必須。
4. スキーマはコード/マイグレーションに現れた関係だけ Mermaid ERD で。
   推測カラムは禁止。

出力は日本語 Markdown。不確かなら確信度を低く明示。

--- BEGINNING OF CODEBASE ---
(combined_payment.txt 全体)
--- END OF CODEBASE ---
```

「20 年キャリアのペルソナ」より **根拠強制**の方が幻覚を抑えやすいです。1 の実行フローが誤っていれば残りは捨てます。

### 4. 検証ループ（15〜30 分の予算）

| 段階 | やること | 合格線 |
| --- | --- | --- |
| シンボル検証 | 回答のクラス・メソッドを `rg` | すべてコードに存在 |
| 入口追跡 | IDE の Find Usages で create → service | モデルの次呼び出しと一致 |
| 反証質問 | 「この流れを壊す early return はあるか」 | 分岐がコードに実在 |
| コスト確認 | 入力トークン・遅延 | 些細な質問に全体ダンプを再利用しない |

Before/After を誇張せず書くとおおよそ次の通りです（チーム差大）。

* **Before**: 関連ファイル探索とスタック素描に 3〜6 時間、誤った入口仮定 1〜2 回
* **After（モジュール範囲の長コンテキスト）**: 梱包と 1 次地図 20〜40 分、シンボル検証 15 分、残りを実装デバッグへ
* **After の方が遅い場合**: リポジトリ全体ダンプ＋検証省略 → 誤ったリファクタ計画で半日浪費

## コスト・限界・運用

* **コスト**: 大容量入力を毎質問で繰り返さない。大きな絵は 1〜2 回、以後は数ファイルの短いコンテキストで足りることが多い。料金は [Vertex AI / Gemini 価格](https://cloud.google.com/vertex-ai/generative-ai/pricing)に合わせる。
* **干し草の中の針**: コンテキストが長くなると特定箇所の回収が不安定になり得る。重要パスを質問本文に再掲するか、「`external_api_client.rb` のみ根拠」と注意を固定する。公式は [Long context](https://ai.google.dev/gemini-api/docs/long-context)。
* **遅延**: 数十秒〜数分はリアルタイムペアプロより **非同期解析**向き。
* **モデル名は変わる**: 持続する型は「長いコンテキスト＋狭い範囲＋シンボル検証」。1.5 Pro はその型を実務に広げた里程標として捉えればよい。

## いつ使うか

| 状況 | アプローチ | 理由 |
| --- | --- | --- |
| 小さなサイドプロジェクト | 短いコンテキストの IDE チャット | モジュールが一画面に収まる |
| 新機能、ファイル 3〜5 | そのファイルを直接添付 | 長い窓の費用対効果が小さい |
| 引き継ぎドメイン、15 ファイル超 | 長コンテキストで **地図**→狭めてデバッグ | 探索時間の削減が大きい |
| 本番ホットフィックス | ログ・メトリクス優先、モデルは補助 | 幻覚コストが高い |

## 結論

長いコンテキストはレガシー解析で **断片化した文脈を一枚の盤に載せる道具**です。効果を出すには (1) モジュール単位で切る (2) 除外リストを置く (3) 答えの全シンボルをコードで再確認する (4) 巨大ダンプを連発しない——が必要です。丸ごと貼るだけでは、理解より先に誤った確信が生まれます。

### 参考文献
- [Google AI, "Our next-generation model: Gemini 1.5"](https://blog.google/technology/ai/google-gemini-next-generation-model-february-2024/ "Google AI Blog on Gemini 1.5"){:target="_blank"}
- [Google AI for Developers, "Long context"](https://ai.google.dev/gemini-api/docs/long-context "Gemini API long context"){:target="_blank"}
- [Google Cloud, "Vertex AI pricing"](https://cloud.google.com/vertex-ai/generative-ai/pricing "Vertex AI Pricing Page"){:target="_blank"}
