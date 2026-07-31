(() => {
  "use strict";

  const growth = globalThis.AffiliateGrowth;
  const root = document.querySelector("#affiliate-dashboard");
  if (!growth || !root) return;

  const ACTUAL_KEY = "a8_growth_actuals_v1";

  function summarize(events) {
    const counts = {
      page_view: 0,
      diagnosis_start: 0,
      diagnosis_complete: 0,
      offer_impression: 0,
      affiliate_click: 0,
    };
    let simulated = 0;
    events.forEach((event) => {
      if (Object.hasOwn(counts, event.event_name)) counts[event.event_name] += 1;
      if (event.event_name === "affiliate_click") simulated += Number(event.payload?.expected_approved_reward_yen || 0);
    });
    return {
      counts,
      completionRate: counts.diagnosis_start ? counts.diagnosis_complete / counts.diagnosis_start : 0,
      ctr: counts.offer_impression ? counts.affiliate_click / counts.offer_impression : 0,
      simulated,
    };
  }

  function readActuals() {
    try {
      return JSON.parse(localStorage.getItem(ACTUAL_KEY) || '{"revenue":0,"conversions":0}');
    } catch (_error) {
      return { revenue: 0, conversions: 0 };
    }
  }

  function render() {
    const summary = summarize(growth.readEvents());
    const actuals = readActuals();
    const goal = 1000000;
    const average = actuals.conversions > 0 ? actuals.revenue / actuals.conversions : 10000;
    const remaining = Math.max(0, goal - actuals.revenue);
    const needed = average > 0 ? Math.ceil(remaining / average) : 0;
    document.querySelector("[data-page-views]").textContent = summary.counts.page_view;
    document.querySelector("[data-starts]").textContent = summary.counts.diagnosis_start;
    document.querySelector("[data-completions]").textContent = summary.counts.diagnosis_complete;
    document.querySelector("[data-clicks]").textContent = summary.counts.affiliate_click;
    document.querySelector("[data-completion-rate]").textContent = `${(summary.completionRate * 100).toFixed(1)}%`;
    document.querySelector("[data-ctr]").textContent = `${(summary.ctr * 100).toFixed(1)}%`;
    document.querySelector("[data-simulated]").textContent = growth.formatYen(summary.simulated);
    document.querySelector("[data-actual]").textContent = growth.formatYen(actuals.revenue);
    document.querySelector("[data-needed]").textContent = `${needed.toLocaleString("ja-JP")}件`;
    document.querySelector("#actual-revenue").value = actuals.revenue;
    document.querySelector("#actual-conversions").value = actuals.conversions;
    document.querySelector("[data-sample-warning]").textContent = summary.counts.diagnosis_complete < 100
      ? "サンプル不足: 診断完了100件までは勝敗を確定しません。"
      : "最低サンプルに到達しました。確定報酬と媒体別差分を確認してください。";
  }

  document.querySelector("#save-actuals").addEventListener("click", () => {
    const actuals = {
      revenue: Math.max(0, Number(document.querySelector("#actual-revenue").value || 0)),
      conversions: Math.max(0, Number(document.querySelector("#actual-conversions").value || 0)),
    };
    localStorage.setItem(ACTUAL_KEY, JSON.stringify(actuals));
    render();
  });

  document.querySelector("#export-events").addEventListener("click", () => {
    const blob = new Blob([growth.exportCsv()], { type: "text/csv;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `affiliate-events-${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  });

  document.querySelector("#clear-events").addEventListener("click", () => {
    if (!globalThis.confirm("匿名イベントをこのブラウザから削除しますか？")) return;
    growth.clearEvents();
    render();
  });

  render();
})();
