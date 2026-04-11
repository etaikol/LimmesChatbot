"""
Per-language UI strings + language metadata.

Coverage today (12 languages):
    en  English
    he  Hebrew (RTL)
    ar  Arabic (RTL)
    fa  Farsi  (RTL)
    th  Thai
    fr  French
    es  Spanish
    de  German
    ru  Russian
    ja  Japanese
    zh  Chinese (Simplified)
    hi  Hindi

Add a new language by appending to ``SUPPORTED_LANGUAGES`` and ``MESSAGES``.
The native_name is what users see in the language picker.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LanguageInfo:
    code: str           # ISO-639-1 (or BCP-47 short tag)
    name: str           # English label
    native_name: str    # Self-name shown in the picker
    rtl: bool = False


SUPPORTED_LANGUAGES: list[LanguageInfo] = [
    LanguageInfo("en", "English",   "English"),
    LanguageInfo("he", "Hebrew",    "עברית",     rtl=True),
    LanguageInfo("ar", "Arabic",    "العربية",   rtl=True),
    LanguageInfo("fa", "Farsi",     "فارسی",     rtl=True),
    LanguageInfo("th", "Thai",      "ไทย"),
    LanguageInfo("fr", "French",    "Français"),
    LanguageInfo("es", "Spanish",   "Español"),
    LanguageInfo("de", "German",    "Deutsch"),
    LanguageInfo("ru", "Russian",   "Русский"),
    LanguageInfo("ja", "Japanese",  "日本語"),
    LanguageInfo("zh", "Chinese",   "中文"),
    LanguageInfo("hi", "Hindi",     "हिन्दी"),
]

# Pre-built tuple of ISO codes — used by language detection call sites
# so they don't rebuild the list on every message.
SUPPORTED_LANGUAGE_CODES: tuple[str, ...] = tuple(l.code for l in SUPPORTED_LANGUAGES)

_BY_CODE: dict[str, LanguageInfo] = {l.code: l for l in SUPPORTED_LANGUAGES}

# ── UI strings per language ─────────────────────────────────────────────────
#
# Keep keys ASCII so editors and IDEs handle them well.
# Missing keys fall back to English (see ``get_messages``).

_EN: dict[str, str] = {
    "placeholder":       "Type your message…",
    "send":              "Send",
    "thinking":          "Thinking…",
    "connection_error":  "Connection error. Please try again.",
    "rate_limited":      "You're sending messages too quickly. Please slow down.",
    "too_long":          "Your message is too long.",
    "language":          "Language",
    "clear":             "Clear conversation",
    "minimize":          "Minimize",
    "powered_by":        "AI assistant",
    "welcome":           "Hello! 👋 Welcome — I'm here to help with products, pricing, design tips, or booking a consultation. What can I do for you? 😊",
    "budget_reached":    "Sorry, today's usage limit has been reached. Please try again tomorrow.",
    "handoff_resolved":  "You are now back with the bot. How can I help?",
}

MESSAGES: dict[str, dict[str, str]] = {
    "en": _EN,

    "he": {
        "placeholder":      "כתוב/כתבי הודעה…",
        "send":             "שליחה",
        "thinking":         "חושב…",
        "connection_error": "שגיאת חיבור. נסו שוב.",
        "rate_limited":     "שליחת הודעות מהירה מדי. נסו שוב בעוד רגע.",
        "too_long":         "ההודעה ארוכה מדי.",
        "language":         "שפה",
        "clear":             "ניקוי שיחה",
        "minimize":         "מזעור",
        "powered_by":       "עוזר AI",
        "welcome":          "שלום! 👋 אני כאן לעזור — שאלות על מוצרים, מחירים, עיצוב, או לתיאום פגישה. במה אוכל לעזור? 😊",
        "budget_reached":   "מצטערים, מכסת השימוש להיום הסתיימה. נסו שוב מחר.",
        "handoff_resolved": "חזרת לשיחה עם הבוט. במה אוכל לעזור?",
    },

    "ar": {
        "placeholder":      "اكتب رسالتك…",
        "send":             "إرسال",
        "thinking":         "يفكر…",
        "connection_error": "خطأ في الاتصال. حاول مرة أخرى.",
        "rate_limited":     "ترسل رسائل بسرعة كبيرة. يرجى الإبطاء.",
        "too_long":         "رسالتك طويلة جدا.",
        "language":         "اللغة",
        "clear":             "مسح المحادثة",
        "minimize":         "تصغير",
        "powered_by":       "مساعد ذكي",
        "welcome":          "أهلاً وسهلاً! 👋 أنا هنا لمساعدتك في المنتجات والأسعار والتصميم أو لحجز استشارة. كيف أقدر أساعدك؟ 😊",
        "budget_reached":   "نأسف، تم بلوغ حد الاستخدام لليوم. يرجى المحاولة غدا.",
    },

    "fa": {
        "placeholder":      "پیام خود را بنویسید…",
        "send":             "ارسال",
        "thinking":         "در حال فکر کردن…",
        "connection_error": "خطای اتصال. لطفا دوباره تلاش کنید.",
        "rate_limited":     "پیام‌ها را خیلی سریع ارسال می‌کنید. لطفا آهسته‌تر.",
        "too_long":         "پیام شما خیلی طولانی است.",
        "language":         "زبان",
        "clear":             "پاک کردن گفتگو",
        "minimize":         "کوچک کردن",
        "powered_by":       "دستیار هوشمند",
        "welcome":          "سلام! 👋 برای کمک درباره محصولات، قیمت‌ها، مشاوره طراحی یا رزرو مشاوره اینجام. چطور می‌تونم کمکت کنم؟ 😊",
        "budget_reached":   "متأسفیم، حد مصرف امروز پر شده است. لطفا فردا تلاش کنید.",
    },

    "th": {
        "placeholder":      "พิมพ์ข้อความของคุณ…",
        "send":             "ส่ง",
        "thinking":         "กำลังคิด…",
        "connection_error": "การเชื่อมต่อขัดข้อง โปรดลองอีกครั้ง",
        "rate_limited":     "คุณส่งข้อความเร็วเกินไป โปรดช้าลง",
        "too_long":         "ข้อความของคุณยาวเกินไป",
        "language":         "ภาษา",
        "clear":             "ล้างการสนทนา",
        "minimize":         "ย่อเล็กสุด",
        "powered_by":       "ผู้ช่วย AI",
        "welcome":          "สวัสดีครับ/ค่ะ! 👋 ยินดีต้อนรับ — สอบถามเรื่องสินค้า ราคา ไอเดียตกแต่ง หรือนัดปรึกษาได้เลย 😊",
        "budget_reached":   "ขออภัย ถึงขีดจำกัดการใช้งานวันนี้แล้ว โปรดลองใหม่พรุ่งนี้",
        "handoff_resolved": "กลับมาคุยกับบอทแล้วครับ/ค่ะ สอบถามได้เลย",
    },

    "fr": {
        "placeholder":      "Écrivez votre message…",
        "send":             "Envoyer",
        "thinking":         "Réflexion…",
        "connection_error": "Erreur de connexion. Veuillez réessayer.",
        "rate_limited":     "Vous envoyez des messages trop vite. Ralentissez.",
        "too_long":         "Votre message est trop long.",
        "language":         "Langue",
        "clear":             "Effacer la conversation",
        "minimize":         "Réduire",
        "powered_by":       "Assistant IA",
        "welcome":          "Bonjour ! 👋 Je suis là pour vous aider — produits, tarifs, conseils déco ou prise de rendez-vous. Comment puis-je vous aider ? 😊",
        "budget_reached":   "Désolé, la limite d'utilisation du jour est atteinte. Réessayez demain.",
    },

    "es": {
        "placeholder":      "Escribe tu mensaje…",
        "send":             "Enviar",
        "thinking":         "Pensando…",
        "connection_error": "Error de conexión. Inténtalo de nuevo.",
        "rate_limited":     "Estás enviando mensajes demasiado rápido. Más despacio.",
        "too_long":         "Tu mensaje es demasiado largo.",
        "language":         "Idioma",
        "clear":             "Borrar conversación",
        "minimize":         "Minimizar",
        "powered_by":       "Asistente IA",
        "welcome":          "¡Hola! 👋 Estoy aquí para ayudarte con productos, precios, ideas de diseño o para agendar una consulta. ¿En qué puedo ayudarte? 😊",
        "budget_reached":   "Lo sentimos, se alcanzó el límite diario. Vuelve a intentarlo mañana.",
    },

    "de": {
        "placeholder":      "Nachricht schreiben…",
        "send":             "Senden",
        "thinking":         "Denke nach…",
        "connection_error": "Verbindungsfehler. Bitte erneut versuchen.",
        "rate_limited":     "Du sendest zu schnell. Bitte langsamer.",
        "too_long":         "Deine Nachricht ist zu lang.",
        "language":         "Sprache",
        "clear":             "Unterhaltung löschen",
        "minimize":         "Minimieren",
        "powered_by":       "KI-Assistent",
        "welcome":          "Hallo! 👋 Ich helfe gerne weiter — Produkte, Preise, Einrichtungsideen oder Terminbuchung. Wie kann ich Ihnen helfen? 😊",
        "budget_reached":   "Tageslimit erreicht. Bitte versuche es morgen erneut.",
    },

    "ru": {
        "placeholder":      "Введите сообщение…",
        "send":             "Отправить",
        "thinking":         "Думаю…",
        "connection_error": "Ошибка соединения. Попробуйте снова.",
        "rate_limited":     "Вы отправляете сообщения слишком быстро. Помедленнее.",
        "too_long":         "Сообщение слишком длинное.",
        "language":         "Язык",
        "clear":             "Очистить чат",
        "minimize":         "Свернуть",
        "powered_by":       "ИИ ассистент",
        "welcome":          "Здравствуйте! 👋 Я здесь, чтобы помочь — товары, цены, советы по дизайну или запись на консультацию. Чем могу помочь? 😊",
        "budget_reached":   "Дневной лимит исчерпан. Попробуйте завтра.",
    },

    "ja": {
        "placeholder":      "メッセージを入力…",
        "send":             "送信",
        "thinking":         "考え中…",
        "connection_error": "接続エラーです。再度お試しください。",
        "rate_limited":     "送信が速すぎます。少しお待ちください。",
        "too_long":         "メッセージが長すぎます。",
        "language":         "言語",
        "clear":             "会話をクリア",
        "minimize":         "最小化",
        "powered_by":       "AIアシスタント",
        "welcome":          "こんにちは！👋 商品・価格・インテリアのアドバイス・ご予約など、何でもお気軽にどうぞ 😊",
        "budget_reached":   "本日の利用上限に達しました。明日お試しください。",
    },

    "zh": {
        "placeholder":      "输入消息…",
        "send":             "发送",
        "thinking":         "思考中…",
        "connection_error": "连接错误，请重试。",
        "rate_limited":     "发送速度过快，请稍候。",
        "too_long":         "消息太长。",
        "language":         "语言",
        "clear":             "清除对话",
        "minimize":         "最小化",
        "powered_by":       "AI 助手",
        "welcome":          "您好！👋 欢迎光临 — 产品咨询、报价、装饰建议或预约均可，请问有什么能帮您的？😊",
        "budget_reached":   "今日使用额度已用完，请明天再试。",
    },

    "hi": {
        "placeholder":      "अपना संदेश लिखें…",
        "send":             "भेजें",
        "thinking":         "सोच रहा हूँ…",
        "connection_error": "कनेक्शन त्रुटि। कृपया पुनः प्रयास करें।",
        "rate_limited":     "आप बहुत तेज़ी से संदेश भेज रहे हैं।",
        "too_long":         "आपका संदेश बहुत लंबा है।",
        "language":         "भाषा",
        "clear":             "बातचीत साफ़ करें",
        "minimize":         "छोटा करें",
        "powered_by":       "AI सहायक",
        "welcome":          "नमस्ते! 👋 उत्पाद, कीमतें, डिज़ाइन सुझाव या अपॉइंटमेंट बुक करने में मदद के लिए मैं यहाँ हूँ 😊",
        "budget_reached":   "क्षमा करें, आज की सीमा समाप्त हो गई है। कल पुनः प्रयास करें।",
    },
}


# ── Public helpers ──────────────────────────────────────────────────────────


def resolve_language(lang: Optional[str]) -> str:
    """Return a supported language code, falling back to English."""
    if not lang:
        return "en"
    code = lang.strip().lower().split("-")[0].split("_")[0]
    return code if code in _BY_CODE else "en"


def get_language(code: Optional[str]) -> LanguageInfo:
    """Return metadata for ``code`` (or English if unknown)."""
    return _BY_CODE[resolve_language(code)]


def is_rtl(code: Optional[str]) -> bool:
    return get_language(code).rtl


def get_messages(code: Optional[str]) -> dict[str, str]:
    """Return UI strings for ``code``, English-filled where missing."""
    resolved = resolve_language(code)
    base = dict(MESSAGES["en"])
    base.update(MESSAGES.get(resolved, {}))
    return base
