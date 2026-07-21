---
title: "Cloudflare Pages＋Hugoでブログ公開を自動化する方法【3サイト・836記事の運用記録を検証】"
date: 2026-07-21T19:51:10+09:00
draft: false
tags:
  - "Cloudflare Pages"
  - "Hugo"
  - "静的サイト"
  - "AI"
  - "不動産"
categories:
  - "AI・テック"
description: "ブログ記事を増やすたびにサーバーへログインしてファイルをアップロードし、公開後に表示崩れを確認する——。この定型作業は、HugoとCloudflare Pagesを組み合わせることで大部分を自動化できます。"
---
ブログ記事を増やすたびにサーバーへログインしてファイルをアップロードし、公開後に表示崩れを確認する——。この定型作業は、HugoとCloudflare Pagesを組み合わせることで大部分を自動化できます。

基本的な仕組みは、記事をGitHubへpushするとCloudflare PagesがHugoを実行し、生成されたHTMLを公開するというものです。

提供されたHiroの運用記録では、次の規模まで拡張されています。

- 運用サイト数：3サイト
- 記事数：合計836記事
- 記録当日のコミット数：22件
- 公開確認：各サイトのURLを3回ずつ計測

ただし、元の記録には計測日時、対象URL、HTTPステータス、応答時間、コミットSHAなどが含まれていません。そのため、この記事では確認できる数値だけを掲載し、表示速度やSEO、収益への効果を推測で補いません。

この記事を読むと、初心者向けの構築手順だけでなく、複数サイトを壊さずに運用する方法、証拠として使えるログの残し方、失敗時の復旧方法、SEOとKPIの設計まで理解できます。

