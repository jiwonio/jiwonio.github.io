---
layout: post
title: Antigravity CLI利用時に発生したコンテキスト喪失問題
slug: antigravity-cli-context-loss-mistakes
lang: ja
translation_key: antigravity-cli-context-loss-mistakes
post_type: deep-dive
date: 2026-07-08 00:00:00 +0900
categories:
- AI
tags:
- Antigravity CLI
- コンテキスト管理
- CLIワークフロー
- コーディング自動化
description: Antigravity CLIを実務導入した際にコンテキスト喪失で発生した問題を再現し、その防止パターンを段階的にまとめます。
image: /uploads/antigravity-cli-context-loss-mistakes/thumbnail.webp
ai_generated: true
permalink: /ja/posts/antigravity-cli-context-loss-mistakes/
---
レガシーサービス移行作業中にAntigravity CLIを初めて導入しました。最初の数日はうまくいきましたが、ファイル数が増えるにつれてCLIが「既に修正したファイル」に再び手を加え始めました。確認したところ、セッション間でコンテキストが初期化され、以前の決定を全く知らない状態で次の作業に進んでいたのです。その結果、同じ関数のシグネチャが2回変更され、その間に作成されたテストは2回とも壊れました。

この記事では、Antigravity CLIがコンテキストをどのように扱い、どこで喪失が発生するのか、そしてセッションを超えても意図が維持されるようにするためのパターンを扱います。「CLIが勝手にコードを変更する」という症状に悩んでいる場合、その原因はツール側のバグではない可能性が高いです。

この記事を読めば、Antigravity CLIでセッション境界を越える際にコンテキストが途切れる理由、そしてそれを防ぐためにどのようなファイル構造と呼び出しパターンを使用すべきかを理解できるでしょう。

<!--more-->

![Antigravity CLI利用時に発生したコンテキスト喪失問題](/uploads/antigravity-cli-context-loss-mistakes/thumbnail.webp "Antigravity CLI利用時に発生したコンテキスト喪失問題")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>

-----

## 症状の確認から始める

再現可能なシナリオは次のとおりです。

1. 最初のセッションで、`user_service.py`の`get_user`関数の戻り型を`dict`から`UserDTO`に変更するよう指示します。
2. CLIが修正を完了します。
3. ターミナルを閉じ、翌日新しいセッションを開始します。
4. `order_service.py`で`get_user`を呼び出す部分をリファクタリングするよう指示します。
5. CLIが`get_user`を再び`dict`戻り型に戻してしまいます。

原因は単純です。Antigravity CLIは基本的にセッション単位でコンテキストを管理します。新しいセッションが開始されると、以前のセッションで下された決定やファイル変更履歴は引き継がれません。CLIは現在のファイルの状態のみを読み込み、ファイル内のコメントや型ヒントが不完全な場合、元のパターンで推論してしまいます。

---

## コンテキスト喪失が発生する3つのポイント

### 1. セッション境界

最も一般的なポイントです。`antigravity session`オブジェクトは、プロセスが終了するとメモリから消滅します。`--session-file`オプションでセッション状態をファイルに保存できますが、デフォルトはオフです。

```bash
# セッション状態をファイルに保存 — デフォルトは保存しない
antigravity run --session-file .ag/session.json "get_user戻り型をUserDTOに変更"
```

このオプションを省略すると、次の実行時にセッションファイルがないため、コンテキストが完全に空の状態で開始されます。

### 2. スコープの超過

一度にあまりにも多くのファイルを含めると、内部コンテキストウィンドウが途切れます。Antigravity CLIは指示されたファイルリストをトークンに変換しますが、限界を超えると後方のファイルが欠落します。このとき、欠落したファイルにある型定義やインターフェースが途切れてしまい、以前の決定と矛盾する修正が発生します。

```bash
# 悪い例: ディレクトリ全体を一度に渡す
antigravity run --include "src/**/*.py" "UserDTOを適用"

# 良い例: モジュール単位で分割
antigravity run --include "src/user/*.py" "UserDTOを適用"
antigravity run --include "src/order/*.py" --session-file .ag/session.json "UserDTO呼び出し部を修正"
```

### 3. 暗黙的な決定の不在

CLIはファイルを読み込み、パターンを推論します。ドメイン決定（「このサービスはDTOレイヤーを強制する」）がコードのどこにも明示されていない場合、新しいセッションでその決定を再度推論する根拠がありません。結果として、CLIはファイルに見られる最も単純なパターンに従います。

---

## 防止パターン

### コンテキストファイルで決定を明示する

プロジェクトルートに`.ag/context.md`ファイルを置き、すべてのセッションに自動的に含めます。このファイルには、コードからは読み取れないドメイン決定のみを記述します。

```markdown
<!-- .ag/context.md -->
# プロジェクトコンテキスト

## アーキテクチャ決定 (ADR)
- サービスレイヤーはDTOを返す。dictの直接返却は禁止。
- UserDTO: src/models/dto.pyを参照。
- 外部API応答は必ずパース後DTOに変換する。

## 現在進行中の移行
- get_user: dict → UserDTO変換完了 (2025-07-01)
- get_order: 進行中
```

