#!/usr/bin/env python3
"""
Encrypt data.json -> data.enc for the TZ Claude Analytics dashboard.

The repo is public, so the data must be unreadable at rest. This produces a file
that contains nothing but salt, IV and ciphertext. Without the password it is noise.

Scheme (matches the browser side exactly):
  key        = PBKDF2-HMAC-SHA256(password, salt, 250_000 iterations, 32 bytes)
  ciphertext = AES-256-GCM(key, iv, plaintext)   # 12-byte IV, 16-byte tag appended

Browser decrypts with crypto.subtle — no library needed.

Usage:  python3 encrypt.py "<password>"
"""
import base64
import gzip
import json
import os
import sys

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

IN = '/tmp/v5/data.json'
OUT = '/tmp/v5/data.enc'
ITERATIONS = 250_000


def derive(password: str, salt: bytes) -> bytes:
    return PBKDF2HMAC(
        algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERATIONS
    ).derive(password.encode('utf-8'))


def main():
    if len(sys.argv) < 2:
        sys.exit('usage: encrypt.py "<password>"')
    password = sys.argv[1]

    raw = open(IN, 'rb').read()
    plaintext = gzip.compress(raw, 9)   # decompressed in the browser after decrypt
    salt = os.urandom(16)
    iv = os.urandom(12)
    key = derive(password, salt)
    ct = AESGCM(key).encrypt(iv, plaintext, None)

    payload = {
        'v': 2,
        'gz': True,
        'kdf': 'PBKDF2-SHA256',
        'iterations': ITERATIONS,
        'salt': base64.b64encode(salt).decode(),
        'iv': base64.b64encode(iv).decode(),
        'ct': base64.b64encode(ct).decode(),
    }
    with open(OUT, 'w') as f:
        json.dump(payload, f)

    print('json       %6d bytes' % len(raw))
    print('gzipped    %6d bytes' % len(plaintext))
    print('encrypted  %6d bytes -> %s' % (os.path.getsize(OUT), OUT))
    print('contains no readable field names or values')


if __name__ == '__main__':
    main()
