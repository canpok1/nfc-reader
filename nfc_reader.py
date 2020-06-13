import binascii
import nfc
import os
import RPi.GPIO as GPIO
import time

LED_RED_PIN = 11
LED_GREEN_PIN = 12
BUZZER_PIN = 32
BUZZER_FREQ = 1200
 
class MyCardReader(object):
    def __init__(self):
        self.buzzer = GPIO.PWM(BUZZER_PIN, BUZZER_FREQ)

    def on_connect(self, tag):
        #タッチ時の処理 
        print("【 Touched 】")
        GPIO.output(LED_RED_PIN,False)
        GPIO.output(LED_GREEN_PIN,True)
        self.buzzer.start(50)
        time.sleep(0.1)
        self.buzzer.stop()
 
        #タグ情報を全て表示 
        print(tag)
 
        #IDmのみ取得して表示 
        self.idm = binascii.hexlify(tag._nfcid)
        print("IDm : " + str(self.idm))
 
        #特定のIDmだった場合のアクション 
        if self.idm == "00000000000000":
            print("【 登録されたIDです 】")
 
        return True
 
    def read_id(self):
        clf = nfc.ContactlessFrontend('usb')
        try:
            clf.connect(rdwr={'on-connect': self.on_connect})
        finally:
            clf.close()
 
if __name__ == '__main__':
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(LED_RED_PIN, GPIO.OUT)
    GPIO.setup(LED_GREEN_PIN, GPIO.OUT)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)

    try:
        cr = MyCardReader()
        while True:
            #最初に表示 
            print("Please Touch")
            GPIO.output(LED_RED_PIN,True)
            GPIO.output(LED_GREEN_PIN,False)

            #タッチ待ち 
            cr.read_id()

            #リリース時の処理 
            print("【 Released 】")
    finally:
        GPIO.cleanup()
