# -*- coding: utf-8 -*-
import json, os, random, re, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTRIES = json.load(open(os.path.join(HERE, "countries.json"), encoding="utf-8"))
EVENTS = json.load(open(os.path.join(HERE, "events.json"), encoding="utf-8"))
EV_BY_TITLE = {e["t"]: e for e in EVENTS}
TOTAL_BIRTHS = sum(c["births"] for c in COUNTRIES)
RUB = 80

REL_NAME = {"Christian": "христианство", "Muslim": "ислам", "Hindu": "индуизм",
            "Buddhist": "буддизм", "Christian_Orthodox": "православие",
            "Folk": "народные и традиционные верования", "No_religion": "религии нет",
            "Taoist": "даосизм", "Jain": "джайнизм", "Zoroastrian": "зороастрианство",
            "Sikh": "сикхизм"}
QUINTILE = {1: "Самые бедные 20%", 2: "Нижние 40%", 3: "Средние 40%",
            4: "Верхние 40%", 5: "Самые богатые 20%"}
NAMES = {"health": "Здоровье", "happiness": "Счастье", "knowledge": "Знания",
         "family_meter": "Семья", "love": "Близкие"}
FIRST_M = ["Амир", "Арджун", "Вэй", "Чиди", "Мухаммад", "Хосе", "Иван", "Ли", "Кофи",
           "Рахим", "Лука", "Тенцин", "Омар", "Даниэль", "Нгуен", "Бату", "Каи", "Рави"]
FIRST_F = ["Ана", "Прия", "Мэй", "Ада", "Фатима", "Мария", "Аня", "Юки", "Амара", "Лейла",
           "София", "Нур", "Зара", "Эмма", "Линь", "Айгерим", "Хана", "Айко"]
JOBS = ["учитель", "врач", "инженер", "водитель", "программист", "строитель", "продавец",
        "повар", "фермер", "медсестра", "швея", "рыбак", "механик", "бухгалтер", "торговец на рынке"]
JOBS_REMOTE = ["пастух", "охотник", "земледелец", "рыбак", "ремесленник", "собиратель", "оленевод"]
PLACES_CITY = ["столица", "крупный город", "небольшой город", "посёлок"]
PLACES_REMOTE = ["отдалённая деревня", "кочевая стоянка", "изолированная община"]
FAMILY_TYPES = [("полная семья", 48), ("один родитель", 14), ("многодетная семья", 11),
                ("приёмная семья", 4), ("детский дом", 2), ("мама одна", 8),
                ("бабушка и дедушка", 3), ("семья алкоголиков", 10)]


def money(v):
    return "%s ₽" % format(int(round(v)) * RUB, ",d").replace(",", " ")


