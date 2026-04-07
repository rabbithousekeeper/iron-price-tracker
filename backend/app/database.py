"""データベース接続・テーブル初期化・CRUD操作

Supabase PostgreSQLへの直接接続（psycopg2経由）
garmin_ プレフィックスのテーブルを管理する
"""

import json
import logging
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    create_engine, Column, Text, Date, Integer, BigInteger, Numeric,
    Boolean, DateTime, func, text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)

# Supabase PostgreSQL接続エンジン
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# ── テーブル定義 ──

class GarminActivity(Base):
    """アクティビティテーブル"""
    __tablename__ = "garmin_activities"

    id = Column(Text, primary_key=True)
    name = Column(Text)
    sport_type = Column(Text)
    start_time = Column(DateTime(timezone=True))
    duration_s = Column(Numeric)
    distance_m = Column(Numeric)
    avg_hr = Column(Numeric)
    max_hr = Column(Numeric)
    avg_pace_ms = Column(Numeric)
    elevation_m = Column(Numeric)
    calories = Column(Numeric)
    training_effect = Column(Numeric)
    aerobic_te = Column(Numeric)
    anaerobic_te = Column(Numeric)
    vo2max = Column(Numeric)
    training_load = Column(Numeric)
    raw_json = Column(JSONB)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())


class GarminSleep(Base):
    """睡眠データテーブル"""
    __tablename__ = "garmin_sleep"

    date = Column(Date, primary_key=True)
    sleep_start = Column(DateTime(timezone=True))
    sleep_end = Column(DateTime(timezone=True))
    total_sleep_s = Column(Numeric)
    deep_sleep_s = Column(Numeric)
    light_sleep_s = Column(Numeric)
    rem_sleep_s = Column(Numeric)
    awake_s = Column(Numeric)
    sleep_score = Column(Numeric)
    avg_spo2 = Column(Numeric)
    avg_respiration = Column(Numeric)
    avg_hr_sleep = Column(Numeric)
    raw_json = Column(JSONB)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())


class GarminDailyHealth(Base):
    """日別健康データテーブル"""
    __tablename__ = "garmin_daily_health"

    date = Column(Date, primary_key=True)
    steps = Column(Integer)
    active_kcal = Column(Numeric)
    resting_kcal = Column(Numeric)
    total_kcal = Column(Numeric)
    resting_hr = Column(Numeric)
    max_hr = Column(Numeric)
    avg_stress = Column(Numeric)
    max_stress = Column(Numeric)
    hrv_status = Column(Text)
    hrv_value = Column(Numeric)
    intensity_min_moderate = Column(Integer)
    intensity_min_vigorous = Column(Integer)
    floors_climbed = Column(Integer)
    hydration_ml = Column(Numeric)
    raw_json = Column(JSONB)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())


class GarminBodyComposition(Base):
    """体組成データテーブル"""
    __tablename__ = "garmin_body_composition"

    date = Column(Date, primary_key=True)
    weight_kg = Column(Numeric)
    bmi = Column(Numeric)
    body_fat_pct = Column(Numeric)
    muscle_mass_kg = Column(Numeric)
    bone_mass_kg = Column(Numeric)
    body_water_pct = Column(Numeric)
    metabolic_age = Column(Integer)
    raw_json = Column(JSONB)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())


class GarminSession(Base):
    """Garmin認証セッション保存テーブル（Renderのephemeral FS対策）"""
    __tablename__ = "garmin_session"

    id = Column(Integer, primary_key=True, default=1)
    session_data = Column(JSONB)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class GarminSyncLog(Base):
    """同期ログテーブル"""
    __tablename__ = "garmin_sync_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    synced_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(Text)
    activities = Column(Integer, default=0)
    sleep_days = Column(Integer, default=0)
    health_days = Column(Integer, default=0)
    body_days = Column(Integer, default=0)
    message = Column(Text)


# ── DB操作関数 ──

def get_db():
    """FastAPI依存性注入用のDBセッション生成"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Supabase上にテーブルを作成（存在しない場合のみ）"""
    Base.metadata.create_all(bind=engine)
    logger.info("データベーステーブルを初期化しました")


def save_session(db, session_data: dict):
    """Garmin認証セッションをDBに保存"""
    existing = db.query(GarminSession).filter(GarminSession.id == 1).first()
    if existing:
        existing.session_data = session_data
        existing.updated_at = func.now()
    else:
        db.add(GarminSession(id=1, session_data=session_data))
    db.commit()


def load_session(db) -> dict | None:
    """DBからGarmin認証セッションを読み込む"""
    row = db.query(GarminSession).filter(GarminSession.id == 1).first()
    if row and row.session_data:
        return row.session_data
    return None


