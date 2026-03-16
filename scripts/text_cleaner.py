#!/usr/bin/env python3
# text_cleaner.py - simple text normalization
import re

def clean_text(s):
    s = s.strip()
    s = re.sub(r"\s+", " ", s)   # collapse whitespace
    s = re.sub(r"[^\w\s\-\.,:;\(\)\?\!\/]", "", s)  # remove weird chars
    return s

if __name__ == '__main__':
    sample = "  Hello––世界!!  This is    a test. \n Date: 2026/03/16  "
    print('Before:', sample)
    print('After: ', clean_text(sample))
