#!/bin/bash
cd $(dirname $0)
GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/credentials/gcp-service-account-cred.json python3 $(pwd)/nfc_reader.py
