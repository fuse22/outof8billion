# -*- coding: utf-8 -*-
"""Telegram-бот «Один из 8 миллиардов». Запуск: BOT_TOKEN=... python bot.py"""
import asyncio, json, logging, os, sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton, BotCommand)

import game

logging.basicConfig(level=logging.INFO)
DB_PATH = os.environ.get("DB_PATH") or ("/data/lives.db" if os.path.isdir("/data") else "lives.db")

B_BORN, B_YEAR, B_TEN, B_ALL, B_ME, B_HELP = ("👶 Родиться", "➡️ Прожить год", "⏩ +10 лет",
                                              "⚡ Прожить до конца", "📊 Моя жизнь", "❓ Помощь")
MENU = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=B_YEAR)],
                                     [KeyboardButton(text=B_TEN), KeyboardButton(text=B_ALL)],
                                     [KeyboardButton(text=B_BORN), KeyboardButton(text=B_ME), KeyboardButton(text=B_HELP)]],
                           resize_keyboard=True, input_field_placeholder="родиться · год · +10 · до конца")
HELP = ("🌍 Один из 8 миллиардов\n\n"
        "Ты рождаешься сегодня — там, где реально рождаются дети: страна выпадает с тем же шансом, "
        "что и у настоящего новорождённого (Индия и Китай часто, Исландия почти никогда). "
        "Семья, язык, деньги и здоровье зависят от страны.\n\n"
        f"{B_BORN} — новая жизнь\n{B_YEAR} — год жизни и выбор\n{B_TEN} — промотать 10 лет\n"
        f"{B_ALL} — прожить до конца автоматически\n{B_ME} — как дела сейчас\n\n"
        "В 5, 15, 30, 50 и 70 лет — 🔑 ключевые решения. Можно и просто писать: «родиться», «год», «+10».\n"
        "Деньги: $ ≈ ₽ ≈ ⭐ (примерный курс).")


# ---------- хранение ----------
_conn = None
def db():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.execute("CREATE TABLE IF NOT EXISTS lives (uid INTEGER PRIMARY KEY, data TEXT)")
        _conn.commit()
    return _conn

def load(uid):
    r = db().execute("SELECT data FROM lives WHERE uid=?", (uid,)).fetchone()
    return json.loads(r[0]) if r else None

def store(uid, st):
    db().execute("INSERT OR REPLACE INTO lives VALUES (?,?)", (uid, json.dumps(st, ensure_ascii=False)))
    db().commit()


# ---------- логика ответов (без Telegram, чтобы легко тестировать) ----------
def event_kb(st):
    e = game.EV_BY_TITLE[st["ev"]]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=o["x"], callback_data=f"c:{st['steps']}:{i}")] for i, o in enumerate(e["o"])])

def event_msg(st):
    return (f"{st['ev']}\n\n{game.card(st)}", event_kb(st))

def act_born(uid):
    st = game.new_life()
    store(uid, st)
    return [(game.birth_text(st), MENU)]

def act_year(uid):
    st = load(uid)
    if not st or st["over"]:
        return [("Сначала нужно родиться 👶", MENU)]
    if st.get("ev"):
        return [("Сначала сделай выбор 👇",), event_msg(st)]
    if game.grow(st):
        store(uid, st)
        return [(game.final_text(st), MENU)]
    e = game.draw_event(st)
    if not e:
        store(uid, st)
        return [(f"Спокойный год, ничего особенного.\n\n{game.card(st)}", MENU)]
    st["ev"] = e["t"]
    store(uid, st)
    return [event_msg(st)]

def act_fast(uid, years):
    st = load(uid)
    if not st or st["over"]:
        return [("Сначала нужно родиться 👶", MENU)]
    st["ev"] = None
    start = st["age"]
    game.auto_live(st, years)
    store(uid, st)
    if st["over"]:
        return [(game.final_text(st), MENU)]
    lines = [s for s in st["log"] if s.split(":")[0].isdigit() and int(s.split(":")[0]) > start][-8:]
    return [(f"⏩ Прошло {st['age'] - start} лет\n\n" + "\n".join("• " + l for l in lines) +
             f"\n\n{game.card(st)}", MENU)]

def act_me(uid):
    st = load(uid)
    if not st:
        return [("Ты ещё не родился 👶", MENU)]
    if st["over"]:
        return [(game.final_text(st), MENU)]
    return [(f"{st['flag']} {st['name']}, {st['country']}\n💼 {st['job'] or 'пока не работает'}\n\n{game.card(st)}", MENU)]

def act_choice(uid, data):
    st = load(uid)
    try:
        _, step, i = data.split(":")
        step, i = int(step), int(i)
    except ValueError:
        return None
    if not st or st["over"] or not st.get("ev") or step != st["steps"]:
        return None
    e = game.EV_BY_TITLE[st["ev"]]
    choice = e["o"][i]["x"]
    eff = game.apply(st, e, i)
    st["ev"] = None
    store(uid, st)
    return [(f"✅ {choice}\n{eff}\n\n{game.card(st)}", MENU)]

WORDS = {B_BORN: "born", "родиться": "born", "заново": "born", "новая жизнь": "born",
         B_YEAR: "year", "год": "year", "дальше": "year", "выбор": "year",
         B_TEN: "ten", "+10": "ten", "10": "ten",
         B_ALL: "all", "до конца": "all", "авто": "all",
         B_ME: "me", "жизнь": "me", "статус": "me", B_HELP: "help", "помощь": "help"}

def act_text(uid, text):
    a = WORDS.get((text or "").strip().lower()) or WORDS.get((text or "").strip())
    if a == "born": return act_born(uid)
    if a == "year": return act_year(uid)
    if a == "ten": return act_fast(uid, 10)
    if a == "all": return act_fast(uid, None)
    if a == "me": return act_me(uid)
    return [(HELP, MENU)]


# ---------- Telegram ----------
dp = Dispatcher()

async def send(m: Message, msgs):
    for msg in msgs:
        await m.answer(msg[0], reply_markup=msg[1] if len(msg) > 1 else None)

@dp.message(CommandStart())
async def on_start(m: Message):
    await m.answer(HELP, reply_markup=MENU)

@dp.message(Command("help"))
async def on_help(m: Message):
    await m.answer(HELP, reply_markup=MENU)

@dp.message(Command("born"))
async def on_born(m: Message):
    await send(m, act_born(m.from_user.id))

@dp.message(F.text)
async def on_text(m: Message):
    await send(m, act_text(m.from_user.id, m.text))

@dp.callback_query(F.data.startswith("c:"))
async def on_choice(c: CallbackQuery):
    res = act_choice(c.from_user.id, c.data)
    if res is None:
        await c.answer("Эта кнопка уже устарела")
        return
    await c.answer()
    try:
        await c.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await send(c.message, res)

async def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise SystemExit("Нет переменной BOT_TOKEN")
    bot = Bot(token)
    await bot.set_my_commands([BotCommand(command="start", description="Начать"),
                               BotCommand(command="born", description="Родиться заново"),
                               BotCommand(command="help", description="Как играть")])
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
