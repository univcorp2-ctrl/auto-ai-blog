# A8.net EC売上確定API v3 連携

## 最重要: 媒体向け報酬APIではない

このAPIはA8.netの**広告主向け**です。自社プログラムで発生した成果を取得し、広告主側の注文・申込データと照合して、確定、キャンセル、修正するために使います。

次の用途には使えません。

- アフィリエイト媒体側の発生報酬・確定報酬レポート取得
- A8案件の検索、EPC・確定率の自動収集
- 広告リンク生成
- 提携申請

univ合同会社が「AI導入相談」「無料診断」「テンプレート販売」などをA8広告主として出稿する場合には有効です。`auto-ai-blog`で獲得した申込だけでなく、A8上の各媒体から届いた申込を自社CRMと照合できます。

## できること

### 読取

- プログラム単位の未確定売上一覧
- プログラム単位・広告主配下全体の未確定件数
- 当日に確定またはキャンセルしたデータ
- 当日の確定件数
- 前日以前に確定またはキャンセルしたデータ
- メディアID、媒体名、A8オーダーID、自社注文番号、注文金額、成果報酬額、商品明細の取得

### 更新

- 未確定売上の単価・数量・商品明細の修正
- 未確定成果の確定
- 未確定成果のキャンセル
- 当日中に行った確定・キャンセルの取消

更新系は事故時の影響が大きいため、このリポジトリでは既定で完全停止しています。

## 取得に必要なもの

A8.netから次を取得します。

1. 広告主ID、または対象の15文字プログラムID
2. プログラムIDに紐づく確定API認証キー
3. A8.netへ申請・登録したアクセス元グローバルIP

APIキーをChatGPT、GitHub Issue、README、公開Pages、ブラウザJavaScriptへ入力しないでください。GETではAPIキーがクエリパラメータになる仕様のため、アクセスログ・プロキシログ・例外ログにもURL全体を残さないでください。

## 実行場所

推奨順は次のとおりです。

1. 固定グローバルIPを持つVPSまたは社内サーバー
2. 固定IP契約のあるローカルPC・自社ネットワーク
3. 固定egress IPを保証できる自ホストGitHub Actions Runner

Cloudflare Pagesのブラウザコードからは呼びません。静的サイトでは秘密を保持できず、アクセス元IPもA8登録条件を満たせないためです。GitHub-hosted Runnerも通常は単一固定IPではないため、A8側に登録できる固定egressを別途用意します。

## 環境変数

```powershell
$env:A8_EC_PROGRAM_ID = "s00000000000000"
$env:A8_EC_API_KEY = "A8から発行されたキー"
$env:A8_EC_ADVERTISER_ID = "s00000000000"  # 広告主全体の件数取得時のみ
$env:A8_EC_MUTATIONS_ENABLED = "false"
$env:A8_EC_BLOCK_MAINTENANCE_WINDOW = "true"
$env:A8_EC_CALLS_PER_MINUTE = "240"
```

`.env`へ保存する場合もGit管理対象外であることを確認してください。

## CLI

### 機能一覧と設定確認

```powershell
python -m affiliate_agent.a8_cli capabilities
python -m affiliate_agent.a8_cli doctor
```

`doctor`はキーの値を表示せず、設定済みかどうかだけを返します。

### 未確定データ

```powershell
python -m affiliate_agent.a8_cli unsealed-count
python -m affiliate_agent.a8_cli unsealed --date 20260731 --limit 100
```

既定出力は件数・注文金額・成果報酬額だけの集計です。注文ID、媒体ID、媒体名が必要な管理者処理だけ、非公開保存先を指定して `--raw` を付けます。

```powershell
python -m affiliate_agent.a8_cli unsealed `
  --date 20260731 `
  --limit 100 `
  --raw `
  --output G:\マイドライブ\AI_Agents\private\a8\unsealed-20260731.json
```

### 確定済みデータ

```powershell
python -m affiliate_agent.a8_cli sealed-today-count
python -m affiliate_agent.a8_cli sealed-today --limit 100
python -m affiliate_agent.a8_cli sealed --date 20260730 --limit 100
```

確定済みデータはAPI上、91日以上前のデータを取得できないため、日次で非公開DBへ同期します。

## 更新系の三重ロック

成果確定を例にすると、次の3条件がすべて必要です。

1. `A8_EC_MUTATIONS_ENABLED=true`
2. CLIに `--execute`
3. `--confirm decide:PROGRAM_ID:ORDER_ID` が完全一致

```powershell
$env:A8_EC_MUTATIONS_ENABLED = "true"
python -m affiliate_agent.a8_cli decide `
  --order-id 123456789012 `
  --execute `
  --confirm "decide:s00000000000000:123456789012"
```

キャンセルにはA8仕様の理由コード1〜6が必要です。

```powershell
python -m affiliate_agent.a8_cli cancel `
  --order-id 123456789012 `
  --reason-code 2 `
  --execute `
  --confirm "cancel:s00000000000000:123456789012"
```

本番では、CRMの注文状態、返金状態、本人確認、サービス提供完了、クーリングオフ期間を確認した後にだけ候補を作成し、最終確定は人間承認にします。

## 100万円エージェントへの組込み

広告主側で次のループを作れます。

1. **A8 Conversion Fetcher**: 未確定売上を取得
2. **CRM Reconciler**: `order_no`で自社申込と照合
3. **Eligibility Auditor**: 重複、返金、対象外条件、提供完了を判定
4. **Decision Draft Builder**: 確定・キャンセル・要確認の案を作成
5. **Human Approval Gate**: 管理者が注文単位で承認
6. **A8 Decision Executor**: 三重ロックを満たした注文だけAPI処理
7. **Quality Optimizer**: `as_id`・媒体別の確定率、平均単価、キャンセル理由を集計

これにより、自社AI相談をA8へ出稿した場合、媒体ごとの送客品質、未確定バックログ、確定までの日数、キャンセル理由を測定できます。一方、現在の`auto-ai-blog`が媒体として他社案件を紹介して得た報酬は、このAPIからは取得できません。

## API運用制限

- v3を使用
- 1回の一覧取得は最大10,000件。`offset`でページング
- 同一キーから約300回/分が目安。本実装は既定240回/分
- 日本時間23:30〜翌1:00頃は日次処理のため利用できない場合がある
- 登録IP以外は認証エラー
- 確定済み履歴は91日以内
- 当日確定取消は当日の処理だけ。前日以前は戻せない

## 公式仕様

- https://document.a8.net/a8docs/ecsales-api/ecsales-api-doc.html
- https://document.a8.net/a8docs/ecsales-api/v3/ecsales-api-v3.html
