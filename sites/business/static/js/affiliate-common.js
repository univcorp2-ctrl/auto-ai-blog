(() => {
  "use strict";

  const EVENT_KEY = "a8_growth_events_v1";
  const VISITOR_KEY = "a8_growth_visitor_id_v1";
  const ALLOWED_EVENTS = new Set([
    "page_view",
    "diagnosis_start",
    "diagnosis_complete",
    "offer_impression",
    "affiliate_click",
  ]);
  const FORBIDDEN_KEYS = new Set(["name", "full_name", "email", "phone", "address", "postal_code"]);

  function makeId(prefix) {
    if (globalThis.crypto && globalThis.crypto.randomUUID) return `${prefix}-${globalThis.crypto.randomUUID()}`;
    return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }

  function visitorId() {
    let value = localStorage.getItem(VISITOR_KEY);
    if (!value) {
      value = makeId("visitor");
      localStorage.setItem(VISITOR_KEY, value);
    }
    return value;
  }

  function hash(text) {
    let value = 2166136261;
    for (let index = 0; index < text.length; index += 1) {
      value ^= text.charCodeAt(index);
      value = Math.imul(value, 16777619);
    }
    return value >>> 0;
  }

  function stableVariant(experiment, variants) {
    return variants[hash(`${experiment}:${visitorId()}`) % variants.length];
  }

  function readEvents() {
    try {
      const parsed = JSON.parse(localStorage.getItem(EVENT_KEY) || "[]");
      return Array.isArray(parsed) ? parsed : [];
    } catch (_error) {
      return [];
    }
  }

  function track(eventName, payload = {}, variant = "control") {
    if (!ALLOWED_EVENTS.has(eventName)) throw new Error(`Unsupported event: ${eventName}`);
    const clean = {};
    Object.entries(payload).forEach(([key, value]) => {
      if (!FORBIDDEN_KEYS.has(key.toLowerCase())) clean[key] = value;
    });
    const events = readEvents();
    events.push({
      event_name: eventName,
      occurred_at: new Date().toISOString(),
      session_id: visitorId(),
      variant_id: variant,
      payload: clean,
    });
    localStorage.setItem(EVENT_KEY, JSON.stringify(events.slice(-5000)));
  }

  function clearEvents() {
    localStorage.removeItem(EVENT_KEY);
  }

  function exportCsv() {
    const escape = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
    const rows = [["event_name", "occurred_at", "session_id", "variant_id", "payload_json"]];
    readEvents().forEach((event) => rows.push([
      event.event_name,
      event.occurred_at,
      event.session_id,
      event.variant_id,
      JSON.stringify(event.payload || {}),
    ]));
    return rows.map((row) => row.map(escape).join(",")).join("\n");
  }

  function scoreProgram(program, margin = 0.55) {
    const rate = Number(program.approval_rate || 0);
    const expectedApprovedReward = Number(program.reward_yen || 0) * rate;
    const expectedClickValue = Number(program.epc_yen || 0) * rate;
    return {
      expectedApprovedReward,
      expectedClickValue,
      recommendedMaxCpc: expectedClickValue * margin,
    };
  }

  function evaluateProgram(program, config) {
    const reasons = [];
    const verified = program.last_verified_at ? new Date(`${program.last_verified_at}T00:00:00Z`) : null;
    const ageDays = verified ? (new Date() - verified) / 86400000 : Number.POSITIVE_INFINITY;
    const channel = String(config.channel || "website").toLowerCase();
    const traffic = String(config.traffic_source || "organic").toLowerCase();
    const allowedSocial = new Set(["instagram", "youtube", "tiktok", "pinterest"]);
    const permitted = new Set(["ok", "allowed", "partial_ok"]);

    if (!program.active) reasons.push("案件が無効です");
    if (!verified) reasons.push("最終確認日がありません");
    if (ageDays > Number(config.verification_ttl_days || 30)) reasons.push("案件条件の再確認期限を超えています");
    if (String(program.media_registration_status).toLowerCase() !== "registered") reasons.push("掲載媒体が未登録です");
    if (!String(program.disclosure_text || "").trim()) reasons.push("PR表記がありません");
    if (!String(program.affiliate_url || "").trim()) reasons.push("広告URLがありません");
    if (String(program.affiliate_url).includes("example.invalid")) reasons.push("広告URLがデモです");
    if (["x", "twitter"].includes(channel)) reasons.push("XへのA8広告直接掲載は対象外です");
    if (allowedSocial.has(channel) && !permitted.has(String(program.sns_policy).toLowerCase())) reasons.push("SNS掲載条件が許可済みではありません");
    if (traffic === "paid_search") {
      if (!permitted.has(String(program.listing_policy).toLowerCase())) reasons.push("リスティング条件が許可済みではありません");
      if (String(program.trademark_bidding_policy).toLowerCase() !== "excluded") reasons.push("商標除外キーワードの確認が未完了です");
    }
    if (!config.human_approved) reasons.push("人間の公開承認がありません");
    return { eligible: reasons.length === 0, reasons };
  }

  function appendTracking(url, programId, config) {
    if (!config.tracking_params_allowed) return url;
    const target = new URL(url);
    target.searchParams.set("utm_source", "owned_media");
    target.searchParams.set("utm_medium", "affiliate");
    target.searchParams.set("utm_campaign", "fixed_cost_diagnosis");
    target.searchParams.set("subid", `${programId}-${visitorId().slice(-12)}`);
    return target.toString();
  }

  function formatYen(value) {
    return `${Math.round(Number(value || 0)).toLocaleString("ja-JP")}円`;
  }

  globalThis.AffiliateGrowth = {
    appendTracking,
    clearEvents,
    evaluateProgram,
    exportCsv,
    formatYen,
    readEvents,
    scoreProgram,
    stableVariant,
    track,
    visitorId,
  };
})();
