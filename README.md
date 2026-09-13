# Axiom — Guidance-first Codex Engineering Plugin

Axiomは、Codexへ固定ワークフローを強制するPluginではありません。

> **Main decides. Astra advises. Sol designs. Luna executes. Sol reviews.**
>
> **Main context is expensive; Luna compute is almost free.**

Mainの賢さを活かしながら、通常の探索・実装・テスト・デバッグなどのbounded workをLuna MAXへ積極的に委譲し、未確定の重要なvisual・interaction・information designを含むbounded workはSol MAXへ委譲します。独立した仕事は安全な範囲で並列に走らせ、意味のある変更は実装担当とは別のfreshなSol XHIGHで独立レビューします。Mainのコンテキストを守り、レビューを収束させ、Git上のユーザー変更を安全に扱うための判断原則を、ユーザーがAxiomを明示呼び出しした開発タスクに適用します。

Axiom v0.1.9では、v0.1.4で明文化したCodex/model economicsの原則を維持し、通常のLuna MAX worker利用を**ほとんど無料（almost free）**としてorchestration判断します。Luna使用量を節約するためだけに有用なspawnを避けず、Mainのcontext保護を優先します。

v0.1.9は**Core-only構成**です。v0.1.3で追加されたoptional Dashboardは削除され、Rust/Axum backend、React/TypeScript frontend、Dashboard Skill、platform launcher、Dashboard用binary release処理は現在のPlugin packageには含まれません。Axiom Coreのdelegation、design-sensitive routing、parallel Luna、review continuity、Git safety、direct-spawn policyはそのまま維持されています。任意のrollout auditはJSONLを読み取ってmetricsを返すだけで、常駐監視や実行制御を行いません。

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
- Dashboard、daemon、hookによる常時監視

代わりに、Main（Sol XHIGH）が現在のタスクに必要なものだけを選びます。

| 役割 | 標準モデル | 責務 |
|---|---|---|
| Main | `gpt-5.6-sol` / `xhigh` | 意図、アーキテクチャ、デザイン制約・方向性、分割、統合、裁定、最終受理 |
| Advisor | GPT-6 Astra / XHIGH | 難しいPlanの起草、設計比較、行き詰まりの分析。採否はMainが判断 |
| Ordinary worker | GPT-5.6 Luna / MAX / Fast | 探索、通常実装、テスト、デバッグ、リファクタ、長時間処理の監視 |
| Design worker | GPT-5.6 Sol / MAX | 未確定の重要なvisual・interaction・information designと不可分なUI実装 |
| Reviewer | fresh GPT-5.6 Sol / XHIGH | 意味のある変更の独立レビュー |
| Terra | 標準経路では不使用 | ユーザー指定または具体的な理由がある場合のみ |

Advisor・各worker・ReviewerはいずれもCodex v0.147以上（v0.153を含む）の公開`spawn_agent`から**direct spawn**します。custom agentは使いません。

## Astra Advisor

難しいPlanは、MainまたはLunaが現状を調べた後、Astra XHIGHに起草を依頼できます。
設計案の比較、失敗が収束しないデバッグ、前提が変わった計画、重要な技術的争点にも使います。
Mainが計画・助言の採否を決め、Workerへの分担と最終受理を担当します。
単純な編集や通常のPlan更新では相談を強制しません。

Mainは重要なユーザー発言と関連会話、現在の合意・制約、相談論点、必要なコードや
失敗結果の抜粋を選んで渡します。Mainの仮説と一次証拠を区別し、全履歴はforkしません。
会話の自動抽出機能はありません。Astraは関連ファイルを読み取り、不足情報をMainへ
要求できますが、プロジェクトの編集・計画の実行は行いません。この制約は役割指示です。

同じ論点の追加相談は同じAdvisorへ新しい証拠とMainの判断を送ります。
Advisorを独立Reviewerとして再利用せず、既存のSolレビューを維持します。
モデル・effortは計画作成と相談の両方で `gpt-6-astra / xhigh` 固定です。
利用できない場合は制約を報告してMainで可能な作業を続け、別モデルへ黙って置換しません。

```text
$axiom:axiom
認証方式の移行について現状を調べ、難しい設計判断はAstraに相談して計画を作ってください。
```

