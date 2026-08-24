# -*- coding: utf-8 -*-
"""Thin DeepSeek (OpenAI-compatible) chat client built on `requests`.

DeepSeek exposes an OpenAI-style API at https://api.deepseek.com.
"""
import json
import os
import time

import requests

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"


def get_api_key():
    from dotenv import load_dotenv
    load_dotenv()
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set in .env or the environment")
    return key


def _strip_fences(text):
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```")[1]
        if t.startswith("json"):
            t = t[4:]
    return t.strip()


def chat(messages, temperature=0.8, max_tokens=4096, json_mode=True, retries=3):
    """Call DeepSeek chat completions. Returns a dict when json_mode, else str."""
    key = get_api_key()
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    last_err = None
    for attempt in range(retries):
        try:
            resp = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=180)
            if resp.status_code != 200:
                last_err = RuntimeError(f"DeepSeek HTTP {resp.status_code}: {resp.text[:300]}")
                if resp.status_code in (429, 500, 502, 503):
                    time.sleep(2 * (attempt + 1))
                    continue
                raise last_err
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            content = _strip_fences(content)
            if json_mode:
                return json.loads(content)
            return content
        except (requests.RequestException, KeyError, ValueError) as e:
            last_err = e
            time.sleep(2 * (attempt + 1))

    raise RuntimeError(f"DeepSeek call failed after {retries} attempts: {last_err}")
