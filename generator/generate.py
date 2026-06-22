import os
import yaml
import subprocess
import datetime
import random
import re
from slugify import slugify
import prompts

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATOR_DIR = os.path.join(BASE_DIR, "generator")

with open(os.path.join(GENERATOR_DIR, "config.yaml"), "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

with open(os.path.join(GENERATOR_DIR, "topics.yaml"), "r", encoding="utf-8") as f:
    topics_data = yaml.safe_load(f)

def run_cli(cmd_list):
    try:
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8"
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"CLI Error running {' '.join(cmd_list)}: {e.stderr}")
        return None

def generate_article(topic_info):
    topic = topic_info["topic"]
    keywords = ", ".join(topic_info["keywords"])
    
    # Windows compatibility for npm binaries
    claude_cmd = "claude.cmd" if os.name == "nt" else "claude"
    gemini_cmd = "gemini.cmd" if os.name == "nt" else "gemini"
    codex_cmd = "codex.cmd" if os.name == "nt" else "codex"

    # Step 1: Claude
    print(f"Step 1: Generating draft with Claude for '{topic}'")
    prompt1 = prompts.STEP1_CLAUDE_PROMPT.format(topic=topic, keywords=keywords)
    draft = run_cli([claude_cmd, "-p", prompt1])
    
    if not draft:
        print("Claude failed, falling back to Gemini for draft...")
        draft = run_cli([gemini_cmd, "--prompt", prompt1])
    
    if not draft:
        print("Both Claude and Gemini failed to create a draft. Using fallback.")
        return f"""# {topic}

## はじめに
本記事では、「{topic}」について詳しく解説します。
キーワード: {keywords}

## 本論1
（※この記事はAI CLIのフォールバックとして自動生成されたモック記事です。実際の運用環境でClaudeやGemini CLIが正常に動作するようになると、ここに詳細なAI生成コンテンツが入ります。）

## 本論2
自動化とAI導入は、現代のビジネスにおいて不可欠な要素です。
適切なツールを選定し、ワークフローに組み込むことが重要です。

## まとめ
今回は「{topic}」の基礎について解説しました。
ぜひ実際の業務やビジネスに活かしてみてください。
"""
        
    # Step 2: Gemini
    print("Step 2: Reviewing and improving with Gemini")
    prompt2 = prompts.STEP2_GEMINI_PROMPT.format(draft=draft)
    improved = run_cli([gemini_cmd, "--prompt", prompt2])
    
    if not improved:
        print("Gemini failed, skipping review...")
        improved = draft

    # Step 3: Codex
    print("Step 3: Final check with Codex")
    prompt3 = prompts.STEP3_CODEX_PROMPT.format(improved=improved)
    final = run_cli([codex_cmd, "-q", prompt3])
    
    if not final:
        print("Codex failed, using Step 2 output...")
        final = improved
        
    if not final:
        print("All CLIs failed. Using fallback generated article to ensure pipeline completes.")
        final = f"""# {topic}

## はじめに
本記事では、「{topic}」について詳しく解説します。
キーワード: {keywords}

## 本論1
（※この記事はAI CLIのフォールバックとして自動生成されたモック記事です。実際の運用環境でClaudeやGemini CLIが正常に動作するようになると、ここに詳細なAI生成コンテンツが入ります。）

## 本論2
自動化とAI導入は、現代のビジネスにおいて不可欠な要素です。
適切なツールを選定し、ワークフローに組み込むことが重要です。

## まとめ
今回は「{topic}」の基礎について解説しました。
ぜひ実際の業務やビジネスに活かしてみてください。
"""
        
    return final

def clean_markdown(text):
    # Remove code blocks wrapper if the AI accidentally wrapped the whole text in ```markdown
    text = re.sub(r"^```markdown\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()

def main():
    # Pick a random topic for today
    if not topics_data["topics"]:
        print("No topics found in topics.yaml")
        return
        
    topic_info = random.choice(topics_data["topics"])
    category = topic_info["category"]
    
    # Map to site
    site_map = config["blog"]["site_map"]
    if category not in site_map:
        print(f"Category '{category}' not mapped to any site in config.yaml. Skipping.")
        return
        
    site_dir_rel = site_map[category]
    site_dir = os.path.join(BASE_DIR, site_dir_rel)
    posts_dir = os.path.join(site_dir, "content", "posts")
    
    os.makedirs(posts_dir, exist_ok=True)
    
    content = generate_article(topic_info)
    if not content:
        print("Failed to generate article.")
        return
        
    content = clean_markdown(content)
    
    # Generate Hugo Front Matter
    date_str = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%dT%H:%M:%S+09:00")
    title = topic_info["topic"]
    slug = slugify(title)
    
    front_matter = f"""---
title: "{title}"
date: {date_str}
draft: false
tags: {topic_info['keywords']}
categories: ["{category}"]
---

"""
    
    filename = f"{datetime.datetime.now().strftime('%Y-%m-%d')}-{slug}.md"
    filepath = os.path.join(posts_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(front_matter + content)
        
    print(f"Article saved to {filepath}")
    
    if config["git"].get("auto_push", False):
        print("Committing and pushing to git...")
        commit_msg = config["git"]["commit_message_template"].format(title=title)
        os.chdir(BASE_DIR)
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("Git push complete.")

if __name__ == "__main__":
    main()
