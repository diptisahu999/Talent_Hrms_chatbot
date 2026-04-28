from langdetect import detect

def detect_user_language(text: str) -> str:
    try:
        lang = detect(text)
        print(f"Detected language: {lang}")
        return lang
    except:
        return "en"  # Default to English if detection fails

def get_voice_for_language(lang: str) -> str:
    """
    Return best voice_id for Indian multilingual users
    """

    if lang == "hi":
        return "21m00Tcm4TlvDq8ikWAM"  # Hindi-friendly neutral voice

    if lang in ["gu", "ta", "te", "mr", "bn"]:
        return "21m00Tcm4TlvDq8ikWAM"  # Multilingual voice works best

    # Default: Indian English users
    return "pNInz6obpgDQGcFmaJgB"