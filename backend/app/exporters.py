"""Claude用JSONエクスポート生成モジュール

各分析タイプに応じたJSON構造を組み立てる。
Claudeが分析しやすいフォーマットで出力する。
"""

import logging
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import (
    GarminActivity, GarminSleep, GarminDailyHealth, GarminBodyComposition,
)

logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))


def _decimal_to_float(val):
    """Decimal/数値をfloatに変換"""
    if val is None:
        return None
    if isinstance(val, Decimal):
        return float(val)
    return val


def _seconds_to_hours(s):
    """秒を時間に変換（小数点1桁）"""
    if s is None:
        return None
    return round(float(s) / 3600, 1)


def _seconds_to_minutes(s):
    """秒を分に変換（整数）"""
    if s is None:
        return None
    return round(float(s) / 60)


def _pace_from_speed(speed_ms):
    """m/sからmin/km表記に変換"""
    if not speed_ms or float(speed_ms) <= 0:
        return None
    pace_s_per_km = 1000 / float(speed_ms)
    minutes = int(pace_s_per_km // 60)
    seconds = int(pace_s_per_km % 60)
    return f"{minutes}:{seconds:02d}"


def _common_header(export_type: str, start_date: date, end_date: date, days: int) -> dict:
    """共通ヘッダーを生成"""
    return {
        "export_type": export_type,
        "export_date": datetime.now(JST).isoformat(),
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days,
        },
        "user_context": {
            "note": "このJSONをClaudeに貼り付けて分析を依頼してください"
        },
    }


def _get_activities(db: Session, start_date: date, end_date: date) -> list[GarminActivity]:
    """期間内のアクティビティを取得"""
    return db.query(GarminActivity).filter(
        GarminActivity.start_time >= datetime.combine(start_date, datetime.min.time()),
        GarminActivity.start_time <= datetime.combine(end_date, datetime.max.time()),
    ).order_by(desc(GarminActivity.start_time)).all()


def _get_sleep(db: Session, start_date: date, end_date: date) -> list[GarminSleep]:
    """期間内の睡眠データを取得"""
    return db.query(GarminSleep).filter(
        GarminSleep.date >= start_date,
        GarminSleep.date <= end_date,
    ).order_by(desc(GarminSleep.date)).all()


def _get_health(db: Session, start_date: date, end_date: date) -> list[GarminDailyHealth]:
    """期間内の健康データを取得"""
    return db.query(GarminDailyHealth).filter(
        GarminDailyHealth.date >= start_date,
        GarminDailyHealth.date <= end_date,
    ).order_by(desc(GarminDailyHealth.date)).all()


def _get_body(db: Session, start_date: date, end_date: date) -> list[GarminBodyComposition]:
    """期間内の体組成データを取得"""
    return db.query(GarminBodyComposition).filter(
        GarminBodyComposition.date >= start_date,
        GarminBodyComposition.date <= end_date,
    ).order_by(desc(GarminBodyComposition.date)).all()


def _format_activity(act: GarminActivity) -> dict:
    """アクティビティを出力用dictに変換"""
    return {
        "date": act.start_time.strftime("%Y-%m-%d") if act.start_time else None,
        "sport": act.sport_type,
        "name": act.name,
        "distance_km": round(float(act.distance_m) / 1000, 1) if act.distance_m else None,
        "duration_min": _seconds_to_minutes(act.duration_s),
        "pace_min_km": _pace_from_speed(act.avg_pace_ms),
        "avg_hr": _decimal_to_float(act.avg_hr),
        "max_hr": _decimal_to_float(act.max_hr),
        "calories": _decimal_to_float(act.calories),
        "training_load": _decimal_to_float(act.training_load),
        "aerobic_te": _decimal_to_float(act.aerobic_te),
        "elevation_m": _decimal_to_float(act.elevation_m),
    }


