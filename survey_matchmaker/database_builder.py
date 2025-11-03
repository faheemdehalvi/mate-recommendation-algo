from __future__ import annotations

"""SQLite database builder and loader for survey-based matchmaking."""

from typing import Iterable, Tuple, List
import os
import sqlite3
import pandas as pd


def _connect(db_path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def build_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            city TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS survey_responses (
            user_id INTEGER NOT NULL,
            s1_q1 INTEGER, s1_q2 INTEGER, s1_q3 INTEGER,
            s2_q1 INTEGER, s2_q2 INTEGER, s2_q3 INTEGER,
            s3_q1 INTEGER, s3_q2 INTEGER, s3_q3 INTEGER,
            s4_q1 INTEGER, s4_q2 INTEGER, s4_q3 INTEGER,
            s5_q1 INTEGER, s5_q2 INTEGER, s5_q3 INTEGER,
            s6_q1 INTEGER, s6_q2 INTEGER, s6_q3 INTEGER,
            s7_q1 INTEGER, s7_q2 INTEGER, s7_q3 INTEGER,
            s8_q1 INTEGER, s8_q2 INTEGER, s8_q3 INTEGER,
            s9_q1 INTEGER, s9_q2 INTEGER, s9_q3 INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS traits (
            user_id INTEGER PRIMARY KEY,
            t0 REAL, t1 REAL, t2 REAL, t3 REAL, t4 REAL,
            t5 REAL, t6 REAL, t7 REAL, t8 REAL, t9 REAL,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS engagement (
            user_id INTEGER PRIMARY KEY,
            e0 REAL, e1 REAL, e2 REAL, e3 REAL, e4 REAL,
            e5 REAL, e6 REAL, e7 REAL, e8 REAL, e9 REAL,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS matches (
            user_id_a INTEGER NOT NULL,
            user_id_b INTEGER NOT NULL,
            score REAL NOT NULL,
            FOREIGN KEY(user_id_a) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY(user_id_b) REFERENCES users(user_id) ON DELETE CASCADE
        );
        """
    )
    conn.commit()


def populate(conn: sqlite3.Connection, responses: pd.DataFrame, traits: pd.DataFrame, engagement: pd.DataFrame) -> None:
    # users
    users_df = responses[["user_id", "name", "age", "gender", "city"]].drop_duplicates("user_id")
    users_df.to_sql("users", conn, if_exists="replace", index=False)

    # survey_responses
    resp_cols = [c for c in responses.columns if c.startswith("s") or c in ("user_id",)]
    responses[resp_cols].to_sql("survey_responses", conn, if_exists="replace", index=False)

    # traits/engagement
    traits.to_sql("traits", conn, if_exists="replace", index=False)
    engagement.to_sql("engagement", conn, if_exists="replace", index=False)


def insert_matches(conn: sqlite3.Connection, matches: List[Tuple[int, int, float]]) -> None:
    cur = conn.cursor()
    cur.execute("DELETE FROM matches")
    cur.executemany("INSERT INTO matches(user_id_a, user_id_b, score) VALUES (?, ?, ?)", matches)
    conn.commit()


def build_database(responses: pd.DataFrame, traits: pd.DataFrame, engagement: pd.DataFrame, db_path: str = "survey_matchmaker/output/survey_matchmaker.db") -> str:
    conn = _connect(db_path)
    try:
        build_schema(conn)
        populate(conn, responses, traits, engagement)
    finally:
        conn.close()
    return db_path

