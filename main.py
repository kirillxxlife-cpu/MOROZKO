"""
VK BOT — «Морозко» v3. Мульти-дети, соц. инженерия, без страха мошенников.
"""
import asyncio
import json
import os
import re
import uuid
from datetime import date, datetime, timedelta
from urllib.parse import quote

from loguru import logger
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text, OpenLink

import state
import texts
import keyboards as kb
import sheets

VK_TOKEN = os.getenv("VK_GROUP_TOKEN", "")
VK_GROUP_ID = int(os.getenv("VK_GROUP_ID", "0"))
ADMIN_VK_ID = int(os.getenv("ADMIN_VK_ID", "0"))
HOLD_MIN = int(os.getenv("HOLD_MINUTES", "15"))

if not VK_TOKEN:
    raise RuntimeError("VK_GROUP_TOKEN не задан в env")

bot = Bot(token=VK_TOKEN)
bot.labeler.vbml_ignore_case = True

def parse_payload(message: Message) -> str:
    p = getattr(message, "payload", None)
    if isinstance(p, dict):
        return p.get("cmd") or ""
    if isinstance(p, str):
        try:
            return (json.loads(p) or {}).get("cmd") or ""
        except Exception:
            return ""
    return ""

async def safe_name(message: Message) -> str:
    try:
        u = (await bot.api.users.get(user_ids=message.from_id))[0]
        return u.first_name or "друг"
    except Exception:
        return "друг"

async def notify_admin(text: str) -> None:
    if not ADMIN_VK_ID:
        return
    try:
        await bot.api.messages.send(user_id=ADMIN_VK_ID, message=text, random_id=0)
    except Exception as e:
        logger.error("admin notify: {}", e)

def build_review_text(st: state.UserState) -> str:
    d = st.draft
    extras = ", ".join(state.EXTRA_NAMES[e] for e in d.get("extras", [])) or "нет"
    children_str = ", ".join(f"{c['name']} ({c['age']})" for c in d.get("children", []))
    total = state.calc_total(d)
    lines = [
        texts.REVIEW_HEADER,
        f"👦 <b>{children_str}</b>",
        f"📅 <b>{d.get('date_display', '')} в {d.get('time_display', '')}</b>",
        f"🎁 {state.PACKAGE_NAMES.get(d.get('package', ''), '')}",
        f"➕ {extras}",
        f"📍 {d.get('address', '')}",
        f"📞 {d.get('phone', '')}",
        f"💰 <b>{int(total)} ₽</b>",
        texts.REVIEW_GUARANTEE,
    ]
    return "\n".join(lines)

def share_url_for(vk_id: int) -> str:
    bot_link = f"https://vk.me/club{VK_GROUP_ID}"
    return f"https://vk.com/share.php?url={quote(bot_link)}&title={quote('Забронировали Деда Мороза!')}"

async def send_main_menu(message: Message, st: state.UserState, prepend: str = ""):
    st.step = "main"
    st.draft = {}
    text = (prepend + "\n\n" if prepend else "") + texts.WELCOME
    await message.answer(text, keyboard=kb.kb_welcome())

async def step_welcome(message: Message, st: state.UserState):
    st.step = "main"
    st.draft = {}
    await message.answer(texts.WELCOME, keyboard=kb.kb_welcome())

async def step_children_count(message: Message, st: state.UserState):
    st.step = "children_count"
    st.draft = {"children": [], "current_child_idx": 0}
    await message.answer(texts.ASK_CHILDREN_COUNT, keyboard=kb.kb_children_count())

async def ask_child_age(message: Message, st: state.UserState):
    idx = st.draft.get("current_child_idx", 0)
    child_num = ["первому", "второму", "третьему", "четвёртому", "пятому"][idx] if idx < 5 else f"{idx+1}-му"
    st.step = "child_age"
    await message.answer(texts.ASK_CHILD_AGE.format(child_num=child_num), keyboard=kb.kb_age())

