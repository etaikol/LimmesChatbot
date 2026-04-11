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
    "placeholder":              "Type your message…",
    "send":                     "Send",
    "thinking":                 "Thinking…",
    "connection_error":         "Something went wrong on our end. Please try again in a moment.",
    "rate_limited":             "You're sending messages a little too fast — slow down and try again 😊",
    "too_long":                 "That message is a bit too long. Can you shorten it a little?",
    "language":                 "Language",
    "clear":                    "Clear conversation",
    "minimize":                 "Minimize",
    "powered_by":               "AI assistant",
    "welcome":                  "Hello! 👋 Welcome — I'm here to help with products, pricing, design tips, or booking a consultation. What can I do for you? 😊",
    "budget_reached":           "Sorry, today's usage limit has been reached. Please try again tomorrow.",
    "handoff_resolved":         "You are now back with the bot. How can I help? 😊",
    "handoff_active":           "Connected to a human agent",
    "handoff_waiting":          "Our team has been notified and will be with you shortly. Feel free to keep typing — we'll see everything you write. 💬",
    "handoff_connecting":       "Got it! I'm connecting you with our team right now — please hold on for just a moment. 🤝",
    "gibberish":                "Hmm, I didn't quite catch that. Could you rephrase? 😊",
    "duplicate_message":        "Looks like you sent the same message twice — no worries, I got it the first time! 😄",
    "session_blocked":          "You've sent a lot of messages that I couldn't understand. Please take a short break and try again in {seconds} seconds.",
    "blocked_temporarily":      "I'm having trouble understanding your messages right now. Please try again in {seconds} seconds.",
    "off_topic":                "I'm here to help with questions about our business. For other topics, a general assistant like ChatGPT would be a better fit! 😊",
    "server_error":             "Something went wrong on our end — our team has been notified. Please try again in a moment.",
    # Feedback
    "feedback_thanks":          "Thanks for your feedback! 👍",
    "feedback_sorry":           "Sorry to hear that. We'll work to improve! 🙏",
    "feedback_prompt":          "Was this answer helpful?",
    "thumbs_up":                "👍",
    "thumbs_down":              "👎",
    # Analytics / returning user
    "welcome_back":             "Welcome back! 👋 How can I help you today?",
    # LINE Login
    "line_login_prompt":        "Log in with LINE for a personalized experience",
    "line_login_success":       "You're logged in! Welcome, {name} 👋",
    # Campaign
    "campaign_sent":            "Campaign message sent successfully",
}

