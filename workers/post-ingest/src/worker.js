const CATEGORY_SITE_MAP = {
  "AI・テック": { siteDir: "sites/ai-tech", baseUrl: "https://ai-tech-blog-97e.pages.dev" },
  "AI×不動産": { siteDir: "sites/ai-tech", baseUrl: "https://ai-tech-blog-97e.pages.dev" },
  "ビジネス・副業": { siteDir: "sites/business", baseUrl: "https://business-blog.pages.dev" },
  "不動産マーケティング": { siteDir: "sites/business", baseUrl: "https://business-blog.pages.dev" },
  "不動産投資": { siteDir: "sites/real-estate", baseUrl: "https://real-estate-blog.pages.dev" },
  "賃貸経営": { siteDir: "sites/real-estate", baseUrl: "https://real-estate-blog.pages.dev" },
};

const DEFAULT_ROUTE = CATEGORY_SITE_MAP["AI・テック"];

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "GET" && url.pathname === "/health") {
      return json({ ok: true, service: "auto-ai-blog-post-ingest" });
    }
    if (request.method === "POST" && url.pathname === "/api/posts") {
      return handlePost(request, env);
    }
    return json({ ok: false, error: "not_found" }, 404);
  },
};

async function handlePost(request, env) {
  const authError = checkAuth(request, env);
  if (authError) return authError;

  let payload;
  try {
    payload = await request.json();
  } catch {
    return json({ ok: false, error: "invalid_json" }, 400);
  }

  const title = clean(payload.title || "");
  const category = clean(payload.category || "AI・テック");
  const body = buildBody(payload);
  if (!title || !body) {
    return json({ ok: false, error: "title_and_body_required" }, 400);
  }

  const route = CATEGORY_SITE_MAP[category] || DEFAULT_ROUTE;
  const now = new Date();
  const slug = slugify(title, now);
  const postPath = `${route.siteDir}/content/posts/${datePart(now)}-${slug}.md`;
  const cover = await resolveCoverImage(env, route.siteDir, slug, payload);
  const markdown = buildMarkdown({ title, category, payload, body, now, coverPath: cover?.publicPath });

  await putGitHubFile(env, postPath, utf8ToBase64(markdown), `external post: ${title}`);
  if (cover) {
    await putGitHubFile(env, cover.repoPath, cover.base64, `cover image: ${title}`);
  }

  const postUrl = `${route.baseUrl}/posts/${datePart(now)}-${slug}/`;
  return json({ ok: true, site: route.siteDir, post_path: postPath, post_url: postUrl, cover_path: cover?.repoPath || null });
}

function checkAuth(request, env) {
  const expected = env.INGEST_API_KEY;
  if (!expected) return json({ ok: false, error: "ingest_api_key_not_configured" }, 500);
  const authorization = request.headers.get("Authorization") || "";
  const xApiKey = request.headers.get("x-api-key") || "";
  const token = authorization.startsWith("Bearer ") ? authorization.slice("Bearer ".length) : xApiKey;
  if (token !== expected) return json({ ok: false, error: "unauthorized" }, 401);
  return null;
}

function buildBody(payload) {
  const body = clean(payload.body_markdown || "");
  if (body) return body;
  const freeBody = clean(payload.free_body_markdown || "");
  const paidTeaser = clean(payload.paid_teaser_markdown || "");
  const productId = clean(payload.product_id || "");
  const cta = productId
    ? `\n\n## 続きは有料マニュアルで\n\n詳しい実装手順は [有料マニュアル](/manuals/${productId}/) で確認できます。\n`
    : "";
  return [freeBody, paidTeaser, cta].filter(Boolean).join("\n\n");
}

function buildMarkdown({ title, category, payload, body, now, coverPath }) {
  const tags = Array.isArray(payload.tags) && payload.tags.length ? payload.tags : ["AI"];
  const summary = clean(payload.summary || title).slice(0, 150);
  const lines = [
    "---",
    `title: ${JSON.stringify(title)}`,
    `date: ${now.toISOString()}`,
    "draft: false",
    "tags:",
    ...tags.map((tag) => `  - ${JSON.stringify(String(tag))}`),
    "categories:",
    `  - ${JSON.stringify(category)}`,
    `description: ${JSON.stringify(summary)}`,
  ];
  if (coverPath) {
    lines.push("cover:", `  image: ${JSON.stringify(coverPath)}`, "  relative: false");
  }
  lines.push("---", "", body, "");
  return lines.join("\n");
}

async function resolveCoverImage(env, siteDir, slug, payload) {
  const extension = normalizeExtension(payload.cover_image_extension || ".png");
  let base64 = clean(payload.cover_image_base64 || "");
  if (!base64 && payload.cover_image_url) {
    const imageResponse = await fetch(String(payload.cover_image_url));
    if (!imageResponse.ok) throw new Error(`cover_image_url fetch failed: ${imageResponse.status}`);
    base64 = arrayBufferToBase64(await imageResponse.arrayBuffer());
  }
  if (!base64 && payload.cover_image_prompt && env.OPENAI_API_KEY) {
    base64 = await generateOpenAIImage(env.OPENAI_API_KEY, String(payload.cover_image_prompt));
  }
  if (!base64) return null;
  const filename = `${slug}${extension}`;
  return {
    repoPath: `${siteDir}/static/images/posts/${filename}`,
    publicPath: `/images/posts/${filename}`,
    base64,
  };
}

async function generateOpenAIImage(apiKey, prompt) {
  const response = await fetch("https://api.openai.com/v1/images/generations", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "gpt-image-2",
      prompt: `${prompt}\nJapanese editorial web article cover image, no text, no watermark.`,
      size: "1536x1024",
      quality: "medium",
    }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(`OpenAI image generation failed: ${data.error?.message || response.status}`);
  const image = data.data?.[0]?.b64_json;
  if (!image) throw new Error("OpenAI image generation returned no image");
  return image;
}

async function putGitHubFile(env, path, contentBase64, message) {
  const owner = env.GITHUB_OWNER || "univcorp2-ctrl";
  const repo = env.GITHUB_REPO || "auto-ai-blog";
  const branch = env.GITHUB_BRANCH || "main";
  const token = env.GITHUB_TOKEN;
  if (!token) throw new Error("GITHUB_TOKEN is not configured");
  const response = await fetch(`https://api.github.com/repos/${owner}/${repo}/contents/${encodeURIComponentPath(path)}`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "User-Agent": "auto-ai-blog-post-ingest",
    },
    body: JSON.stringify({
      message,
      content: contentBase64,
      branch,
    }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(`GitHub write failed: ${data.message || response.status}`);
  return data;
}

function slugify(title, now) {
  const ascii = title
    .normalize("NFKD")
    .replace(/[^\w\s-]/g, "")
    .trim()
    .toLowerCase()
    .replace(/[-\s]+/g, "-")
    .slice(0, 80);
  return ascii || `post-${now.getTime()}`;
}

function datePart(value) {
  return value.toISOString().slice(0, 10);
}

function clean(value) {
  return String(value || "").trim();
}

function normalizeExtension(value) {
  const extension = String(value || ".png").toLowerCase();
  return extension.startsWith(".") ? extension : `.${extension}`;
}

function utf8ToBase64(value) {
  const bytes = new TextEncoder().encode(value);
  return arrayBufferToBase64(bytes.buffer);
}

function arrayBufferToBase64(buffer) {
  let binary = "";
  const bytes = new Uint8Array(buffer);
  for (let i = 0; i < bytes.byteLength; i += 1) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

function encodeURIComponentPath(path) {
  return path.split("/").map(encodeURIComponent).join("/");
}

function json(value, status = 200) {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}