async def ask_child_name(message: Message, st: state.UserState):
    idx = st.draft.get("current_child_idx", 0)
    child_num = ["первого", "второго", "третьего", "четвёртого", "пятого"][idx] if idx < 5 else f"{idx+1}-го"
    st.step = "child_name"
    await message.answer(texts.ASK_CHILD_NAME.format(child_num=child_num), keyboard=kb.kb_back_main())

async def step_package(message: Message, st: state.UserState):
    st.step = "package"
    await message.answer(texts.ASK_PACKAGE, keyboard=kb.kb_package())

async def step_extras(message: Message, st: state.UserState):
    st.step = "extras"
    await message.answer(texts.ASK_EXTRAS, keyboard=kb.kb_extras(st.draft))

async def step_dates(message: Message, st: state.UserState):
    st.step = "date"
    summary = state.get_dates_summary()
    await message.answer(texts.ASK_DATE, keyboard=kb.kb_dates(summary))

async def step_times(message: Message, st: state.UserState, d: date):
    st.draft["date"] = d.isoformat()
    st.draft["date_display"] = d.strftime("%d.%m.%Y")
    st.step = "time"
    slots = state.get_free_slots_by_date(d)
    if not any(s.status.value == "free" for s in slots):
        await message.answer(texts.NO_SLOTS_LEFT, keyboard=kb.kb_dates(state.get_dates_summary()))
        return
    await message.answer(
        texts.ASK_TIME.format(date=d.strftime("%d.%m.%Y")),
        keyboard=kb.kb_times(slots),
    )

async def step_address(message: Message, st: state.UserState):
    st.step = "address"
    await message.answer(texts.ASK_ADDRESS, keyboard=kb.kb_back_main())

async def step_phone(message: Message, st: state.UserState):
    st.step = "phone"
    await message.answer(texts.ASK_PHONE, keyboard=kb.kb_back_main())

async def step_review(message: Message, st: state.UserState):
    st.step = "review"
    await message.answer(build_review_text(st), keyboard=kb.kb_review())

async def step_consent(message: Message, st: state.UserState):
    st.step = "consent"
    await message.answer(texts.CONSENT, keyboard=kb.kb_consent())

async def step_payment(message: Message, st: state.UserState):
    booking = state.create_booking(message.from_id, st.draft)
    slot = await state.hold_slot(booking.slot_id, booking.id, HOLD_MIN)
    if not slot:
        await message.answer(texts.SLOT_TAKEN, keyboard=kb.kb_back_main())
        st.step = "main"
        return
    st.draft["booking_id"] = str(booking.id)
    st.step = "payment"
    await message.answer(texts.PAYMENT_SCREEN, keyboard=kb.kb_payment())

async def step_confirm_payment(message: Message, st: state.UserState):
    bid_str = st.draft.get("booking_id")
    if not bid_str:
        await message.answer("Бронь не найдена. Начните заново — /start", keyboard=kb.kb_welcome())
        return
    bid = uuid.UUID(bid_str)
    ok = await state.confirm_booking(bid)
    if not ok:
        await message.answer(
            "Слот освободился. Начните заново — /start",
            keyboard=kb.kb_welcome(),
        )
        return

    booking = state.get_booking(bid)
    d = st.draft
    children_str = "; ".join(f"{c['name']} ({c['age']})" for c in d.get("children", []))

    asyncio.create_task(sheets.log_booking({
        "booking_id": str(bid),
        "vk_id": message.from_id,
        "user_name": st.name,
        "date": d.get("date", ""),
        "time": d.get("time_display", ""),
        "package": state.PACKAGE_NAMES.get(d.get("package", ""), ""),
        "extras": d.get("extras", []),
        "child_name": children_str,
        "child_age": "",
        "address": d.get("address", ""),
        "phone": d.get("phone", ""),
        "total": str(booking.total),
        "promo": d.get("promo"),
        "status": "paid",
        "created_at": booking.created_at.isoformat(),
        "paid_at": booking.paid_at.isoformat() if booking.paid_at else "",
    }))

    children_names = ", ".join(c["name"] for c in d.get("children", []))
    paid_text = (
        texts.PAID_HEADER
        + texts.PAID_BODY.format(
            date=d.get("date_display", ""),
            time=d.get("time_display", ""),
            children=children_names,
        )
    )
    await message.answer(
        paid_text,
        keyboard=kb.kb_after_paid(share_url_for(message.from_id), state.make_friend_code(message.from_id)),
    )
    st.step = "done"
    asyncio.create_task(_schedule_reminders(bid, message.from_id, d))