def _build_activity_summary(activities: list[GarminActivity]) -> dict:
    """アクティビティのサマリーを構築"""
    total_distance = sum(float(a.distance_m or 0) for a in activities)
    total_duration = sum(float(a.duration_s or 0) for a in activities)
    total_calories = sum(float(a.calories or 0) for a in activities)
    total_elevation = sum(float(a.elevation_m or 0) for a in activities)
    hr_values = [float(a.avg_hr) for a in activities if a.avg_hr]

    # スポーツ別集計
    by_sport: dict[str, dict] = defaultdict(lambda: {"count": 0, "distance_km": 0.0, "duration_h": 0.0})
    for a in activities:
        sport = a.sport_type or "other"
        by_sport[sport]["count"] += 1
        by_sport[sport]["distance_km"] += float(a.distance_m or 0) / 1000
        by_sport[sport]["duration_h"] += float(a.duration_s or 0) / 3600

    # 丸め処理
    for sport_data in by_sport.values():
        sport_data["distance_km"] = round(sport_data["distance_km"], 1)
        sport_data["duration_h"] = round(sport_data["duration_h"], 1)

    return {
        "total_activities": len(activities),
        "total_distance_km": round(total_distance / 1000, 1),
        "total_duration_h": round(total_duration / 3600, 1),
        "total_calories": round(total_calories),
        "total_elevation_m": round(total_elevation),
        "avg_hr": round(sum(hr_values) / len(hr_values)) if hr_values else None,
        "by_sport": dict(by_sport),
    }


def _build_sleep_summary(sleep_list: list[GarminSleep]) -> dict:
    """睡眠サマリーを構築"""
    if not sleep_list:
        return {"avg_sleep_h": None, "avg_sleep_score": None, "avg_deep_sleep_h": None, "avg_rem_sleep_h": None}

    total_h = [float(s.total_sleep_s) / 3600 for s in sleep_list if s.total_sleep_s]
    scores = [float(s.sleep_score) for s in sleep_list if s.sleep_score]
    deep_h = [float(s.deep_sleep_s) / 3600 for s in sleep_list if s.deep_sleep_s]
    rem_h = [float(s.rem_sleep_s) / 3600 for s in sleep_list if s.rem_sleep_s]

    return {
        "avg_sleep_h": round(sum(total_h) / len(total_h), 1) if total_h else None,
        "avg_sleep_score": round(sum(scores) / len(scores)) if scores else None,
        "avg_deep_sleep_h": round(sum(deep_h) / len(deep_h), 1) if deep_h else None,
        "avg_rem_sleep_h": round(sum(rem_h) / len(rem_h), 1) if rem_h else None,
    }


def _build_health_summary(health_list: list[GarminDailyHealth]) -> dict:
    """健康サマリーを構築"""
    if not health_list:
        return {"avg_resting_hr": None, "avg_stress": None, "avg_hrv": None, "hrv_trend": "unknown"}

    rhr = [float(h.resting_hr) for h in health_list if h.resting_hr]
    stress = [float(h.avg_stress) for h in health_list if h.avg_stress]
    hrv = [float(h.hrv_value) for h in health_list if h.hrv_value]

    # HRVトレンド判定（前半 vs 後半の平均を比較）
    hrv_trend = "unknown"
    if len(hrv) >= 4:
        mid = len(hrv) // 2
        first_half = sum(hrv[:mid]) / mid
        second_half = sum(hrv[mid:]) / (len(hrv) - mid)
        diff = second_half - first_half
        if diff > 3:
            hrv_trend = "improving"
        elif diff < -3:
            hrv_trend = "declining"
        else:
            hrv_trend = "stable"

    return {
        "avg_resting_hr": round(sum(rhr) / len(rhr)) if rhr else None,
        "avg_stress": round(sum(stress) / len(stress)) if stress else None,
        "avg_hrv": round(sum(hrv) / len(hrv)) if hrv else None,
        "hrv_trend": hrv_trend,
    }


# ── エクスポートビルダー ──

def _export_training(db: Session, days: int) -> dict:
    """週次/月次トレーニング振り返り"""
    today = date.today()
    start = today - timedelta(days=days)

    activities = _get_activities(db, start, today)
    sleep_list = _get_sleep(db, start, today)
    health_list = _get_health(db, start, today)

    result = _common_header("weekly_training" if days <= 14 else "monthly_training", start, today, days)
    result["summary"] = _build_activity_summary(activities)
    result["activities"] = [_format_activity(a) for a in activities]
    result["sleep_summary"] = _build_sleep_summary(sleep_list)
    result["health_summary"] = _build_health_summary(health_list)
    return result


