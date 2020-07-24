import binascii
import nfc
import os
import RPi.GPIO as GPIO
import time
import datetime
from google.cloud import logging

APP_NAME = 'nfc-reader'
LED_RED_PIN = 11
LED_GREEN_PIN = 12
BUZZER_PIN = 32
BUZZER_FREQ = 1200
OUTPUT_DIR = '/tmp/nfc-reader'
 
class MyCardReader(object):
    def __init__(self):
        self.buzzer = GPIO.PWM(BUZZER_PIN, BUZZER_FREQ)
        self.logger = Logger()

    def on_connect(self, tag):
        #タッチ時の処理 
        self.logger.debug("【 Touched 】")
        GPIO.output(LED_RED_PIN,False)
        GPIO.output(LED_GREEN_PIN,True)
        self.buzzer.start(50)
        time.sleep(0.1)
        self.buzzer.stop()
 
        self.save_touched_log(tag)
        
        return True
 
    def read_id(self):
        clf = nfc.ContactlessFrontend('usb')
        try:
            clf.connect(rdwr={'on-connect': self.on_connect})
        finally:
            clf.close()

    def save_touched_log(self, tag):
        try:
            #タグ情報を全て表示 
            self.logger.debug(tag)
 
            #IDmのみ取得して表示 
            idm = binascii.hexlify(tag._nfcid).decode("UTF-8")
            self.logger.debug("IDm : " + str(idm))
 
            now = datetime.datetime.now()
            log_path = OUTPUT_DIR + '/' + idm + '_' + now.strftime('%Y%m%d_%H%M%S')
            self.logger.debug("log path : " + log_path)

            self.logger.info("touched and saved [IDm:" + str(idm) + ", output:" + log_path + "]")

            with open(log_path, mode='w') as f:
                f.write(str(tag))
        except Exception as e:
            self.logger.error(e)

class Logger(object):
    def __init__(self):
        self.level = 0

        self.logger = None
        if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '') != '':
            logging_client = logging.Client()
            self.logger = logging_client.logger(APP_NAME)

    def debug(self, value):
        print(value)

    def info(self, value):
        self._print('info', value)

    def error(self, value):
        self._print('error', value)

    def _print(self, level, value):
        print(value)
        if self.logger is not None :
            self.logger.log_text(str(value))
 
if __name__ == '__main__':
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(LED_RED_PIN, GPIO.OUT)
    GPIO.setup(LED_GREEN_PIN, GPIO.OUT)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)

    logger = Logger()
    try:
        logger.info("start " + APP_NAME)

        os.makedirs(OUTPUT_DIR, exist_ok=True)

        cr = MyCardReader()
        while True:
            #最初に表示 
            logger.debug("Please Touch")
            GPIO.output(LED_RED_PIN,True)
            GPIO.output(LED_GREEN_PIN,False)

            #タッチ待ち 
            cr.read_id()

            #リリース時の処理 
            logger.debug("【 Released 】")
    finally:
        logger.info("stop " + APP_NAME)
        GPIO.cleanup()
