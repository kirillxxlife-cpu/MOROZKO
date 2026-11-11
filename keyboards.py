"""Все клавиатуры. Тексты кнопок — здесь, для краткости."""
from datetime import date
from vkbottle import Keyboard, KeyboardButtonColor, Text, OpenLink

WD_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

def kb_main() -> str:
    kb = Keyboard(one_time=False, inline=False)
    kb.add(Text("🎅 Забронировать", payload={"cmd": "book"}), color=KeyboardButtonColor.POSITIVE)
    kb.row()
    kb.add(Text("📅 Свободные даты", payload={"cmd": "free_dates"}), color=KeyboardButtonColor.PRIMARY)
    kb.row()
    kb.add(Text("👤 Живой человек", payload={"cmd": "operator"}), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()

def kb_welcome() -> str:
    return kb_main()

def kb_children_count() -> str:
    kb = Keyboard(one_time=False, inline=False)
    kb.add(Text("1 ребёнок", payload={"cmd": "children_1"}), color=KeyboardButtonColor.PRIMARY)
    kb.row()
    kb.add(Text("2 ребёнка", payload={"cmd": "children_2"}), color=KeyboardButtonColor.PRIMARY)
    kb.row()
    kb.add(Text("3 ребёнка", payload={"cmd": "children_3"}), color=KeyboardButtonColor.PRIMARY)
    kb.row()
    kb.add(Text("4 и больше", payload={"cmd": "children_4"}), color=KeyboardButtonColor.SECONDARY)
    kb.row()
    kb.add(Text("← Назад", payload={"cmd": "back_main"}), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()

def kb_age() -> str:
    kb = Keyboard(one_time=False, inline=False)
    kb.add(Text("1–3 года", payload={"cmd": "age_1_3"}), color=KeyboardButtonColor.PRIMARY)
    kb.row()
    kb.add(Text("4–7 лет", payload={"cmd": "age_4_7"}), color=KeyboardButtonColor.PRIMARY)
    kb.row()
    kb.add(Text("8–12 лет", payload={"cmd": "age_8_12"}), color=KeyboardButtonColor.PRIMARY)
    kb.row()
    kb.add(Text("← Назад", payload={"cmd": "back_main"}), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()

def kb_package() -> str:
    kb = Keyboard(one_time=False, inline=False)
    kb.add(Text("🎁 Мини — 3 500 ₽", payload={"cmd": "pkg_mini"}), color=KeyboardButtonColor.SECONDARY)
    kb.row()
    kb.add(Text("⭐ Стандарт — 5 500 ₽", payload={"cmd": "pkg_standard"}), color=KeyboardButtonColor.POSITIVE)
    kb.row()
    kb.add(Text("👑 Премиум — 8 500 ₽", payload={"cmd": "pkg_premium"}), color=KeyboardButtonColor.PRIMARY)
    kb.row()
    kb.add(Text("← Назад", payload={"cmd": "back_main"}), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()

def kb_extras(draft: dict) -> str:
    kb = Keyboard(one_time=False, inline=False)
    chosen = set(draft.get("extras", []))
    mk = lambda k, l: f"{'✅ ' if k in chosen else ''}{l}"
    kb.add(Text(mk("photo", "📸 Фотограф +2 000 ₽"), payload={"cmd": "extra_photo"}), color=KeyboardButtonColor.SECONDARY)
    kb.row()
    kb.add(Text(mk("cake", "🎂 Торт +1 500 ₽"), payload={"cmd": "extra_cake"}), color=KeyboardButtonColor.SECONDARY)
    kb.row()
    kb.add(Text(mk("balls", "🎈 Шары +800 ₽"), payload={"cmd": "extra_balls"}), color=KeyboardButtonColor.SECONDARY)
    kb.row()
    kb.add(Text("✅ Готово, выбрать дату", payload={"cmd": "extras_done"}), color=KeyboardButtonColor.POSITIVE)
    kb.row()
    kb.add(Text("← К пакетам", payload={"cmd": "back_package"}), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()

def kb_dates(dates_summary: list[dict]) -> str:
    kb = Keyboard(one_time=False, inline=False)
    col = 0
    for item in dates_summary:
        d: date = item["date"]
        free = item["free"]
        if free == 0:
            kb.add(Text(f"{d.day} {WD_RU[d.weekday()]} · занято", payload={"cmd": "noop"}),
                   color=KeyboardButtonColor.SECONDARY)
        else:
            kb.add(Text(f"{d.day} {WD_RU[d.weekday()]} · {free} окон",
                        payload={"cmd": f"date_{d.isoformat()}"}),
                   color=KeyboardButtonColor.PRIMARY)
        col += 1
        if col == 4:
            kb.row()
            col = 0
    if col:
        kb.row()
    kb.add(Text("← Назад", payload={"cmd": "back_main"}), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()

def kb_times(slots: list) -> str:
    kb = Keyboard(one_time=False, inline=False)
    col = 0
    for slot in slots:
        t = slot.time.strftime("%H:%M")
        if slot.status.value == "free":
            kb.add(Text(t, payload={"cmd": f"slot_{slot.id}"}), color=KeyboardButtonColor.PRIMARY)
        else:
            kb.add(Text(f"{t} — занято", payload={"cmd": "noop"}), color=KeyboardButtonColor.SECONDARY)
        col += 1
        if col == 3:
            kb.row()
            col = 0
    if col:
        kb.row()
    kb.add(Text("← К датам", payload={"cmd": "back_dates"}), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()

def kb_review() -> str:
    kb = Keyboard(one_time=False, inline=False)
    kb.add(Text("✅ Всё верно", payload={"cmd": "review_ok"}), color=KeyboardButtonColor.POSITIVE)
    kb.row()
    kb.add(Text("✏️ Изменить", payload={"cmd": "review_edit"}), color=KeyboardButtonColor.SECONDARY)
    kb.row()
    kb.add(Text("✖ Отменить", payload={"cmd": "cancel"}), color=KeyboardButtonColor.NEGATIVE)
    return kb.get_json()

def kb_consent() -> str:
    kb = Keyboard(one_time=False, inline=False)
    kb.add(Text("✅ Согласен и оплатить", payload={"cmd": "consent_yes"}), color=KeyboardButtonColor.POSITIVE)
    kb.row()
    kb.add(Text("← Назад", payload={"cmd": "review_back"}), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()

def kb_payment() -> str:
    kb = Keyboard(one_time=False, inline=False)
    kb.add(Text("💳 Оплатить картой / СБП", payload={"cmd": "pay_now"}), color=KeyboardButtonColor.POSITIVE)
    kb.row()
    kb.add(Text("✖ Отменить", payload={"cmd": "cancel"}), color=KeyboardButtonColor.NEGATIVE)
    return kb.get_json()

def kb_after_paid(share_url: str, code: str) -> str:
    kb = Keyboard(one_time=False, inline=False)
    kb.add(OpenLink(share_url, "📤 Поделиться с родными"), color=KeyboardButtonColor.POSITIVE)
    kb.row()
    kb.add(Text("🎁 Получить свой промокод", payload={"cmd": "show_my_code"}), color=KeyboardButtonColor.PRIMARY)
    kb.row()
    kb.add(Text("🏠 В главное меню", payload={"cmd": "back_main"}), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()

def kb_my_code(code: str) -> str:
    kb = Keyboard(one_time=False, inline=False)
    kb.add(Text("📋 Скопировать код", payload={"cmd": "copy_code"}), color=KeyboardButtonColor.PRIMARY)
    kb.row()
    kb.add(Text("🏠 В главное меню", payload={"cmd": "back_main"}), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()

def kb_free_dates(dates_summary: list[dict]) -> str:
    kb = Keyboard(one_time=False, inline=False)
    for item in dates_summary:
        if item["free"] > 0:
            d: date = item["date"]
            kb.add(Text(f"{d.day} {WD_RU[d.weekday()]} · {item['free']} окон",
                        payload={"cmd": f"date_{d.isoformat()}"}),
                   color=KeyboardButtonColor.PRIMARY)
    kb.row()
    kb.add(Text("🎅 Забронировать", payload={"cmd": "book"}), color=KeyboardButtonColor.POSITIVE)
    kb.row()
    kb.add(Text("🏠 В меню", payload={"cmd": "back_main"}), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()

def kb_back_main() -> str:
    kb = Keyboard(one_time=False, inline=False)
    kb.add(Text("🏠 В меню", payload={"cmd": "back_main"}), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()
