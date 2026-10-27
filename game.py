# -*- coding: utf-8 -*-
"""Игровая логика без Telegram — можно тестировать отдельно."""
import json, os, random, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTRIES = json.load(open(os.path.join(HERE, "countries.json"), encoding="utf-8"))
EVENTS = json.load(open(os.path.join(HERE, "events.json"), encoding="utf-8"))
EV_BY_TITLE = {e["t"]: e for e in EVENTS}
TOTAL_BIRTHS = sum(c["births"] for c in COUNTRIES)
METRICS = [("health", "❤️ Здоровье"), ("happiness", "😊 Счастье"),
           ("knowledge", "📚 Знания"), ("relationships", "💞 Отношения")]
NAMES = {"health": "Здоровье", "happiness": "Счастье", "knowledge": "Знания", "relationships": "Отношения"}
RUB, STARS = 80, 66  # примерно: 1$ ≈ 80 ₽ ≈ 66 ⭐

FIRST_M = ["Амир", "Арджун", "Вэй", "Чиди", "Мухаммад", "Хосе", "Иван", "Ли", "Кофи", "Рахим", "Лука", "Тенцин", "Омар", "Даниэль", "Нгуен", "Бату", "Каи", "Рави"]
FIRST_F = ["Ана", "Прия", "Мэй", "Ада", "Фатима", "Мария", "Аня", "Юки", "Амара", "Лейла", "София", "Нур", "Зара", "Эмма", "Линь", "Айгерим", "Хана", "Айко"]
JOBS = ["учитель", "врач", "инженер", "водитель", "программист", "строитель", "продавец", "повар",
        "фермер", "медсестра", "швея", "рыбак", "механик", "бухгалтер", "торговец на рынке"]
JOBS_REMOTE = ["пастух", "охотник", "земледелец", "рыбак", "ремесленник", "собиратель", "оленевод"]
FAMILY = [("полная семья", 55), ("один родитель", 15), ("многодетная семья", 12), ("приёмная семья", 4),
          ("детский дом", 2), ("растит мама одна", 9), ("растят бабушка и дедушка", 3)]
PLACES_CITY = ["столица", "крупный город", "небольшой город", "посёлок"]
PLACES_REMOTE = ["отдалённая деревня", "кочевая стоянка", "изолированная община"]


def money(v):
    v = round(v)
    return f"${v:,} ≈ {v*RUB:,} ₽ ≈ {v*STARS:,} ⭐".replace(",", " ")


def bar(v):
    v = max(0, min(100, round(v)))
    f = v // 10
    return "▰" * f + "▱" * (10 - f) + f" {v}"


def pick_country():
    r = random.uniform(0, TOTAL_BIRTHS)
    for c in COUNTRIES:
        r -= c["births"]
        if r <= 0:
            return c
    return COUNTRIES[0]


def new_life():
    c = pick_country()
    tribal = c.get("is_tribal", False)
    remote = tribal or random.random() * 100 < c.get("remote_pct", 0)
    male = random.random() < 0.512
    poor = c["gdp"] < 4000
    sibs = random.randint(3, 7) if random.random() * 100 < c.get("multi_pct", 20) else random.randint(0, 2)
    st = {
        "born": datetime.date.today().isoformat(),
        "name": random.choice(FIRST_M if male else FIRST_F),
        "male": male, "father": random.choice(FIRST_M), "mother": random.choice(FIRST_F),
        "flag": c["flag"], "country": c["name"], "lang": c["lang"],
        "le": c["le"], "lit": c["lit"], "gdp": c["gdp"],
        "tribal": tribal, "remote": remote,
        "place": random.choice(PLACES_REMOTE if remote else PLACES_CITY),
        "family": random.choices([f for f, _ in FAMILY], [w for _, w in FAMILY])[0],
        "sibs": sibs, "age": 0,
        "health": random.randint(60, 92) - (8 if poor else 0) - (8 if remote else 0),
        "happiness": random.randint(50, 85),
        "knowledge": random.randint(3, 12),
        "relationships": random.randint(50, 85),
        "money": round(c["gdp"] * random.uniform(0.01, 0.06) * (0.3 if remote else 1)),
        "income": c["gdp"] * (0.25 if remote else 0.6),
        "job": None, "edu": None, "kids": 0, "married": False,
        "used": [], "log": [], "steps": 0, "ev": None, "over": False, "cause": None,
    }
    st["log"].append(f"0: родился(ась) — {st['flag']} {st['country']}, {st['place']}")
    return st