def _export_sleep_correlation(db: Session, days: int) -> dict:
    """睡眠×トレーニング相関"""
    today = date.today()
    start = today - timedelta(days=days)

    sleep_list = _get_sleep(db, start, today)
    activities = _get_activities(db, start, today)
    health_list = _get_health(db, start, today)

    # 日別のアクティビティをマッピング
    act_by_date: dict[str, list] = defaultdict(list)
    for a in activities:
        if a.start_time:
            d = a.start_time.strftime("%Y-%m-%d")
            act_by_date[d].append(a)

    # HRVマッピング
    hrv_by_date = {h.date.isoformat(): _decimal_to_float(h.hrv_value) for h in health_list if h.hrv_value}

    daily_pairs = []
    for s in sleep_list:
        next_day = (s.date + timedelta(days=1)).isoformat()
        next_acts = act_by_date.get(next_day, [])
        next_activity = None
        if next_acts:
            a = next_acts[0]
            next_activity = {
                "sport": a.sport_type,
                "distance_km": round(float(a.distance_m) / 1000, 1) if a.distance_m else None,
                "pace_min_km": _pace_from_speed(a.avg_pace_ms),
                "avg_hr": _decimal_to_float(a.avg_hr),
            }

        daily_pairs.append({
            "date": next_day,
            "sleep": {
                "date": s.date.isoformat(),
                "total_h": round(float(s.total_sleep_s) / 3600, 1) if s.total_sleep_s else None,
                "score": _decimal_to_float(s.sleep_score),
                "deep_h": round(float(s.deep_sleep_s) / 3600, 1) if s.deep_sleep_s else None,
                "rem_h": round(float(s.rem_sleep_s) / 3600, 1) if s.rem_sleep_s else None,
                "hrv": hrv_by_date.get(s.date.isoformat()),
            },
            "next_day_activity": next_activity,
        })

    # 相関ヒント
    scored_sleep = [(s.date.isoformat(), float(s.sleep_score)) for s in sleep_list if s.sleep_score]
    scored_sleep.sort(key=lambda x: x[1], reverse=True)
    best = [d for d, _ in scored_sleep[:3]]
    worst = [d for d, _ in scored_sleep[-3:]]

    load_days = []
    for a in activities:
        if a.training_load and float(a.training_load) > 80:
            if a.start_time:
                load_days.append(a.start_time.strftime("%Y-%m-%d"))

    result = _common_header("sleep_correlation", start, today, days)
    result["daily_pairs"] = daily_pairs
    result["correlation_hints"] = {
        "best_sleep_days": best,
        "worst_sleep_days": worst,
        "high_load_days": sorted(set(load_days)),
    }
    return result