MESSAGES: dict[str, dict[str, str]] = {
    "en": _EN,

    "he": {
        "placeholder":         "כתוב/כתבי הודעה…",
        "send":                "שליחה",
        "thinking":            "חושב…",
        "connection_error":    "משהו השתבש אצלנו. אפשר לנסות שוב? 😊",
        "rate_limited":        "שלחת הודעות קצת מהר מדי — נשמנו רגע, ננסה שוב 😊",
        "too_long":            "ההודעה קצת ארוכה מדי, אפשר לקצר?",
        "language":            "שפה",
        "clear":               "ניקוי שיחה",
        "minimize":            "מזעור",
        "powered_by":          "עוזר AI",
        "welcome":             "שלום! 👋 אני כאן לעזור — שאלות על מוצרים, מחירים, עיצוב, או לתיאום פגישה. במה אוכל לעזור? 😊",
        "budget_reached":      "מצטערים, מכסת השימוש להיום הסתיימה. נסו שוב מחר.",
        "handoff_resolved":    "חזרת לשיחה עם הבוט. במה אוכל לעזור? 😊",
        "handoff_active":      "מחובר/ת לנציג אנושי",
        "handoff_waiting":     "הצוות שלנו קיבל הודעה ויחזור אליך בקרוב. תוכל/י להמשיך לכתוב — נראה הכל 💬",
        "handoff_connecting":  "מצוין! אני מעביר/ה אותך לצוות שלנו עכשיו — רגע קטן 🤝",
        "gibberish":           "לא הבנתי לגמרי. תנסה/י לנסח מחדש? 😊",
        "duplicate_message":   "נראה ששלחת את אותה הודעה פעמיים — לא נורא, קיבלתי 😄",
        "session_blocked":     "שלחת הרבה הודעות שלא הצלחתי להבין. אנא נסו שוב בעוד {seconds} שניות.",
        "blocked_temporarily": "קשה לי להבין את ההודעות שלך כרגע. נסו שוב בעוד {seconds} שניות.",
        "off_topic":           "אני כאן לשאלות על העסק שלנו. לנושאים אחרים, עוזר כמו ChatGPT יתאים יותר 😊",
        "server_error":        "משהו השתבש אצלנו — הצוות קיבל הודעה. אפשר לנסות שוב? 😊",
        "feedback_thanks":     "תודה על המשוב! 👍",
        "feedback_sorry":      "מצטערים לשמוע. נשתפר! 🙏",
        "feedback_prompt":     "התשובה הייתה מועילה?",
        "welcome_back":        "שמחים לראותך שוב! 👋 במה אוכל לעזור?",
        "line_login_prompt":   "התחבר/י עם LINE לחוויה מותאמת אישית",
        "line_login_success":  "התחברת בהצלחה! ברוך/ה הבא/ה, {name} 👋",
    },

    "ar": {
        "placeholder":         "اكتب رسالتك…",
        "send":                "إرسال",
        "thinking":            "يفكر…",
        "connection_error":    "حدث خطأ من جانبنا. هل يمكنك المحاولة مجدداً؟ 😊",
        "rate_limited":        "أرسلت رسائل بسرعة كبيرة قليلاً — خذ لحظة وحاول مجدداً 😊",
        "too_long":            "رسالتك طويلة قليلاً، هل يمكنك اختصارها؟",
        "language":            "اللغة",
        "clear":               "مسح المحادثة",
        "minimize":            "تصغير",
        "powered_by":          "مساعد ذكي",
        "welcome":             "أهلاً وسهلاً! 👋 أنا هنا لمساعدتك في المنتجات والأسعار والتصميم أو لحجز استشارة. كيف أقدر أساعدك؟ 😊",
        "budget_reached":      "نأسف، تم بلوغ حد الاستخدام لليوم. يرجى المحاولة غداً.",
        "handoff_waiting":     "تم إبلاغ فريقنا وسيتواصل معك قريباً. يمكنك الاستمرار في الكتابة 💬",
        "handoff_connecting":  "حسناً! أقوم بتحويلك إلى فريقنا الآن — لحظة من فضلك 🤝",
        "gibberish":           "لم أفهم ذلك جيداً. هل يمكنك إعادة الصياغة؟ 😊",
        "session_blocked":     "لم أتمكن من فهم رسائلك. يرجى المحاولة مجدداً بعد {seconds} ثانية.",
        "off_topic":           "أنا هنا للمساعدة في أسئلة عن نشاطنا التجاري. للمواضيع الأخرى، مساعد عام سيكون أنسب 😊",
        "server_error":        "حدث خطأ من جانبنا — فريقنا أُبلغ. يرجى المحاولة مجدداً 😊",
        "feedback_thanks":     "شكراً لملاحظاتك! 👍",
        "feedback_sorry":      "نأسف لذلك. سنعمل على التحسين! 🙏",
        "feedback_prompt":     "هل كانت هذه الإجابة مفيدة؟",
        "welcome_back":        "أهلاً بعودتك! 👋 كيف أقدر أساعدك؟",
        "line_login_prompt":   "سجّل دخولك عبر LINE لتجربة مخصصة",
        "line_login_success":  "تم تسجيل الدخول! أهلاً {name} 👋",
    },

    "fa": {
        "placeholder":         "پیام خود را بنویسید…",
        "send":                "ارسال",
        "thinking":            "در حال فکر کردن…",
        "connection_error":    "مشکلی از سمت ما پیش آمد. لطفاً دوباره امتحان کنید 😊",
        "rate_limited":        "پیام‌ها را کمی سریع می‌فرستید — یک لحظه صبر کرده دوباره امتحان کنید 😊",
        "too_long":            "پیام کمی طولانی است، می‌شه کوتاهش کنید؟",
        "language":            "زبان",
        "clear":               "پاک کردن گفتگو",
        "minimize":            "کوچک کردن",
        "powered_by":          "دستیار هوشمند",
        "welcome":             "سلام! 👋 برای کمک درباره محصولات، قیمت‌ها، مشاوره طراحی یا رزرو مشاوره اینجام. چطور می‌تونم کمکت کنم؟ 😊",
        "budget_reached":      "متأسفیم، حد مصرف امروز پر شده است. لطفاً فردا تلاش کنید.",
        "handoff_waiting":     "تیم ما مطلع شد و به زودی با شما در تماس خواهد بود 💬",
        "handoff_connecting":  "باشه! الان شما را به تیممون وصل می‌کنم — یه لحظه 🤝",
        "gibberish":           "متوجه نشدم. می‌شه دوباره بنویسید؟ 😊",
        "session_blocked":     "پیام‌های شما قابل فهم نبودند. لطفاً بعد از {seconds} ثانیه دوباره تلاش کنید.",
        "off_topic":           "من اینجام که به سوالات مربوط به کسب‌وکارمون جواب بدم. برای سایر موضوعات، یه دستیار عمومی مناسب‌تره 😊",
        "server_error":        "مشکلی از سمت ما پیش آمد — تیم ما مطلع شد. لطفاً دوباره امتحان کنید 😊",
        "feedback_thanks":     "ممنون از بازخوردتان! 👍",
        "feedback_sorry":      "متأسفیم. بهتر می‌کنیم! 🙏",
        "feedback_prompt":     "آیا این پاسخ مفید بود؟",
        "welcome_back":        "خوش برگشتید! 👋 چطور کمکتون کنم؟",
        "line_login_prompt":   "برای تجربه شخصی‌سازی شده با LINE وارد شوید",
        "line_login_success":  "ورود موفق! خوش آمدید {name} 👋",
    },

    "th": {
        "placeholder":         "พิมพ์ข้อความของคุณ…",
        "send":                "ส่ง",
        "thinking":            "กำลังคิด…",
        "connection_error":    "เกิดข้อผิดพลาดจากฝั่งเรา โปรดลองอีกครั้ง 😊",
        "rate_limited":        "ส่งข้อความเร็วเกินไปนิดหน่อย — พักสักครู่แล้วลองใหม่นะครับ/ค่ะ 😊",
        "too_long":            "ข้อความยาวเกินไปนิดหน่อย ลองสั้นลงได้ไหมครับ/ค่ะ?",
        "language":            "ภาษา",
        "clear":               "ล้างการสนทนา",
        "minimize":            "ย่อเล็กสุด",
        "powered_by":          "ผู้ช่วย AI",
        "welcome":             "สวัสดีครับ/ค่ะ! 👋 ยินดีต้อนรับ — สอบถามเรื่องสินค้า ราคา ไอเดียตกแต่ง หรือนัดปรึกษาได้เลย 😊",
        "budget_reached":      "ขออภัย ถึงขีดจำกัดการใช้งานวันนี้แล้ว โปรดลองใหม่พรุ่งนี้",
        "handoff_resolved":    "กลับมาคุยกับบอทแล้วครับ/ค่ะ สอบถามได้เลย 😊",
        "handoff_active":      "เชื่อมต่อกับเจ้าหน้าที่แล้ว",
        "handoff_waiting":     "ทีมงานได้รับแจ้งแล้วและจะติดต่อกลับเร็วๆ นี้ครับ/ค่ะ พิมพ์ต่อได้เลย 💬",
        "handoff_connecting":  "ได้เลย! กำลังโอนสายให้ทีมงานเลยครับ/ค่ะ — รอสักครู่นะ 🤝",
        "gibberish":           "ไม่แน่ใจว่าเข้าใจถูกไหม ลองพิมพ์ใหม่ได้ไหมครับ/ค่ะ? 😊",
        "duplicate_message":   "ดูเหมือนส่งข้อความซ้ำกัน — ไม่เป็นไร ได้รับแล้วครับ/ค่ะ 😄",
        "session_blocked":     "ส่งข้อความที่ไม่สามารถเข้าใจได้หลายครั้ง โปรดลองใหม่ใน {seconds} วินาที",
        "off_topic":           "ผม/หนูเป็นผู้ช่วยสำหรับคำถามเกี่ยวกับธุรกิจของเราครับ/ค่ะ สำหรับเรื่องอื่นๆ ลอง ChatGPT ดูนะครับ/ค่ะ 😊",
        "server_error":        "เกิดข้อผิดพลาดจากฝั่งเรา — ทีมงานได้รับแจ้งแล้ว โปรดลองอีกครั้ง 😊",
        "feedback_thanks":     "ขอบคุณสำหรับความคิดเห็น! 👍",
        "feedback_sorry":      "ขอโทษด้วย เราจะปรับปรุงให้ดีขึ้น! 🙏",
        "feedback_prompt":     "คำตอบนี้เป็นประโยชน์ไหมครับ/ค่ะ?",
        "welcome_back":        "ยินดีต้อนรับกลับ! 👋 สอบถามได้เลยครับ/ค่ะ",
        "line_login_prompt":   "เข้าสู่ระบบด้วย LINE เพื่อประสบการณ์ที่เหมาะกับคุณ",
        "line_login_success":  "เข้าสู่ระบบสำเร็จ! ยินดีต้อนรับ {name} 👋",
    },

    "fr": {
        "placeholder":         "Écrivez votre message…",
        "send":                "Envoyer",
        "thinking":            "Réflexion…",
        "connection_error":    "Quelque chose a mal tourné de notre côté. Réessayez dans un moment 😊",
        "rate_limited":        "Vous envoyez des messages un peu trop vite — une pause et réessayez 😊",
        "too_long":            "Votre message est un peu long, pourriez-vous le raccourcir ?",
        "language":            "Langue",
        "clear":               "Effacer la conversation",
        "minimize":            "Réduire",
        "powered_by":          "Assistant IA",
        "welcome":             "Bonjour ! 👋 Je suis là pour vous aider — produits, tarifs, conseils déco ou prise de rendez-vous. Comment puis-je vous aider ? 😊",
        "budget_reached":      "Désolé, la limite d'utilisation du jour est atteinte. Réessayez demain.",
        "handoff_waiting":     "Notre équipe a été notifiée et reviendra vers vous bientôt. Continuez à écrire 💬",
        "handoff_connecting":  "Très bien ! Je vous connecte avec notre équipe maintenant — un instant 🤝",
        "gibberish":           "Je n'ai pas bien compris. Pourriez-vous reformuler ? 😊",
        "session_blocked":     "Trop de messages incompréhensibles. Réessayez dans {seconds} secondes.",
        "off_topic":           "Je suis là pour les questions sur notre activité. Pour d'autres sujets, un assistant général sera plus adapté 😊",
        "server_error":        "Une erreur s'est produite de notre côté — nos équipes ont été notifiées. Réessayez 😊",
        "feedback_thanks":     "Merci pour votre retour ! 👍",
        "feedback_sorry":      "Désolé. Nous allons nous améliorer ! 🙏",
        "feedback_prompt":     "Cette réponse vous a-t-elle été utile ?",
        "welcome_back":        "Ravi de vous revoir ! 👋 Comment puis-je vous aider ?",
        "line_login_prompt":   "Connectez-vous avec LINE pour une expérience personnalisée",
        "line_login_success":  "Vous êtes connecté ! Bienvenue, {name} 👋",
    },

    "es": {
        "placeholder":         "Escribe tu mensaje…",
        "send":                "Enviar",
        "thinking":            "Pensando…",
        "connection_error":    "Algo salió mal de nuestro lado. ¿Intentas de nuevo? 😊",
        "rate_limited":        "Estás enviando mensajes un poco rápido — espera un momento 😊",
        "too_long":            "Tu mensaje es un poco largo, ¿puedes acortarlo?",
        "language":            "Idioma",
        "clear":               "Borrar conversación",
        "minimize":            "Minimizar",
        "powered_by":          "Asistente IA",
        "welcome":             "¡Hola! 👋 Estoy aquí para ayudarte con productos, precios, ideas de diseño o para agendar una consulta. ¿En qué puedo ayudarte? 😊",
        "budget_reached":      "Lo sentimos, se alcanzó el límite diario. Vuelve a intentarlo mañana.",
        "handoff_waiting":     "Nuestro equipo ha sido notificado y estará contigo pronto. Sigue escribiendo 💬",
        "handoff_connecting":  "¡Entendido! Te conecto con nuestro equipo ahora mismo — un momento 🤝",
        "gibberish":           "No entendí bien eso. ¿Puedes reformularlo? 😊",
        "session_blocked":     "Demasiados mensajes que no pude entender. Intenta de nuevo en {seconds} segundos.",
        "off_topic":           "Estoy aquí para preguntas sobre nuestro negocio. Para otros temas, un asistente general es más adecuado 😊",
        "server_error":        "Algo salió mal de nuestro lado — el equipo fue notificado. Intenta de nuevo 😊",
        "feedback_thanks":     "¡Gracias por tu opinión! 👍",
        "feedback_sorry":      "Lo sentimos. ¡Vamos a mejorar! 🙏",
        "feedback_prompt":     "¿Te fue útil esta respuesta?",
        "welcome_back":        "¡Bienvenido de nuevo! 👋 ¿En qué te puedo ayudar?",
        "line_login_prompt":   "Inicia sesión con LINE para una experiencia personalizada",
        "line_login_success":  "¡Has iniciado sesión! Bienvenido, {name} 👋",
    },

    "de": {
        "placeholder":         "Nachricht schreiben…",
        "send":                "Senden",
        "thinking":            "Denke nach…",
        "connection_error":    "Bei uns ist etwas schiefgelaufen. Bitte versuche es gleich erneut 😊",
        "rate_limited":        "Du sendest etwas zu schnell — kurze Pause, dann nochmal 😊",
        "too_long":            "Deine Nachricht ist etwas lang — kannst du sie kürzen?",
        "language":            "Sprache",
        "clear":               "Unterhaltung löschen",
        "minimize":            "Minimieren",
        "powered_by":          "KI-Assistent",
        "welcome":             "Hallo! 👋 Ich helfe gerne weiter — Produkte, Preise, Einrichtungsideen oder Terminbuchung. Wie kann ich Ihnen helfen? 😊",
        "budget_reached":      "Tageslimit erreicht. Bitte versuche es morgen erneut.",
        "handoff_waiting":     "Unser Team wurde benachrichtigt und meldet sich gleich. Schreib gerne weiter 💬",
        "handoff_connecting":  "Verstanden! Ich verbinde dich jetzt mit unserem Team — einen Moment 🤝",
        "gibberish":           "Das habe ich leider nicht verstanden. Kannst du es umformulieren? 😊",
        "session_blocked":     "Zu viele unverständliche Nachrichten. Bitte versuche es in {seconds} Sekunden erneut.",
        "off_topic":           "Ich bin für Fragen zu unserem Geschäft da. Für andere Themen ist ein allgemeiner Assistent besser geeignet 😊",
        "server_error":        "Bei uns ist etwas schiefgelaufen — das Team wurde benachrichtigt. Bitte erneut versuchen 😊",
        "feedback_thanks":     "Danke für Ihr Feedback! 👍",
        "feedback_sorry":      "Das tut uns leid. Wir arbeiten daran! 🙏",
        "feedback_prompt":     "War diese Antwort hilfreich?",
        "welcome_back":        "Willkommen zurück! 👋 Wie kann ich Ihnen helfen?",
        "line_login_prompt":   "Melden Sie sich mit LINE an für ein personalisiertes Erlebnis",
        "line_login_success":  "Angemeldet! Willkommen, {name} 👋",
    },

    "ru": {
        "placeholder":         "Введите сообщение…",
        "send":                "Отправить",
        "thinking":            "Думаю…",
        "connection_error":    "Что-то пошло не так с нашей стороны. Попробуйте ещё раз 😊",
        "rate_limited":        "Вы отправляете сообщения слишком быстро — сделайте паузу и попробуйте снова 😊",
        "too_long":            "Сообщение немного длинновато, можете сократить?",
        "language":            "Язык",
        "clear":               "Очистить чат",
        "minimize":            "Свернуть",
        "powered_by":          "ИИ ассистент",
        "welcome":             "Здравствуйте! 👋 Я здесь, чтобы помочь — товары, цены, советы по дизайну или запись на консультацию. Чем могу помочь? 😊",
        "budget_reached":      "Дневной лимит исчерпан. Попробуйте завтра.",
        "handoff_waiting":     "Наша команда получила уведомление и скоро свяжется с вами. Продолжайте писать 💬",
        "handoff_connecting":  "Понял! Сейчас соединяю вас с нашей командой — одну секунду 🤝",
        "gibberish":           "Не совсем понял. Можете перефразировать? 😊",
        "duplicate_message":   "Похоже, вы отправили одно и то же сообщение дважды — ничего страшного, я уже получил 😄",
        "session_blocked":     "Слишком много непонятных сообщений. Попробуйте снова через {seconds} секунд.",
        "off_topic":           "Я здесь для вопросов о нашем бизнесе. Для других тем лучше подойдёт общий ассистент вроде ChatGPT 😊",
        "server_error":        "Что-то пошло не так с нашей стороны — команда уведомлена. Попробуйте ещё раз 😊",
        "feedback_thanks":     "Спасибо за отзыв! 👍",
        "feedback_sorry":      "Извините. Мы будем работать над улучшением! 🙏",
        "feedback_prompt":     "Был ли этот ответ полезен?",
        "welcome_back":        "С возвращением! 👋 Чем могу помочь?",
        "line_login_prompt":   "Войдите через LINE для персонализированного опыта",
        "line_login_success":  "Вы вошли! Добро пожаловать, {name} 👋",
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
        "feedback_thanks":  "フィードバックありがとうございます！👍",
        "feedback_sorry":   "申し訳ありません。改善に努めます！🙏",
        "feedback_prompt":  "この回答は役に立ちましたか？",
        "welcome_back":     "おかえりなさい！👋 何かお手伝いできますか？",
        "line_login_prompt": "LINEでログインしてパーソナライズ体験を",
        "line_login_success": "ログインしました！ようこそ、{name}さん 👋",
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
        "feedback_thanks":  "感谢您的反馈！👍",
        "feedback_sorry":   "很抱歉。我们会改进的！🙏",
        "feedback_prompt":  "这个回答对您有帮助吗？",
        "welcome_back":     "欢迎回来！👋 有什么可以帮您的？",
        "line_login_prompt": "使用LINE登录以获得个性化体验",
        "line_login_success": "登录成功！欢迎，{name} 👋",
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
        "feedback_thanks":  "आपकी प्रतिक्रिया के लिए धन्यवाद! 👍",
        "feedback_sorry":   "क्षमा करें। हम सुधार करेंगे! 🙏",
        "feedback_prompt":  "क्या यह उत्तर सहायक था?",
        "welcome_back":     "वापस स्वागत है! 👋 कैसे मदद कर सकता हूँ?",
        "line_login_prompt": "व्यक्तिगत अनुभव के लिए LINE से लॉगिन करें",
        "line_login_success": "लॉगिन सही! स्वागत है, {name} 👋",
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