このファイルを`--context`オプションで常に含めます。

```bash
antigravity run \
  --context .ag/context.md \
  --session-file .ag/session.json \
  --include "src/order/*.py" \
  "get_orderにUserDTOパターンを適用"
```

### セッションファイルのGit追跡の有無を決定する

`.ag/session.json`をGitに追加するかどうかは、チーム規模によって異なります。

- **一人で作業**: 追加しても問題ありません。セッション状態がブランチと共に管理されます。
- **チーム作業**: `.gitignore`に追加し、`context.md`のみを共有します。セッションファイルは作業者個人の実行状態を含むため、衝突が頻繁に発生します。

```gitignore
# .gitignore
.ag/session.json
.ag/*.log
# context.mdは追跡 — チーム共有決定ファイル
```

### 実行単位を小さく分割する

単一の実行で変更するファイル数を制限します。経験上、1回の実行につきファイルは10個以下、1ファイルにつき200行以下が、コンテキストが途切れない安全な範囲でした。正確なトークン限界はバージョンごとに異なる場合があるため、`--dry-run`で含まれるファイルリストを最初に確認することをお勧めします。

```bash
# 実際の修正前に含まれるファイルリストを確認
antigravity run --dry-run \
  --context .ag/context.md \
  --include "src/**/*.py" \
  "UserDTOを適用"
```

出力で「context truncated」警告が表示されたら、`--include`の範囲を減らす必要があります。

---

## 実際に変わったワークフロー

以前はAntigravity CLIを即興的に呼び出していました。ターミナルから必要な時にコマンド一行、セッションファイルなし、コンテキストファイルなしで。結果が気に入らなければ元に戻して再度試すというやり方でした。

今は、移行単位で`.ag/context.md`をまず更新し、モジュールごとにセッションを続ける方式を採用しています。面倒に思えるかもしれませんが、実際にかかる時間は5分程度です。一方、誤った修正を追跡して元に戻す時間ははるかに長いです。

```bash
# 移行開始時にコンテキストファイルを更新
echo "- get_order: 進行中 ($(date +%Y-%m-%d))" >> .ag/context.md

# モジュール単位の順次実行
antigravity run \
  --context .ag/context.md \
  --session-file .ag/session.json \
  --include "src/order/service.py" \
  "get_orderの戻り型をOrderDTOに変更"

antigravity run \
  --context .ag/context.md \
  --session-file .ag/session.json \
  --include "src/order/repository.py" \
  "サービス変更に合わせてリポジトリを調整"
```

---

## チーム導入時にさらに注意すべき点

3人以上のチームの場合、`context.md`の所有権を定める必要があります。誰でも修正できると、異なる決定が混ざり合い、かえってノイズになります。PRレビューの対象に`context.md`を含め、ADR（Architecture Decision Record）形式で管理すれば、変更理由を追跡しやすくなります。

また、CIでAntigravity CLIを自動実行する場合、セッションファイルパスを環境変数で分離しないと、並列ワークフロー間でセッションファイルが衝突します。

```yaml
# .github/workflows/antigravity.yml の一部
- name: Run Antigravity
  env:
    AG_SESSION_FILE: .ag/session-${{ github.run_id }}.json
  run: |
    antigravity run \
      --context .ag/context.md \
      --session-file $AG_SESSION_FILE \
      --include "src/**/*.py" \
      "lint修正"
```

---

## 結論

| 状況 | 推奨パターン | 理由 |
|------|--------------|------|
| 1人サイドプロジェクト | `--session-file` + `context.md` 基本構成 | セッション再開時のコンテキスト喪失防止に十分 |
| スタートアップ（3〜5人チーム） | `context.md` Git追跡、セッションファイルは`.gitignore` | 決定の共有は必要だが、セッション衝突は避けるべき |
| レガシー移行進行中 | モジュール単位実行 + ADR形式 `context.md` | ファイル数が多いほどコンテキストが途切れるリスクが高まる |
| CI自動化を含む | `run_id`ベースのセッションファイル分離 | 並列ワークフロー間のセッションファイル衝突防止 |

Antigravity CLI自体が誤動作していたわけではありません。ツールがセッション境界をどのように扱うかを理解せずに使用したことが問題でした。コンテキストファイルとセッションファイルを明示的に管理するだけで、ほとんどの「勝手に変更される」症状は解消されます。

---

## 参照

- [OpenAI Prompt engineering](https://platform.openai.com/docs/guides/prompt-engineering)
- [Anthropic Prompt engineering - Long context tips](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/long-context-tips)

### 参考文献
- [OpenAI: Best practices for prompt engineering](https://platform.openai.com/docs/guides/prompt-engineering){:target="_blank"}
- [Anthropic: Long context tips](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/long-context-tips){:target="_blank"}
