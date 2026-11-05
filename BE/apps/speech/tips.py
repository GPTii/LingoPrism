"""Common pronunciation errors of Vietnamese learners: an error code, what happened and how to fix it (in Vietnamese).

A rule matches (expected phone, heard phone or None = missing). Hand-written from the usual teaching notes on English
and Mandarin phonetics for Vietnamese speakers; anything not listed gets the generic message.
"""
from .phonology import ZH_TONE_NAMES, base

# (language, expected, heard) -> (code, tip). heard None = the sound was missing; "*" = any other sound.
RULES = {
    ("en", "θ", "s"): ("en.TH_S", "Âm /θ/ (như think): đặt đầu lưỡi giữa hai hàm răng rồi thổi hơi, đừng rít như /s/."),
    ("en", "θ", "t"): ("en.TH_T", "Âm /θ/ (như think): lưỡi chạm nhẹ giữa hai hàm răng và thổi hơi liên tục, không bật như /t/."),
    ("en", "θ", "f"): ("en.TH_F", "Âm /θ/: dùng đầu lưỡi giữa hai răng, không dùng môi dưới chạm răng như /f/."),
    ("en", "ð", "d"): ("en.DH_D", "Âm /ð/ (như this, mother): đầu lưỡi giữa hai răng, rung dây thanh, hơi đi ra liên tục."),
    ("en", "ð", "z"): ("en.DH_Z", "Âm /ð/: đưa đầu lưỡi ra giữa hai răng, không rít sau răng như /z/."),
    ("en", "ɪ", "i"): ("en.SHIP_SHEEP", "Âm /ɪ/ (ship) ngắn và thả lỏng; /iː/ (sheep) dài và căng miệng sang hai bên."),
    ("en", "i", "ɪ"): ("en.SHEEP_SHIP", "Âm /iː/ (sheep) phải kéo dài, miệng căng như đang cười."),
    ("en", "æ", "ɛ"): ("en.CAT_BED", "Âm /æ/ (cat): mở miệng rộng hơn, hàm hạ thấp, giữa 'a' và 'e'."),
    ("en", "æ", "e"): ("en.CAT_BED", "Âm /æ/ (cat): mở miệng rộng hơn, hàm hạ thấp, giữa 'a' và 'e'."),
    ("en", "ʃ", "s"): ("en.SH_S", "Âm /ʃ/ (she): chu môi, lưỡi lùi về sau một chút, hơi ra như 'suỵt'."),
    ("en", "z", "s"): ("en.Z_S", "Âm /z/: giống /s/ nhưng rung dây thanh (đặt tay lên cổ phải thấy rung)."),
    ("en", "v", "b"): ("en.V_B", "Âm /v/: răng trên chạm nhẹ môi dưới rồi thổi hơi có rung, không mím hai môi như /b/."),
    ("en", "v", "w"): ("en.V_W", "Âm /v/: răng trên chạm môi dưới; /w/ thì tròn môi, không chạm răng."),
    ("en", "ɹ", "z"): ("en.R_Z", "Âm /r/ tiếng Anh: cong lưỡi về sau, không chạm vòm miệng, không rung như 'r' tiếng Việt."),
    ("en", "l", "n"): ("en.L_N", "Âm /l/: đầu lưỡi chạm lợi trên, hơi đi ra hai bên lưỡi, không qua mũi như /n/."),
    ("en", "n", "l"): ("en.N_L", "Âm /n/: hơi đi ra mũi (bịt mũi sẽ thấy khó nói)."),
    ("en", "tʃ", "ʃ"): ("en.CH_SH", "Âm /tʃ/ (chair): bật ra từ /t/ rồi mới thành /ʃ/."),
    ("en", "dʒ", "z"): ("en.J_Z", "Âm /dʒ/ (job): như /tʃ/ nhưng rung dây thanh; chu môi, lưỡi chạm lợi rồi bật ra."),
    ("zh", "ts.", "ts"): ("zh.ZH_Z", "zh: cong đầu lưỡi lên chạm vòm cứng phía trước (âm uốn lưỡi); z thì lưỡi thẳng, chạm răng."),
    ("zh", "ts.h", "tsh"): ("zh.CH_C", "ch: uốn lưỡi như zh và bật mạnh hơi ra; c thì lưỡi thẳng sau răng."),
    ("zh", "s.", "s"): ("zh.SH_S", "sh: cong đầu lưỡi lên (uốn lưỡi), hơi ra giữa lưỡi và vòm miệng; s thì lưỡi thẳng."),
    ("zh", "ts", "ts."): ("zh.Z_ZH", "z: đầu lưỡi thẳng, chạm sau răng trên, không uốn lưỡi."),
    ("zh", "s", "s."): ("zh.S_SH", "s: đầu lưỡi thẳng sau răng, không uốn lưỡi như sh."),
    ("zh", "tɕh", "ts.h"): ("zh.Q_CH", "q: mặt lưỡi áp vào vòm cứng, môi dẹt như cười; không uốn lưỡi như ch."),
    ("zh", "ɕ", "s"): ("zh.X_S", "x: mặt lưỡi nâng lên sát vòm cứng, môi dẹt (gần 'x' tiếng Việt nhưng mỏng hơn)."),
    ("zh", "ɕ", "s."): ("zh.X_SH", "x: mặt lưỡi (không phải đầu lưỡi) nâng lên; sh thì uốn đầu lưỡi."),
    ("zh", "y", "u"): ("zh.U_UMLAUT", "ü: đặt lưỡi như 'i' rồi tròn môi lại (như 'uy' nói liền một âm)."),
    ("zh", "y", "i"): ("zh.U_UMLAUT", "ü: giữ lưỡi như 'i' nhưng tròn môi lại."),
    ("zh", "ɻ", "l"): ("zh.R_L", "r: uốn đầu lưỡi lên gần vòm miệng, không chạm như l."),
    ("zh", "ɻ", "z"): ("zh.R_Z", "r: uốn lưỡi, hơi rung nhẹ, gần 'r' của tiếng Anh, không phải 'z'."),
    ("zh", "ŋ", "n"): ("zh.NG_N", "-ng cuối (ang, eng, ing): cuống lưỡi nâng lên, miệng mở; -n thì đầu lưỡi chạm lợi."),
    ("zh", "n", "ŋ"): ("zh.N_NG", "-n cuối (an, en, in): kết thúc bằng đầu lưỡi chạm lợi trên."),
    ("zh", "n", "l"): ("zh.N_L", "n: hơi đi ra mũi; l thì đi ra hai bên lưỡi."),
    ("zh", "l", "n"): ("zh.L_N", "l: hơi đi ra hai bên lưỡi, không ra mũi."),
    ("vi", "n", "l"): ("vi.N_L", "n: hơi đi ra mũi; l: đầu lưỡi chạm lợi, hơi ra hai bên."),
    ("vi", "l", "n"): ("vi.L_N", "l: đầu lưỡi chạm lợi, hơi ra hai bên lưỡi, không ra mũi."),
}

