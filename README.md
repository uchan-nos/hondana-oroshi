# hondana-oroshi
kintone 図書管理システムの棚卸用ツール

## kintone アプリの仕様

アプリのフォーム仕様

| フィールド名 | タイプ           | 説明 |
|--------------|------------------|------|
| レコード番号 | RECORD_NUMBER    | レコード番号 |
| title        | SINGLE_LINE_TEXT | 書籍タイトル |
| isbn10       | SINGLE_LINE_TEXT | 10桁ISBN |
| isbn13       | SINGLE_LINE_TEXT | 13桁ISBN |
| exists       | RADIO_BUTTON     | "o": 本がある, "x": 本が無い |
| inventoried  | CHECK_BOX        | "済み": 棚卸済 |

プロセス管理のステータス仕様

| ステータス     | 意味 |
|----------------|------|
| 本棚にあります | 本が本棚にある |
| レンタル中     | 本が誰かに借りられている |
| 紛失中         | 紛失している |