def _export_overtraining(db: Session, days: int) -> dict:
    """オーバートレーニング兆候分析"""
    today = date.today()
    start = today - timedelta(days=days)

    activities = _get_activities(db, start, today)
    health_list = _get_health(db, start, today)
    sleep_list = _get_sleep(db, start, today)

    # 日別メトリクス
    health_by_date = {h.date: h for h in health_list}
    sleep_by_date = {s.date: s for s in sleep_list}
    act_by_date: dict[date, list] = defaultdict(list)
    for a in activities:
        if a.start_time:
            act_by_date[a.start_time.date()].append(a)

    daily_metrics = []
    for i in range(days):
        d = start + timedelta(days=i)
        h = health_by_date.get(d)
        s = sleep_by_date.get(d)
        day_acts = act_by_date.get(d, [])
        day_load = sum(float(a.training_load or 0) for a in day_acts)

        activity_desc = None
        if day_acts:
            parts = []
            for a in day_acts:
                sport = a.sport_type or "activity"
                dist = f" {round(float(a.distance_m) / 1000, 1)}km" if a.distance_m else ""
                parts.append(f"{sport}{dist}")
            activity_desc = ", ".join(parts)

        daily_metrics.append({
            "date": d.isoformat(),
            "resting_hr": _decimal_to_float(h.resting_hr) if h else None,
            "hrv": _decimal_to_float(h.hrv_value) if h else None,
            "sleep_score": _decimal_to_float(s.sleep_score) if s else None,
            "stress": _decimal_to_float(h.avg_stress) if h else None,
            "training_load": round(day_load) if day_load else None,
            "activity": activity_desc,
        })

    # 警告シグナル判定
    rhr_values = [float(h.resting_hr) for h in health_list if h.resting_hr]
    hrv_values = [float(h.hrv_value) for h in health_list if h.hrv_value]
    sleep_scores = [float(s.sleep_score) for s in sleep_list if s.sleep_score]

    rhr_elevated = False
    if len(rhr_values) >= 4:
        recent = sum(rhr_values[:3]) / 3
        earlier = sum(rhr_values[3:]) / (len(rhr_values) - 3)
        rhr_elevated = recent > earlier + 3

    hrv_declining = False
    if len(hrv_values) >= 4:
        mid = len(hrv_values) // 2
        recent_hrv = sum(hrv_values[:mid]) / mid
        earlier_hrv = sum(hrv_values[mid:]) / (len(hrv_values) - mid)
        hrv_declining = recent_hrv < earlier_hrv - 5

    sleep_drop = False
    if len(sleep_scores) >= 4:
        recent_sleep = sum(sleep_scores[:3]) / 3
        earlier_sleep = sum(sleep_scores[3:]) / (len(sleep_scores) - 3)
        sleep_drop = recent_sleep < earlier_sleep - 10

    # 連続高負荷日数
    consecutive = 0
    max_consecutive = 0
    for m in reversed(daily_metrics):
        if m["training_load"] and m["training_load"] > 60:
            consecutive += 1
            max_consecutive = max(max_consecutive, consecutive)
        else:
            consecutive = 0

    total_load = sum(m["training_load"] or 0 for m in daily_metrics)

    # 週別負荷
    week1_load = sum(m["training_load"] or 0 for m in daily_metrics[:7])
    week2_load = sum(m["training_load"] or 0 for m in daily_metrics[7:14])
    acr = round(week2_load / week1_load, 2) if week1_load > 0 else None

    result = _common_header("overtraining", start, today, days)
    result["warning_signals"] = {
        "resting_hr_elevated": rhr_elevated,
        "hrv_declining": hrv_declining,
        "sleep_quality_drop": sleep_drop,
        "consecutive_hard_days": max_consecutive,
        "total_load_14days": round(total_load),
    }
    result["daily_metrics"] = daily_metrics
    result["load_trend"] = {
        "week1_total": round(week1_load),
        "week2_total": round(week2_load),
        "acute_chronic_ratio": acr,
    }
    return result


def _export_peaking(db: Session, days: int, race_date: str | None) -> dict:
    """ピーキング分析"""
    today = date.today()
    start = today - timedelta(days=days)

    activities = _get_activities(db, start, today)
    health_list = _get_health(db, start, today)
    sleep_list = _get_sleep(db, start, today)

    # レース日までの日数
    race_d = date.fromisoformat(race_date) if race_date else None
    days_until = (race_d - today).days if race_d else None

    # 週別距離計算
    weekly_km: dict[int, float] = defaultdict(float)
    for a in activities:
        if a.distance_m and a.start_time:
            week_num = a.start_time.isocalendar()[1]
            weekly_km[week_num] += float(a.distance_m) / 1000

    weeks = sorted(weekly_km.values()) if weekly_km else [0]
    avg_weekly_km = round(sum(weeks) / len(weeks), 1) if weeks else 0
    peak_week_km = round(max(weeks), 1) if weeks else 0

    # ロングラン最大距離
    long_run_max = 0
    for a in activities:
        if a.distance_m:
            d = float(a.distance_m) / 1000
            if d > long_run_max:
                long_run_max = d

    # 週別トレーニングロード
    weekly_load: dict[int, float] = defaultdict(float)
    for a in activities:
        if a.training_load and a.start_time:
            week_num = a.start_time.isocalendar()[1]
            weekly_load[week_num] += float(a.training_load)
    loads = list(weekly_load.values()) if weekly_load else [0]
    avg_load = round(sum(loads) / len(loads)) if loads else 0

    # VO2Maxトレンド
    vo2max_values = [float(a.vo2max) for a in activities if a.vo2max]
    # 直近4つ
    vo2max_trend = vo2max_values[:4] if vo2max_values else []

    # 現在のフィットネス
    rhr = [float(h.resting_hr) for h in health_list if h.resting_hr]
    hrv_statuses = [h.hrv_status for h in health_list if h.hrv_status]
    sleep_scores = [float(s.sleep_score) for s in sleep_list if s.sleep_score]

    result = _common_header("peaking", start, today, days)
    result["race_date"] = race_date
    result["days_until_race"] = days_until
    result["recent_60days"] = {
        "avg_weekly_km": avg_weekly_km,
        "peak_week_km": peak_week_km,
        "long_run_max_km": round(long_run_max, 1),
        "avg_training_load": avg_load,
        "vo2max_trend": vo2max_trend,
    }
    result["current_fitness"] = {
        "resting_hr": round(sum(rhr[:7]) / len(rhr[:7])) if rhr else None,
        "hrv_status": hrv_statuses[0] if hrv_statuses else None,
        "avg_sleep_score": round(sum(sleep_scores[:7]) / len(sleep_scores[:7])) if sleep_scores else None,
    }
    result["activities_60days"] = [_format_activity(a) for a in activities]
    return result


