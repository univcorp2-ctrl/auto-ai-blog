---
title: "Cloudflare Pages × Hugoで高速ブログを作る実践手順: 自動収益メディアの公開基盤を作る"
date: 2026-07-10T09:52:02+09:00
draft: false
tags:
  - "Cloudflare Pages"
  - "Hugo"
  - "静的サイト"
  - "AI"
  - "不動産"
categories:
  - "AI・テック"
description: "!Cloudflare PagesとHugoによる自動ブログ配信の全体像https://image.pollinations.ai/prompt/cloudflare%20pages%20hugo%20static%20site%20automated%20blog%20publishing%20s"
---
![Cloudflare PagesとHugoによる自動ブログ配信の全体像](https://image.pollinations.ai/prompt/cloudflare%20pages%20hugo%20static%20site%20automated%20blog%20publishing%20system%20dashboard?width=800&height=400&nologo=true)

ブログを収益導線にしたいのに、毎回の投稿、サーバー管理、表示速度の改善、デプロイ確認に時間を取られていませんか。

検索流入から商品ページ、資料請求、アフィリエイト、ポイント案件へ読者を送るブログでは、記事を書く時間だけでなく、**公開後に安定して速く配信される仕組み**が収益機会を左右します。表示が遅い、更新が面倒、公開ミスが多い状態では、記事数を増やしても運用が詰まります。

そこで使いやすい構成が、**Cloudflare Pages × Hugo** です。HugoでMarkdown記事を静的HTMLに変換し、Cloudflare PagesからCDN配信します。WordPressのようにアクセスごとにDBからページを組み立てる構成ではないため、ブログ、資料ページ、商品導線ページのような「読み物中心の収益メディア」と相性があります。

この記事では、初心者が手順通りに進められるように、Cloudflare PagesでHugoブログを公開する流れ、失敗しやすい設定、SEO改善、KPI、Hiro環境で確認した実行ログまでまとめます。

収益化に関する内容は一般的な情報提供です。成果や利益を保証するものではありません。

## Cloudflare PagesとHugoの役割

Cloudflare Pagesは、Git連携またはDirect Uploadで静的サイトを公開できるホスティング基盤です。Cloudflare公式のHugoガイドでは、Hugoの `baseURL` をCloudflare Pagesの環境変数 `CF_PAGES_URL` に合わせる例として、次のようなビルドコマンドが紹介されています。

```bash
hugo -b $CF_PAGES_URL
```

出典: [Cloudflare Pages Hugo guide](https://developers.cloudflare.com/pages/framework-guides/deploy-a-hugo-site/)

Hugoは、MarkdownやテンプレートからHTMLを生成する静的サイトジェネレーターです。公式リポジトリでも、Go製の高速な静的サイト生成ツールとして説明されています。

出典: [Hugo GitHub repository](https://github.com/gohugoio/hugo)

全体の流れは次の通りです。

1. Markdownで記事を書く、またはAI生成する
2. HugoでHTML、RSS、sitemap、OGP用ページを生成する
3. GitHubへpushする、またはWranglerで直接アップロードする
4. Cloudflare Pagesが `public` ディレクトリを配信する
5. 読者が検索結果やSNSから記事へ流入する
6. 記事内CTAから `/products/` や案件ページへ進む

この構成の強みは、投稿作業を「人間が管理画面で毎回やる作業」から「ログが残る公開パイプライン」に変えられる点です。

## Hiro検証メモ: このサイトで確認した一次情報

この記事は一般論だけで書いていません。手元の `auto-ai-blog` リポジトリで、次の一次情報を確認しました。

| 確認対象 | 確認できた内容 |
|---|---|
| `README_ja.md` | 「Hugo + PaperMod + Python CLI 自動生成 + GitHub + Cloudflare Pages」で動く日本語ブログ自動運用システムと明記 |
| `.github/workflows/daily-post.yml` | Python 3.12、Hugo `0.163.3`、Node 22をセットアップし、`scripts/deploy_cloudflare_pages.py` を実行 |
| `generator/config.yaml` | 3サイトをCloudflare Pagesへデプロイする設定 |
| `scripts/deploy_cloudflare_pages.py` | `hugo --source <site> --gc --minify` でビルドし、`npx wrangler pages deploy` でPagesへ送信 |
| `generator/logs/generate.log` | 2026-07-10 09:22:13 JSTに `git push succeeded to origin/main` を記録 |

設定されているPagesプロジェクトは次の3つです。

| サイト | source_dir | Pages URL |
|---|---|---|
| AI・テック | `sites/ai-tech` | `https://ai-tech-blog-97e.pages.dev/` |
| ビジネス | `sites/business` | `https://business-blog.pages.dev/` |
| 不動産 | `sites/real-estate` | `https://real-estate-blog.pages.dev/` |

さらに、各サイトの `hugo.toml` には `baseURL` と `theme = 'PaperMod'` が設定されています。つまり、このサイトではCloudflare Pages × Hugoを単なる高速配信ではなく、**複数メディアを自動生成し、GitHub ActionsとWranglerで公開し続ける運用基盤**として使っています。

## なぜ自動収益メディアに向いているのか

### 1. 表示速度がCTA到達率に影響する

静的サイトは、アクセスごとにDBへ問い合わせてHTMLを作る方式ではありません。Hugoが先にHTMLを作り、Cloudflare Pagesが配信します。

読者が「Cloudflare Pages Hugo」「Hugo ブログ 収益化」「静的サイト SEO」のような検索キーワードで訪問したとき、表示が遅いとCTAを見る前に離脱します。逆に、記事本文、比較表、内部リンク、商品導線まで速く表示できれば、収益ページへ進むチャンスを増やせます。

見るべきポイントは「なんとなく速そう」ではなく、次の3つです。

- Search Consoleで対象記事のCTRが上がっているか
- Cloudflare Web Analyticsで流入ページと離脱ページを確認できるか
- `/products/` や案件ページへのクリックが計測できているか

### 2. 保守作業を減らし、記事改善に時間を使える

WordPressは柔軟ですが、プラグイン更新、DB、ログイン管理、表示崩れ対応が発生しやすい構成です。Hugo + Cloudflare Pagesなら、運用の中心は次の3つに寄せられます。

- Markdown記事の生成
- Hugoビルドの検証
- Cloudflare Pagesへのデプロイ

Hiro環境では、`generator/generate.py` が記事生成、レビュー、保存、git commit、pushまで担当します。2026-07-10のログでは、09:22:01に記事保存、09:22:03にNotion保存、09:22:13にGitHubへのpush成功が記録されています。

このようにログが残ると、失敗時に「AI生成で止まったのか」「Hugoビルドで落ちたのか」「Cloudflareへのデプロイで止まったのか」を切り分けられます。

### 3. 複数サイト展開しやすい

![複数HugoサイトをCloudflare Pagesへ配信する構成](https://image.pollinations.ai/prompt/three%20hugo%20static%20sites%20deploying%20to%20cloudflare%20pages%20cdn%20with%20seo%20traffic%20and%20product%20funnels?width=800&height=400&nologo=true)

1つのブログだけで全ジャンルを扱うと、読者の検索意図がぼやけます。Hiro環境のように、AI・テック、ビジネス、不動産でサイトを分けると、キーワード、CTA、商品ページを合わせやすくなります。

例:

| サイト | 狙う検索意図 | CTA例 |
|---|---|---|
| AI・テック | AI活用、業務自動化、ツール比較 | 自動化マニュアル、テンプレート |
| ビジネス | 副業、SNS導線、販売自動化 | 商品一覧、決済導線、実践教材 |
| 不動産 | 賃貸経営、不動産投資、空室対策 | 分析シート、相談導線、資料請求 |

類似記事との差別化は、「Cloudflare Pagesは速い」で止めないことです。記事生成、公開ログ、複数サイト、商品導線、KPIまでつなげて初めて、自動収益メディアの土台になります。

## ステップ・バイ・ステップ: HugoブログをCloudflare Pagesで公開する

### 1. Hugoサイトを作成する

新規サイトなら、まずHugoサイトを作ります。

```bash
hugo new site my-hugo-blog
cd my-hugo-blog
git init
```

テーマにPaperModを使う場合は、submoduleまたは通常のcloneで追加します。Cloudflare PagesやGitHub Actions上でもテーマが取得できるように、READMEやビルドコマンドに取得手順を残してください。

### 2. 記事をMarkdownで追加する

```bash
hugo new content posts/cloudflare-pages-hugo.md
```

front matterには、SEOで使うタイトル、description、タグ、公開状態を入れます。

```yaml
---
title: "Cloudflare PagesとHugoで高速ブログを作る方法"
date: 2026-07-10T09:00:00+09:00
draft: false
tags:
  - "Cloudflare Pages"
  - "Hugo"
  - "静的サイト"
description: "Cloudflare PagesとHugoで高速な静的ブログを作り、自動収益メディアの公開基盤にする手順を解説します。"
---
```

公開記事は `draft: false` にします。`draft: true` のままだと通常ビルドでは公開対象から外れます。

### 3. ローカルでビルドする

```bash
hugo --gc --minify
```

標準では `public` ディレクトリに静的ファイルが出力されます。サブディレクトリ構成の場合は、出力先が `sites/ai-tech/public` のように変わるため、実際に生成された場所を確認してください。

確認コマンド例:

```bash
find . -maxdepth 3 -type d -name public
```

Windows PowerShellなら次のように確認できます。

```powershell
Get-ChildItem -Recurse -Directory -Filter public
```

### 4. Cloudflare Pagesの設定を合わせる

Cloudflare Pagesの設定例です。

| 項目 | 設定例 |
|---|---|
| Framework preset | Hugo |
| Production branch | `main` |
| Build command | `hugo --gc --minify` または `hugo -b $CF_PAGES_URL --gc --minify` |
| Build output directory | `public` |
| Root directory | サイトがリポジトリ直下でなければ対象ディレクトリを指定 |
| Hugo version | 必要に応じて `HUGO_VERSION` を設定 |

CloudflareのBuild configurationでは、Root directoryはリポジトリ内のどこをプロジェクトルートとして扱うかを決める項目です。モノレポや複数Hugoサイト構成では、ここを曖昧にすると `public` の場所を間違えます。

出典: [Cloudflare Pages Build configuration](https://developers.cloudflare.com/pages/configuration/build-configuration/)

### 5. Git連携かWrangler直接デプロイを選ぶ

運用方法は大きく2つあります。

| 方法 | 向いているケース |
|---|---|
| GitHub連携 | 1サイトをシンプルに運用したい |
| Wrangler直接デプロイ | 複数サイトを1つのworkflowでビルドして配信したい |

Wranglerでは次の形式でPagesへアップロードできます。

```bash
npx wrangler pages deploy public --project-name=<PROJECT_NAME>
```

CloudflareのWrangler Pagesコマンドでは、`[DIRECTORY]`、`--project-name`、`--branch` などのオプションが用意されています。

出典: [Wrangler Pages commands](https://developers.cloudflare.com/workers/wrangler/commands/pages/)

Hiro環境では、GitHub Actionsが `scripts/deploy_cloudflare_pages.py` を呼び、各サイトをビルドしてから `npx wrangler pages deploy` でCloudflare Pagesへ送っています。

## SEOを強くする見出し構成

この記事のSEOキーワードは、次のように配置します。

| 場所 | 入れるキーワード |
|---|---|
| H1 | Cloudflare Pages、Hugo、高速ブログ |
| 導入文 | 自動収益メディア、静的サイト、公開基盤 |
| H2 | Cloudflare PagesとHugoの役割、公開手順、失敗対策 |
| H3 | `baseURL`、Build output directory、HUGO_VERSION、Wrangler |
| description | Cloudflare PagesとHugoで高速ブログを作る手順 |

避けたいのは、見出しが「メリット」「手順」「まとめ」だけになる構成です。検索エンジンにも読者にも、何についての手順なのか伝わりません。

改善例:

- 悪い例: `## 手順`
- 良い例: `## ステップ・バイ・ステップ: HugoブログをCloudflare Pagesで公開する`

## 専門家目線のチェックポイント

### Build output directoryを実際の出力先に合わせる

Hugoの標準出力は `public` です。ただし、Hiro環境のように `sites/ai-tech`、`sites/business`、`sites/real-estate` に分かれている場合、出力先は各サイト配下の `public` になります。

チェック方法:

```powershell
Get-ChildItem sites -Recurse -Directory -Filter public
```

Cloudflare PagesでRoot directoryをリポジトリ直下にするなら、Build output directoryは `sites/ai-tech/public` のように指定する必要があります。Root directoryを `sites/ai-tech` にするなら、Build output directoryは `public` です。

### baseURLを本番URLに合わせる

`baseURL` はcanonical URL、RSS、OGP、内部リンクに影響します。Pagesの初期URLで公開したあと独自ドメインへ移行した場合、`hugo.toml` の `baseURL` を更新してください。

確認方法:

1. 公開ページを開く
2. ページソースを表示する
3. `canonical`、`og:url`、RSS内URLを確認する
4. 古い `pages.dev` URLが残っていないか見る

Hiro環境では、2026-07-10時点で次の `baseURL` が設定されています。

```toml
baseURL = 'https://ai-tech-blog-97e.pages.dev/'
baseURL = 'https://business-blog.pages.dev/'
baseURL = 'https://real-estate-blog.pages.dev/'
```

独自ドメインへ切り替えたら、ここは更新対象です。

### Hugo versionを固定する

ローカルでは成功するのにCloudflare PagesやGitHub Actionsで落ちる場合、Hugoのバージョン差が原因になることがあります。

Hiro環境の `.github/workflows/daily-post.yml` では、GitHub Actions上でHugo `0.163.3` を指定しています。

```yaml
- name: Setup Hugo
  uses: peaceiris/actions-hugo@v3
  with:
    hugo-version: '0.163.3'
    extended: true
```

Cloudflare Pages側でビルドする場合も、必要に応じて `HUGO_VERSION` を環境変数で指定します。

### AI生成記事はレビュー工程をログに残す

自動生成記事は量を増やしやすい反面、薄い一般論が増えるリスクがあります。Hiro環境では、ログ上で `draft`、`review`、`final_check` の段階が残ります。

2026-07-10のログ例:

```text
09:12:47 draft: calling codex CLI
09:15:41 draft: codex CLI succeeded
09:15:41 review: calling gemini CLI
09:15:41 review: gemini CLI failed: The command line is too long.
09:15:41 review: calling codex CLI
09:18:55 review: codex CLI succeeded
09:22:01 final_check: codex CLI succeeded
09:22:13 git push succeeded to origin/main
```

このログから、Gemini CLIはコマンド長で失敗したが、Codex CLIに切り替えて公開まで進んだことが分かります。自動化では、成功ログだけでなく失敗ログも資産です。次の改善点を具体化できるからです。

## 画像で説明すべき箇所

![KPIダッシュボードで見る自動収益ブログの改善ポイント](https://image.pollinations.ai/prompt/seo%20analytics%20dashboard%20for%20automated%20hugo%20blog%20cloudflare%20pages%20kpi%20conversion%20funnel?width=800&height=400&nologo=true)

記事内に入れると理解が深まる画像は、次の3つです。

| 画像 | 目的 |
|---|---|
| アーキテクチャ図 | Markdown → Hugo → public → Cloudflare Pages → 読者 → 商品ページの流れを見せる |
| デプロイログ画面 | GitHub ActionsまたはCloudflare Pagesの成功時刻、commit、deploy URLを見せる |
| KPIダッシュボード | Search Console、Cloudflare Analytics、商品ページクリック、成約数をつなげて見せる |

とくに収益メディアでは、デプロイ成功画面だけでは不十分です。検索流入からCTAクリックまで見える図を入れると、読者は「公開して終わりではなく、改善まで回す」と理解できます。

## よくある失敗と対策

### 失敗1: `public` の場所を間違える

症状:

- ビルドは成功している
- しかし公開ページが空
- CSSや画像だけ読み込まれない

対策:

- ローカルで `public` の生成場所を確認する
- Root directoryとBuild output directoryの組み合わせを表にする
- 複数サイト構成では、サイトごとに出力先を固定する

### 失敗2: `baseURL` が古い

症状:

- canonicalが古いURLを指す
- OGP画像やRSSのURLがずれる
- 独自ドメイン移行後も `pages.dev` が残る

対策:

- `hugo.toml` の `baseURL` を本番URLへ更新する
- Preview環境では `hugo -b $CF_PAGES_URL` を検討する
- 公開後にページソースでURLを確認する

### 失敗3: テーマがCIで取得できない

症状:

- ローカルでは表示される
- GitHub ActionsやCloudflare Pagesでテーマが見つからない
- `themes/PaperMod` が空になる

対策:

```bash
git submodule update --init --recursive
```

または、ビルド前にテーマがなければcloneする処理を入れます。Hiro環境のREADMEにも、PaperModが取得できない場合のclone手順が記載されています。

### 失敗4: 記事は増えるが収益導線がない

症状:

- 記事数は増えている
- Search Consoleの表示回数もある
- しかし商品ページへのクリックが少ない

対策:

- 記事末CTAを固定する
- 関連記事から `/products/` へ内部リンクする
- 商品一覧ページにカテゴリ別の導線を作る
- Cloudflare Web Analyticsまたは別の計測でクリックを追う

記事生成を自動化しても、収益導線がなければ単なるコンテンツ倉庫になります。

## 成果を測るKPI

| KPI | 見る理由 | 改善アクション |
|---|---|---|
| インデックス数 | 記事が検索対象に入っているか | sitemap送信、robots確認、Search Console確認 |
| 表示回数 | 検索結果に出ているか | タイトル、H2、導入文のキーワードを調整 |
| CTR | 検索結果でクリックされているか | titleとdescriptionを書き直す |
| 平均掲載順位 | 狙った検索意図に近づいているか | 実行ログ、手順、比較表、失敗例を追加 |
| Cloudflareアクセス数 | 配信後に読まれているか | 人気記事から収益ページへ内部リンク |
| `/products/` クリック数 | 収益導線へ進んだか | CTA位置、文言、商品カテゴリを調整 |
| 成約・申込数 | 事業成果に近い指標 | 記事テーマと商品内容の一致度を見直す |
| 自動実行成功率 | 人間の介在が減っているか | リトライ、ログ、通知、CLIフォールバックを整備 |

数字を書くときは、必ず前提を残してください。

例:

- 対象期間: 2026-07-10から7日間
- 対象サイト: `sites/ai-tech`
- 計測対象: `/products/` クリック
- 公開方式: GitHub Actions + Wrangler Pages deploy
- Hugo version: GitHub Actions上で `0.163.3`

前提がない数字は、改善判断に使いにくくなります。

## 使えないケースと限界

Cloudflare Pages × Hugoは、読み物中心のブログ、LP、ドキュメント、商品一覧ページには向いています。一方で、次の用途では静的サイトだけでは足りない場合があります。

- 会員ごとに表示内容を変えるダッシュボード
- リアルタイム在庫や価格を頻繁に更新するサイト
- 複雑な検索、絞り込み、ログイン機能が中心のサービス
- ユーザー投稿や決済後コンテンツ制御が必要なメディア

その場合は、Cloudflare Workers、D1、KV、外部API、または別のアプリ基盤を組み合わせます。

また、Hugoは高速ですが、テンプレート、shortcode、front matter、テーマ構造に慣れるまで学習コストがあります。初心者がいきなり3サイトを自動運用するより、最初は1サイト、1カテゴリ、10記事で公開から計測まで確認する方が現実的です。

## 読了後すぐにやること

今日やる作業は1つで十分です。既存ブログまたは新規Hugoサイトで、次の項目を表にしてください。

- [ ] Hugoサイトの場所
- [ ] Build command
- [ ] Build output directory
- [ ] Root directory
- [ ] `baseURL`
- [ ] Hugo version
- [ ] テーマ取得方法
- [ ] GitHub連携かWrangler直接デプロイか
- [ ] `/products/` への導線
- [ ] Search ConsoleとAnalyticsの計測有無
- [ ] 失敗時ログの保存場所

この表が埋まらない場合、自動化する前に公開基盤が曖昧です。記事を増やす前に、ビルド、デプロイ、計測の流れを固めてください。

## まとめ: 高速配信を公開パイプラインに変える

Cloudflare Pages × Hugoの価値は、表示速度だけではありません。Markdownで記事を管理し、Hugoで静的HTMLを作り、Cloudflare Pagesで配信することで、ブログ運営を「毎回手作業で投稿する作業」から「ログが残る公開パイプライン」に変えられます。

Hiro環境では、3つのHugoサイト、PaperMod、Python CLI、GitHub Actions、Hugo `0.163.3`、Wrangler Pages deploy、生成ログ、Notion保存、git pushまでが確認できています。この形に近づけるほど、検索流入から商品一覧ページへ読者を送る仕組みを、人間の作業時間に依存しにくくできます。

次の一手は、Hugoサイトを1つ作り、Cloudflare Pagesへ公開し、記事末に `/products/` へのCTAを置き、Search Consoleで計測を始めることです。

## 本気で自動化・不労所得を構築したい方向けの実践マニュアル

ブログを公開するだけでは、収益化まで遠回りです。必要なのは、記事生成、画像作成、レビュー、公開、検索流入、商品導線、決済、納品までを1本の流れにすることです。

Cloudflare Pages、Hugo、AI生成、SNS導線、商品ページを組み合わせて、自分の時間を切り売りしない自動化資産を作りたい方は、次に進んでください。

**本気で自動化・不労所得を構築したい方向けの実践マニュアルはこちらです。**  
[商品一覧ページを見る](/products/)
