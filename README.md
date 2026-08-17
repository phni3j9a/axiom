# Axiom — Guidance-first Codex Engineering Plugin

Axiomは、Codexへ固定ワークフローを強制するPluginではありません。

> **Sol thinks. Luna works. Sol reviews.**

Mainの賢さを活かしながら、探索・実装・テスト・デバッグなどのbounded workをLuna MAXへ積極的に委譲し、意味のある変更はfreshなSol XHIGHで独立レビューします。Mainのコンテキストを守り、レビューを収束させ、Git上のユーザー変更を安全に扱うための判断原則を、必要な開発タスクで自動的に適用します。

## Axiomの立ち位置

Axiomは次を**行いません**。

- 「Axiomモード」の開始宣言
- Spec → Plan → Runの固定phase
- 毎回のroute分類やpreflight儀式
- Terraを常設Orchestratorとして挟むこと
- custom agent TOMLのインストール
- 1 Task = 1 commitの強制
- 常時作成されるstate/artifact
- 無制限のレビュー反復

代わりに、Main Solが現在のタスクに必要なものだけを選びます。

| 役割 | 標準モデル | 責務 |
|---|---|---|
| Main | GPT-5.6 Sol / XHIGH | 意図、設計、分割、統合、裁定、最終受理 |
| Worker | GPT-5.6 Luna / MAX | 探索、実装、テスト、デバッグ、リファクタ |
| Reviewer | fresh GPT-5.6 Sol / XHIGH | 意味のある変更の独立レビュー |
| Terra | 標準経路では不使用 | ユーザー指定または具体的な理由がある場合のみ |

WorkerとReviewerはいずれもCodex v0.147の`spawn_agent`から**direct spawn**します。custom agentは使いません。

## 積極的な自動適用

`skills/axiom/agents/openai.yaml`では次を明示しています。

```yaml
policy:
  products:
    - CODEX
  allow_implicit_invocation: true
```

そのため、feature実装、bug fix、refactor、debug、test、コードベース調査、code reviewなど、非自明なsoftware engineering requestではAxiomが暗黙選択されることを狙っています。

一方、単純な説明、1行だけの明白な修正、typo修正などでは、subagentやreviewを無理に追加しません。Axiomは「積極利用」と「儀式化しない」を両立させます。

明示利用も可能です。

```text
$axiom:axiom

認証処理を追加してください。
```

通常は明示呼び出し不要です。

## 対象環境

- Codex CLI: **v0.147.x**
- Main model: **gpt-5.6-sol / xhigh** 推奨
- Worker: **gpt-5.6-luna / max**
- Reviewer: **gpt-5.6-sol / xhigh**
- Multi-Agent V2

## v0.147の一度だけの設定

`~/.codex/config.toml`へ、同梱の
`plugins/axiom/config/codex-0.147.example.toml`
を参考に設定してください。

```toml
[features.multi_agent_v2]
enabled = true
expose_spawn_agent_model_overrides = true
wait_agent_enabled = true

# v0.147の30秒defaultを60分へ延長。agent activityがあれば早く復帰します。
default_wait_timeout_ms = 3600000
max_wait_timeout_ms = 3600000

# routing確認時に便利。通常運用ではtrueへ戻しても構いません。
hide_spawn_agent_metadata = false
```

設定後はCodexを完全に再起動してください。

Axiomはユーザー設定を自動変更しません。`spawn_agent`に`model`と`reasoning_effort`が見えない場合、親Solを黙って継承するworkerは作らず、Mainで継続するか一度だけ設定不足を報告します。

## インストール

このsource archiveを展開したrootで実行します。

```bash
codex --enable plugins plugin marketplace add "$(pwd)" --json
codex --enable plugins plugin add axiom@axiom-local --json
```

その後、新しいCodex sessionを開始してください。

### 単体Plugin ZIPを使う場合

`axiom-v0.1.2-plugin.zip`は、`.codex-plugin/plugin.json`と`skills/`を含む配布用Plugin packageです。ローカルMarketplace repositoryとして使う場合はsource archiveのほうが便利です。

## 判断の仕方

Axiomは固定手順を持ちません。Main Solは作業中に次の観点を必要に応じて見直します。

- 重要な意味・設計・受理判断はMainに残すべきか
- どのbounded workをLuna MAXへ逃がすとcontext/速度/コスト面で得か
- `fork_turns: "none"`で十分か、少量のrecent turnsを渡した方が安全か
- どのverification evidenceが必要か
- risk / uncertainty / blast radiusを考えるとfresh Sol reviewが有益か
- shared tree / worktree / commit ownershipをどうすると統合コストが低いか

