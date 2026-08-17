# Axiom Trigger Evals

These prompts are intended to test implicit skill selection.

## Should trigger Axiom

1. `この認証機能を実装して、テストまで通してください。`
2. `このリポジトリで断続的に落ちるintegration testの原因を調査して直してください。`
3. `このモジュールを新しいAPIへ移行してください。影響範囲が広そうです。`
4. `Add caching to this service and make sure invalidation is correct.`
5. `Refactor this parser without changing behavior, then review the diff.`
6. `Investigate where this configuration value flows through the codebase.`
7. `Review and finish the current multi-file implementation.`
8. `複数パッケージにまたがる型エラーを解消してください。`

Expected behavior:

- Axiom is applied without an activation announcement.
- Main keeps architecture and acceptance.
- Luna MAX is considered early for bounded work.
- A meaningful code change receives fresh Sol review.
- The number of agents matches the useful independent work, not a fixed count.

## Should usually not trigger Axiom

1. `この関数名の意味を説明してください。`
2. `READMEのtypoを1文字直してください。`
3. `Gitのrebaseとは何ですか？`
4. `この1行を日本語に翻訳してください。`
5. `コードは変更せず、一般論としてMVCを説明してください。`

Expected behavior:

- no subagent is created
- no review ritual is introduced
- the request is answered directly

## Boundary prompts

### Small bug with obvious location

`このnull checkを追加して落ちないようにしてください。`

Acceptable outcomes:

- Main fixes and verifies directly
- one Luna worker is used only if repository context makes it non-trivial
- Sol review is skipped when the change is genuinely trivial

### Large investigation with no requested edit

`メモリリークの原因候補を調査して、修正案だけ報告してください。`

Expected:

- Luna workers may inspect independent subsystems
- workers are explicitly read-only
- raw logs remain out of Main context
- no Sol reviewer is needed unless code is changed or a high-stakes conclusion needs independent challenge
