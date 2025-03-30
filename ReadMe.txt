PyMin – 日経225mini 1分足 OHLC自動生成ツール
PyMin は、kabuステーション API を通じて取得した日経225mini のリアルタイムティックから、
1分足ベースのOHLC（始値・高値・安値・終値）データを自動構築・補完・保存する Python アプリケーションです。

---

主な特徴
kabuステーションの WebSocket 配信からリアルタイムでティックデータを受信

ティックから 1分足の OHLC を逐次構築し、欠損補完・終値補完にも対応

日中／夜間セッション、自動限月切替、取引日管理を自動判定

1分足データを取引日ごとに CSV で出力（dummy判定／限月付き）

ティック全件保存（任意）＋ 各分の最初のティック（first_tick）は常に保存

接続情報（SymbolCode, ExchangeCode, Token）をCSVに記録

settings.json による柔軟な設定切替

ログ出力（タイムスタンプ＆ラベル付き）


ティックが来なかった時間帯は、前回の終値を用いて補完 (is_dummy=True)

プレクロージング（例：15:45）にティックがなければ、次セッションの始値を使ってOHLC補完

dummyであること・限月が不明であることをCSVに明記


PyMin/
├── csv/                      ← 1分足データ（取引日ごと）
├── tick/                     ← ティックデータ（通常Tick、latest_first_tick）
├── pymin_main.py             ← メインエントリ
├── ohlc_builder.py           ← OHLC構築・補完ロジック
├── price_handler.py          ← Tick処理／欠損補完／終値補完など
├── tick_writer.py            ← Tick保存（通常+first_tick）
├── ohlc_writer.py            ← OHLC CSV書き出し
├── time_util.py              ← セッション／取引日／夜間の判定
├── symbol_resolver.py        ← 限月からの銘柄コード解決
├── settings.py / settings.json
├── logger.py                 ← ログ出力（ファイル+標準出力）
