import csv
import random
from pathlib import Path
from datetime import date, timedelta

random.seed(42)


FIRST_NAMES_M = [
    "Liam","Noah","Oliver","Elijah","James","William","Benjamin","Lucas","Henry","Alexander",
    "Ethan","Jacob","Michael","Daniel","Logan","Jackson","Levi","Sebastian","Mateo","Jack",
    "Owen","Theodore","Aiden","Samuel","Joseph","John","David","Wyatt","Matthew","Luke",
]

FIRST_NAMES_F = [
    "Olivia","Emma","Ava","Sophia","Isabella","Mia","Charlotte","Amelia","Evelyn","Abigail",
    "Harper","Emily","Elizabeth","Avery","Sofia","Ella","Madison","Scarlett","Victoria","Aria",
    "Grace","Chloe","Camila","Penelope","Riley","Layla","Lillian","Nora","Zoey","Mila",
]

FIRST_NAMES_N = [
    "Quinn","Jordan","Alex","Taylor","Casey","Avery","Riley","Skyler","Rowan","Emerson",
    "Reese","Parker","Morgan","Hayden","Reagan","Sawyer","Finley","Elliot","Dakota","Cameron",
]

LAST_INITS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

APP_CITIES = [
    "New York","San Francisco","Chicago","Austin","Seattle","Boston","Denver","Miami","Portland",
    "Los Angeles","Atlanta","Dallas","Washington","Phoenix","Philadelphia","San Diego","Houston",
]

INDIA_BIRTH_CITIES = [
    "Mumbai","Delhi","Bengaluru","Chennai","Kolkata","Hyderabad"
]

TAGS = [
    "art","coffee","books","tech","climbing","cooking","travel","yoga","bbq","gaming","photography",
    "fitness","boardgames","poetry","beach","basketball","comedy","music","hiking","cinema"
]

MUSIC = ["indie","rock","pop","rap","edm","metal","jazz","classical"]
ENERGY = ["introvert","ambivert","extrovert"]
RISK = ["low","medium","high"]
HUMOR = ["wholesome","dark"]
DATES = [
    "bookstore","live music","farmer's market","board games","trail walk","arcade","day hike","dance night",
    "art museum","barcade","art crawl","concert","tea house","local show","photo walk","brewery","poetry night",
    "club","museum","movie night","coffee walk","food trucks","gallery opening","escape room","karaoke",
]


def pick_name(gender: str) -> str:
    if gender == "M":
        first = random.choice(FIRST_NAMES_M)
    elif gender == "F":
        first = random.choice(FIRST_NAMES_F)
    else:
        first = random.choice(FIRST_NAMES_N)
    last = random.choice(LAST_INITS)
    return f"{first} {last}."


def pick_gender() -> str:
    r = random.random()
    if r < 0.45:
        return "F"
    if r < 0.90:
        return "M"
    return "NB"


def pick_orientation(gender: str) -> str:
    # Hetero ~65%, Homo ~15%, Bi/Pan (any) ~20%
    r = random.random()
    if r < 0.65:
        if gender == "M":
            return "F"
        if gender == "F":
            return "M"
        return "any"
    elif r < 0.80:
        return gender if gender in ("M","F") else "any"
    else:
        return "any"


def age_window(age: int) -> tuple:
    span = random.randint(3, 6)
    return max(21, age - span), min(42, age + span)


def city_interest(city: str) -> str:
    # In the new schema, treat as a single city or "Any"
    return city if random.random() < 0.7 else "Any"


def tag_list() -> str:
    k = random.choice([2,3,3,4])
    return ", ".join(sorted(random.sample(TAGS, k=k)))


def anchor(val, noise=0.1):
    x = val + random.uniform(-noise, noise)
    return max(0.0, min(1.0, x))


