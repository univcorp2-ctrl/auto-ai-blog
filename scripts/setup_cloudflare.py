import json
import os
import subprocess
import urllib.request

import pandas as pd

EXCEL_PATH = r"G:\マイドライブ\AI_Agents\Private\API_AWS_DB.xlsx"

def main():
    print("Reading Excel file...")
    df = pd.read_excel(EXCEL_PATH)
    
    # Extract Cloudflare token
    cf_row = df[df['Applications'] == 'cloudflare api']
    if cf_row.empty:
        raise ValueError("cloudflare api token not found in Excel")
    cf_token = cf_row['API, secret key tokens'].values[0].strip()
    
    # Extract GitHub token
    gh_row = df[df['Applications'].astype(str).str.contains('Github New Personal access tokens', na=False, case=False)]
    if gh_row.empty:
        # fallback to any Github token
        gh_row = df[df['Applications'].astype(str).str.contains('Github', na=False, case=False)]
    if gh_row.empty:
        raise ValueError("GitHub PAT not found in Excel")
    gh_token = gh_row.iloc[-1]['API, secret key tokens'].strip()

    # Get Cloudflare Account ID via API
    print("Fetching Cloudflare Account ID...")
    req = urllib.request.Request(
        'https://api.cloudflare.com/client/v4/accounts',
        headers={'Authorization': f'Bearer {cf_token}'}
    )
    try:
        res = urllib.request.urlopen(req).read()
        accounts = json.loads(res)['result']
        if not accounts:
            raise ValueError("No Cloudflare accounts found")
        cf_account_id = accounts[0]['id']
        print(f"Found Cloudflare Account ID: {cf_account_id}")
    except Exception as e:
        print(f"Error fetching account ID: {e}")
        return

    # Set GitHub CLI auth token using env var
    os.environ["GH_TOKEN"] = gh_token

    print("Setting GitHub Secrets...")
    try:
        subprocess.run(["gh", "secret", "set", "CLOUDFLARE_API_TOKEN", "-b", cf_token], check=True, capture_output=True, text=True)
        subprocess.run(["gh", "secret", "set", "CLOUDFLARE_ACCOUNT_ID", "-b", cf_account_id], check=True, capture_output=True, text=True)
        print("GitHub Secrets set successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to set GitHub secrets: {e.stderr}")
        return

    # Create Cloudflare Pages projects using npx wrangler
    # We must pass CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID as env vars for wrangler
    os.environ["CLOUDFLARE_API_TOKEN"] = cf_token
    os.environ["CLOUDFLARE_ACCOUNT_ID"] = cf_account_id
    os.environ["WRANGLER_SEND_METRICS"] = "false"

    projects = [
        ("ai-tech-blog", "sites/ai-tech"),
        ("real-estate-blog", "sites/real-estate"),
        ("business-blog", "sites/business")
    ]

    for proj_name, _proj_dir in projects:
        print(f"Creating Cloudflare Pages project: {proj_name}...")
        # Note: wrangler pages project create doesn't support setting framework to hugo directly from CLI if it's not interactive, 
        # but deploy command handles the upload. We just need to create the project.
        try:
            subprocess.run(
                ["npx", "-y", "wrangler", "pages", "project", "create", proj_name, "--production-branch", "main"],
                check=True,
                shell=True
            )
            print(f"Successfully created project {proj_name}")
        except subprocess.CalledProcessError:
            print(f"Project {proj_name} might already exist or creation failed. Proceeding anyway.")

if __name__ == "__main__":
    main()
