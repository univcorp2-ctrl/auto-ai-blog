from __future__ import annotations

from scripts import submit_external_post


def test_prepare_payload_generates_cover_and_inline_images(monkeypatch) -> None:
    generated_prompts: list[str] = []

    def fake_generate(api_key: str, prompt: str, *, quality: str) -> str:
        generated_prompts.append(f"{api_key}:{quality}:{prompt}")
        return "ZmFrZS1pbWFnZQ=="

    monkeypatch.setattr(submit_external_post, "generate_image_base64", fake_generate)

    payload = {
        "title": "CLI投稿",
        "category": "AI・テック",
        "body_markdown": "本文\n\n{{image:flow}}",
        "cover_image_prompt": "記事全体を説明する画像",
        "inline_images": [{"id": "flow", "prompt": "本文途中の図解", "alt": "図解"}],
    }

    prepared = submit_external_post.prepare_payload(payload, openai_api_key="sk-test", image_quality="medium")

    assert prepared["cover_image_base64"] == "ZmFrZS1pbWFnZQ=="
    assert prepared["cover_image_extension"] == ".png"
    assert prepared["inline_images"][0]["base64"] == "ZmFrZS1pbWFnZQ=="
    assert prepared["inline_images"][0]["extension"] == ".png"
    assert generated_prompts == [
        "sk-test:medium:記事全体を説明する画像",
        "sk-test:medium:本文途中の図解",
    ]


def test_submit_external_post_uses_latest_high_quality_image_defaults() -> None:
    assert submit_external_post.IMAGE_MODEL == "gpt-image-2"
    assert submit_external_post.DEFAULT_IMAGE_QUALITY == "high"


def test_enhance_prompt_requires_explanatory_image() -> None:
    prompt = submit_external_post.enhance_image_prompt("AI投稿フローを説明する図")

    assert "visually explain" in prompt
    assert "specific article" in prompt
    assert "no generic AI" in prompt