この判断に固定順序はありません。小さな変更ならMainだけで完結して構いません。

### Luna MAX worker

conceptual direct spawn:

```text
spawn_agent(
  task_name = "implement_bounded_change",
  message = "<必要十分なbounded handoff>",
  model = "gpt-5.6-luna",
  reasoning_effort = "max",
  fork_turns = "none"
)
```

`fork_turns: "none"`はstrong defaultです。直近の会話を少量引き継ぐ方が意図を安全に保てる場合は、Mainがrecent-turn forkを選べます。

### Sol XHIGH reviewer

初回だけfresh reviewerをdirect spawnします。

```text
spawn_agent(
  task_name = "review_meaningful_change",
  message = "<fresh review context; no edits>",
  model = "gpt-5.6-sol",
  reasoning_effort = "xhigh",
  fork_turns = "none"
)
```

再レビューが有益なら同じReviewer sessionへfollow-upします。`MAX` / `XHIGH`は`reasoning_effort`であり、`service_tier`とは別です。

### wait_agent

v0.147は`wait_agent`のdefault timeoutが30秒、hard maximumが60分です。Axiomでは短いpollingを避けるため、config defaultを60分にし、必要なら明示的にも次を使います。

```text
wait_agent(timeout_ms = 3600000)
```

これは「必ず60分待つ」という意味ではありません。agent activityや新しいsteering inputが入れば早く復帰します。そのため、Luna MAXの長い実装中にMainが30秒ごとに不要なtimeout復帰を繰り返すのを避けられます。

## Review convergence

Reviewerを呼ぶ場合、初回はfresh Sol XHIGHです。以後のre-reviewは、利用可能なら**同じReviewer session**を継続します。LunaをReviewerには使いません。

Reviewerはstyleや好みではなく、具体的なimpactを持つmaterial findingをstable ID付きで返します。`SHIP / FIX_FIRST / RETHINK`や`CRITICAL / MAJOR`といった固定判定は要求しません。最終判断はMainが持ちます。

Mainは各findingを`ACCEPT / DEFER / REJECT / ESCALATE`として裁定し、accepted findingだけを現在のdesign boundaryに沿ったfix requirementへ変換します。再レビュー時は同じReviewerが以前のfinding IDとMain裁定を保持したまま更新candidateを確認します。

Finding件数やreview round数には固定上限を置きません。収束性は、**same-reviewer continuity + stable finding IDs + Main adjudication + Finding Freeze + Mainによる終了判断**で確保します。新しいmaterial findingは、新しい具体的証拠やfixによって発生・顕在化した問題なら追加できます。

Reviewの有無もファイル数では決めません。risk、uncertainty、blast radius、deterministic verificationの強さをMainが総合して判断します。

## Direct spawn reviewerのread-only性

custom agentを使わないため、Reviewerのsandboxを専用TOMLでhard read-onlyに固定しません。Axiomはreview packetで次を明示します。

- ファイルを変更しない
- commitしない
- formatterや自動修正を実行しない
- working treeを変える可能性があるcommandを実行しない
- evidenceと提案だけを返す

つまりread-onlyは**behavioral contract**です。この制約と導入容易性のトレードオフは意図的です。最終diff確認と受理はMainが担当します。

## Repository構成

```text
axiom-codex-plugin/
├── .agents/plugins/marketplace.json
├── plugins/axiom/
│   ├── .codex-plugin/plugin.json
│   ├── plugin.json
│   ├── assets/
│   ├── config/
│   └── skills/axiom/
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       └── references/
├── docs/
├── tests/
└── tools/
```

## 検証

```bash
python3 tools/validate_plugin.py
python3 -m unittest discover -s tests -v
```

配布ZIPの生成:

```bash
python3 tools/package_release.py --output dist
```

## 設計資料

- [`DESIGN.md`](DESIGN.md)
- [`docs/TRIGGER_EVALS.md`](docs/TRIGGER_EVALS.md)
- [`plugins/axiom/skills/axiom/references/delegation.md`](plugins/axiom/skills/axiom/references/delegation.md)
- [`plugins/axiom/skills/axiom/references/review.md`](plugins/axiom/skills/axiom/references/review.md)
- [`plugins/axiom/skills/axiom/references/context-management.md`](plugins/axiom/skills/axiom/references/context-management.md)
- [`plugins/axiom/skills/axiom/references/git.md`](plugins/axiom/skills/axiom/references/git.md)
- [`plugins/axiom/skills/axiom/references/codex-0.147-subagents.md`](plugins/axiom/skills/axiom/references/codex-0.147-subagents.md)

## License

MIT
