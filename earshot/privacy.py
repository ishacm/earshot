"""Mentions are public, but people are not the point. Strip what identifies them before anything is stored."""
import re

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
HANDLE = re.compile(r"(?<![\w/])@[A-Za-z0-9_]{2,}")
PHONE = re.compile(r"\+?\d[\d ()/-]{7,}\d")
URL_USER = re.compile(r"(?i)(reddit\.com/u(?:ser)?/|news\.ycombinator\.com/user\?id=)[\w-]+")


def scrub(text: str) -> str:
    text = EMAIL.sub("[email]", text or "")
    text = URL_USER.sub(r"\1[user]", text)
    text = HANDLE.sub("@[user]", text)
    text = PHONE.sub("[phone]", text)
    return text
