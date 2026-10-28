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
B_NEW = "🔄 Новая жизнь"

MENU_BORN = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=B_BORN), KeyboardButton(text=B_HELP)]],
                                resize_keyboard=True, input_field_placeholder="родиться")
MENU_CHOICE = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=B_BORN), KeyboardButton(text=B_ME),
                                             KeyboardButton(text=B_HELP)]],
                                 resize_keyboard=True, input_field_placeholder="сделай выбор")
MENU_ALIVE = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=B_YEAR)],
                                           [KeyboardButton(text=B_TEN), KeyboardButton(text=B_ALL)],
                                           [KeyboardButton(text=B_NEW), KeyboardButton(text=B_ME),
                                            KeyboardButton(text=B_HELP)]],
                                resize_keyboard=True, input_field_placeholder="год · +10 · до конца")

HELP = ("🌍 Один из 8 миллиардов\n\n"
        "Ты рождаешься сегодня — там, где реально рождаются дети: страна выпадает с тем же шансом, "
        "что и у настоящего новорождённого (Индия и Китай часто, Исландия почти никогда). "
        "Семья, язык, религия, деньги и здоровье зависят от страны.\n\n"
        f"{B_BORN} — новая жизнь\n{B_YEAR} — год жизни и выбор\n{B_TEN} — промотать 10 лет\n"
        f"{B_ALL} — прожить до конца автоматически\n{B_ME} — как дела сейчас\n\n"
        "В 5, 15, 30, 50 и 70 лет — 🔑 ключевые решения. Можно и просто писать: «родиться», «год», «+10».\n"
        "Деньги в игре — только в рублях.")


def keyboard(st):
    if not st:
        return MENU_BORN
    if st.get("ev"):
        return MENU_CHOICE
    return MENU_ALIVE


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
    if not r:
        return None
    try:
        st = json.loads(r[0])
    except Exception:
        return None
    try:
        return game.migrate(st)
    except Exception:
        return game.new_life()

def store(uid, st):
    db().execute("INSERT OR REPLACE INTO lives VALUES (?,?)", (uid, json.dumps(st, ensure_ascii=False)))
    db().commit()


def event_kb(st):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=o, callback_data="c:%d:%d" % (st["steps"], i))]
        for i, o in enumerate(st["opts"])])

def event_msg(st):
    return ("%s\n\n%s" % (st["ev"], game.card(st)), event_kb(st))

def act_born(uid):
    st = game.new_life()
    store(uid, st)
    return [(game.birth_text(st), MENU_ALIVE)]

def act_year(uid):
    st = load(uid)
    if not st:
        return [("Сначала нужно родиться 👶\n\nЖми «👶 Родиться»", MENU_BORN)]
    if st.get("over"):
        return [(game.final_text(st), MENU_ALIVE)]
    if st.get("ev"):
        return [("Сначала сделай выбор 👇",), event_msg(st)]
    if game.grow(st):
        store(uid, st)
        return [(game.final_text(st), MENU_ALIVE)]
    ev = game.special_event(st)
    if ev:
        txt, opts, key = ev
        st["ev"], st["opts"], st["evkind"], st["evkey"] = txt, opts, "special", key
        store(uid, st)
        return [(txt + "\n\n" + game.card(st), event_kb(st))]
    e = game.draw_event(st)
    if e and game.is_auto(e):
        i, res = game.auto_apply(st, e)
        store(uid, st)
        return [("👨‍👩‍👧 Это решение приняли за тебя: %s\n\n%s\n\nПоследствия: %s"
                 % (e["o"][i]["x"], game.card(st), res or "без последствий"), MENU_ALIVE)]
    if not e:
        store(uid, st)
        return [("Спокойный год, ничего особенного.\n\n" + game.card(st), MENU_ALIVE)]
    st["ev"], st["opts"], st["evkind"], st["evkey"] = e["t"], [o["x"] for o in e["o"]], "normal", None
    store(uid, st)
    return [event_msg(st)]

def act_fast(uid, years):
    st = load(uid)
    if not st:
        return [("Сначала нужно родиться 👶\n\nЖми «👶 Родиться»", MENU_BORN)]
    if st.get("over"):
        return [(game.final_text(st), MENU_ALIVE)]
    st["ev"] = None
    start = st["age"]
    game.auto_live(st, years)
    store(uid, st)
    if st.get("over"):
        return [(game.final_text(st), MENU_ALIVE)]
    lines = [s for s in st["log"] if s.split(":")[0].isdigit() and int(s.split(":")[0]) > start][-8:]
    return [("⏩ Прошло %d лет\n\n" % (st["age"] - start) + "\n".join("• " + l for l in lines) +
             "\n\n" + game.card(st), MENU_ALIVE)]

