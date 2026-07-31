(() => {
  "use strict";

  const growth = globalThis.AffiliateGrowth;
  const form = document.querySelector("#fixed-cost-form");
  if (!growth || !form) return;

  const headlineVariant = growth.stableVariant("diagnosis-headline", ["savings", "three-minutes"]);
  const ctaVariant = growth.stableVariant("diagnosis-cta", ["check", "start"]);
  const orderVariant = growth.stableVariant("offer-order", ["score", "category"]);
  const variantId = `${headlineVariant}:${ctaVariant}:${orderVariant}`;
  let started = false;

  const heading = document.querySelector("#diagnosis-heading");
  const submitButton = document.querySelector("#diagnosis-submit");
  if (heading) heading.textContent = headlineVariant === "savings" ? "毎月の通信費・固定費を3分で見直す" : "3分入力で、見直す順番を整理する";
  if (submitButton) submitButton.textContent = ctaVariant === "check" ? "見直し候補を確認" : "無料診断を始める";

  growth.track("page_view", { page: "fixed_cost_diagnosis" }, variantId);
  form.addEventListener("input", () => {
    if (!started) {
      growth.track("diagnosis_start", { page: "fixed_cost_diagnosis" }, variantId);
      started = true;
    }
  });

  function numberValue(id) {
    return Math.max(0, Number(document.querySelector(`#${id}`).value || 0));
  }

  function diagnose(values) {
    const categories = [];
    const notes = [];
    let low = 0;
    let high = 0;
    const perLine = values.mobile / Math.max(1, values.lines);
    if (perLine >= 4500) {
      categories.push("mobile");
      const gap = Math.max(0, values.mobile - values.lines * 3500);
      low += gap * 0.25;
      high += gap * 0.7;
      notes.push("スマホはデータ容量、通話、端末残債を分けて比較します。");
    }
    if (values.internet >= 5500 || ["unknown", "legacy", "home-router"].includes(values.internetType)) {
      categories.push("internet");
      const gap = Math.max(500, values.internet - 4500);
      low += gap * 0.3;
      high += gap * 0.8;
      notes.push("回線は工事費残債、解約金、セット割の消失を含めて比較します。");
    }
    const electricityBaseline = 7000 + Math.max(0, values.household - 1) * 2000;
    if (values.electricity >= electricityBaseline * 1.15) {
      categories.push("electricity");
      const gap = Math.max(500, values.electricity - electricityBaseline);
      low += gap * 0.1;
      high += gap * 0.35;
      notes.push("電力は地域、使用量、燃料費調整、解約条件を同じ期間で比較します。");
    }
    if (!categories.length) {
      categories.push("general_review");
      notes.push("大きな割高サインはありません。更新月と不要オプションを定期確認してください。");
    }
    if (!values.willing) notes.push("乗り換え前に、現契約のプラン変更と不要オプション解約を優先します。");
    return { categories, low: Math.round(low), high: Math.round(Math.max(low, high)), notes };
  }

  async function loadData() {
    const [programsResponse, configResponse] = await Promise.all([
      fetch("/data/affiliate-programs.demo.json", { cache: "no-store" }),
      fetch("/data/affiliate-config.json", { cache: "no-store" }),
    ]);
    if (!programsResponse.ok || !configResponse.ok) throw new Error("affiliate data load failed");
    return { programs: await programsResponse.json(), config: await configResponse.json() };
  }

  function renderResult(result) {
    const box = document.querySelector("#diagnosis-result");
    box.hidden = false;
    box.querySelector("[data-saving]").textContent = `${growth.formatYen(result.low)}〜${growth.formatYen(result.high)} / 月の見直し余地（概算）`;
    box.querySelector("[data-categories]").textContent = result.categories.join(" / ");
    const list = box.querySelector("[data-notes]");
    list.replaceChildren(...result.notes.map((note) => {
      const item = document.createElement("li");
      item.textContent = note;
      return item;
    }));
  }

  function renderPrograms(programs, config, categories) {
    const container = document.querySelector("#offer-list");
    const visible = programs.filter((program) => categories.includes(program.category) || categories.includes("general_review"));
    const rows = visible.map((program) => ({
      program,
      score: growth.scoreProgram(program, Number(config.margin || 0.55)),
      audit: growth.evaluateProgram(program, config),
    }));
    if (orderVariant === "score") rows.sort((a, b) => b.score.expectedClickValue - a.score.expectedClickValue);
    else rows.sort((a, b) => a.program.category.localeCompare(b.program.category, "ja"));

    container.replaceChildren();
    rows.forEach(({ program, score, audit }) => {
      const card = document.createElement("article");
      card.className = "affiliate-offer-card";
      const badge = document.createElement("p");
      badge.className = "affiliate-demo-badge";
      badge.textContent = "DEMO / 実案件ではありません";
      const title = document.createElement("h3");
      title.textContent = program.name;
      const metrics = [
        `期待承認報酬: ${growth.formatYen(score.expectedApprovedReward)}`,
        `期待クリック価値: ${growth.formatYen(score.expectedClickValue)}`,
        `推奨上限CPC: ${growth.formatYen(score.recommendedMaxCpc)}（margin ${config.margin}）`,
      ].map((text) => {
        const item = document.createElement("p");
        item.textContent = text;
        return item;
      });
      const status = document.createElement("p");
      status.className = `affiliate-status ${audit.eligible ? "is-ok" : "is-stop"}`;
      status.textContent = audit.eligible ? "条件確認済み" : `停止中: ${audit.reasons.join(" / ")}`;
      const button = document.createElement("button");
      button.type = "button";
      button.disabled = !audit.eligible;
      button.textContent = "PR案件の詳細を確認";
      card.append(badge, title, ...metrics, status, button);
      if (audit.eligible) {
        growth.track("offer_impression", { program_id: program.program_id }, variantId);
        button.addEventListener("click", () => {
          const approved = globalThis.confirm("PRリンクとして外部サイトへ移動します。案件条件と申込条件を再確認してください。");
          if (!approved) return;
          growth.track("affiliate_click", {
            program_id: program.program_id,
            expected_approved_reward_yen: score.expectedApprovedReward,
          }, variantId);
          const target = growth.appendTracking(program.affiliate_url, program.program_id, config);
          globalThis.open(target, "_blank", "noopener,noreferrer");
        });
      }
      container.appendChild(card);
    });
    if (!rows.length) container.textContent = "該当カテゴリの案件は未登録です。";
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const values = {
      mobile: numberValue("mobile-cost"),
      lines: Math.max(1, numberValue("mobile-lines")),
      internet: numberValue("internet-cost"),
      internetType: document.querySelector("#internet-type").value,
      electricity: numberValue("electricity-cost"),
      household: Math.max(1, numberValue("household-size")),
      willing: document.querySelector("#willing-switch").checked,
    };
    const result = diagnose(values);
    renderResult(result);
    growth.track("diagnosis_complete", { categories: result.categories }, variantId);
    try {
      const { programs, config } = await loadData();
      renderPrograms(programs, config, result.categories);
    } catch (_error) {
      document.querySelector("#offer-list").textContent = "案件台帳を読み込めませんでした。";
    }
  });
})();