def upsert_activity(db, data: dict):
    """アクティビティをUPSERT"""
    activity_id = str(data.get("activityId", ""))
    if not activity_id:
        return

    existing = db.query(GarminActivity).filter(GarminActivity.id == activity_id).first()
    values = {
        "id": activity_id,
        "name": data.get("activityName"),
        "sport_type": data.get("activityType", {}).get("typeKey") if isinstance(data.get("activityType"), dict) else data.get("activityType"),
        "start_time": data.get("startTimeLocal"),
        "duration_s": data.get("duration"),
        "distance_m": data.get("distance"),
        "avg_hr": data.get("averageHR"),
        "max_hr": data.get("maxHR"),
        "avg_pace_ms": data.get("averageSpeed"),
        "elevation_m": data.get("elevationGain"),
        "calories": data.get("calories"),
        "training_effect": data.get("trainingEffectLabel"),
        "aerobic_te": data.get("aerobicTrainingEffect"),
        "anaerobic_te": data.get("anaerobicTrainingEffect"),
        "vo2max": data.get("vO2MaxValue"),
        "training_load": data.get("activityTrainingLoad"),
        "raw_json": data,
    }

    if existing:
        for k, v in values.items():
            if k != "id":
                setattr(existing, k, v)
    else:
        db.add(GarminActivity(**values))


def upsert_sleep(db, sleep_date: date, data: dict):
    """睡眠データをUPSERT"""
    existing = db.query(GarminSleep).filter(GarminSleep.date == sleep_date).first()

    # dailySleepDTO から値を取得
    daily = data.get("dailySleepDTO", data)
    values = {
        "date": sleep_date,
        "sleep_start": daily.get("sleepStartTimestampLocal") or daily.get("sleepStart"),
        "sleep_end": daily.get("sleepEndTimestampLocal") or daily.get("sleepEnd"),
        "total_sleep_s": daily.get("sleepTimeSeconds"),
        "deep_sleep_s": daily.get("deepSleepSeconds"),
        "light_sleep_s": daily.get("lightSleepSeconds"),
        "rem_sleep_s": daily.get("remSleepSeconds"),
        "awake_s": daily.get("awakeSleepSeconds"),
        "sleep_score": daily.get("sleepScores", {}).get("overall", {}).get("value") if isinstance(daily.get("sleepScores"), dict) else daily.get("sleepScores"),
        "avg_spo2": daily.get("averageSpO2Value"),
        "avg_respiration": daily.get("averageRespirationValue"),
        "avg_hr_sleep": daily.get("averageHeartRate"),
        "raw_json": data,
    }

    if existing:
        for k, v in values.items():
            if k != "date":
                setattr(existing, k, v)
    else:
        db.add(GarminSleep(**values))


def upsert_daily_health(db, health_date: date, data: dict):
    """日別健康データをUPSERT"""
    existing = db.query(GarminDailyHealth).filter(GarminDailyHealth.date == health_date).first()
    values = {
        "date": health_date,
        "steps": data.get("totalSteps"),
        "active_kcal": data.get("activeKilocalories"),
        "resting_kcal": data.get("bmrKilocalories"),
        "total_kcal": data.get("totalKilocalories"),
        "resting_hr": data.get("restingHeartRate"),
        "max_hr": data.get("maxHeartRate"),
        "avg_stress": data.get("averageStressLevel"),
        "max_stress": data.get("maxStressLevel"),
        "hrv_status": data.get("hrvStatus"),
        "hrv_value": data.get("hrvValue"),
        "intensity_min_moderate": data.get("moderateIntensityMinutes"),
        "intensity_min_vigorous": data.get("vigorousIntensityMinutes"),
        "floors_climbed": data.get("floorsAscended"),
        "hydration_ml": data.get("hydrationIntakeMl"),
        "raw_json": data,
    }

    if existing:
        for k, v in values.items():
            if k != "date":
                setattr(existing, k, v)
    else:
        db.add(GarminDailyHealth(**values))


def upsert_body_composition(db, body_date: date, data: dict):
    """体組成データをUPSERT"""
    existing = db.query(GarminBodyComposition).filter(GarminBodyComposition.date == body_date).first()
    values = {
        "date": body_date,
        "weight_kg": data.get("weight", 0) / 1000 if data.get("weight") else None,  # gをkgに変換
        "bmi": data.get("bmi"),
        "body_fat_pct": data.get("bodyFat"),
        "muscle_mass_kg": data.get("muscleMass", 0) / 1000 if data.get("muscleMass") else None,
        "bone_mass_kg": data.get("boneMass", 0) / 1000 if data.get("boneMass") else None,
        "body_water_pct": data.get("bodyWater"),
        "metabolic_age": data.get("metabolicAge"),
        "raw_json": data,
    }

    if existing:
        for k, v in values.items():
            if k != "date":
                setattr(existing, k, v)
    else:
        db.add(GarminBodyComposition(**values))


def add_sync_log(db, status: str, activities: int = 0, sleep_days: int = 0,
                 health_days: int = 0, body_days: int = 0, message: str = ""):
    """同期ログを追加"""
    log = GarminSyncLog(
        status=status,
        activities=activities,
        sleep_days=sleep_days,
        health_days=health_days,
        body_days=body_days,
        message=message,
    )
    db.add(log)
    db.commit()
    return log
