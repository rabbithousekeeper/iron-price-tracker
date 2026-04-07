"""エクスポートエンドポイント

GET /export/claude?type={type}&days={N} → Claude用JSONエクスポート
GET /export/prompt?type={type}          → 分析依頼プロンプトテンプレート
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.exporters import build_export, PROMPT_TEMPLATES

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/export", tags=["export"])

VALID_TYPES = [
    "weekly_training", "monthly_training", "sleep_correlation",
    "overtraining", "peaking", "body_composition",
    "health_overview", "full",
]


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """API Key認証"""
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")


@router.get("/claude")
def export_claude(
    type: str = Query(..., description="エクスポートタイプ"),
    days: int = Query(30, description="対象日数"),
    race_date: str | None = Query(None, description="レース日（peaking用）"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Claude用JSONエクスポート"""
    if type not in VALID_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"無効なtype: {type}。有効な値: {', '.join(VALID_TYPES)}"
        )

    try:
        result = build_export(db, export_type=type, days=days, race_date=race_date)
        return result
    except Exception as e:
        logger.error(f"エクスポートエラー: {e}")
        raise HTTPException(status_code=500, detail=f"エクスポート生成エラー: {e}")


@router.get("/prompt")
def export_prompt(
    type: str = Query(..., description="プロンプトタイプ"),
    _: str = Depends(verify_api_key),
):
    """Claude分析依頼プロンプトテンプレートを返す"""
    if type not in PROMPT_TEMPLATES:
        raise HTTPException(
            status_code=400,
            detail=f"無効なtype: {type}。有効な値: {', '.join(PROMPT_TEMPLATES.keys())}"
        )

    return {
        "type": type,
        "prompt": PROMPT_TEMPLATES[type],
    }