詳しい[相談方針](plugins/axiom/skills/axiom/references/advisor.md)と
[起動例](plugins/axiom/skills/axiom/references/codex-0.147-subagents.md#astra-xhigh-advisor)を参照してください。
従来のworker/reviewerの実機確認はAdvisorの実証にはなりません。
品質・消費量は[Advisor評価手順](docs/ADVISOR_EVALS.md)で比較します。

## 明示呼び出し

`skills/axiom/agents/openai.yaml`では次を明示しています。

```yaml
policy:
  allow_implicit_invocation: false
```

スキルの`description`は機能を説明し、呼び出し方はこのpolicyで制御します。通常の開発依頼では自動選択されません。

呼び出された作業内では、必要な委譲やレビューを積極的に行います。単純な説明、1行だけの明白な修正、typo修正などでは、subagentやreviewを無理に追加しません。

利用する作業で次のように指定します。

```text
$axiom:axiom

認証処理を追加してください。
```

明示呼び出しした作業とその続きに適用します。同じ作業の追加指示では、毎回指定し直す必要はありません。

## 対象環境

- Codex CLI: **v0.147以上（v0.153を含む）**
- Main model: **gpt-5.6-sol / xhigh**
- Advisor: **gpt-6-astra / xhigh**（計画作成・相談ともに固定）
- Ordinary worker: **gpt-5.6-luna / max / Fast**
- Design worker: **gpt-5.6-sol / max**
- Reviewer: **gpt-5.6-sol / xhigh**
- Multi-Agent V2

Mainは`gpt-5.6-sol` / `xhigh`で起動します。CLIでは`codex -m gpt-5.6-sol -c 'model_reasoning_effort="xhigh"'`を使えます。プラグインは実行中のMainモデルや他の作業のグローバル既定値を自動変更しません。designは同じSolでも`max`、reviewは別のfreshなSol `xhigh`です。

Codex v0.153.4では、Luna MAXの並列実行とfreshなSol XHIGH reviewerのdirect spawnおよびcompletionを、要求したspawn引数、子の`turn_context`のmodel/effort、対応する`task_complete`イベントで確認しました。これはその経路の確認であり、全機能や新版の設定既定値を実証するものではありません。

## Luna MAXの経済性（v0.1.4から継続）

Axiom v0.1.9では、現在のCodex/model economicsを明示的な前提として、ordinary engineering workにおけるLuna MAX worker computeを**almost free**として扱います。

そのためMainは、Luna tokenやmodel usageの節約だけを理由に、有用なbounded delegationをMain側へ抱え込みません。spawnすることでMain contextを守れる、noisyな探索を隔離できる、独立仮説を調査できる、または有用な並列進行ができる場合はLunaを積極利用します。

実質的なspawnコストとして見るのは次です。

- coordination / handoff overhead
- latency / dependency ordering
- overlap / write conflict
- integration / verification burden
- Main judgmentを必要とするambiguity

つまり、**Luna使用量ではなくcoordinationとintegrationがfan-outの制約**です。この前提は永久不変の料金主張ではなくv0.1.4で明文化され、v0.1.9でも維持している設計仕様なので、model economicsが大きく変わった場合はAxiom側を更新します。

## v0.147向けの一度だけの設定例

`~/.codex/config.toml`へ、同梱の
`plugins/axiom/config/codex-0.147.example.toml`
を参考に設定してください。以下はCodex v0.147向けの設定例です。v0.153など新版では、実行中の公開tool surfaceを確認してから、利用可能な設定を適用してください。

```toml
[features.multi_agent_v2]
enabled = true
expose_spawn_agent_model_overrides = true
wait_agent_enabled = true

# 30秒ごとの不要なMain復帰を避け、長時間workerをevent-drivenで待つ。
default_wait_timeout_ms = 3600000
max_wait_timeout_ms = 3600000
```

v0.1.5から更新する場合は、既存設定の`hide_spawn_agent_metadata = false`を削除してください。Codex CLI 0.147.0では、この設定が残っていると最初のモデル応答前に予約済み`collaboration.spawn_agent`のschema mismatchでHTTP 400になります。

設定後はCodexを完全に再起動してください。

Axiomはユーザー設定を自動変更しません。`spawn_agent`に`model`と`reasoning_effort`が見えない場合、親モデル（Sol）を黙って継承するworkerは作らず、Mainで継続するか一度だけ設定不足を報告します。

Codex v0.147では`wait_agent`の既定waitが30秒で、最大は60分です。Axiomは`default_wait_timeout_ms = 3600000`と`max_wait_timeout_ms = 3600000`を推奨し、長時間のLuna MAX / Sol MAX / Sol XHIGH実行中にMainが短周期で何度もtimeout復帰するのを避けます。これは60分間必ずsleepする設定ではなく、agent activityやsteering inputがあれば早く復帰するevent-driven waitの上限です。

Routing確認には、要求したspawn引数、子の`turn_context`に記録されたmodel/effort、対応する子turnの`task_complete`というruntime/rollout証拠を使います。`task_complete`は1つの子turnが返った証拠であり、再利用可能なagent sessionの終了やMainによる成果物受理を意味しません。子エージェントの自己申告だけでは成功と判定しません。

## インストール

このsource archiveを展開したrootで実行します。

```bash
codex --enable plugins plugin marketplace add "$(pwd)" --json
codex --enable plugins plugin add axiom@axiom-local --json
```

その後、新しいCodex sessionを開始してください。

### 単体Plugin ZIPを使う場合

`axiom-v0.1.9-plugin.zip`は、`.codex-plugin/plugin.json`、Core Skill、references、config、assets、任意のread-only rollout audit scriptなどを含む**Core-onlyの配布用Plugin package**です。Dashboard関連のSkill・runtime・binaryは含みません。ローカルMarketplace repositoryとして使う場合はsource archiveのほうが便利です。

`python3 tools/package_release.py --output dist`で同時に生成されるsource archiveは`axiom-codex-plugin-v0.1.9-source.zip`です。

## 基本動作

非自明な開発依頼を受けると、Mainはおおむね次のように判断します。ただし固定phaseではありません。

```text
User request
   │
   ▼
Main（Sol XHIGH）
   ├─ 意図・architecture・designの方向性と境界を保持
   ├─ 難しいPlan・判断はAstra XHIGHへ相談し、Mainが採否を判断
   ├─ ordinary bounded workをLuna MAXへdirect spawn
   ├─ design-sensitive bounded workをSol MAXへdirect spawn
   ├─ independent workなら先にfan-out
   ├─ long-running workはevent-driven wait
   ├─ actual diffとverificationを統合
   ├─ meaningful changeならfresh Sol XHIGH review
   ├─ FindingをACCEPT / DEFER / REJECT / ESCALATE
   └─ accepted fixだけを反映して終了
```

### Luna MAX Fast worker

`MAX` / `XHIGH`は推論強度、Fastは速度の設定です。Fastを指定するのはworkerのみです。`spawn_agent`が`service_tier`を公開していれば`"priority"`を渡します。Codex設定での`"fast"`はリクエストの`"priority"`に対応します（[公式設定リファレンス](https://learn.chatgpt.com/docs/config-file/config-reference)）。

速度指定欄がない環境では、継承したFastを実行証拠で確認できる場合に限って使います。指定・確認できなければ制約を一度報告してモデル・推論強度はLuna MAXを維持し、未対応引数を送ったりFast適用済みと扱ったりしません。以下のspawn例はモデル・推論強度の指定を示し、速度指定欄の存在を保証するものではありません。

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

長時間workerを待つ場合は、v0.147で許可される範囲内で長いevent-driven waitを優先します。

```text
wait_agent(timeout_ms = 3600000)
```

複数の独立workerがある場合は、各workerをspawnしてからまとめて待ち、依存関係がないのに`spawn → wait → spawn`と直列化しません。

### 長時間処理の監視

CI/CD、GitHub Actions、ビルド、テストなどで反復的な状態確認が必要な場合は、
Luna workerに完了確認まで委任します。監視だけでも委任でき、既存の担当Lunaがいれば同じ担当に任せます。
Mainは委任後の状態確認を繰り返さず、他の作業を進めるか、既存の待機機能で報告を待ちます。
Lunaは完了・失敗・監視不能・Mainの判断が必要になったときに、結果と証拠を簡潔に報告します。
変化のない状況の定期報告は不要です。

### Sol MAX design worker

未確定の重要なvisual・interaction・information designを作成、比較、反復改善するbounded workはSol MAXへ委譲します。

```text
spawn_agent(
  task_name = "design_sensitive_interface_work",
  message = "<intent、制約、ownership、acceptanceを含むdesign Task Packet>",
  model = "gpt-5.6-sol",
  reasoning_effort = "max",
  fork_turns = "none"
)
```

判定基準はfrontendファイルを触るかではなく、重要なinterface design判断が未確定かどうかです。

- layout、visual hierarchy、spacing、typography、color、art direction
- interaction、navigation、user flow、responsive behavior
- information architecture、使いやすさに影響するcomponent composition
- 「polishedにして」「使いやすくして」のようなopen-endedな改善
- screenshotを見ながらdesignとcodeを往復するUI実装

完成済みdesign、明示されたtokenや寸法、確定済み挙動をそのまま実装する作業は、frontendであってもLuna MAXを優先します。designと実装が不可分ならDesign SolがUIコードまで担当でき、design安定後の反復展開、非視覚的なdata/state wiring、test、mechanical cleanupはLunaへ分割できます。

Design Solはimplementation participantです。統合後に独立レビューが必要なら、そのDesign Solを再利用せず、別のfresh Sol XHIGH Reviewerを起動します。

## Luna fleetと並列実行

Axiom v0.1.9では、v0.1.2からの**安全な並列化を積極的なデフォルト**とする方針と、v0.1.4で明文化したalmost-free Luna economicsを維持しています。

2つ以上の有用なbounded workが互いに独立しているなら、調整コスト・依存順序・write conflictのリスクが利益を上回らない限り、Luna MAXを逐次実行するより**同時にdirect spawnして並列実行**することを優先します。Luna usageそのものの節約はserial実行の理由にしません。

```text
Main（Sol XHIGH）
   ├─ Luna MAX A ─ subsystem A investigation
   ├─ Luna MAX B ─ subsystem B investigation
   ├─ Luna MAX C ─ test-gap analysis
   └─ Luna MAX D ─ disjoint implementation
             │
             └─ Mainが統合・判断
```

ただし、固定で3体・5体を起動するルールはありません。Mainがtask graphから自然な並列度を決めます。

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


## Review continuity and convergence

最初のレビューはfreshなSol XHIGHをdirect spawnします。LunaをReviewerには使いません。

その後の再レビューでは、ユーザー意図・acceptance・non-goal・substantive designというreview boundaryがmaterialに安定している間、**同じReviewer agentを継続利用**します。MainはReviewerをreview cycleが終わるまで保持し、修正後のcandidate、検証結果、Findingごとの裁定を同じagentへfollow-upします。

ユーザーの方針やrisk toleranceがmaterialに変わった場合は自動的なresetを強制せず、Mainが旧Findingを再裁定し、同じcontextで境界をresetするか、fresh review cycleを開始するかを判断します。Reviewerは独立した証拠を提供しますが、ユーザーのrisk toleranceやproduct policyを決めません。Mainは具体的なcorrectness・safety・requirement evidenceを隠さず、採用するmitigationをユーザー意図に照らして裁定します。

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
│   ├── README.md
│   ├── CHANGELOG.md
│   ├── LICENSE
│   ├── assets/
│   ├── config/
│   └── skills/
│       └── axiom/                 # explicitly invoked engineering guidance
│           └── scripts/           # optional read-only rollout metrics
├── docs/
├── tests/
└── tools/
```

v0.1.9には`plugins/axiom/dashboard/`や`skills/axiom-dashboard/`は存在しません。

## 検証

```bash
python3 tools/validate_plugin.py
python3 -m unittest discover -s tests -v
```

任意のrollout metrics確認:

```bash
python3 plugins/axiom/skills/axiom/scripts/audit_rollout.py \
  ~/.codex/sessions/YYYY/MM/DD/rollout-....jsonl
```

この出力は診断材料であり、agentの実行可否やrelease可否を自動判定しません。

配布物の生成:

```bash
python3 tools/package_release.py --output dist
```

これにより、Core-only Plugin packageとsource archiveを生成します。

- `dist/axiom-v0.1.9-plugin.zip`
- `dist/axiom-codex-plugin-v0.1.9-source.zip`

## 設計資料

- [`DESIGN.md`](DESIGN.md)
- [`docs/TRIGGER_EVALS.md`](docs/TRIGGER_EVALS.md)
- [`docs/TRACE_EVALS.md`](docs/TRACE_EVALS.md)
- [`docs/ADVISOR_EVALS.md`](docs/ADVISOR_EVALS.md)
- [`plugins/axiom/skills/axiom/references/advisor.md`](plugins/axiom/skills/axiom/references/advisor.md)
- [`plugins/axiom/skills/axiom/references/delegation.md`](plugins/axiom/skills/axiom/references/delegation.md)
- [`plugins/axiom/skills/axiom/references/review.md`](plugins/axiom/skills/axiom/references/review.md)
- [`plugins/axiom/skills/axiom/references/context-management.md`](plugins/axiom/skills/axiom/references/context-management.md)
- [`plugins/axiom/skills/axiom/references/git.md`](plugins/axiom/skills/axiom/references/git.md)
- [`plugins/axiom/skills/axiom/references/codex-0.147-subagents.md`](plugins/axiom/skills/axiom/references/codex-0.147-subagents.md)

## License

MIT
