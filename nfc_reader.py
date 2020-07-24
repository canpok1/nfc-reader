import binascii
import nfc
import os
import RPi.GPIO as GPIO
import time
import datetime
import logging
import sys

import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler

APP_NAME = 'nfc-reader'
LED_RED_PIN = 11
LED_GREEN_PIN = 12
BUZZER_PIN = 32
BUZZER_FREQ = 1200
OUTPUT_DIR = '/tmp/nfc-reader'

def makeLogger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    client = google.cloud.logging.Client()
    gcpHandler = CloudLoggingHandler(client, name=APP_NAME)
    gcpHandler.setLevel(logging.INFO)
    logger.addHandler(gcpHandler)

    stdoutHandler = logging.StreamHandler(sys.stdout)
    stdoutHandler.setLevel(logging.DEBUG)
    logger.addHandler(stdoutHandler)

    return logger
 
class MyCardReader(object):
    def __init__(self):
        self.buzzer = GPIO.PWM(BUZZER_PIN, BUZZER_FREQ)
        self.logger = makeLogger(self.__class__.__name__)

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
            self.logger.debug("IDm : %s", str(idm))
 
            now = datetime.datetime.now()
            log_path = OUTPUT_DIR + '/' + idm + '_' + now.strftime('%Y%m%d_%H%M%S')
            self.logger.debug("log path : %s", log_path)

            self.logger.info("touched and saved [IDm:%s, output:%s]", str(idm), log_path)

            with open(log_path, mode='w') as f:
                f.write(str(tag))
        except Exception as e:
            self.logger.error(e)

if __name__ == '__main__':
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(LED_RED_PIN, GPIO.OUT)
    GPIO.setup(LED_GREEN_PIN, GPIO.OUT)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)

    logger = makeLogger(__name__)
    try:
        logger.info("start %s", APP_NAME)

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
        logger.info("stop %s", APP_NAME)
        GPIO.cleanup()