def phase(a):
    for lim, name in [(3, "младенчество"), (7, "детство"), (13, "школьные годы"), (18, "юность"),
                      (35, "молодость"), (60, "зрелость"), (75, "пожилой возраст")]:
        if a < lim:
            return name
    return "старость"


def card(st):
    lines = [f"🎂 {st['age']} лет · {phase(st['age'])}"]
    lines += [f"{n}  {bar(st[k])}" for k, n in METRICS]
    lines.append(f"💰 {money(st['money'])}")
    return "\n".join(lines)


def birth_text(st):
    he = st["male"]
    share = sum(c["births"] for c in COUNTRIES if c["name"] == st["country"]) / TOTAL_BIRTHS * 100
    t = [f"👶 {'Ты родился' if he else 'Ты родилась'} сегодня, {st['born']}", "",
         f"{st['flag']} {st['country']} · {st['place']}",
         f"Тебя зовут {st['name']}",
         f"🗣 Родной язык: {st['lang']}",
         f"👪 {st['family'].capitalize()} · отец {st['father']}, мать {st['mother']}",
         f"👥 Братьев и сестёр: {st['sibs']}"]
    if st["tribal"]:
        t.append("🏕 Ты из коренного народа: свой язык, свой уклад, до больницы и школы далеко.")
    elif st["remote"]:
        t.append("🌾 Глубинка: до школы, врача и интернета далеко.")
    t.append(f"🎲 Здесь рождается {share:.2f}% всех детей мира")
    t += ["", card(st), "", "Жми «➡️ Прожить год»"]
    return "\n".join(t)


def draw_event(st):
    a = st["age"]
    pool = [e for e in EVENTS if e["a0"] <= a <= e["a1"] and e["t"] not in st["used"]]
    key = [e for e in pool if "key_age" in e["tags"]]
    if key:
        return key[0]
    pool = [e for e in pool if "key_age" not in e["tags"]]
    if not st["remote"]:
        pool = [e for e in pool if "remote" not in e["tags"]]
    elif random.random() < 0.6:
        pool = [e for e in pool if "remote" in e["tags"]] or pool
    if not pool:
        return None
    return random.choices(pool, [e["w"] for e in pool])[0]


def death_risk(st):
    a = st["age"]
    base = 0.004 if a < 15 else 0.002 if a < 50 else 0.012 if a < 70 else 0.04 if a < 80 else 0.12
    if a < 2:
        base = 0.02 if st["gdp"] < 4000 else 0.004
    risk = base * (2.2 - max(0, st["health"]) / 60)
    if a >= st["le"] + 15 or st["health"] <= 0:
        risk = 0.9
    return max(0.0, risk)


def cause(st):
    a = st["age"]
    if st["health"] <= 10:
        return "умер(ла) от болезни"
    if a < 5:
        return "умер(ла) в раннем детстве от инфекции"
    if a < 40:
        return random.choice(["погиб(ла) в аварии", "умер(ла) от болезни", "погиб(ла) в несчастном случае"])
    if a < 70:
        return random.choice(["умер(ла) от инфаркта", "умер(ла) от рака", "умер(ла) от инсульта"])
    return random.choice(["тихо умер(ла) во сне", "умер(ла) от старости", "умер(ла) от сердечной недостаточности"])


