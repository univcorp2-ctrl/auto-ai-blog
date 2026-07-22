---
title: "Cloudflare Pages×Hugo完全ガイド｜公開を自動化し、高速・低保守のブログ資産をつくる"
date: 2026-07-22T15:54:59+09:00
draft: false
tags:
  - "Cloudflare Pages"
  - "Hugo"
  - "静的サイト"
  - "AI"
  - "不動産"
categories:
  - "AI・テック"
description: "!Cloudflare PagesとHugoによる自動ブログ配信https://image.pollinations.ai/prompt/Cloudflare%20Pages%20Hugo%20automated%20blog%20global%20CDN%20clean%20technical%2"
---
![Cloudflare PagesとHugoによる自動ブログ配信](https://image.pollinations.ai/prompt/Cloudflare%20Pages%20Hugo%20automated%20blog%20global%20CDN%20clean%20technical%20illustration?width=800&height=400&nologo=true)

*概念図です。Cloudflare Pagesの実際の管理画面ではありません。*

「ブログを増やしたいが、サーバー管理や記事公開に時間を取られたくない」「アクセスが増えたときの表示速度や費用が心配」という悩みは、収益化を目指すサイト運営で繰り返し発生します。

記事を書くたびに管理画面へログインし、画像を登録して公開ボタンを押していると、記事数に比例して作業時間が増えます。自分が動き続けなければ止まる運用は、自動化された資産とは呼べません。

そこで相性がよいのが、**Hugoで静的サイトを生成し、Cloudflare Pagesで配信する構成**です。静的サイトとは、アクセスのたびにデータベースからページを組み立てるのではなく、あらかじめ生成したHTMLを配るサイトです。たとえば、完成済みの`index.html`をそのまま読者へ返します。

この記事では、HugoブログをCloudflare Pagesへ接続する手順に加え、筆者（Hiro）が運用する`auto-ai-blog`の実測結果、失敗ログ、公開判定基準、KPI、収益導線まで紹介します。読了後には、Gitへ記事を追加すると、検査・ビルド・公開確認まで進む仕組みを設計できるようになります。

> 本記事は一般的な技術情報です。サイトのアクセス数、広告収入、アフィリエイト成果などを保証するものではありません。料金やサービス制限は変更される可能性があるため、導入時には公式ドキュメントも確認してください。

## Cloudflare PagesとHugoの全体像

Hugoは、Markdownで書いた記事をHTMLへ変換する静的サイトジェネレーターです。Markdownとは、`## 見出し`や`**強調**`のような簡単な記法で文章を構造化できる形式です。

Cloudflare Pagesは、生成されたHTML、CSS、画像などをCloudflareのネットワークから配信するサービスです。GitHubまたはGitLabと接続すると、ブランチへのプッシュを検知し、ビルドとデプロイを自動実行できます。

[CloudflareのHugo公式ガイド](https://developers.cloudflare.com/pages/framework-guides/deploy-a-hugo-site/)では、標準的な設定としてビルドコマンド`hugo`、出力先`public`が案内されています。

処理の流れは次のとおりです。

```text
記事テーマ・一次情報
        ↓
Markdown記事を作成
        ↓
品質検査・Hugoビルド
        ↓
GitHubへコミット・プッシュ
        ↓
Cloudflare Pagesが変更を検知
        ↓
HugoがHTMLを生成
        ↓
プレビュー環境で検査
        ↓
Cloudflareのネットワークから本番公開
        ↓
検索流入・商品ページ・成果計測
```

この構成では、人間の役割を「毎回の公開作業」から「テーマ選定、一次情報の追加、品質基準の設計、例外への対応」へ移せます。記事生成、テスト、公開、リンク確認を連結できれば、手作業を減らしながら更新を続けられるメディアへ近づきます。

![記事生成からGitHubとCloudflare Pagesを経て公開される流れ](https://image.pollinations.ai/prompt/automated%20content%20pipeline%20Markdown%20GitHub%20Hugo%20Cloudflare%20Pages%20SEO%20revenue%20diagram?width=800&height=400&nologo=true)

*概念図です。実際のデプロイ結果や収益を示すものではありません。*

## Cloudflare PagesでHugoブログを配信するメリット

### 1. 閲覧時にデータベース処理を待たなくてよい

WordPressなどの動的CMSでは、アクセスを受けてからPHPやデータベースがページを組み立てる場合があります。Hugoは公開前にHTMLを生成するため、閲覧時の処理を単純化できます。

ただし、「Hugoなら必ず何秒で表示される」とは断定できません。画像容量、外部広告、アクセス解析タグ、Webフォント、読者の回線も表示速度を左右します。静的化は高速化に有利な土台ですが、画像やJavaScriptの最適化は別途必要です。

### 2. 世界各地へ配信しやすい

Cloudflare Pagesでは、サイトのファイルがCloudflareの分散ネットワークから配信されます。読者から遠い単一サーバーへ毎回アクセスする構成と比べ、遅延を抑えやすくなります。

ただし、キャッシュの有無をサービス名だけで決めつけてはいけません。次のコマンドでレスポンスヘッダーを確認し、実際の配信状態を判断してください。

```powershell
curl.exe -I https://example.com/
```

確認候補は`CF-Cache-Status`、`Cache-Control`、`Age`、`Server`です。キャッシュ動作はファイル種別、レスポンスヘッダー、Cache Rulesなどによって変わります。[Cloudflareのキャッシュ解説](https://developers.cloudflare.com/cache/get-started/)も参照してください。

### 3. Gitへの保存と公開を同じ流れにできる

記事をMarkdownファイルとしてGit管理すると、誰が、いつ、何を変更したかを追跡できます。誤った商品リンクを公開した場合も、変更履歴から原因と影響範囲を調査できます。

Cloudflare PagesのGit連携では、プッシュごとの自動デプロイ、ブランチ別プレビュー、Git上でのデプロイ状況確認を利用できます。[Git連携の公式説明](https://developers.cloudflare.com/pages/configuration/git-integration/)によると、GitHubとGitLabが対応対象です。

### 4. 静的配信の費用を予測しやすい

2026年7月22日に確認した[Cloudflare Pagesの料金説明](https://developers.cloudflare.com/pages/functions/pricing/)では、Functionsを呼び出さない静的アセットへのリクエストは、Free・有料プランともに無料かつ無制限とされています。

これは「Cloudflare Pagesのすべての機能が無制限」という意味ではありません。同日に確認した[Pagesの制限](https://developers.cloudflare.com/pages/platform/limits/)では、Freeプランに次の条件があります。

| 項目 | Freeプランの上限 |
|---|---:|
| Gitビルド | 月500回 |
| 同時ビルド | 1回 |
| 1回のビルド時間 | 20分でタイムアウト |
| 1サイトのファイル数 | 20,000ファイル |
| 単一アセット | 25MiB |
| Pagesプロジェクト数 | 1アカウント100件 |

毎日1回更新する1サイトなら、31日ある月でも単純計算では31ビルドです。ただし、細かな修正を何度もプッシュする運用や、同じモノレポに接続した複数サイトが一斉にビルドされる設定では、消費回数が増えます。

### 5. 公開前にプレビューできる

Cloudflare Pagesは、本番ブランチへ統合する前にプレビューURLを生成できます。商品リンク、画像、表、スマートフォン表示を確認してから公開できるため、自動運用にも品質ゲートを設けられます。

[プレビュー配信の公式説明](https://developers.cloudflare.com/pages/configuration/preview-deployments/)によると、プレビューデプロイには既定で`X-Robots-Tag: noindex`が付与されます。検索エンジンに本番ページとプレビューの重複ページを登録させないための仕組みです。

次のコマンドで実際のヘッダーを確認できます。

```powershell
curl.exe -I https://PREVIEW_HASH.example.pages.dev/
```

出力に次の行が含まれていることを確認します。

```text
x-robots-tag: noindex
```

## Hiroのサイトで確認した実測データ

2026年7月22日、筆者の`auto-ai-blog`リポジトリで、Hugo Extended `v0.163.3`を使い、次のコマンド相当でメモリ内ビルドを実行しました。

```powershell
hugo --source sites/ai-tech --renderToMemory --minify
```

測定環境はWindows amd64、Google Drive配下の作業フォルダです。各サイト1回のみの測定であり、Cloudflare側のビルド時間ではありません。

| サイト | Markdown記事数 | Hugo生成ページ数 | Hugo表示の処理時間 |
|---|---:|---:|---:|
| AI・テック | 357本 | 585ページ | 4,546ms |
| ビジネス | 404本 | 962ページ | 3,797ms |
| 不動産 | 135本 | 253ページ | 1,547ms |

「生成ページ数」には記事だけでなく、一覧、ページ送り、分類ページ、エイリアスなどが含まれます。そのため、Markdown記事数とは一致しません。

同じ端末から各本番トップページへ`curl`で3回アクセスした結果は次のとおりでした。TTFBは、リクエスト開始から最初の応答データを受け取るまでの時間です。

| URL | 3回のTTFB | HTML転送量 |
|---|---|---:|
| `ai-tech-blog-97e.pages.dev` | 359ms、56ms、96ms | 51,967 bytes |
| `business-blog.pages.dev` | 348ms、54ms、88ms | 59,855 bytes |
| `real-estate-blog.pages.dev` | 92ms、57ms、55ms | 68,616 bytes |

全リクエストはHTTP 200で、`Server: cloudflare`を確認しました。

TTFBは、次のようなコマンドで再測定できます。

```powershell
1..3 | ForEach-Object {
    curl.exe -sS -o NUL `
      -w "status=%{http_code} ttfb=%{time_starttransfer}s total=%{time_total}s size=%{size_download}bytes`n" `
      https://ai-tech-blog-97e.pages.dev/
}
```

ただし、これは単一地点・各3回の簡易測定です。初回が遅い理由をキャッシュだけに帰属することはできません。DNS名前解決、TCP・TLS接続、回線状態、測定地点なども影響します。継続評価には、Cloudflare Web AnalyticsやSearch Consoleなどの実ユーザーデータも利用します。

この実測値と測定条件を掲載している点が、設定値だけを並べた記事との違いです。さらにビルド時には、PaperMod内の非推奨プロパティと`desktop.ini`に関する警告も検出されました。ビルドの終了コードが0でも、警告を放置すると、将来のHugo更新で互換性問題が発生する可能性があります。

## ステップ・バイ・ステップで構築する

### 1. Hugoをインストールする

Windowsでは、Hugo Extendedをインストールしてバージョンを確認します。

```powershell
winget install Hugo.Hugo.Extended
hugo version
```

このインストール方法は[HugoのWindows公式ガイド](https://gohugo.io/installation/windows/)にも掲載されています。

Sass処理などを使うテーマではExtended版が必要になる場合があります。ローカルとCloudflare PagesでHugoのバージョンをそろえてください。

### 2. Hugoサイトを作成する

```powershell
hugo new site my-blog
cd my-blog
git init
```

続いてテーマを追加します。PaperModをGit submoduleとして追加する例は次のとおりです。

```powershell
git submodule add https://github.com/adityatelange/hugo-PaperMod.git themes/PaperMod
git submodule update --init --recursive
```

`.gitmodules`もコミット対象に含め、外部から取得できるURLになっていることを確認します。ローカルではテーマが存在していても、リポジトリに設定が保存されていなければ、Cloudflare側でテーマを取得できません。

`hugo.toml`には最低限、URL、言語、タイトル、テーマを設定します。

```toml
baseURL = "https://example.com/"
languageCode = "ja-JP"
title = "自動化ブログ"
theme = "PaperMod"
```

### 3. 最初の記事を作る

```powershell
hugo new content posts/cloudflare-pages-hugo.md
```

front matterに`draft: true`が残っている記事は、通常の本番ビルドでは公開されません。公開時には日付、タイトル、description、canonical URLも確認します。

### 4. ローカルでビルドする

```powershell
hugo server -D
hugo --gc --minify
```

`hugo server -D`は下書きを含む確認用です。公開用コマンドとは条件が異なるため、最後に`hugo --gc --minify`でもエラーが出ないか確認します。生成先は既定で`public`です。

自動化では、終了コードが0かどうかも判定してください。

```powershell
hugo --gc --minify

if ($LASTEXITCODE -ne 0) {
    throw "Hugo build failed. Exit code: $LASTEXITCODE"
}
```

### 5. GitHubへプッシュする

```powershell
git add .
git commit -m "Initial Hugo blog"
git branch -M main
git remote add origin https://github.com/USER/REPOSITORY.git
git push -u origin main
```

APIキーや管理用トークンをリポジトリへ含めないでください。静的サイトのJavaScriptへ秘密情報を埋め込むと、ブラウザから閲覧できてしまいます。

プッシュ前に最低限、次も確認します。

```powershell
git status
git diff --cached
```

### 6. Cloudflare Pagesと接続する

Cloudflareダッシュボードの「Workers & Pages」からGitリポジトリを接続し、次の値を設定します。

| 設定項目 | 値 |
|---|---|
| Production branch | `main` |
| Build command | `hugo --gc --minify` |
| Build output directory | `public` |
| 環境変数 | `HUGO_VERSION=0.163.3`など、ローカルと同じ版 |

`HUGO_VERSION`には、`hugo version`で確認したバージョンに対応する値を設定します。プレビュー環境を使う場合は、Preview側にも同じ環境変数が設定されているか確認してください。

サイトがサブディレクトリにある場合は、Root directoryまたはビルドコマンド、出力パスを実際の構成に合わせます。たとえば`sites/ai-tech`がHugoサイトのルートなら、次のどちらかで設計します。

- Root directoryを`sites/ai-tech`にして、ビルドコマンドを`hugo --gc --minify`にする
- リポジトリ直下から`hugo --source sites/ai-tech --gc --minify`を実行し、出力先も構成に合わせる

モノレポでは、関係のない変更によるビルドを減らすため、[Build watch paths](https://developers.cloudflare.com/pages/configuration/build-watch-paths/)も設定します。

### 7. 独自ドメインとURLを確認する

独自ドメインを設定したら、次を確認します。

```powershell
curl.exe -I https://example.com/
```

チェック対象は次のとおりです。

- HTTPステータスが200か
- HTTPSで配信されているか
- `content-type`が意図した値か
- 不要なリダイレクトがないか
- canonical URLが本番ドメインを指しているか
- プレビュー環境に`X-Robots-Tag: noindex`があるか

本文内のcanonicalは、次のように取得して確認できます。

```powershell
$response = Invoke-WebRequest -Uri "https://example.com/"
$response.StatusCode
$response.Content | Select-String -Pattern '<link[^>]+rel="canonical"[^>]*>'
```

PagesのプレビューURLを`baseURL`へ固定すると、本番canonicalが誤る場合があります。環境ごとにURLを変える場合は、Cloudflare公式ガイドで案内されている`CF_PAGES_URL`とHugoの`--baseURL`オプションも検討してください。

### 8. 記事生成と公開を自動化する

Windowsタスクスケジューラ、GitHub Actions、クラウドVMなどから、次の処理を順番に実行します。

1. トピックと検索意図を選ぶ
2. Markdown記事を生成する
3. 一次情報、出典、画像、CTAを検査する
4. Hugoビルドを実行する
5. 内部リンクと商品リンクを検査する
6. Gitへコミット・プッシュする
7. 対象コミットのデプロイ成功を確認する
8. 本番URLがHTTP 200になるまで監視する
9. canonicalや主要CTAが本番HTMLに存在することを確認する
10. 失敗時に再試行または通知する

筆者の実行ログでは、2026年7月22日15時27分に本記事のトピックが選ばれた後、15時32分に記事生成CLIが240秒でタイムアウトし、生成がスキップされました。その前の15時15分と15時22分には、`git push succeeded to origin/main`が記録されています。

このログが示すのは、「スケジュール登録＝完全自動化の完成」ではないということです。タイムアウト、認証切れ、品質検査失敗を検知し、再試行または通知する設計まで必要です。

また、`git push succeeded`はデプロイ完了の証拠ではありません。ローカルログだけでは、Cloudflare Pagesでのビルド成功や本番反映まで証明できないため、対象コミットに対応するデプロイ結果と本番URLの確認を追加します。

## 公開完了の判定基準を決める

自動化では、「コマンドを実行した」ではなく「何を満たせば公開成功か」を定義します。

実務上のDefinition of Doneは、次のように設定できます。

| 判定項目 | 合格条件 |
|---|---|
| Markdown検査 | 構文エラー、必須項目の欠落がない |
| Hugoビルド | 終了コード0 |
| ビルド警告 | 新規警告0、または許容リスト内 |
| Git | 対象コミットがリモートへ存在する |
| Pages | 対象コミットのデプロイが成功 |
| 本番URL | HTTP 200 |
| canonical | 本番ドメインと一致 |
| CTA | 本番HTMLに主要リンクが存在 |
| 外部リンク | 必須リンクが有効 |
| プレビュー | `X-Robots-Tag: noindex`を確認 |
| 記録 | コミットID、デプロイ時刻、URLをログへ保存 |

「Pagesのデプロイ成功」と「本番HTMLの確認」を分けるのが重要です。デプロイ画面が成功でも、誤った出力ディレクトリやcanonical、欠落したCTAまでは検知できないからです。

## 専門家目線のチェックポイント

- **Hugoのバージョンを固定する**  
  ローカルでは成功し、Pagesでは失敗する場合、最初にバージョン差を確認します。

- **テーマの取得方法を確認する**  
  Git submoduleの設定漏れや取得できないURLは、テーマが見つからないビルドエラーにつながります。

- **ビルド時間と閲覧速度を分けて測る**  
  Hugoの処理時間が短くても、大画像や広告スクリプトがあれば閲覧は遅くなります。

- **警告を成功扱いで捨てない**  
  非推奨APIの警告は、Hugoや依存テーマを更新する判断材料です。

- **収益リンクを自動検査する**  
  CTAが消えていないか、リンク先が有効か、計測パラメータが残っているかをテストします。

- **生成本数より公開成功率を見る**  
  品質検査に落ちた記事やデプロイに失敗した記事は、収益資産として稼働していません。

- **計測値と測定条件を一緒に保存する**  
  数値だけでは比較できません。日時、地点、回数、URL、コマンド、Hugoバージョンも残します。

- **生成AIの画像と実画面の証拠を区別する**  
  概念図は理解を助けますが、デプロイ成功や表示速度の証拠にはなりません。

## 画像で説明すべき箇所と視覚的証拠

![Cloudflare Pagesのデプロイ履歴とWebパフォーマンスKPI画面](https://image.pollinations.ai/prompt/Cloudflare%20Pages%20deployment%20history%20and%20web%20analytics%20KPI%20dashboard%20screenshot%20style?width=800&height=400&nologo=true)

*AI生成の概念画像です。実在するデプロイ履歴やWeb Analyticsの測定結果ではありません。*

実務資料へ追加するなら、次の3点を1枚の図解にすると理解が深まります。

- 左側：Markdown生成、品質検査、Gitへのプッシュ
- 中央：Cloudflare Pagesのビルド履歴とコミットID
- 右側：本番URL、LCP、INP、CLS、CTAクリック数

視覚的証拠として使えるのは、AI生成画像ではなく、実際のCloudflare Pagesのデプロイ画面や計測画面です。撮影時は、**コミットID、ビルド時刻、本番URL**が同時に分かる状態にします。

一方で、アカウントID、メールアドレス、APIトークン、非公開リポジトリ名などは必ず隠してください。スクリーンショットだけでなく、再現用コマンドや測定条件も併記すると、第三者が検証しやすくなります。

## よくある失敗と対策

| 症状 | 原因候補 | 対策 |
|---|---|---|
| デザインが表示されない | テーマ未取得 | submoduleを初期化し、ビルドログを確認 |
| 記事が公開されない | `draft: true`または未来日 | front matterとタイムゾーンを確認 |
| CSSやリンクが別URLを向く | `baseURL`の誤り | 本番ドメインまたは環境変数を設定 |
| Pagesだけビルドに失敗する | Hugoのバージョン差 | `HUGO_VERSION`を固定 |
| 更新のたびに不要なビルドが走る | モノレポの監視範囲が広すぎる | Branch controlとBuild watch pathsを設定 |
| 検索結果に重複ページが出る | プレビューや旧URLの扱いが不適切 | `noindex`、canonical、301を確認 |
| 自動投稿が止まる | CLIタイムアウト、認証切れ | 再試行、通知、失敗ログを実装 |
| プッシュ成功後も記事が見えない | デプロイ失敗、出力先の誤り、キャッシュ | 対象コミットと本番HTMLを照合 |
| 表示は速いが成果が出ない | 検索意図やCTAが弱い | クエリ別CTRと商品ページ遷移率を改善 |

会員サイト、在庫が頻繁に変わるEC、ユーザーごとに内容が変わるダッシュボードでは、Hugoだけでは機能不足です。

Pages Functionsや外部APIを組み合わせると動的機能を追加できますが、実行回数、認証、キャッシュ、データ整合性、障害時の挙動を管理する必要があります。更新頻度が高いデータをすべて静的ビルドへ載せる構成も、ビルド時間やファイル数の上限に近づきやすくなります。

## 成果を測るKPI

| KPI | 見る理由 | 判断例 |
|---|---|---|
| デプロイ成功率 | 無人公開が成立しているか | 成功数÷全デプロイ数 |
| プッシュからHTTP 200までの時間 | 公開待ち時間を把握する | コミット時刻と本番確認時刻の差 |
| TTFB | 初期応答の遅延を確認する | 地域・端末別に継続測定 |
| LCP | 主な内容の表示速度を確認する | 75パーセンタイルで2.5秒以下 |
| INP | 操作への反応を確認する | 75パーセンタイルで200ms以下 |
| CLS | 表示のずれを確認する | 75パーセンタイルで0.1以下 |
| 自然検索クリック数 | SEO流入の増減を確認する | Search Consoleでクエリ別に比較 |
| CTAクリック率 | 記事から商品への移動を確認する | CTAクリック数÷記事閲覧数 |
| 商品ページ到達後の成果率 | 導線の質を判断する | 成果数÷商品ページ訪問数 |
| 記事1本当たりの保守時間 | 自動化の効果を確認する | 月間作業時間÷公開本数 |
| 警告件数 | 将来の破損リスクを把握する | ビルドごとの新規警告数 |
| リンク切れ率 | 収益導線の健全性を確認する | リンク切れ数÷検査対象数 |

Core Web Vitalsの基準値は、[web.devの現行ガイド](https://web.dev/articles/vitals?hl=en)に基づきます。

ただし、速度だけを改善しても検索流入や収益が伸びるとは限りません。SEOでは、一次情報、検索意図との一致、独自データ、内部リンク、更新日も併せて評価してください。

## まとめ｜今日着手するアクション

Cloudflare PagesとHugoを組み合わせると、静的サイトの高速配信、Gitベースの変更管理、プレビュー、公開自動化を一つの流れにできます。

そこへ記事生成、品質検査、リンク確認、デプロイ確認、KPI計測を接続すれば、人間が毎回公開ボタンを押さなくても更新できるメディア運用へ近づきます。

今日の具体的なアクションは、手元のHugoサイトで次のコマンドを実行し、**処理時間、生成ページ数、警告内容、Hugoバージョン**を記録することです。

```powershell
hugo version
hugo --renderToMemory --minify
```

次にGitHubへテストブランチをプッシュし、Pagesのプレビューで次を確認してください。

- 画像が表示される
- canonicalが意図したURLを指す
- CTAが存在する
- HTTPステータスが200になる
- `X-Robots-Tag: noindex`が付いている
- 対象コミットとデプロイ履歴が一致する

この小さな一周が、自動化されたブログ資産の最初の稼働テストになります。

収益は配信基盤だけでは生まれません。読者の課題を解決する記事、検証可能な一次情報、適切な商品、壊れない導線がそろって初めて成果へつながります。

月に一度はログとKPIを確認し、完全放置ではなく、**少ない保守時間で安定して回り続ける仕組み**を目指してください。

## 記事生成から収益計測まで一本化したい方へ

「Hugoを公開できた」で止まらず、記事生成、品質判定、Git連携、障害時の再試行、商品導線、成果計測まで一本につなげるには、実装順序と公開判定基準が必要です。

試行錯誤を毎回ゼロから繰り返すのではなく、検証可能な作業手順を使い、手作業を減らしながらコンテンツが蓄積される仕組みへ時間を投じてください。

**自動化ブログ、AI活用、ポイント・アフィリエイト導線などを実装レベルで学べる実践マニュアルは、[商品一覧ページ](/products/)で確認できます。**

収益を保証する教材ではありませんが、自分の作業時間だけに依存しないデジタル資産を組み立てたい方は、現在の環境と課題に合うマニュアルから次の一歩を選んでください。
