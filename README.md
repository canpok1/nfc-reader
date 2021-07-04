# nfc-reader

NFCを読み取り特定APIへとリクエストするプログラムです。


## 実行環境

次の環境での実行を想定しています。

* Raspberry Pi 3 Model B (OS: Raspberry Pi OS)
* GPIOに以下が接続されている
    * GPIO12 ブザー
    * GPIO17 LED赤
    * GPIO18 LED緑
* USBに以下が接続されている
    * Sony Pasori (RC-S380)


## 環境構築

1. 必要コマンド等をインストール

```
sudo apt-get -y install python3-dev python3-pip git
```

2. ソースコードを取得

```
git clone https://github.com/canpok1/nfc-reader.git
cd nfc-reader
```

3. Google Cloud Logging の認証情報用JSONファイルを下記に配置
  * nfc-reader/credentials/gcp-service-account-cred.json
  * JSONファイルは[こちら](https://cloud.google.com/logging/docs/reference/libraries?hl=ja#setting_up_authentication)を参考に取得する

4. Google Sheet API の認証情報用JSONファイルを下記に配置
  * nfc-reader/credentials/credentials.json
  * JSONファイルは[こちら](https://developers.google.com/workspace/guides/create-credentials#desktop)を参考に取得する

5. 次のコマンドを実行

```
#必要ライブラリをインストール
$ sudo pip3 install --default-timeout=100 --upgrade nfcpy google-cloud-logging google-api-python-client google-auth-httplib2 google-auth-oauthlib

# sudoなしで実行できるようにする
$ echo 'SUBSYSTEM=="usb", ACTION=="add", ATTRS{idVendor}=="054c", ATTRS{idProduct}=="06c3", GROUP="plugdev" # Sony RC-S380/P' > nfcdev.rules
$ sudo mv nfcdev.rules /etc/udev/rules.d/
```

6. 動作確認

```
$ bash start_nfc_reader.sh
# 赤色LEDが点灯、NFCタグをかざして/tmp/nfc-reader/にファイルが生成されればOK
# ctrl+Cを長押しして止める

$ bash start_nfc_reader_sender.sh
# スプレッドシートに反映されればOK
# 初回は手動で認証する必要あるので出力されるログに従う
# (URLをブラウザで開いてアカウント等を選択、表示されるコードをコピーしてアプリ側に入力する流れになるはず）
```

7. systemdに登録

```
# 設定ファイル生成
sudo ./make_systemd_file.sh
# 自動起動on
sudo systemctl enable nfc-reader
sudo systemctl enable nfc-reader-sender.timer
# 起動
sudo systemctl start nfc-reader
sudo systemctl start nfc-reader-sender
# ステータス確認
sudo systemctl status nfc-reader
sudo systemctl status nfc-reader-sender
```


## 参考

次のページを参考にさせていただきました。

* https://jellyware.jp/kurage/raspi/nfc.html
* https://qiita.com/DQNEO/items/0b5d0bc5d3cf407cb7ff