def act_me(uid):
    st = load(uid)
    if not st:
        return [("Ты ещё не родился 👶\n\nЖми «👶 Родиться»", MENU_BORN)]
    if st.get("over"):
        return [(game.final_text(st), MENU_ALIVE)]
    return [(game.card(st), MENU_ALIVE)]

def act_choice(uid, data):
    st = load(uid)
    try:
        _, step, i = data.split(":")
        step, i = int(step), int(i)
    except ValueError:
        return None
    if not st or st.get("over") or not st.get("ev") or step != st.get("steps"):
        return None
    opts = st.get("opts") or []
    if i < 0 or i >= len(opts):
        return None
    if st.get("evkind") == "special":
        res = game.apply_special(st, st["evkey"], i)
    else:
        ev = game.EV_BY_TITLE.get(st["ev"])
        if ev is None:
            st["ev"] = None; st["opts"] = []; store(uid, st)
            return [("Событие устарело, начни год заново 👆", MENU_ALIVE)]
        res = game.apply(st, ev, i)
    st["ev"] = None
    st["opts"] = []
    st["evkind"] = None
    st["evkey"] = None
    store(uid, st)
    return [("✅ %s\n%s\n\n%s" % (opts[i], res, game.card(st)), MENU_ALIVE)]

WORDS = {B_BORN: "born", "родиться": "born",
         B_YEAR: "year", "год": "year", "дальше": "year", "выбор": "year",
         B_TEN: "ten", "+10": "ten", "10": "ten",
         B_ALL: "all", "до конца": "all", "авто": "all",
         B_ME: "me", "жизнь": "me", "статус": "me", B_HELP: "help", "помощь": "help",
         B_NEW: "new", "новая жизнь": "new", "заново": "new", "перезапуск": "new"}

def act_new(uid):
    st = load(uid)
    if not st:
        return act_born(uid)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Да, начать заново", callback_data="r:yes"),
         InlineKeyboardButton(text="↩️ Оставить эту жизнь", callback_data="r:no")]])
    return [("Начать жизнь заново?\n\nВся текущая жизнь (возраст, деньги, семья, отношения) будет стёрта.",
             kb)]


def act_text(uid, text):
    t = (text or "").strip()
    a = WORDS.get(t.lower()) or WORDS.get(t)
    if a == "born":
        return act_born(uid)
    if a == "new":
        return act_new(uid)
    if a == "year":
        return act_year(uid)
    if a == "ten":
        return act_fast(uid, 10)
    if a == "all":
        return act_fast(uid, None)
    if a == "me":
        return act_me(uid)
    return [(HELP, MENU_ALIVE)]


dp = Dispatcher()

async def send(m: Message, msgs):
    for msg in msgs:
        await m.answer(msg[0], reply_markup=msg[1] if len(msg) > 1 else None)

@dp.message(CommandStart())
async def on_start(m: Message):
    st = load(m.from_user.id)
    await m.answer(HELP, reply_markup=MENU_BORN if not st else MENU_ALIVE)

@dp.message(Command("help"))
async def on_help(m: Message):
    await m.answer(HELP, reply_markup=MENU_ALIVE)

@dp.message(Command("born"))
async def on_born(m: Message):
    await send(m, act_born(m.from_user.id))

@dp.message(F.text)
async def on_text(m: Message):
    try:
        await send(m, act_text(m.from_user.id, m.text))
    except Exception as e:
        logging.exception("on_text failed")
        await m.answer("Что-то сломалось. Попробуй «👶 Родиться» заново 🙈")

@dp.callback_query(F.data.startswith("r:"))
async def on_reset(c: CallbackQuery):
    await c.answer()
    if c.data.endswith("yes"):
        await send(c.message, act_born(c.from_user.id))
    else:
        await send(c.message, act_me(c.from_user.id))


@dp.callback_query(F.data.startswith("c:"))
async def on_choice(c: CallbackQuery):
    try:
        res = act_choice(c.from_user.id, c.data)
    except Exception:
        logging.exception("act_choice failed")
        res = None
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
