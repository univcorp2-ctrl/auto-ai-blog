import json
import os

def main():
    try:
        with open('notion_search.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print("Failed to load notion_search.json", e)
        return

    output = []
    output.append('# Notion Contents')
    output.append('Here are the parsed contents from Notion:')
    output.append('')

    for page in data.get('results', []):
        if page.get('object') != 'page': continue
        
        props = page.get('properties', {})
        
        title_text = 'Untitled'
        for prop_name, prop_data in props.items():
            if prop_data.get('type') == 'title':
                title_array = prop_data.get('title', [])
                if title_array and len(title_array) > 0:
                    title_text = title_array[0].get('plain_text', 'Untitled')
                break
                
        url = page.get('url', '')
        output.append(f'## [{title_text}]({url})')
        
        details = []
        for prop_name, prop_data in props.items():
            prop_type = prop_data.get('type')
            if prop_type == 'select' and prop_data.get('select'):
                val = prop_data['select']['name']
                details.append(f'- **{prop_name}**: {val}')
            elif prop_type == 'checkbox':
                val = '✅' if prop_data['checkbox'] else '⬜'
                details.append(f'- **{prop_name}**: {val}')
            elif prop_type == 'number' and prop_data.get('number') is not None:
                details.append(f'- **{prop_name}**: {prop_data["number"]}')
            elif prop_type == 'rich_text':
                rt = prop_data.get('rich_text', [])
                if rt and len(rt) > 0:
                    rt_text = "".join([t.get('plain_text', '') for t in rt])
                    details.append(f'- **{prop_name}**: {rt_text}')
        
        if details:
            output.extend(details)
        output.append('')

    artifact_dir = os.path.expandvars(r'C:\Users\user\.gemini\antigravity-cli\brain\e440615e-875e-49cb-87f1-e9ee7268e5c3')
    if not os.path.exists(artifact_dir):
        os.makedirs(artifact_dir, exist_ok=True)
    
    out_path = os.path.join(artifact_dir, 'notion_contents.md')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))

    print(f'Generated markdown at {out_path}')

if __name__ == "__main__":
    main()