def _export_body_composition(db: Session, days: int) -> dict:
    """体組成トレンド"""
    today = date.today()
    start = today - timedelta(days=days)

    body_list = _get_body(db, start, today)
    activities = _get_activities(db, start, today)

    # 最新値
    latest = None
    if body_list:
        b = body_list[0]
        latest = {
            "date": b.date.isoformat(),
            "weight_kg": _decimal_to_float(b.weight_kg),
            "body_fat_pct": _decimal_to_float(b.body_fat_pct),
            "muscle_mass_kg": _decimal_to_float(b.muscle_mass_kg),
            "bmi": _decimal_to_float(b.bmi),
        }

    # トレンド（最新 - 最古）
    trend = {"weight_change_kg": None, "body_fat_change_pct": None, "muscle_change_kg": None}
    if len(body_list) >= 2:
        newest, oldest = body_list[0], body_list[-1]
        if newest.weight_kg and oldest.weight_kg:
            trend["weight_change_kg"] = round(float(newest.weight_kg) - float(oldest.weight_kg), 1)
        if newest.body_fat_pct and oldest.body_fat_pct:
            trend["body_fat_change_pct"] = round(float(newest.body_fat_pct) - float(oldest.body_fat_pct), 1)
        if newest.muscle_mass_kg and oldest.muscle_mass_kg:
            trend["muscle_change_kg"] = round(float(newest.muscle_mass_kg) - float(oldest.muscle_mass_kg), 1)

    history = []
    for b in body_list:
        history.append({
            "date": b.date.isoformat(),
            "weight_kg": _decimal_to_float(b.weight_kg),
            "body_fat_pct": _decimal_to_float(b.body_fat_pct),
            "muscle_mass_kg": _decimal_to_float(b.muscle_mass_kg),
        })

    # トレーニングコンテキスト
    total_distance = sum(float(a.distance_m or 0) for a in activities)
    total_calories = sum(float(a.calories or 0) for a in activities)
    weeks = max(days / 7, 1)

    result = _common_header("body_composition", start, today, days)
    result["latest"] = latest
    result["trend"] = trend
    result["history"] = history
    result["training_context"] = {
        "avg_weekly_km": round(total_distance / 1000 / weeks, 1),
        "avg_weekly_calories": round(total_calories / weeks),
    }
    return result


