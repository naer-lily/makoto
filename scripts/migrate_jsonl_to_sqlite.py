"""一次性 JSONL → SQLite 迁移脚本。

用法: python scripts/migrate_jsonl_to_sqlite.py

读完所有 JSONL 文件 + profile.json 后写入 data/makoto.db。
此脚本仅用于一次迁移，将来不再维护。
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

# 项目根
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DB = DATA / "makoto.db"


def migrate() -> None:
    if not any(DATA.glob("*.jsonl")) and not (DATA / "profile.json").exists():
        print("未找到 JSONL/profile.json 文件，无需迁移。")
        return

    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()

    # 建表
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS profile (
            id              INTEGER PRIMARY KEY CHECK (id = 1),
            name            TEXT NOT NULL,
            gender          TEXT NOT NULL,
            age             INTEGER NOT NULL,
            height_cm       REAL NOT NULL,
            weight_kg       REAL NOT NULL,
            body_fat_pct    REAL NOT NULL,
            target_weight_kg REAL NOT NULL,
            target_date     TEXT NOT NULL,
            activity_level  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS food (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            name                TEXT NOT NULL UNIQUE,
            calories_per_100g   REAL NOT NULL DEFAULT 0.0,
            protein_per_100g    REAL NOT NULL DEFAULT 0.0,
            carbs_per_100g      REAL NOT NULL DEFAULT 0.0,
            fat_per_100g        REAL NOT NULL DEFAULT 0.0,
            search_keywords     TEXT NOT NULL DEFAULT '[]',
            note                TEXT,
            created_at          TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS body_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date        TEXT NOT NULL UNIQUE,
            weight_kg       REAL NOT NULL,
            body_fat_pct    REAL NOT NULL,
            waist_cm        REAL,
            arm_cm          REAL,
            thigh_cm        REAL,
            note            TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS diet_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            log_time      TEXT NOT NULL,
            food_name     TEXT NOT NULL,
            grams         REAL NOT NULL,
            note          TEXT,
            created_at    TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS exercise_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            log_time        TEXT NOT NULL,
            exercise_name   TEXT NOT NULL,
            duration_desc   TEXT NOT NULL,
            calories_kcal   REAL NOT NULL,
            note            TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # Profile
    profile_file = DATA / "profile.json"
    if profile_file.exists():
        pf = json.loads(profile_file.read_text(encoding="utf-8"))
        cur.execute(
            """INSERT OR REPLACE INTO profile
               (id, name, gender, age, height_cm, weight_kg, body_fat_pct,
                target_weight_kg, target_date, activity_level)
               VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                pf["name"],
                pf["gender"],
                pf["age"],
                pf["height_cm"],
                pf["weight_kg"],
                pf["body_fat_pct"],
                pf["target_weight_kg"],
                pf["target_date"],
                pf["activity_level"],
            ),
        )
        print("  profile: 1 条")
    else:
        print("  profile.json 不存在，跳过")

    # Food
    foods_file = DATA / "foods.jsonl"
    food_count = 0
    if foods_file.exists():
        for line in foods_file.read_text(encoding="utf-8").strip().splitlines():
            if not line.strip():
                continue
            f = json.loads(line)
            cur.execute(
                """INSERT INTO food (name, calories_per_100g, protein_per_100g,
                   carbs_per_100g, fat_per_100g, search_keywords, note)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    f["name"],
                    f["calories_per_100g"],
                    f["protein_per_100g"],
                    f["carbs_per_100g"],
                    f["fat_per_100g"],
                    json.dumps(f.get("search_keywords", []), ensure_ascii=False),
                    f.get("note"),
                ),
            )
            food_count += 1
        print(f"  foods: {food_count} 条")
    else:
        print("  foods.jsonl 不存在，跳过")

    # Body logs
    body_file = DATA / "body_logs.jsonl"
    body_count = 0
    if body_file.exists():
        for line in body_file.read_text(encoding="utf-8").strip().splitlines():
            if not line.strip():
                continue
            b = json.loads(line)
            cur.execute(
                """INSERT INTO body_log (log_date, weight_kg, body_fat_pct,
                   waist_cm, arm_cm, thigh_cm, note)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    b["log_date"],
                    b["weight_kg"],
                    b["body_fat_pct"],
                    b.get("waist_cm"),
                    b.get("arm_cm"),
                    b.get("thigh_cm"),
                    b.get("note"),
                ),
            )
            body_count += 1
        print(f"  body_logs: {body_count} 条")
    else:
        print("  body_logs.jsonl 不存在，跳过")

    # Diet logs
    diet_file = DATA / "diet_logs.jsonl"
    diet_count = 0
    if diet_file.exists():
        for line in diet_file.read_text(encoding="utf-8").strip().splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            cur.execute(
                "INSERT INTO diet_log (log_time, food_name, grams, note) VALUES (?, ?, ?, ?)",
                (d["log_time"], d["food_name"], d["grams"], d.get("note")),
            )
            diet_count += 1
        print(f"  diet_logs: {diet_count} 条")
    else:
        print("  diet_logs.jsonl 不存在，跳过")

    # Exercise logs
    ex_file = DATA / "exercise_logs.jsonl"
    ex_count = 0
    if ex_file.exists():
        for line in ex_file.read_text(encoding="utf-8").strip().splitlines():
            if not line.strip():
                continue
            e = json.loads(line)
            cur.execute(
                """INSERT INTO exercise_log (log_time, exercise_name, duration_desc,
                   calories_kcal, note) VALUES (?, ?, ?, ?, ?)""",
                (e["log_time"], e["exercise_name"], e["duration_desc"],
                 e["calories_kcal"], e.get("note")),
            )
            ex_count += 1
        print(f"  exercise_logs: {ex_count} 条")
    else:
        print("  exercise_logs.jsonl 不存在，跳过")

    conn.commit()
    conn.close()
    print(f"\n迁移完成 → {DB}")


if __name__ == "__main__":
    migrate()
