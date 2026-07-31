---
title: "アフィリエイト運用ダッシュボード"
description: "匿名イベント、実績、シミュレーション、100万円目標を分けて確認します。"
draft: false
url: "/affiliate-dashboard/"
---

<div id="affiliate-dashboard" class="affiliate-shell">
  <aside class="affiliate-disclosure">
    <strong>この画面の数値区分</strong><br>
    「実績」は手入力した確定報酬だけです。「シミュレーション」はクリック時の期待承認報酬であり、A8の発生・確定・入金ではありません。
  </aside>

  <section class="affiliate-metrics">
    <article class="affiliate-metric"><strong data-page-views>0</strong><br>ページ閲覧</article>
    <article class="affiliate-metric"><strong data-starts>0</strong><br>診断開始</article>
    <article class="affiliate-metric"><strong data-completions>0</strong><br>診断完了</article>
    <article class="affiliate-metric"><strong data-clicks>0</strong><br>広告クリック</article>
    <article class="affiliate-metric"><strong data-completion-rate>0%</strong><br>診断完了率</article>
    <article class="affiliate-metric"><strong data-ctr>0%</strong><br>案件CTR</article>
  </section>

  <section class="affiliate-panel">
    <h2>収益の区分</h2>
    <p>シミュレーション期待承認報酬: <strong data-simulated>0円</strong></p>
    <p>手入力した確定報酬実績: <strong data-actual>0円</strong></p>
    <p>100万円までの必要確定件数（現在の平均単価、未入力時1万円）: <strong data-needed>100件</strong></p>
    <div class="affiliate-grid">
      <label class="affiliate-field">確定報酬累計（円）<input id="actual-revenue" type="number" min="0" step="1" value="0"></label>
      <label class="affiliate-field">確定件数<input id="actual-conversions" type="number" min="0" step="1" value="0"></label>
    </div>
    <p><button id="save-actuals" class="affiliate-button" type="button">実績を保存</button></p>
  </section>

  <section class="affiliate-panel">
    <h2>A/B実験と停止基準</h2>
    <p data-sample-warning>サンプル不足です。</p>
    <ul>
      <li>見出し、CTA、案件順を匿名IDで安定割当</li>
      <li>既定の日次テスト上限 3,000円、累計損失上限 10,000円</li>
      <li>既定はdry-run・人間未承認。広告APIや課金APIには接続しない</li>
    </ul>
  </section>

  <section class="affiliate-panel">
    <h2>匿名イベント管理</h2>
    <p>このブラウザのlocalStorageに最大5,000件を保存します。氏名、メール、電話、住所は記録しません。</p>
    <p><button id="export-events" class="affiliate-button" type="button">CSVを書き出す</button> <button id="clear-events" type="button">イベントを削除</button></p>
  </section>

  <p><a href="/diagnosis/">診断へ戻る</a></p>
</div>

<script src="/js/affiliate-common.js" defer></script>
<script src="/js/affiliate-dashboard.js" defer></script>
