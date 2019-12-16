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

## セットアップ

On Windows:

1. Python と Git をインストール
    - https://www.python.org/downloads/ から Python 3 系をダウンロードし、インストール
    - cmd.exe で py.exe が起動できれば OK
    - https://git-scm.com/ から Git for Windows をダウンロードし、インストール
    - Git Bash がインストールされれば OK
2. hondana-oroshi と、その依存パッケージをインストール
```
（Git Bash 上で以下のコマンドを実行）
git clone git@github.com:uchan-nos/hondana-oroshi.git
git clone git@github.com:uchan-nos/pykintone.git
pip3 install pyyaml pytz tzlocal requests
```
3. kintone.yml を準備
```
domain: your-domain
apps:
    hondana:
        id: xxx
	token: yyy
```
4. パソコンにバーコードスキャナを接続する
    - 動作確認しているバーコードスキャナは BUSICOM BC-BR900L
## 使い方

On Windows:

```
run.bat
```

で起動したら "Scan barcodes" と言われるので、ISBN バーコードをスキャンする。複数の本を連続でスキャンしてよい。同じ本（ISBN が同じ本）が複数冊ある場合でも、省略せずすべてスキャンすること。

バーコードを一通りスキャンしたらエンターキーで空行を入力する。すると、各バーコードが kintone から検索され、アクションが決定される。

あり得るアクションは次の通り。

| アクション名  | 意味 |
|---------------|------|
| TakeInventory | 「棚卸」フラグにチェックを付ける。もっとも一般的なアクション |
| RegisterNew   | kintone 上に、その ISBN を持つ棚卸未済のレコードがないので、新たに登録する |
| Investigate   | レコードが不正な状態になっているので要調査。kintone に対しては何もしない |
| Found         | 紛失中だった本が見つかったので「棚卸」フラグをチェックしつつ「紛失中」ステータスを更新する |
| Discard       | この本は本棚に戻さず、破棄する |
