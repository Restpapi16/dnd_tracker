# app/routers/reference.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from ..database import get_db
from ..deps import get_current_tg_user_id
from .. import crud_reference, schemas_reference

router = APIRouter(prefix="/reference", tags=["reference"])


# ============ AUTOCOMPLETE / SUGGESTIONS ============

@router.get("/search/suggestions", response_model=schemas_reference.AllSuggestions)
async def get_search_suggestions(
    q: str = Query(..., min_length=2, description="Поисковый запрос"),
    limit: int = Query(5, le=10, description="Количество результатов на каждый тип"),
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    """
    Быстрый поиск для автодополнения.
    Возвращает подсказки по заклинаниям, предметам и существам.
    """
    suggestions = crud_reference.get_all_suggestions(db, q, limit_per_type=limit)
    return suggestions


# ============ SPELLS ============

@router.get("/spells/search", response_model=List[schemas_reference.Spell])
async def search_spells(
    q: str = Query("", description="Поиск по названию"),
    level: Optional[int] = Query(None, ge=0, le=9, description="Уровень заклинания"),
    school: Optional[str] = Query(None, description="Школа магии"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    """Поиск заклинаний с фильтрами"""
    spells = crud_reference.search_spells(db, q, level, school, limit)
    return spells


@router.get("/spells/{spell_id}", response_model=schemas_reference.Spell)
async def get_spell(
    spell_id: int,
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    """Получить полную информацию о заклинании"""
    spell = crud_reference.get_spell_by_id(db, spell_id)
    if not spell:
        raise HTTPException(status_code=404, detail="Заклинание не найдено")
    return spell


# ============ ITEMS ============

@router.get("/items/search", response_model=List[schemas_reference.Item])
async def search_items(
    q: str = Query("", description="Поиск по названию"),
    category: Optional[str] = Query(None, description="Категория предмета"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    """Поиск предметов с фильтрами"""
    items = crud_reference.search_items(db, q, category, limit)
    return items


@router.get("/items/{item_id}", response_model=schemas_reference.Item)
async def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    """Получить полную информацию о предмете"""
    item = crud_reference.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Предмет не найден")
    return item


# ============ CREATURES ============

@router.get("/creatures/search", response_model=List[schemas_reference.Creature])
async def search_creatures(
    q: str = Query("", description="Поиск по названию"),
    cr: Optional[str] = Query(None, description="Показатель опасности"),
    creature_type: Optional[str] = Query(None, description="Тип существа"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    """Поиск существ с фильтрами"""
    creatures = crud_reference.search_creatures(db, q, cr, creature_type, limit)
    return creatures


@router.get("/creatures/{creature_id}", response_model=schemas_reference.Creature)
async def get_creature(
    creature_id: int,
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    """Получить полную информацию о существе"""
    creature = crud_reference.get_creature_by_id(db, creature_id)
    if not creature:
        raise HTTPException(status_code=404, detail="Существо не найдено")
    return creature