def bar(v):
    v = max(0, min(100, round(v)))
    return "▰" * (v // 10) + "▱" * (10 - v // 10) + " %d" % v


def age_years(a):
    if a % 10 == 1 and a % 100 != 11:
        return "год"
    if 2 <= a % 10 <= 4 and not (12 <= a % 100 <= 14):
        return "года"
    return "лет"


def plural(n, one, few, many):
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
        return few
    return many


def tpl(text, st):
    def pick(m):
        return m.group(1) if st["male"] else m.group(2)
    text = re.sub(r"\{м:([^}]*)\}\{ж:([^}]*)\}", pick, text)
    text = text.replace("{имя}", st["name"]).replace("{age}", str(st["age"]))
    text = text.replace("{agew}", "%d %s" % (st["age"], age_years(st["age"])))
    text = text.replace("{partner}", st.get("partner") or st.get("ex") or "близкий человек")
    return text


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
    fam = random.choices([f for f, _ in FAMILY_TYPES], [w for _, w in FAMILY_TYPES])[0]
    sibs = random.randint(3, 7) if random.random() * 100 < c.get("multi_pct", 20) else random.randint(0, 2)
    st = {
        "born": datetime.date.today().isoformat(),
        "name": random.choice(FIRST_M if male else FIRST_F), "male": male,
        "father": random.choice(FIRST_M), "mother": random.choice(FIRST_F),
        "has_father": fam in ("полная семья", "многодетная семья", "приёмная семья",
                              "бабушка и дедушка", "семья алкоголиков"),
        "has_mother": fam in ("полная семья", "многодетная семья", "приёмная семья",
                              "мама одна", "семья алкоголиков"),
        "alco": fam == "семья алкоголиков",
        "flag": c["flag"], "country": c["name"], "lang": c["lang"], "rel": c["rel"],
        "quintile": c["quintile"], "iso3": c["iso3"], "le": c["le"], "lit": c["lit"],
        "gdp": c["gdp"], "tribal": tribal, "remote": remote,
        "place": random.choice(PLACES_REMOTE if remote else PLACES_CITY),
        "family": fam, "family_meter": random.randint(45, 85), "sibs": sibs, "age": 0,
        "health": random.randint(60, 92) - (8 if poor else 0) - (8 if remote else 0)
                  - (8 if fam == "семья алкоголиков" else 0),
        "happiness": random.randint(45, 85) - (14 if fam == "семья алкоголиков" else 0),
        "knowledge": random.randint(3, 12), "love": random.randint(40, 70),
        "money": round(c["gdp"] * random.uniform(0.01, 0.06) * (0.3 if remote else 1)),
        "income": c["gdp"] * (0.25 if remote else 0.6),
        "job": None, "edu": None, "kids": 0, "married": False, "married_since": None,
        "partner": None, "partner_since": None, "crush": None, "ex": None,
        "used": [], "log": [], "steps": 0, "ev": None, "evkind": None, "evkey": None,
        "opts": [], "over": False, "cause": None, "last_result": None,
    }
    st["log"].append("0: родился — %s %s, %s" % (st["flag"], st["country"], st["place"]))
    return st


def phase(a):
    for lim, name in [(3, "младенчество"), (7, "детство"), (13, "школьные годы"),
                      (18, "юность"), (35, "молодость"), (60, "зрелость"), (75, "пожилой возраст")]:
        if a < lim:
            return name
    return "старость"


def has_close(st):
    return bool(st.get("married")) or st.get("kids", 0) > 0


def card(st):
    a = st["age"]
    lines = ["🎂 %s · %s" % (tpl("{agew}", st), phase(a)),
             "%s %s" % ("👨" if st["male"] else "👩", st["name"]),
             "❤️ Здоровье   %s" % bar(st["health"]),
             "😊 Счастье    %s" % bar(st["happiness"]),
             "📚 Знания     %s" % bar(st["knowledge"])]
    if a >= 6:
        lines.append("🤝 Семья      %s" % bar(st.get("family_meter", 50)))
    if has_close(st):
        lines.append("💕 Близкие    %s" % bar(st.get("love", 50)))
    lines.append("💰 %s" % money(st["money"]))
    if st.get("job"):
        lines.append("💼 %s" % st["job"])
    return "\n".join(lines)


def family_line(st):
    f = st["family"]
    if f == "полная семья":
        return "отец %s, мать %s" % (st["father"], st["mother"])
    if f == "многодетная семья":
        return "отец %s, мать %s, детей много" % (st["father"], st["mother"])
    if f == "приёмная семья":
        return "приёмные родители — %s и %s" % (st["father"], st["mother"])
    if f in ("один родитель", "мама одна"):
        return "только мать %s, отца нет" % st["mother"]
    if f == "бабушка и дедушка":
        return "растят бабушка и дедушка, родителей нет"
    if f == "детский дом":
        return "детский дом, родителей нет"
    if f == "семья алкоголиков":
        return "отец %s и мать %s пьют, дома покоя нет" % (st["father"], st["mother"])
    return f


def birth_text(st):
    share = sum(c["births"] for c in COUNTRIES if c["name"] == st["country"]) / TOTAL_BIRTHS * 100
    born = "Ты родился" if st["male"] else "Ты родилась"
    month = ["январе", "феврале", "марте", "апреле", "мае", "июне", "июле", "августе",
             "сентябре", "октябре", "ноябре", "декабре"][int(st["born"][5:7]) - 1]
    first = "первый ребёнок в семье" if st["sibs"] == 0 else "не первый ребёнок в семье"
    t = ["%s сегодня. %s %s, %s, %s." % (born, st["flag"], st["country"], st["place"], month),
         "Тебя зовут %s. Ты %s." % (st["name"], first), "",
         "🗣 Родной язык: %s" % st["lang"],
         "⛪ Религия семьи: %s" % REL_NAME.get(st["rel"], "народные верования"),
         "👪 %s" % family_line(st),
         "👥 Братьев и сестёр: %d" % st["sibs"],
         "💵 Доход семьи: %s" % QUINTILE.get(st["quintile"], "")]
    if st["alco"]:
        t.append("🍺 В доме постоянно пьют. Денег нет, дома покоя нет.")
    elif st["family"] == "детский дом":
        t.append("🏡 Ты вырос в детском доме: ни мамы, ни папы.")
    elif st["family"] in ("один родитель", "мама одна"):
        t.append("👩‍👧 Ты живёшь только с мамой: отца нет, денег не хватает.")
    elif st["family"] == "бабушка и дедушка":
        t.append("👵👴 Тебя растят бабушка и дедушка.")
    if st["tribal"]:
        t.append("🏕 Ты из коренного народа: свой язык, свой уклад, до школы далеко.")
    elif st["remote"]:
        t.append("🌾 Глубинка: до школы, врача и интернета далеко.")
    t.append("🎲 Здесь рождается %.2f%% всех детей мира" % share)
    t += ["", card(st), "", "Жми «➡️ Прожить год»"]
    return "\n".join(t)


def _love_event(st):
    a = st["age"]
    if st.get("married") or st.get("partner") or a < 16 or a > 45:
        return None
    if random.random() > 0.16:
        return None
    who = random.choice(FIRST_F if st["male"] else FIRST_M)
    st["crush"] = who
    txt = ("💘 Тебе приглянулся человек: %s.\n\nТы чувствуешь, что влюбился." % who) if st["male"] \
          else ("💘 Тебе приглянулась девушка: %s.\n\nТы чувствуешь, что влюбилась." % who)
    return (txt, ["Признаться в чувствах", "Предложить встречаться", "Промолчать"], "влюбился")


def _proposal_event(st):
    n = st["age"] - st["partner_since"]
    txt = ("💍 Ты %s с %s уже %d %s. Пора решать.\n\n%s сделал%s тебе предложение." % (
        "вместе", st["partner"], n, plural(n, "год", "года", "лет"),
        st["partner"], "" if st["male"] else "а"))
    return (txt, ["Сделать предложение", "Продолжить встречаться, но не жениться"], "предложение")


def _cheat_event(st):
    if not st.get("married"):
        return None
    roll = random.random()
    if roll < 0.18:
        who = random.choice(FIRST_M if st["male"] else FIRST_F)
        txt = "⚠️ Тебе написал%s %s. Похоже, у %s в браке другая жизнь." % (
            "" if st["male"] else "а", who, st["partner"])
        return (txt, ["Простить и разобраться", "Уйти и подать на развод", "Закрыть глаза и молчать"], "измена")
    if roll < 0.42:
        txt = "💔 Ты и %s всё реже вместе. Разговоры о вечерах превратились в молчание." % st["partner"]
        return (txt, ["Попытаться сохранить семью", "Решили расстаться", "Отложить разговор на потом"], "измена")
    return None


def _pregnancy_event(st):
    if not st.get("married") or st.get("kids", 0) >= 4:
        return None
    if random.random() > 0.22:
        return None
    txt = ("🤰 %s забеременела. Вопрос, который решают двое." % st["partner"]) if st["male"] \
          else "🤰 Ты забеременела. Вопрос, который решают двое."
    return (txt, ["Оставить ребёнка", "Сделать аборт"], "беременность")


def special_event(st):
    if st.get("partner") and not st.get("married"):
        if st["age"] - st["partner_since"] >= random.choice([3, 4, 5]):
            ev = _proposal_event(st)
            if ev:
                return ev
    if st.get("married"):
        ev = _pregnancy_event(st) or _cheat_event(st)
        if ev:
            return ev
    return _love_event(st)


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


def _effect(d=None, m=0):
    parts = []
    if d:
        for k, v in d.items():
            if v:
                parts.append("%s %+d" % (NAMES.get(k, k), v))
    if m:
        parts.append("деньги %s%s ₽" % ("+" if m > 0 else "−",
                    format(abs(int(m * RUB)), ",d").replace(",", " ")))
    return ", ".join(parts)


def apply_special(st, key, opt):
    if key == "влюбился":
        if opt == 0:
            if random.random() < 0.45:
                st["partner"], st["partner_since"] = st["crush"], st["age"]
                st["love"] = min(100, st.get("love", 50) + 25)
                st["happiness"] = min(100, st["happiness"] + 12)
                res = ("💞 Чувства оказались взаимными. %s теперь твой%s." % (
                    st["crush"], "" if st["male"] else "а"))
            else:
                st["happiness"] = max(0, st["happiness"] - 6)
                res = "💔 Чувства оказались невзаимными. Пришлось отойти в сторону."
        elif opt == 1:
            if random.random() < 0.6:
                st["partner"], st["partner_since"] = st["crush"], st["age"]
                st["love"] = min(100, st.get("love", 50) + 20)
                st["happiness"] = min(100, st["happiness"] + 8)
                res = "☕ Вы стали встречаться."
            else:
                st["happiness"] = max(0, st["happiness"] - 3)
                res = "🙅 Отказали. Вы остались просто знакомыми."
        else:
            st["happiness"] = max(0, st["happiness"] - 2)
            res = "🤐 Ты промолчал. Чувство осталось при тебе." if st["male"] \
                  else "🤐 Ты промолчала. Чувство осталось при тебе."
        st["crush"] = None
    elif key == "предложение":
        if opt == 0:
            if random.random() < 0.75:
                st["married"], st["married_since"] = True, st["age"]
                st["love"] = min(100, st.get("love", 50) + 15)
                st["happiness"] = min(100, st["happiness"] + 10)
                st["money"] = max(0, st["money"] - 300)
                res = ("💍 Вы поженились. С этого дня %s — твоя жена." % st["partner"]) if st["male"] \
                      else ("💍 Вы поженились. С этого дня %s — твой муж." % st["partner"])
            else:
                st["love"] = max(0, st.get("love", 50) - 8)
                st["happiness"] = max(0, st["happiness"] - 4)
                res = "💔 %s сказал%s «пока не готов». Отношения продолжились, но с трещиной." % (
                    st["partner"], "" if st["male"] else "а")
        else:
            st["love"] = max(0, st.get("love", 50) - 3)
            res = "🕰 Ты отложил предложение." if st["male"] else "🕰 Ты отложила предложение."
    elif key == "измена":
        if opt == 0:
            st["love"] = min(100, st.get("love", 50) + 3)
            st["happiness"] = max(0, st["happiness"] - 3)
            res = "🤝 Вы поговорили и решили сохранить семью. Доверие восстановилось не полностью."
        elif opt == 1:
            st["married"], st["ex"], st["partner"] = False, st["partner"], None
            st["love"] = max(0, st.get("love", 50) - 30)
            st["happiness"] = max(0, st["happiness"] - 12)
            res = "📄 Вы развелись. Осталось много тяжёлого, но и много своей жизни впереди."
        else:
            st["happiness"] = max(0, st["happiness"] - 8)
            st["love"] = max(0, st.get("love", 50) - 6)
            res = "🤫 Ты закрыл глаза. Но внутри всё равно горело." if st["male"] \
                  else "🤫 Ты закрыла глаза. Но внутри всё равно горело."
    elif key == "беременность":
        if opt == 0:
            st["kids"] += 1
            st["happiness"] = min(100, st["happiness"] + 8)
            st["love"] = min(100, st.get("love", 50) + 6)
            st["money"] = max(0, st["money"] - 120)
            res = "👶 Ребёнок родился. Семья стала больше."
        else:
            st["happiness"] = max(0, st["happiness"] - 10)
            st["love"] = max(0, st.get("love", 50) - 8)
            st["money"] = max(0, st["money"] - 60)
            res = ("🩺 Ты прервал беременность. Стало легче физически, но что-то осталось внутри.") \
                if st["male"] else \
                ("🩺 Ты прервала беременность. Стало легче физически, но что-то осталось внутри.")
    st["last_result"] = res
    return res


def death_risk(st):
    a = st["age"]
    if a < 2:
        base = 0.02 if st["gdp"] < 4000 else 0.004
    elif a < 15:
        base = 0.004
    elif a < 50:
        base = 0.002
    elif a < 70:
        base = 0.012
    elif a < 80:
        base = 0.04
    else:
        base = 0.12
    risk = base * (2.2 - max(0, st["health"]) / 60)
    if a >= st["le"] + 15 or st["health"] <= 0:
        risk = 0.9
    return max(0.0, risk)


def cause(st):
    a = st["age"]
    if st["health"] <= 10:
        return "умер от болезни"
    if a < 5:
        return "умер в раннем детстве от инфекции"
    if a < 40:
        return random.choice(["погиб в аварии", "умер от болезни", "погиб в несчастном случае"])
    if a < 70:
        return random.choice(["умер от инфаркта", "умер от рака", "умер от инсульта"])
    return random.choice(["тихо умер во сне", "умер от старости", "умер от сердечной недостаточности"])


def grow(st):
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
        st["log"].append("%d: начал работу — %s" % (a, st["job"]))
    if st.get("married"):
        st["love"] = max(0, min(100, st.get("love", 50) + random.choice([-2, -1, 0, 1, 2])))
    elif st.get("partner"):
        st["love"] = max(0, min(100, st.get("love", 50) + random.choice([-1, 0, 1])))
    if st.get("kids"):
        st["love"] = min(100, st.get("love", 50) + random.choice([0, 0, 1]))
    if a < 16:
        st["family_meter"] = max(0, min(100, st.get("family_meter", 50) + random.choice([-1, 0, 1])))
    for k in ("health", "happiness", "knowledge", "family_meter", "love"):
        if k in st:
            st[k] = max(0, min(100, st[k]))
    if random.random() < death_risk(st):
        st["over"] = True
        st["cause"] = cause(st)
        st["log"].append("%d: %s" % (a, st["cause"]))
        return True
    return False


def apply(st, e, i):
    o = e["o"][i]
    for k, v in o["d"].items():
        if k == "family":
            k = "family_meter"
        st[k] = max(0, min(100, st.get(k, 50) + v))
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
    st["log"].append("%d: %s → %s" % (st["age"], t, x))
    eff = _effect(o["d"], o["m"])
    st["last_result"] = eff or "без последствий"
    return st["last_result"]


def label(p):
    if p >= 90:
        return "топ-10%"
    if p >= 70:
        return "сильно выше среднего"
    if p >= 55:
        return "чуть выше среднего"
    if p >= 40:
        return "примерно как у всех"
    return "ниже среднего"


def final_text(st):
    a = st["age"]
    y = int(st["born"][:4])
    t = ["🪦 %s, %d–%d" % (st["name"], y, y + a),
         "%s в %d %s" % (st["cause"] or "жизнь окончена", a, age_years(a)), "",
         "%s %s · %s · язык: %s" % (st["flag"], st["country"], st["place"], st["lang"]),
         "⛪ %s · 💵 %s" % (REL_NAME.get(st["rel"], ""), QUINTILE.get(st["quintile"], "")),
         "👪 %s · братьев и сестёр: %d" % (st["family"], st["sibs"]),
         "💼 Работа: %s · 🎓 %s" % (st["job"] or "не работал", st["edu"] or "без высшего"),
         "💍 %s · 👶 детей: %d" % ("в браке" if st["married"] else "без брака", st["kids"]),
         "💰 Осталось: %s" % money(st["money"]), ""]
    if st.get("partner"):
        t.append("💕 %s" % st["partner"])
    elif st.get("ex"):
        t.append("💔 Были отношения с %s" % st["ex"])
    t += ["", "📊 Твои итоги:"]
    t.append("⏳ Долголетие: %s (в стране в среднем живут %.0f лет)" % (
        label(min(99, max(1, round(50 + (a - st["le"]) * 3)))), st["le"]))
    t.append("📚 Знания: %s" % label(min(99, max(1, round(st["knowledge"] / max(20, st["lit"] * 0.7) * 50)))))
    t.append("😊 Счастье: %s" % label(min(99, max(1, round(st["happiness"] / 60 * 50)))))
    if has_close(st):
        t.append("💕 Близкие: %s" % label(min(99, max(1, round(st.get("love", 50) / 60 * 50)))))
    elif a >= 6:
        t.append("🤝 Семья: %s" % label(min(99, max(1, round(st.get("family_meter", 50) / 60 * 50)))))
    t += ["", "📜 Главное в жизни:"]
    t += ["• " + s for s in st["log"][-12:]]
    t += ["", "Решений принято: %d" % st["steps"],
          "🔄 Жми «👶 Родиться», чтобы прожить новую жизнь"]
    return "\n".join(t)


def auto_live(st, years=None):
    n = 0
    while not st["over"] and (years is None or n < years):
        n += 1
        if grow(st):
            break
        e = draw_event(st)
        if e:
            apply(st, e, random.randrange(len(e["o"])))
    return st
