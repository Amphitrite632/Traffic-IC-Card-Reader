# Traffic-IC-Card-Reader
Suica、ICOCA、PASMOなどのFeliCa規格に準拠した交通系ICカードの利用履歴を表示するPythonスクリプトです。

## Requirements
- Python 3.7 or higher
    - 開発・検証にはPython3.11を使用しました
- requirements.txtに記載のライブラリ
- libusb
- FeliCa規格互換のカードリーダー
    - 開発・検証にはSONYのPaSoRi(RC-S380)を使用しました

## Note
本ソフトウェアで利用している駅コードのデータ`StationCode.csv`は[m2wasabi/nfcpy-suica-sample](https://github.com/m2wasabi/nfcpy-suica-sample)に含まれる同名のファイルを一部修正したものです。

## Cotribute
- 現在、端末ID`0x23`の決済端末の情報を募集中です。
- 実際の利用履歴と駅名・路線名との食い違いや、未登録の駅データがあればご連絡ください。Pull requestも歓迎です。