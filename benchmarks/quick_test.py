#!/usr/bin/env python3
"""
TRU Quick Test — proves it catches hallucinations
"""
import requests
import json

BASE = "https://splashdown2.zo.space/api"

def test_primaries_search():
    """Test that primaries search works."""