def build_vectors(humor: str, energy: str, risk: str, tags: list) -> dict:
    # Base random around 0.5
    t = [anchor(random.random(), 0.3) for _ in range(10)]
    e = [anchor(random.random(), 0.3) for _ in range(6)]

    # Map some interpretable anchors
    # t_3 ~ social energy
    energy_anchor = {"introvert": 0.2, "ambivert": 0.5, "extrovert": 0.8}[energy]
    t[3] = anchor(energy_anchor, 0.12)

    # t_6 ~ humor darkness
    humor_anchor = 0.75 if humor == "dark" else 0.25
    t[6] = anchor(humor_anchor, 0.12)

    # t_5 ~ confidence/risk
    risk_anchor = {"low": 0.35, "medium": 0.5, "high": 0.7}[risk]
    t[5] = anchor(risk_anchor, 0.12)

    # Tags nudge certain traits
    tags_set = set(tags)
    if "art" in tags_set or "photography" in tags_set or "poetry" in tags_set:
        t[8] = anchor(0.7, 0.15)  # creativity
    if "tech" in tags_set or "coding" in tags_set:
        t[0] = anchor(0.65, 0.15)  # openness/logic
    if "fitness" in tags_set or "climbing" in tags_set or "hiking" in tags_set:
        t[4] = anchor(0.65, 0.15)  # energy/discipline

    # Ensure within [0,1]
    t = [max(0.0, min(1.0, x)) for x in t]
    e = [max(0.0, min(1.0, x)) for x in e]
    return {**{f"t_{i}": t[i] for i in range(10)}, **{f"e_{i}": e[i] for i in range(6)}}


def main(n=200, out_path: Path = None):
    out_path = out_path or (Path(__file__).parents[1] / "data" / "mate_db.csv")
    fieldnames = [
        "user_id","name","age","gender","city","tags","humor_style","music_vibe","social_energy","risk_taking","ideal_date",
        "gender_interest","min_age_pref","max_age_pref","city_interest",
        "birth_date","birth_city","birth_time",
        *[f"t_{i}" for i in range(10)], *[f"e_{i}" for i in range(6)]
    ]

    rows = []
    for uid in range(1, n+1):
        gender = pick_gender()
        name = pick_name(gender)
        age = random.randint(21, 40)
        city = random.choice(APP_CITIES)
        tags_str = tag_list()
        tags = [t.strip() for t in tags_str.split(',')]
        humor = random.choice(HUMOR)
        music = random.choice(MUSIC)
        energy = random.choice(ENERGY)
        risk = random.choice(RISK)
        ideal = random.choice(DATES)

        orient = pick_orientation(gender)
        mn, mx = age_window(age)
        cities_pref = city_interest(city)

        # Birth details
        birth_year = max(1984, min(2004, 2024 - (age + random.randint(0, 1)*1)))
        base = date(birth_year, 1, 1) + timedelta(days=random.randint(0, 364))
        birth_date = base.strftime("%Y-%m-%d")
        birth_city = random.choice(INDIA_BIRTH_CITIES) if random.random() < 0.7 else city
        birth_time = "" if random.random() < 0.6 else f"{random.randint(0,23):02d}:{random.randint(0,59):02d}"

        vec = build_vectors(humor, energy, risk, tags)

        row = {
            "user_id": uid,
            "name": name,
            "age": age,
            "gender": gender,
            "city": city,
            "tags": tags_str,
            "humor_style": humor,
            "music_vibe": music,
            "social_energy": energy,
            "risk_taking": risk,
            "ideal_date": ideal,
            "gender_interest": orient,
            "min_age_pref": mn,
            "max_age_pref": mx,
            "city_interest": cities_pref,
            "birth_date": birth_date,
            "birth_city": birth_city,
            "birth_time": birth_time,
            **vec,
        }
        rows.append(row)

    # Force the first row to match the provided example
    rows[0].update({
        "user_id": 1,
        "name": "Liam X.",
        "age": 29,
        "gender": "M",
        "city": "Miami",
        "tags": "climbing, music, tech",
        "humor_style": "wholesome",
        "music_vibe": "jazz",
        "social_energy": "introvert",
        "risk_taking": "low",
        "ideal_date": "farmer's market",
        "gender_interest": "F",
        "min_age_pref": 26,
        "max_age_pref": 32,
        "city_interest": "Miami",
        "birth_date": "1996-05-10",
        "birth_city": "Miami",
        "birth_time": "",
    })

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} profiles to {out_path}")


if __name__ == "__main__":
    main()