def _export_health_overview(db: Session, days: int) -> dict:
    """総合健康分析"""
    today = date.today()
    start = today - timedelta(days=days)

    health_list = _get_health(db, start, today)
    sleep_list = _get_sleep(db, start, today)
    activities = _get_activities(db, start, today)
    body_list = _get_body(db, start, today)

    # バイタルサマリー
    rhr = [float(h.resting_hr) for h in health_list if h.resting_hr]
    hrv = [float(h.hrv_value) for h in health_list if h.hrv_value]
    stress = [float(h.avg_stress) for h in health_list if h.avg_stress]
    spo2 = [float(s.avg_spo2) for s in sleep_list if s.avg_spo2]

    hrv_dist: dict[str, int] = defaultdict(int)
    for h in health_list:
        if h.hrv_status:
            hrv_dist[h.hrv_status.lower()] += 1

    # 睡眠サマリー
    total_h = [float(s.total_sleep_s) / 3600 for s in sleep_list if s.total_sleep_s]
    scores = [float(s.sleep_score) for s in sleep_list if s.sleep_score]
    deep_h = [float(s.deep_sleep_s) / 3600 for s in sleep_list if s.deep_sleep_s]
    rem_h = [float(s.rem_sleep_s) / 3600 for s in sleep_list if s.rem_sleep_s]
    poor_sleep_days = sum(1 for sc in scores if sc < 60)

    # アクティビティサマリー
    steps = [h.steps for h in health_list if h.steps]
    active_kcal = [float(h.active_kcal) for h in health_list if h.active_kcal]
    moderate_min = sum(h.intensity_min_moderate or 0 for h in health_list)
    vigorous_min = sum(h.intensity_min_vigorous or 0 for h in health_list)

    # 体組成最新
    body_latest = None
    if body_list:
        b = body_list[0]
        body_latest = {
            "weight_kg": _decimal_to_float(b.weight_kg),
            "body_fat_pct": _decimal_to_float(b.body_fat_pct),
        }

    # デイリーログ
    health_by_date = {h.date: h for h in health_list}
    sleep_by_date = {s.date: s for s in sleep_list}
    act_by_date: dict[date, list] = defaultdict(list)
    for a in activities:
        if a.start_time:
            act_by_date[a.start_time.date()].append(a)

    daily_log = []
    for i in range(days):
        d = start + timedelta(days=i)
        h = health_by_date.get(d)
        s = sleep_by_date.get(d)
        day_acts = act_by_date.get(d, [])

        activity_desc = None
        if day_acts:
            parts = []
            for a in day_acts:
                sport = a.sport_type or "activity"
                dist = f" {round(float(a.distance_m) / 1000, 1)}km" if a.distance_m else ""
                parts.append(f"{sport}{dist}")
            activity_desc = ", ".join(parts)

        daily_log.append({
            "date": d.isoformat(),
            "steps": h.steps if h else None,
            "resting_hr": _decimal_to_float(h.resting_hr) if h else None,
            "hrv": _decimal_to_float(h.hrv_value) if h else None,
            "stress": _decimal_to_float(h.avg_stress) if h else None,
            "sleep_score": _decimal_to_float(s.sleep_score) if s else None,
            "active_kcal": _decimal_to_float(h.active_kcal) if h else None,
            "activity": activity_desc,
        })

    result = _common_header("health_overview", start, today, days)
    result["vitals_summary"] = {
        "avg_resting_hr": round(sum(rhr) / len(rhr)) if rhr else None,
        "avg_hrv": round(sum(hrv) / len(hrv)) if hrv else None,
        "hrv_status_distribution": dict(hrv_dist),
        "avg_stress": round(sum(stress) / len(stress)) if stress else None,
        "avg_spo2": round(sum(spo2) / len(spo2), 1) if spo2 else None,
    }
    result["sleep_summary"] = {
        "avg_total_h": round(sum(total_h) / len(total_h), 1) if total_h else None,
        "avg_score": round(sum(scores) / len(scores)) if scores else None,
        "avg_deep_h": round(sum(deep_h) / len(deep_h), 1) if deep_h else None,
        "avg_rem_h": round(sum(rem_h) / len(rem_h), 1) if rem_h else None,
        "poor_sleep_days": poor_sleep_days,
    }
    result["activity_summary"] = {
        "avg_daily_steps": round(sum(steps) / len(steps)) if steps else None,
        "avg_active_kcal": round(sum(active_kcal) / len(active_kcal)) if active_kcal else None,
        "intensity_min_moderate": moderate_min,
        "intensity_min_vigorous": vigorous_min,
    }
    result["body_latest"] = body_latest
    result["daily_log"] = daily_log
    return result


