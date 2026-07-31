---
title: "通信費・固定費の無料診断"
description: "個人情報を入力せず、スマホ・光回線・電気の見直し順を3分で整理します。"
draft: false
url: "/diagnosis/"
---

<div class="affiliate-shell">
  <aside class="affiliate-disclosure" role="note" aria-label="広告に関する表示">
    <strong>PR・広告について</strong><br>
    この診断ページは将来アフィリエイト広告を掲載する予定です。現在の案件はすべて架空のDEMOで、外部申込みは無効です。診断結果は一般的な目安であり、節約額や成果を保証しません。
  </aside>

  <section class="affiliate-panel">
    <p class="affiliate-demo-badge">個人情報の入力不要</p>
    <h1 id="diagnosis-heading">毎月の通信費・固定費を3分で見直す</h1>
    <p>氏名、電話番号、メール、住所は取得しません。料金は概算で入力してください。</p>
    <form id="fixed-cost-form" class="affiliate-grid">
      <label class="affiliate-field">スマホ月額合計（円）<input id="mobile-cost" type="number" min="0" step="100" value="10000" required></label>
      <label class="affiliate-field">スマホ回線数<input id="mobile-lines" type="number" min="1" max="20" value="2" required></label>
      <label class="affiliate-field">インターネット月額（円）<input id="internet-cost" type="number" min="0" step="100" value="5500" required></label>
      <label class="affiliate-field">回線タイプ
        <select id="internet-type">
          <option value="fiber">光回線</option>
          <option value="home-router">ホームルーター</option>
          <option value="legacy">旧方式・ADSL等</option>
          <option value="unknown">不明</option>
        </select>
      </label>
      <label class="affiliate-field">電気代月額（円）<input id="electricity-cost" type="number" min="0" step="100" value="12000" required></label>
      <label class="affiliate-field">世帯人数<input id="household-size" type="number" min="1" max="20" value="2" required></label>
      <label class="affiliate-field">気になること
        <select id="contract-concerns">
          <option value="price">月額が高い</option>
          <option value="speed">速度・品質</option>
          <option value="complex">契約が複雑</option>
          <option value="renewal">更新月・解約条件</option>
        </select>
      </label>
      <label class="affiliate-field"><span>乗り換えも検討できる</span><input id="willing-switch" type="checkbox"></label>
      <div><button id="diagnosis-submit" class="affiliate-button" type="submit">見直し候補を確認</button></div>
    </form>
  </section>

  <section id="diagnosis-result" class="affiliate-result" hidden aria-live="polite">
    <h2>診断結果</h2>
    <p><strong data-saving></strong></p>
    <p>優先カテゴリ: <span data-categories></span></p>
    <ul data-notes></ul>
    <p class="affiliate-small">概算は入力値と一般的な基準によるシミュレーションです。実際の料金、違約金、工事費残債、地域条件、セット割を必ず確認してください。</p>
  </section>

  <section class="affiliate-panel">
    <h2>条件を満たした案件だけ表示</h2>
    <p>active、最終確認日、掲載媒体、PR表記、リスティング/SNS条件、人間承認のどれかが不足すると自動停止します。</p>
    <p class="affiliate-formula">期待承認報酬 = 報酬 × 確定率 / 期待クリック価値 = EPC × 確定率 / 推奨上限CPC = 期待クリック価値 × 0.55</p>
    <div id="offer-list" class="affiliate-offers"><p>診断後に候補が表示されます。</p></div>
  </section>

  <p><a href="/affiliate-dashboard/">運用ダッシュボードを見る</a></p>
</div>

<script src="/js/affiliate-common.js" defer></script>
<script src="/js/affiliate-diagnosis.js" defer></script>
