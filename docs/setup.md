# セットアップ手順

## 1. ローカル配置

```powershell
cd G:\マイドライブ\AI_Agents\github\repos
git clone --recursive <YOUR_REPOSITORY_URL> auto-ai-blog
cd auto-ai-blog
```

`--recursive` を忘れた場合:

```powershell
git submodule update --init --recursive
```

PaperMod が取得できない場合:

```powershell
git clone --depth=1 https://github.com/adityatelange/hugo-PaperMod.git hugo-site/themes/PaperMod
```

## 2. Hugo Extended

```powershell
winget install Hugo.Hugo.Extended
hugo version
```

## 3. Python

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## 4. AI CLI

```powershell
claude -p "テスト"
gemini -p "テスト"
codex -q "テスト"
```

## 5. 手動実行

```powershell
.\run_daily.bat
```

## 6. タスクスケジューラ

```powershell
$action = New-ScheduledTaskAction -Execute "G:\マイドライブ\AI_Agents\github\repos\auto-ai-blog\run_daily.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At 9:00am
Register-ScheduledTask -TaskName "auto-ai-blog" -Action $action -Trigger $trigger
```

## 7. Cloudflare Pages

1. Cloudflare Dashboard にログイン
2. Workers & Pages を開く
3. Create application を選択
4. Pages タブで Connect to Git を選択
5. GitHub リポジトリ `auto-ai-blog` を選択
6. Production branch を `main` に設定
7. Framework preset を `Hugo` に設定
8. Build command を以下に設定

```bash
cd hugo-site && git submodule update --init --recursive || true; if [ ! -d themes/PaperMod ]; then git clone --depth=1 https://github.com/adityatelange/hugo-PaperMod.git themes/PaperMod; fi; hugo --gc --minify
```

9. Build output directory を以下に設定

```text
hugo-site/public
```

10. Deploy を押す

## 8. baseURL の変更

Cloudflare Pages の URL が決まったら `hugo-site/config.toml` の `baseURL` を変更します。

```toml
baseURL = "https://your-domain.pages.dev"
```