![Cloudflare PagesとHugoによる3サイト自動運用の概念図](https://image.pollinations.ai/prompt/technical%20diagram%20of%20three%20Hugo%20blogs%20deployed%20through%20GitHub%20to%20Cloudflare%20Pages%20CDN%2C%20clean%20Japanese%20web%20infographic%2C%20white%20background%2C%20blue%20and%20orange?width=1200&height=675&nologo=true)

> 上の画像は構成を説明するための概念図であり、実際のCloudflare管理画面や運用実績の証拠ではありません。運用実績は、後述するURL、コミットSHA、Deployment ID、計測結果で検証します。

## 結論：自動化できるのは「公開作業」であり「ブログの成長」ではない

Cloudflare Pages＋Hugoで自動化できるのは、主に次の処理です。

- MarkdownからHTMLを生成する
- Gitへのpushを検知する
- 本番サイトやプレビュー環境へデプロイする
- 同じ手順を複数サイトへ展開する
- 公開結果をスクリプトで検査する

一方、次の仕事は自動化後も残ります。

- キーワードと検索意図の選定
- 事実確認と引用元の検証
- AIが生成した文章の編集
- 内部リンクの設計
- 古くなった情報の更新
- CTAとコンバージョンの改善
- 障害や誤公開への対応

つまり、この構成の価値は「無人で収益が増えること」ではありません。公開処理を標準化し、人間が事実確認や品質判断に集中できることです。

## Cloudflare Pages＋Hugoで何を自動化できるのか

Hugoは、Markdownで書いた記事からHTMLを生成する静的サイトジェネレーターです。WordPressのようにアクセスのたびにデータベースからページを生成するのではなく、公開前にHTMLを作ります。

Cloudflare PagesのGit連携を利用すると、GitHubまたはGitLabのブランチへ変更をpushするたびに、ビルドとデプロイを自動実行できます。Pull Request単位のプレビューURLも利用できます。ただし、フォークされたリポジトリからのPull Requestではプレビューが作成されないなどの制約があります。[Cloudflare PagesのGit連携に関する公式仕様](https://developers.cloudflare.com/pages/configuration/git-integration/)

基本的な公開フローは次のとおりです。

1. Markdownで記事を作成する
2. Hugoでローカルビルドする
3. GitHubへpushする
4. Cloudflare Pagesが変更を検知する
5. Hugoによる本番ビルドを実行する
6. 生成されたHTMLを公開する
7. 公開URLのHTTPステータスや本文を確認する
8. 計測結果とデプロイ情報をログへ残す

![Git pushからCloudflare Pagesで記事が公開されるまでのフロー](https://image.pollinations.ai/prompt/workflow%20diagram%20Markdown%20article%20to%20Hugo%20build%20to%20GitHub%20push%20to%20Cloudflare%20Pages%20deployment%20to%20public%20website%2C%20minimal%20professional%20infographic?width=1200&height=675&nologo=true)

この構成によって公開作業は減らせますが、収益や検索順位まで自動的に伸びるわけではありません。記事品質、独自情報、内部リンク、情報更新、コンバージョン改善は別途必要です。

## この構成が向いている人・向いていない人

### 向いているケース

Cloudflare Pages＋Hugoは、次のようなサイトに向いています。

- 記事、ドキュメント、比較ページが中心
- 更新履歴をGitで管理したい
- 複数サイトへ同じ公開手順を適用したい
- サーバー保守を減らしたい
- 公開前にプレビュー環境で確認したい
- AIで作成した下書きを人間が確認して公開したい
- 過去の状態へ戻せる運用にしたい

### 向いていないケース

次の場合は、WordPress、ECプラットフォーム、ヘッドレスCMSなども比較してください。

- 編集者がGitやMarkdownを使えない
- 会員管理や複雑な権限制御が必要
- 在庫、予約、決済などの動的処理が中心
- 管理画面上で頻繁に記事を修正したい
- プラグインを組み合わせて短期間で機能を追加したい
- 非エンジニアだけで日常運用を完結させたい

Cloudflare Pages Functionsなどを追加すれば動的処理も可能ですが、構成と障害箇所は増えます。静的サイトの利点を保つなら、動的機能は問い合わせフォームや小規模なAPI連携などに限定するのが現実的です。

## 初心者向け：HugoサイトをCloudflare Pagesへ公開する手順

### ステップ1：HugoとGitをインストールする

Windowsでは、HugoをScoopやChocolateyからインストールできます。

```powershell
scoop install hugo
```

または、次のコマンドを使用します。

```powershell
choco install hugo --confirm
```

インストール後、バージョンを確認します。

```powershell
hugo version
git --version
```

ここでエラーになる場合は先へ進まず、HugoとGitの実行ファイルへPATHが通っているか確認してください。

表示されたHugoのバージョンは、後でCloudflare Pagesにも設定するため記録しておきます。

### ステップ2：Hugoサイトを作成する

現在のHugoでは、次のコマンドでプロジェクトを作成できます。

```powershell
hugo new project my-hugo-site
Set-Location my-hugo-site
git init
```

使用中のHugoで `hugo new project` が認識されない場合は、従来のコマンドを使用します。

```powershell
hugo new site my-hugo-site
Set-Location my-hugo-site
git init
```

利用可能なコマンドは、次の方法で確認できます。

```powershell
hugo new --help
```

コマンドの仕様はHugoのバージョンによって変わる可能性があるため、[Hugoの公式CLIリファレンス](https://gohugo.io/commands/hugo_new_project/)も確認してください。

テーマをGit submoduleとして追加します。以下はAnankeを使う例です。

```powershell
git submodule add https://github.com/gohugo-ananke/ananke themes/ananke
Add-Content hugo.toml "theme = 'ananke'"
```

記事を1件作成します。

```powershell
hugo new content posts/first-post.md
```

作成したMarkdownファイルを開き、タイトルと本文を記入します。

Hugoは通常、`draft = true` の記事を本番ビルドに含めません。公開時は次のように変更します。

```toml
draft = false
```

`draft` だけでなく、未来の `date` や `publishDate`、過去の `expiryDate` が原因で記事が公開されないこともあります。

### ステップ3：ローカル環境で表示を確認する

下書きを含めて確認する場合は、次のコマンドを実行します。

```powershell
hugo server -D
```

ターミナルに表示されたローカルURLをブラウザで開き、最低限、次を確認します。

- タイトルと本文が表示される
- 画像が読み込まれる
- メニューから記事へ移動できる
- スマートフォン幅でも横スクロールが発生しない
- 内部リンクが404にならない
- コードブロックや表が崩れていない
- 下書きが意図せず公開対象になっていない

確認後、本番用ビルドを実行します。

```powershell
hugo
```

Hugoの標準的な出力先は `public` です。ただし、`hugo.toml` の `publishDir` で変更できます。

また、Hugoはビルド前に既存の `public` を自動消去しません。以前は公開対象だった記事が下書きや期限切れになっても、古いHTMLが `public` に残る可能性があります。ローカル検証では出力先を消してから再ビルドするか、毎回クリーンな環境でビルドするCIを利用してください。[Hugoのビルド仕様](https://gohugo.io/getting-started/usage/)

### ステップ4：GitHubへpushする

GitHub上で空のリポジトリを作成し、ローカルサイトを登録します。

```powershell
git add .
git commit -m "Initial Hugo site"
git branch -M main
git remote add origin https://github.com/ユーザー名/リポジトリ名.git
git push -u origin main
```

テーマをsubmoduleで管理している場合は、`.gitmodules` がコミットされていることも確認してください。

```powershell
git status
git submodule status
```

`git status` に未コミットの設定ファイルや記事が残っている場合、その内容はCloudflare Pagesへ渡りません。

### ステップ5：Cloudflare PagesとGitHubを接続する

Cloudflareの管理画面でPagesプロジェクトを作成します。

1. 「Workers & Pages」を開く
2. 「Create application」を選択する
3. 「Pages」タブを選択する
4. 既存のGitリポジトリをインポートする
5. GitHubリポジトリを選択する
6. 本番ブランチを `main` にする
7. ビルドコマンドを `hugo` にする
8. ビルド出力ディレクトリを `public` にする
9. 保存してデプロイする

CloudflareのHugo向け公式設定でも、基本値としてビルドコマンド `hugo`、出力先 `public` が案内されています。[Cloudflare PagesのHugo公式ガイド](https://developers.cloudflare.com/pages/framework-guides/deploy-a-hugo-site/)

Hugoのバージョン差によるビルド失敗を避けるため、Cloudflare Pagesの環境変数に `HUGO_VERSION` を設定します。

```text
HUGO_VERSION=ローカル環境と同じバージョン
```

たとえば、ローカルのバージョンが `0.164.0` なら、Cloudflare側にも `0.164.0` を指定します。プレビュー環境を利用する場合は、Preview側にも同じ環境変数を設定してください。

### ステップ6：独自ドメインとbaseURLを確認する

本番ドメインが決まっている場合は、`hugo.toml` に設定します。

```toml
baseURL = "https://example.com/"
```

URLは `https://` から始め、末尾に `/` を付けます。

Cloudflareの公式ガイドでは、デプロイ先URLをHugoへ渡す方法として次のビルドコマンドが案内されています。

```bash
hugo -b "$CF_PAGES_URL"
```

ただし、独自ドメインを使う本番環境でこの設定をそのまま使うと、canonical、OGP、サイトマップが `pages.dev` のURLを指す可能性があります。

本番とプレビューでbaseURLを分ける場合は、たとえばビルドスクリプトで分岐します。

```bash
#!/usr/bin/env bash
set -euo pipefail

if [ "${CF_PAGES_BRANCH:-}" = "main" ]; then
  hugo --baseURL "https://example.com/"
else
  hugo --baseURL "${CF_PAGES_URL}"
fi
```

この場合、Cloudflare Pagesのビルドコマンドをスクリプトの実行に変更します。

```text
bash build.sh
```

本番公開前に、少なくとも次を確認してください。

- canonicalが独自ドメインを指している
- OGPのURLが本番ドメインを指している
- サイトマップにプレビューURLが混入していない
- CSSや画像の絶対URLが正しい
- プレビュー環境が検索結果へ登録されない

### ステップ7：公開結果を機械的に検証する

デプロイ画面に「Success」と表示されただけでは不十分です。ビルドに成功しても、古いページ、誤ったドメイン、404の画像が公開される可能性があるためです。

PowerShellでは、次のように3回計測できます。

```powershell
1..3 | ForEach-Object {
    curl.exe -sS -o NUL `
      -w "status=%{http_code} dns=%{time_namelookup}s connect=%{time_connect}s ttfb=%{time_starttransfer}s total=%{time_total}s`n" `
      https://example.com/
}
```

新しい記事の本文とcanonicalも確認します。

```powershell
$articleUrl = "https://example.com/posts/first-post/"
$html = curl.exe -fsSL $articleUrl

$html | Select-String -SimpleMatch "公開した記事タイトル"
$html | Select-String -Pattern '<link[^>]+rel=["'']canonical["''][^>]*>'
```

確認する項目は次のとおりです。

- `status=200` になっている
- 3回とも接続に成功する
- `total` が極端にばらついていない
- HTML内に新しい記事タイトルがある
- canonicalが本番ドメインを指している
- CSS、JavaScript、画像で404が発生していない
- 公開された内容が意図したコミットと一致している

応答時間は、測定場所、通信回線、DNSキャッシュなどの影響を受けます。1台のPCから3回測った結果だけで、世界中の表示速度を断定してはいけません。

## Hiroの3サイト・836記事の運用ログをどう評価するか

提供された記録から確認できる運用値は次のとおりです。

| 項目 | 記録値 | 評価時の注意 |
|---|---:|---|
| サイト数 | 3 | サイト名とURLは未提示 |
| 記事数 | 合計836記事 | 公開記事だけか、下書きを含むかは未提示 |
| 当日のコミット数 | 22件 | 対象日、対象リポジトリ、変更内容は未提示 |
| 応答計測 | 各URL3回 | 対象URL、HTTPステータス、計測日時、所要時間は未提示 |

この記録から「複数サイトを継続更新している可能性が高い」ことは読み取れます。一方で、証拠が不足しているため、次の結論までは導けません。

- Cloudflare Pagesへの移行で高速化した
- デプロイの失敗率が下がった
- SEO評価が上がった
- 836記事すべてがインデックスされている
- 収益が増えた
- 完全な無人運用を実現した

### 一次情報として保存すべき項目

検証可能な運用記録にするには、毎回次の項目を保存します。

```text
計測日時:
計測元の地域・回線:
サイト名:
公開URL:
Gitリポジトリ:
本番ブランチ:
コミットSHA:
Cloudflare Deployment ID:
Hugoバージョン:
公開記事数:
HTTPステータス:
TTFB:
総応答時間:
新規記事URL:
canonical URL:
目視確認者:
確認結果:
失敗時のエラー:
復旧内容:
```

記事数はファイル数だけでなく、Hugoが公開対象として認識しているページも確認します。

```powershell
hugo list published
```

公開対象の件数だけを集計する場合は、出力形式を確認したうえで次のように数えられます。

```powershell
$published = hugo list published
($published | Select-Object -Skip 1 | Measure-Object).Count
```

当日のコミットは、タイムゾーンを含む日付範囲を明示して集計します。

```powershell
git log `
  --since="2026-07-21 00:00:00 +09:00" `
  --until="2026-07-21 23:59:59 +09:00" `
  --oneline
```

対象コミットを特定するには、SHAも保存します。

```powershell
git rev-parse HEAD
```

このようにURL、日時、コミットSHA、Deployment ID、測定結果を残せば、「作業した」という報告から「第三者が追跡できる運用ログ」へ変わります。

## 3サイトを安全に自動運用する設計

複数サイトを運用するときは、記事生成と本番公開を直接つなげないことが重要です。

推奨フローは次のとおりです。

1. AIまたは人間が下書きを作る
2. `draft = true` で保存する
3. 事実、引用、リンク、重複、表現を検査する
4. プレビューブランチへpushする
5. Cloudflare PagesのプレビューURLで確認する
6. 承認後に `main` へマージする
7. 本番URLを3回確認する
8. コミットSHAとDeployment IDを保存する
9. Search Consoleとアクセス解析で追跡する
10. 失敗時は原因と復旧内容を記録する

サイトごとに、少なくとも次を分離します。

- Gitリポジトリ
- Cloudflare Pagesプロジェクト
- 独自ドメイン
- Search Consoleプロパティ
- サイトマップ
- KPIログ
- 公開承認ルール
- 本番用の環境変数とシークレット

共通テーマや共通スクリプトを使う場合も、1サイトの変更が3サイトすべてへ即時反映されないよう、GitのタグやコミットSHAでバージョンを固定してください。

### ロールバックできる状態を作る

自動公開では、失敗をゼロにすることより、短時間で戻せることが重要です。

最低限、次の情報を残します。

- 正常だった最後のコミットSHA
- 問題が発生したコミットSHA
- 対応するCloudflare Deployment ID
- 発生した症状
- ロールバックまたは修正に使ったコミット

記事単体の誤りなら修正コミットで対応できます。サイト全体が壊れた場合は、正常だったコミットを基準に差分を調査します。

## よくある失敗と復旧方法

| 症状 | 主な原因 | 確認・復旧方法 |
|---|---|---|
| 記事が公開されない | `draft = true`、未来日、期限切れ | front matterと `hugo list published` を確認 |
| Cloudflareでテーマが見つからない | submodule未取得 | `.gitmodules` をコミットし、ローカルで `git submodule update --init --recursive` を実行 |
| ローカルでは成功するが本番で失敗 | Hugoバージョン差 | `hugo version` と `HUGO_VERSION` を一致させる |
| CSSや画像が404になる | `baseURL` または相対パスの誤り | DevToolsのNetworkと生成HTMLを確認 |
| canonicalが `pages.dev` を指す | `CF_PAGES_URL` を本番ビルドにも使用 | 本番とプレビューのbaseURLを分ける |
| 公開URLが古い | 別ブランチや別プロジェクトを確認している | 本番ブランチ、コミットSHA、Deployment IDを照合 |
| 削除した記事が残る | 古い `public` を再利用 | 出力先を消してからクリーンビルド |
| 大量のデプロイが走る | 小さな変更を連続push | コミットをまとめ、プレビュー対象ブランチを制限 |
| 自動生成記事が重複する | テンプレートと検索意図が同じ | 見出し、結論、対象読者、一次情報の重複を検査 |
| 画像表示でレイアウトが動く | 幅・高さ未指定 | 画像寸法またはCSSの `aspect-ratio` を指定 |
| デプロイ成功後に品質事故が起きる | 成功判定がビルド結果だけ | HTTP、本文、canonical、画像、リンクまで検証 |

Cloudflare Pagesでは、プレビューブランチをすべて自動デプロイするか、対象を限定するかを設定できます。大量更新時は、不要なブランチのビルドを止めると運用しやすくなります。[ブランチデプロイ制御の公式仕様](https://developers.cloudflare.com/pages/configuration/branch-build-controls/)

なお、Git連携で作成したPagesプロジェクトは、後からDirect Upload方式へ切り替えられません。自動デプロイを止めてWranglerから手動デプロイすることはできますが、プロジェクト自体の方式は変更できないため、作成前に運用方針を決めてください。

## SEOで確認すべきポイント

静的サイト化しただけではSEO対策は完了しません。各記事で次を確認します。

### 検索意図

- 誰の、どの問題を解決する記事か
- 読者が次に実行すべき操作が明確か
- 一般論ではなく、手順、判断基準、失敗例があるか
- タイトルと本文の結論が一致しているか
- 既存記事にはない一次情報や検証結果があるか

### ページ要素

- titleに主要キーワードを自然に含める
- H1は原則1つにする
- H2で読者の疑問を分解する
- descriptionをページごとに設定する
- canonicalを確認する
- OGP画像と代替テキストを設定する
- 関連記事へ内部リンクを張る
- XMLサイトマップをSearch Consoleへ送信する
- プレビューURLをインデックスさせない
- 変更日だけを機械的に更新しない

### Core Web Vitals

Googleが案内する良好判定の目安は次のとおりです。

- LCP：2.5秒以内
- INP：200ミリ秒未満
- CLS：0.1未満

これらは検索順位を保証する数値ではありません。ユーザー体験を改善するための指標として、Search Consoleの実ユーザーデータとPageSpeed Insightsの診断結果を併用します。[Google Search CentralのCore Web Vitals解説](https://developers.google.com/search/docs/appearance/core-web-vitals)

1回のLighthouse計測は検査時点のラボデータです。実際の利用者の状態を判断するときは、地域、端末、通信環境を含む実ユーザーデータと区別してください。

## 運用KPI：何を毎週確認するか

![Cloudflare PagesとSEOの運用KPIダッシュボード例](https://image.pollinations.ai/prompt/professional%20website%20operations%20dashboard%20showing%20deployment%20success%20rate%2C%20HTTP%20status%2C%20LCP%2C%20INP%2C%20CLS%2C%20indexed%20pages%20and%20conversions%2C%20clean%20Japanese%20UI?width=1200&height=675&nologo=true)

> 上の画像はKPI設計の例を示す概念図です。実際の計測結果ではありません。

初期KPIは、公開、品質、集客、収益の4段階に分けます。

| 分類 | KPI | 初期目標 |
|---|---|---:|
| 公開 | デプロイ成功率 | 99％以上 |
| 公開 | 公開後のHTTP 200率 | 100％ |
| 公開 | 復旧時間 | 障害ごとに記録 |
| 品質 | 壊れた内部リンク | 0件 |
| 品質 | 未確認の自動生成記事 | 0件 |
| 品質 | 出典未確認の数値・引用 | 0件 |
| 表示 | LCP | 2.5秒以内 |
| 表示 | INP | 200ミリ秒未満 |
| 表示 | CLS | 0.1未満 |
| 検索 | 有効なインデックス登録数 | 週次で増減理由を説明できる |
| 検索 | 検索クリック数 | 28日単位で前期間比較 |
| 収益 | CTAクリック率 | ページ種類別に計測 |
| 収益 | コンバージョン率 | 流入キーワード別に計測 |

デプロイ成功率99％などは公式基準ではなく、運用を始めるための内部目標です。実績が蓄積したら、サイトの更新頻度と重要度に合わせて調整してください。

記事数だけをKPIにすると、検索意図が重複したページや、更新されないページが増えます。「何記事公開したか」よりも、「何ページが読まれ、次の行動につながったか」を重視します。

## AIスロップを防ぐための公開前監査

AIが生成した記事は、文章が整っていても、一次情報、固有の経験、検証可能な証拠が不足しがちです。公開前に次の10項目を1点ずつ確認します。

| 項目 | 合格条件 |
|---|---|
| 1. 対象読者 | 誰の、どの課題を解決するか明記されている |
| 2. 一次情報 | 公式ドキュメント、実測値、操作ログのいずれかがある |
| 3. 再現性 | 読者が実行できるコマンドや手順がある |
| 4. 視覚証拠 | 実画面、ログ、計測表などが概念図と区別されている |
| 5. 数値の根拠 | 数値ごとに対象、日時、条件、出典がある |
| 6. 限界 | 分からないこと、断定できないことが明記されている |
| 7. 失敗例 | 正常系だけでなく、失敗原因と復旧方法がある |
| 8. 差別化 | 実務上の判断基準や独自の検証方法がある |
| 9. 次の行動 | 初心者が次に実行する作業が分かる |
| 10. 更新可能性 | 情報が変わったときに確認すべき公式ページが分かる |

公開基準は8点以上とし、次の項目は合計点にかかわらず必須とします。

- 存在しない引用や実績がない
- 推測を実測値のように書いていない
- 生成画像を実際の証拠として扱っていない
- 読者が損失を受ける可能性のある操作に注意事項がある

この記事は公式資料、再現可能なコマンド、失敗例、限界、次の行動を含んでいます。一方、Hiroの運用記録については対象URLや実測ログがないため、ケーススタディ部分の証拠強度は限定的です。実際のスクリーンショットや匿名化したデプロイログを追加できれば、さらに信頼性を高められます。

## 「無人で育つ収益資産」という表現の限界

Cloudflare PagesとHugoで無人化できるのは、主にビルドと公開です。

次の仕事は自動化後も残ります。

- 情報が古くなっていないか確認する
- AIの誤情報や存在しない引用を検査する
- 検索順位が落ちたページを改善する
- 類似記事を統合する
- 商品情報や価格を更新する
- 問い合わせや法的要請へ対応する
- GitHubやCloudflareの権限を管理する
- 依存するテーマやビルド環境を更新する

また、GitHubへ誤った変更がpushされれば、その変更も自動公開されます。自動化は確認作業を不要にする仕組みではなく、確認地点と責任範囲を明確にする仕組みです。

現実的には「完全無人」ではなく、次の状態を目指します。

> 通常のビルドと公開は自動化し、異常対応と品質判断だけを人間が処理する。

これなら公開作業を減らしながら、誤情報やサイト全体の破損を防げます。

## まず1サイトで試し、公開ログを残そう

最初から3サイトを自動化する必要はありません。まず1サイトで、次の順番を完了させてください。

1. Hugoをインストールしてバージョンを記録する
2. Hugoで1記事を作る
3. ローカルで本番ビルドする
4. GitHubへpushする
5. Cloudflare Pagesへ公開する
6. 公開URLを3回計測する
7. 本文とcanonicalを確認する
8. コミットSHAとDeployment IDを記録する
9. Search Consoleへサイトマップを送信する
10. 1週間後にインデックス、クリック、CTAを確認する

最初の目標は「記事を大量に作ること」ではありません。1記事について、作成、レビュー、公開、検証、記録、修正までを再現できる状態にすることです。

この一連の作業を安定して再現できてから、2サイト目、3サイト目へ展開します。

Hiroの記録にある「3サイト・836記事・22コミット」は運用規模を示す材料です。しかし、本当に差別化になるのは記事数ではありません。公開URL、コミット、計測値、失敗履歴、改善後のKPIまで追跡できることです。

ブログ自動化に使える構成例や運用ツールは、[プロダクト一覧](/products/)から確認できます。