def grow(st):
    """Шаг в один год. True — если человек умер."""
    st["age"] += 1
    a = st["age"]
    if a > 40:
        st["health"] -= random.randint(0, 2)
    if a > 65:
        st["health"] -= random.randint(0, 2)
    if 18 <= a <= 65:
        earn = st["income"] * random.uniform(0.02, 0.08)
        if st["job"]:
            earn *= 1.5
        st["money"] += earn
    elif a > 65:
        st["money"] *= 0.97
    if a >= 20 and not st["job"] and random.random() < 0.3:
        st["job"] = random.choice(JOBS_REMOTE if st["remote"] else JOBS)
        st["log"].append(f"{a}: начал(а) работать — {st['job']}")
    for k in ("health", "happiness", "knowledge", "relationships"):
        st[k] = max(0, min(100, st[k]))
    if random.random() < death_risk(st):
        st["over"] = True
        st["cause"] = cause(st)
        st["log"].append(f"{a}: {st['cause']}")
        return True
    return False


def apply(st, e, i):
    o = e["o"][i]
    for k, v in o["d"].items():
        st[k] = max(0, min(100, st[k] + v))
    st["money"] = max(0, st["money"] + o["m"])
    st["used"].append(e["t"])
    st["steps"] += 1
    x, t = o["x"], e["t"]
    if x == "Университет":
        st["edu"] = "высшее"
    elif x == "Колледж" and not st["edu"]:
        st["edu"] = "среднее специальное"
    if t in ("Первый ребёнок", "Второй ребёнок") and o["m"] < 0:
        st["kids"] += 1
    if t == "Свадьба" or (t.startswith("Семья договорилась") and x == "Согласиться"):
        st["married"] = True
    if t == "Первая работа" and not st["job"]:
        st["job"] = random.choice(JOBS)
    st["log"].append(f"{st['age']}: {t} → {x}")
    eff = ", ".join(f"{NAMES[k]} {v:+d}" for k, v in o["d"].items() if v)
    if o["m"]:
        eff += (", " if eff else "") + f"деньги {o['m']:+,}$".replace(",", " ")
    return eff or "без последствий"


def label(p):
    if p >= 90: return "топ-10%"
    if p >= 70: return "сильно выше среднего"
    if p >= 55: return "чуть выше среднего"
    if p >= 40: return "примерно как у всех"
    return "ниже среднего"


def final_text(st):
    a = st["age"]
    life_p = min(99, max(1, round(50 + (a - st["le"]) * 3)))
    know_p = min(99, max(1, round(st["knowledge"] / max(20, st["lit"] * 0.7) * 50)))
    happy_p = min(99, max(1, round(st["happiness"] / 60 * 50)))
    rel_p = min(99, max(1, round(st["relationships"] / 60 * 50)))
    rich_p = min(99, max(1, round(st["money"] / max(1, st["gdp"] * 2) * 50)))
    y = int(st["born"][:4])
    t = [f"🪦 {st['name']}, {y}–{y + a}",
         f"{st['cause'] or 'жизнь окончена'} в {a} лет", "",
         f"{st['flag']} {st['country']} · {st['place']} · язык: {st['lang']}",
         f"👪 {st['family']} · братьев и сестёр: {st['sibs']}",
         f"💼 Работа: {st['job'] or 'не работал(а)'} · 🎓 {st['edu'] or 'без высшего'}",
         f"💍 {'в браке' if st['married'] else 'без брака'} · 👶 детей: {st['kids']}",
         f"💰 Осталось: {money(st['money'])}", "",
         "📊 По сравнению с людьми этой страны:",
         f"⏳ Долголетие: {label(life_p)} (в среднем живут {st['le']:.0f} лет)",
         f"📚 Знания: {label(know_p)}",
         f"😊 Счастье: {label(happy_p)}",
         f"💞 Отношения: {label(rel_p)}",
         f"💰 Богатство: {label(rich_p)}", "",
         "📜 Главное в жизни:"]
    t += ["• " + s for s in st["log"][-12:]]
    t += ["", f"Решений принято: {st['steps']}", "🔄 Жми «👶 Родиться», чтобы прожить новую жизнь"]
    return "\n".join(t)


def auto_live(st, years=None):
    """Проживает жизнь автоматически (до конца или years лет)."""
    n = 0
    while not st["over"] and (years is None or n < years):
        n += 1
        if grow(st):
            break
        e = draw_event(st)
        if e:
            apply(st, e, random.randrange(len(e["o"])))
    return st
