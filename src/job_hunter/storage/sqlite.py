from contextlib import contextmanager
from dataclasses import asdict
import json
from pathlib import Path
import sqlite3
from uuid import uuid4
from job_hunter.domain.models import Profile, SearchConfig, STATES, now


def dump(value):
    return json.dumps(value, ensure_ascii=False)


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS profiles(version INTEGER PRIMARY KEY, data TEXT, created_at TEXT);
                CREATE TABLE IF NOT EXISTS searches(name TEXT PRIMARY KEY, data TEXT, updated_at TEXT);
                CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS jobs(key TEXT PRIMARY KEY, data TEXT, first_seen TEXT, last_seen TEXT);
                CREATE TABLE IF NOT EXISTS run_jobs(
                    run_id TEXT REFERENCES runs(id), job_key TEXT REFERENCES jobs(key),
                    terms TEXT, snapshot TEXT, evaluation TEXT, PRIMARY KEY(run_id,job_key));
                CREATE TABLE IF NOT EXISTS user_states(
                    job_key TEXT PRIMARY KEY REFERENCES jobs(key), state TEXT, notes TEXT);
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def save_profile(self, profile):
        profile.validate()
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            profile.version = db.execute("SELECT COALESCE(MAX(version),0)+1 FROM profiles").fetchone()[0]
            db.execute("INSERT INTO profiles VALUES(?,?,?)", (profile.version, dump(asdict(profile)), now()))
        return profile.version

    def load_profile(self):
        with self.connection() as db:
            row = db.execute("SELECT data FROM profiles ORDER BY version DESC LIMIT 1").fetchone()
        return Profile(**json.loads(row[0])) if row else Profile()

    def save_search(self, config):
        config.validate()
        with self.connection() as db:
            db.execute("INSERT INTO searches VALUES(?,?,?) ON CONFLICT(name) DO UPDATE SET data=excluded.data, updated_at=excluded.updated_at",
                       (config.name, dump(asdict(config)), now()))

    def search_names(self):
        with self.connection() as db:
            return [r[0] for r in db.execute("SELECT name FROM searches ORDER BY updated_at DESC")]

    def load_search(self, name=None):
        with self.connection() as db:
            row = db.execute("SELECT data FROM searches WHERE name=?", (name,)).fetchone() if name else db.execute("SELECT data FROM searches ORDER BY updated_at DESC LIMIT 1").fetchone()
        return SearchConfig(**json.loads(row[0])) if row else SearchConfig()

    def create_run(self, profile, config):
        run = {"id": uuid4().hex, "profile": asdict(profile), "config": asdict(config), "started_at": now(),
               "finished_at": None, "status": "running", "stage": "Preparando navegador", "term": "",
               "pages": 0, "jobs": 0, "duplicates": 0, "failures": 0, "terms_done": 0, "errors": []}
        with self.connection() as db:
            db.execute("INSERT INTO runs VALUES(?,?)", (run["id"], dump(run)))
        return run["id"]

    def update_run(self, run_id, **changes):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            run = json.loads(db.execute("SELECT data FROM runs WHERE id=?", (run_id,)).fetchone()[0])
            run.update(changes)
            db.execute("UPDATE runs SET data=? WHERE id=?", (dump(run), run_id))

    def runs(self):
        with self.connection() as db:
            return [json.loads(r[0]) for r in db.execute("SELECT data FROM runs ORDER BY rowid DESC")]

    def run(self, run_id):
        with self.connection() as db:
            row = db.execute("SELECT data FROM runs WHERE id=?", (run_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def interrupt_running(self):
        for run in self.runs():
            if run["status"] == "running":
                self.update_run(run["id"], status="interrupted", stage="Processo reiniciado", finished_at=now())

    def record_job(self, run_id, job, term, evaluation):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            exists = db.execute("SELECT 1 FROM jobs WHERE key=?", (job.key,)).fetchone()
            db.execute("INSERT INTO jobs VALUES(?,?,?,?) ON CONFLICT(key) DO UPDATE SET data=excluded.data,last_seen=excluded.last_seen",
                       (job.key, dump(job.to_dict()), now(), now()))
            row = db.execute("SELECT terms FROM run_jobs WHERE run_id=? AND job_key=?", (run_id, job.key)).fetchone()
            terms = json.loads(row[0]) if row else []
            if term not in terms:
                terms.append(term)
            db.execute("INSERT INTO run_jobs VALUES(?,?,?,?,?) ON CONFLICT(run_id,job_key) DO UPDATE SET terms=excluded.terms",
                       (run_id, job.key, dump(terms), dump(job.to_dict()), dump(evaluation)))
        return not exists

    def results(self, run_id):
        with self.connection() as db:
            rows = db.execute("""SELECT r.*,j.first_seen,j.last_seen,s.state,s.notes FROM run_jobs r
                JOIN jobs j ON r.job_key=j.key LEFT JOIN user_states s ON s.job_key=j.key WHERE run_id=?""", (run_id,)).fetchall()
        return [{"key": r["job_key"], "job": json.loads(r["snapshot"]), "evaluation": json.loads(r["evaluation"]),
                 "terms": json.loads(r["terms"]), "state": r["state"] or "nova", "notes": r["notes"] or "",
                 "first_seen": r["first_seen"], "last_seen": r["last_seen"]} for r in rows]

    def set_state(self, key, state, notes):
        if state not in STATES:
            raise ValueError("Estado inválido.")
        with self.connection() as db:
            db.execute("INSERT INTO user_states VALUES(?,?,?) ON CONFLICT(job_key) DO UPDATE SET state=excluded.state,notes=excluded.notes", (key, state, notes))
