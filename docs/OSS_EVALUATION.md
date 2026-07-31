# OSS Evaluation

## Umami

プライバシー重視のWeb分析基盤で、リポジトリはMITライセンス。複数端末・複数サイトでファネルを統合する段階の移行候補。MVPではサーバー運用を増やさずlocalStorageイベントを採用した。

## GrowthBook

Feature Flag、実験、Product Analyticsのopen-core製品。大部分はMITだが、enterpriseディレクトリは別ライセンス。安定バケッティング、最小サンプル、実験メタデータの考え方を参照した。MVPでは3実験だけの小さな決定的割当を自前実装した。

## Dub

リンク属性・コンバージョン・アフィリエイト管理のopen-core。コアはAGPLv3、enterprise部分は商用ライセンス。リンク帰属とsubid設計の参考になるが、AGPLのネットワーク提供条件と既存構成への重量を考え、現段階では導入しない。

## 判断

初期は依存を増やさず、Hugo＋Vanilla JS＋Pythonで仮説検証する。月間イベントが増え、複数端末統合、サーバー側CV、統計検定、リンク短縮が必要になった時点で移行する。

- https://github.com/umami-software/umami
- https://github.com/growthbook/growthbook
- https://github.com/dubinc/dub
