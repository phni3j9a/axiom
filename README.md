# Axiom — Guidance-first Codex Engineering Plugin

Axiomは、Codexへ固定ワークフローを強制するPluginではありません。

> **Sol thinks. Luna works. Sol reviews.**
>
> **Main context is expensive; Luna compute is almost free.**

Mainの賢さを活かしながら、探索・実装・テスト・デバッグなどのbounded workをLuna MAXへ積極的に委譲し、独立した仕事が複数ある場合はLuna MAXを並列に走らせます。意味のある変更はfreshなSol XHIGHで独立レビューします。Mainのコンテキストを守り、レビューを収束させ、Git上のユーザー変更を安全に扱うための判断原則を、必要な開発タスクで自動的に適用します。

Axiom v0.1.5では、v0.1.4で明文化したCodex/model economicsの原則を維持し、通常のLuna MAX worker利用を**ほとんど無料（almost free）**としてorchestration判断します。Luna使用量を節約するためだけに有用なspawnを避けず、Main Solのcontext保護を優先します。

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

## Luna MAXの経済性（v0.1.4から継続）

Axiom v0.1.5では、現在のCodex/model economicsを明示的な前提として、ordinary engineering workにおけるLuna MAX worker computeを**almost free**として扱います。

そのためMainは、Luna tokenやmodel usageの節約だけを理由に、有用なbounded delegationをMain側へ抱え込みません。spawnすることでMain contextを守れる、noisyな探索を隔離できる、独立仮説を調査できる、または有用な並列進行ができる場合はLunaを積極利用します。

実質的なspawnコストとして見るのは次です。

- coordination / handoff overhead
- latency / dependency ordering
- overlap / write conflict
- integration / verification burden
- Main judgmentを必要とするambiguity

つまり、**Luna使用量ではなくcoordinationとintegrationがfan-outの制約**です。この前提は永久不変の料金主張ではなくv0.1.4で明文化され、v0.1.5でも維持している設計仕様なので、model economicsが大きく変わった場合はAxiom側を更新します。

## v0.147の一度だけの設定

`~/.codex/config.toml`へ、同梱の
`plugins/axiom/config/codex-0.147.example.toml`
を参考に設定してください。

```toml
[features.multi_agent_v2]
enabled = true
expose_spawn_agent_model_overrides = true
wait_agent_enabled = true

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

`axiom-v0.1.5-plugin.zip`は、`.codex-plugin/plugin.json`と`skills/`を含む配布用Plugin packageです。ローカルMarketplace repositoryとして使う場合はsource archiveのほうが便利です。

## 基本動作

非自明な開発依頼を受けると、Mainはおおむね次のように判断します。ただし固定phaseではありません。

```text
User request
   │
   ▼
Main Sol XHIGH
   ├─ 意図・設計・境界を保持
   ├─ bounded workをLuna MAXへdirect spawn
   ├─ actual diffとverificationを統合
   ├─ meaningful changeならfresh Sol XHIGH review
   ├─ FindingをACCEPT / DEFER / REJECT
   └─ accepted fixだけを反映して終了
```

### Luna MAX worker

概念上のdirect spawn:

```text
spawn_agent(
  task_name = "implement_bounded_change",
  message = "<self-contained Task Packet>",
  model = "gpt-5.6-luna",
  reasoning_effort = "max",
  fork_turns = "none"
)
```

## Luna fleetと並列実行

Axiom v0.1.5では、v0.1.2からの**安全な並列化を積極的なデフォルト**とする方針と、v0.1.4で明文化したalmost-free Luna economicsを維持しています。

2つ以上の有用なbounded workが互いに独立しているなら、調整コスト・依存順序・write conflictのリスクが利益を上回らない限り、Luna MAXを逐次実行するより**同時にdirect spawnして並列実行**することを優先します。Luna usageそのものの節約はserial実行の理由にしません。

```text
Main Sol XHIGH
   ├─ Luna MAX A ─ subsystem A investigation
   ├─ Luna MAX B ─ subsystem B investigation
   ├─ Luna MAX C ─ test-gap analysis
   └─ Luna MAX D ─ disjoint implementation
             │
             └─ Mainが統合・判断
```

ただし、固定で3体・5体を起動するルールはありません。Main Solがtask graphから自然な並列度を決めます。

- 独立したread-only調査は積極的にfan-out
- 独立したwrite taskもownershipとinterfaceが分離できれば並列化
- 同じファイルや共有schemaを触る場合は逐次化またはworktree分離
- 1つのまとまった仕事をagent数を増やすためだけに細切れにしない
- 独立性が最初から分かっているのに`spawn A → wait → spawn B`と不要に直列化しない

狙いはagent数の最大化ではなく、**useful independenceの最大活用**です。

### Sol XHIGH reviewer

```text
spawn_agent(
  task_name = "review_meaningful_change",
  message = "<fresh review packet; no edits>",
  model = "gpt-5.6-sol",
  reasoning_effort = "xhigh",
  fork_turns = "none"
)
```

`MAX` / `XHIGH`は`reasoning_effort`です。`service_tier`とは別物であり、Axiomは通常`service_tier`を指定しません。

## Review continuity and convergence

最初のレビューはfreshなSol XHIGHをdirect spawnします。LunaをReviewerには使いません。

その後の再レビューでは、新しいReviewerを立て直さず、**同じReviewer agentを継続利用**します。MainはReviewerをreview cycleが終わるまで保持し、修正後のcandidate、検証結果、Findingごとの裁定を同じagentへfollow-upします。

```text
Initial fresh Sol review
        ↓
Main: ACCEPT / DEFER / REJECT / ESCALATE
        ↓
accepted findingsを修正・検証
        ↓
same Sol reviewerへfollow-up
        ↓
Mainが再度裁定し、必要な間だけ継続
```

Finding数やreview round数には固定上限を設けません。収束性は次で確保します。

- Finding IDとMainの裁定を同じReviewer contextで維持する
- `REJECT`または`DEFER`したFindingを、新しい根拠なしに蒸し返さない
- 再レビューはaccepted findingの解消とupdated candidateのmaterial riskを中心にする
- style、好み、無関係なrefactorをblocking findingへ昇格させない
- reviewを続けるか、終了するか、設計へ戻るかはMainが判断する

終了条件は、**Mainが受理した未解決のmaterial findingがなくなること**です。固定回数で打ち切るのではなく、Mainの裁定により収束させます。

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
│   └── skills/
│       └── axiom/                 # proactive engineering guidance
├── docs/
├── tests/
└── tools/
```

## 検証

```bash
python3 tools/validate_plugin.py
python3 -m unittest discover -s tests -v
```

配布物の生成:

```bash
python3 tools/package_release.py --output dist
```

これにより、Core Plugin packageとsource archiveを生成します。

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