# missing final sounds
FINAL_DROPPED = {
    "en": ("en.FINAL_DROPPED", "Âm cuối /{e}/ bị nuốt. Tiếng Anh phải nói rõ âm cuối (cat-s, stop-p, bed-d)."),
    "vi": ("vi.FINAL_DROPPED", "Âm cuối /{e}/ chưa rõ."),
    "zh": ("zh.FINAL_DROPPED", "Âm cuối /{e}/ chưa rõ."),
}

# accepted as the same sound (regional Vietnamese, US / UK English)
EQUIVALENT = {
    "vi": {frozenset({"s", "ʂ"}), frozenset({"tʃ", "ʈ"}), frozenset({"z", "ɹ"}), frozenset({"z", "j"}),
           frozenset({"n", "ŋ"}), frozenset({"t", "k"})},
    "en": {frozenset({"ɑ", "ɔ"}), frozenset({"t", "ɾ"}), frozenset({"d", "ɾ"}), frozenset({"ə", "ʌ"}),
           frozenset({"ɚ", "ɜ"}), frozenset({"ɪ", "ᵻ"}), frozenset({"ə", "ᵻ"}), frozenset({"o", "oʊ"})},
    "zh": set(),
}


def lang_key(language: str) -> str:
    return "zh" if language.startswith("zh") else language


def phone_error(language: str, expected: str, heard: str | None, last_in_unit: bool) -> tuple[str, str]:
    lk = lang_key(language)
    e, h = base(expected), base(heard) if heard else None
    rule = RULES.get((lk, e, h))
    if rule:
        return rule
    if h is None:
        if last_in_unit and lk in FINAL_DROPPED:
            code, tip = FINAL_DROPPED[lk]
            return code, tip.format(e=e)
        return f"{lk}.MISSING", f"Thiếu âm /{e}/."
    return f"{lk}.SUBST", f"Âm /{e}/ nghe giống /{h}/."


def tone_error(language: str, expected, heard) -> tuple[str, str]:
    if language == "vi":
        return "vi.TONE", f"Thanh {expected} nghe thành thanh {heard}."
    return f"zh.TONE{expected}_AS_{heard}", (f"Cần {ZH_TONE_NAMES.get(expected, expected)}, máy nghe như "
                                            f"{ZH_TONE_NAMES.get(heard, heard)}." + {
        1: " Thanh 1 giữ cao và bằng từ đầu đến cuối.",
        2: " Thanh 2 đi lên như khi hỏi 'hả?'.",
        3: " Thanh 3 hạ thấp xuống rồi mới lên (đọc nhanh trong câu thì chỉ hạ thấp).",
        4: " Thanh 4 rơi mạnh từ cao xuống thấp, dứt khoát.",
    }.get(expected, ""))