async def _schedule_reminders(bid: uuid.UUID, vk_id: int, draft: dict):
    try:
        target = datetime.fromisoformat(f"{draft.get('date')}T{draft.get('time_display', '14:00')}:00")
        now = datetime.now()
        for hours_before, text in (
            (24, "Напоминание: завтра в {t} приедут Дед Мороз и Снегурочка. "
                 "Подготовьте место у ёлки 🎄"),
            (2, "Скоро визит! В {t} артист выехал к вам 🎅"),
        ):
            delta = (target - timedelta(hours=hours_before) - now).total_seconds()
            if delta <= 0:
                continue
            await asyncio.sleep(delta)
            try:
                await bot.api.messages.send(
                    user_id=vk_id,
                    message=text.format(t=draft.get("time_display", "14:00")),
                    random_id=0,
                )
            except Exception as e:
                logger.error("reminder fail: {}", e)
    except Exception as e:
        logger.error("schedule_reminders: {}", e)

async def enter_operator(message: Message, st: state.UserState):
    st.operator_mode = True
    await message.answer(texts.OPERATOR_REQUESTED, keyboard=kb.kb_back_main())
    await notify_admin(
        texts.ADMIN_NEW_CLIENT.format(
            name=st.name or f"user_{st.vk_id}",
            vk_id=st.vk_id,
            snippet="Нажал «Живой человек»",
        )
    )

async def show_free_dates(message: Message, st: state.UserState):
    st.step = "free_dates"
    summary = state.get_dates_summary()
    await message.answer(texts.FREE_DATES_HEADER, keyboard=kb.kb_free_dates(summary))

async def show_my_code(message: Message, st: state.UserState):
    code = state.make_friend_code(message.from_id)
    await message.answer(
        texts.YOUR_FRIEND_CODE.format(code=code),
        keyboard=kb.kb_my_code(code),
    )