def _export_full(db: Session, days: int) -> dict:
    """全データ統合エクスポート"""
    today = date.today()
    start = today - timedelta(days=days)

    result = _common_header("full", start, today, days)

    # トレーニング
    training = _export_training(db, days)
    result["training"] = {
        "summary": training["summary"],
        "activities": training["activities"],
    }

    # 睡眠
    result["sleep"] = _build_sleep_summary(_get_sleep(db, start, today))

    # 健康
    result["health"] = _build_health_summary(_get_health(db, start, today))

    # 体組成
    body_list = _get_body(db, start, today)
    if body_list:
        b = body_list[0]
        result["body_composition"] = {
            "weight_kg": _decimal_to_float(b.weight_kg),
            "body_fat_pct": _decimal_to_float(b.body_fat_pct),
            "muscle_mass_kg": _decimal_to_float(b.muscle_mass_kg),
        }
    else:
        result["body_composition"] = None

    return result


# ── メインディスパッチャ ──

def build_export(db: Session, export_type: str, days: int = 30, race_date: str | None = None) -> dict:
    """エクスポートタイプに応じたJSON構造を生成"""
    if export_type in ("weekly_training", "monthly_training"):
        return _export_training(db, days)
    elif export_type == "sleep_correlation":
        return _export_sleep_correlation(db, days)
    elif export_type == "overtraining":
        return _export_overtraining(db, days)
    elif export_type == "peaking":
        return _export_peaking(db, days, race_date)
    elif export_type == "body_composition":
        return _export_body_composition(db, days)
    elif export_type == "health_overview":
        return _export_health_overview(db, days)
    elif export_type == "full":
        return _export_full(db, days)
    else:
        raise ValueError(f"未対応のエクスポートタイプ: {export_type}")


# ── プロンプトテンプレート ──

PROMPT_TEMPLATES = {
    "weekly_training": """以下は私のGarminトレーニングデータ（過去7日間）です。
コーチとして、以下の観点で分析してください：
1. 今週のトレーニング量・強度の評価
2. 良かった点・改善すべき点
3. 来週に向けた具体的なアドバイス
4. 睡眠・回復状態との関連

[JSONをここに貼り付け]""",

    "monthly_training": """以下は私のGarminトレーニングデータ（過去30日間）です。
コーチとして、以下の観点で分析してください：
1. 今月のトレーニング量・強度の推移と評価
2. 良かった点・改善すべき点
3. 来月に向けた具体的なトレーニング計画の提案
4. 睡眠・回復状態との関連

[JSONをここに貼り付け]""",

    "sleep_correlation": """以下は私の睡眠とトレーニングの相関データ（過去30日間）です。
スポーツ科学者として、以下を分析してください：
1. 睡眠の質がトレーニングパフォーマンスに与える影響
2. トレーニングが睡眠の質に与える影響
3. 最適な睡眠・トレーニングパターンの提案
4. 改善すべき具体的なアクション

[JSONをここに貼り付け]""",

    "overtraining": """以下は私の直近14日間のトレーニング・健康データです。
スポーツ医師として、以下を分析してください：
1. オーバートレーニングの兆候があるか
2. 特に注意すべき指標とその理由
3. 今後1週間の推奨アクション

[JSONをここに貼り付け]""",

    "peaking": """以下は私の直近60日間のトレーニングデータとレース情報です。
マラソンコーチとして、以下を分析してください：
1. 現在のフィットネスレベルの評価
2. レースに向けたピーキング戦略
3. テーパリング期間の具体的な提案
4. レース当日のペース戦略

[JSONをここに貼り付け]""",

    "body_composition": """以下は私の体組成データ（過去90日間）のトレンドです。
栄養士・トレーナーとして、以下を分析してください：
1. 体重・体脂肪率・筋肉量の変化の評価
2. トレーニング量との関連性
3. 栄養面での改善提案
4. 今後の目標設定のアドバイス

[JSONをここに貼り付け]""",

    "health_overview": """以下は私の直近30日間の総合健康データです。
医師・栄養士・トレーナーの視点で以下を分析してください：
1. 全体的な健康状態の評価
2. 睡眠・運動・ストレスの相互関係
3. 改善すべき優先事項（上位3つ）
4. 食事・栄養面へのアドバイス

[JSONをここに貼り付け]""",

    "full": """以下は私の直近30日間の全Garminデータです。
総合的なヘルスコーチとして、以下を分析してください：
1. トレーニング・睡眠・健康・体組成の総合評価
2. 各指標の相互関係
3. 最も改善すべき領域とその具体的なアクション
4. 今後1ヶ月の推奨プラン

[JSONをここに貼り付け]""",
}
