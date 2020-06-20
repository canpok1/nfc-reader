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

1. 次のコマンドを実行

```
#nfcpyのインストール 
$ sudo pip3 install nfcpy

# sudoなしで実行できるようにする
$ echo 'SUBSYSTEM=="usb", ACTION=="add", ATTRS{idVendor}=="054c", ATTRS{idProduct}=="06c3", GROUP="plugdev" # Sony RC-S380/P' > nfcdev.rules
$ sudo mv nfcdev.rules /etc/udev/rules.d/
```

2. systemdに登録

```
# 設定ファイル生成
sudo ./make_systemd_file.sh
# 自動起動on
sudo systemctl enable nfc-reader
# 起動
sudo systemctl start nfc-reader
# ステータス確認
sudo systemctl status nfc-reader
```


## 参考

次のページを参考にさせていただきました。

* https://jellyware.jp/kurage/raspi/nfc.html
* https://qiita.com/DQNEO/items/0b5d0bc5d3cf407cb7ff