@bot.on.message()
async def router(message: Message):
    vk_id = message.from_id
    st = state.get_user(vk_id)
    if not st.name:
        st.name = await safe_name(message)

    text_raw = (message.text or "").strip()
    cmd = parse_payload(message)

    if vk_id == ADMIN_VK_ID and text_raw.startswith("/"):
        if text_raw.startswith("/take "):
            uid = int(text_raw.split()[1])
            s = state.get_user(uid)
            s.operator_mode = True
            s.operator_taken_by = ADMIN_VK_ID
            await message.answer(texts.ADMIN_TAKEN.format(vk_id=uid))
            return
        if text_raw.startswith("/release "):
            uid = int(text_raw.split()[1])
            s = state.get_user(uid)
            s.operator_mode = False
            s.operator_taken_by = None
            await message.answer(texts.ADMIN_RELEASED.format(vk_id=uid))
            try:
                await bot.api.messages.send(
                    user_id=uid, message=texts.OPERATOR_RETURNED,
                    random_id=0, keyboard=kb.kb_main(),
                )
            except Exception:
                pass
            return

    if st.operator_mode:
        await notify_admin(f"💬 {st.name} ({vk_id}):\n{text_raw[:500]}")
        return

    if text_raw.lower().startswith("/start"):
        await step_welcome(message, st)
        return

    if st.step == "child_name":
        st.draft["children"].append({
            "age": st.draft.get("current_age", ""),
            "name": text_raw
        })
        st.draft["current_child_idx"] += 1
        if st.draft["current_child_idx"] < st.draft.get("target_children_count", 1):
            await ask_child_age(message, st)
        else:
            await step_package(message, st)
        return

    if st.step == "address":
        st.draft["address"] = text_raw
        await step_phone(message, st)
        return
    if st.step == "phone":
        digits = re.sub(r"\D", "", text_raw)
        if len(digits) < 10:
            await message.answer(texts.BAD_PHONE, keyboard=kb.kb_back_main())
            return
        st.draft["phone"] = text_raw
        await step_review(message, st)
        return

    if cmd == "book":
        await step_children_count(message, st); return
    if cmd.startswith("children_"):
        count_str = cmd.split("_")[1]
        count = 4 if count_str == "4" else int(count_str)
        st.draft["target_children_count"] = count
        st.draft["current_child_idx"] = 0
        await ask_child_age(message, st)
        return
    if cmd.startswith("age_"):
        st.draft["current_age"] = {"age_1_3": "1-3", "age_4_7": "4-7", "age_8_12": "8-12"}[cmd]
        await ask_child_name(message, st)
        return
    if cmd in ("pkg_mini", "pkg_standard", "pkg_premium"):
        st.draft["package"] = cmd.split("_", 1)[1]
        st.draft["extras"] = []
        await message.answer(texts.PACKAGE_PRAISED.get(st.draft["package"], ""))
        await step_extras(message, st); return
    if cmd in ("extra_photo", "extra_cake", "extra_balls"):
        key = cmd.split("_", 1)[1]
        chosen = set(st.draft.get("extras", []))
        chosen.symmetric_difference_update({key})
        st.draft["extras"] = list(chosen)
        await message.answer("Отмечено.", keyboard=kb.kb_extras(st.draft)); return
    if cmd == "extras_done":
        await step_dates(message, st); return
    if cmd.startswith("date_"):
        d = date.fromisoformat(cmd[5:])
        await step_times(message, st, d); return
    if cmd.startswith("slot_"):
        slot_id = int(cmd[5:])
        slots = state.get_free_slots_by_date(date.fromisoformat(st.draft["date"]))
        slot = next((s for s in slots if s.id == slot_id), None)
        if not slot or slot.status.value != "free":
            await message.answer(texts.SLOT_TAKEN, keyboard=kb.kb_times(slots))
            return
        st.draft["slot_id"] = slot_id
        st.draft["time_display"] = slot.time.strftime("%H:%M")
        await step_address(message, st); return

    if cmd == "review_ok":
        await step_consent(message, st); return
    if cmd == "review_edit":
        await step_children_count(message, st); return
    if cmd == "review_back":
        await step_review(message, st); return
    if cmd == "consent_yes":
        await step_payment(message, st); return
    if cmd == "pay_now":
        await message.answer("✅ Оплата получена")
        await asyncio.sleep(0.4)
        await step_confirm_payment(message, st)
        return
    if cmd == "cancel":
        bid_str = st.draft.get("booking_id")
        if bid_str:
            await state.release_slot(uuid.UUID(bid_str))
        await message.answer(texts.CANCEL, keyboard=kb.kb_welcome())
        st.draft = {}; st.step = "main"; return
    if cmd == "back_main":
        await send_main_menu(message, st); return
    if cmd == "back_dates":
        await step_dates(message, st); return

    if cmd == "free_dates":
        await show_free_dates(message, st); return
    if cmd == "operator":
        await enter_operator(message, st); return
    if cmd == "show_my_code":
        await show_my_code(message, st); return
    if cmd == "copy_code":
        code = state.make_friend_code(message.from_id)
        await message.answer(f"<code>{code}</code>", keyboard=kb.kb_my_code(code)); return
    if cmd == "noop":
        await message.answer(texts.NOOP, keyboard=kb.kb_back_main()); return

    await send_main_menu(message, st, prepend=texts.MENU_HINT)

async def main():
    state.init_slots()
    if sheets.is_enabled():
        rows = await sheets.load_paid()
        restored = state.mark_booked_from_sheets(rows)
        logger.info("Restored {} paid bookings from Sheets", restored)

    asyncio.create_task(state.cleanup_loop(60))
    logger.info("Морозко запускается. Слотов: {}", len(state._slots))
    await bot.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
