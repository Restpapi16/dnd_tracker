# app/main_enemies.py - Добавьте эти роуты в app/main.py

from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, crud
from .deps import get_current_tg_user_id
import json


# ----- ENEMIES (LIBRARY) API -----

# @app.post("/campaigns/{campaign_id}/enemies", response_model=schemas.Enemy)
def create_enemy_endpoint(
    campaign_id: int,
    enemy: schemas.EnemyBase,
    db: Session,
    tg_user_id: int,
):
    """Создать врага в библиотеке кампании (GM only)"""
    campaign = crud.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Кампания не найдена")
    
    if campaign.owner_id != tg_user_id:
        raise HTTPException(status_code=403, detail="Только GM может добавлять врагов")
    
    enemy_create = schemas.EnemyCreate(
        campaign_id=campaign_id,
        name=enemy.name,
        max_hp=enemy.max_hp,
        ac=enemy.ac,
        initiative_modifier=enemy.initiative_modifier,
        attacks=enemy.attacks
    )
    
    db_enemy = crud.create_enemy(db, enemy_create)
    
    # Десериализуем атаки для ответа
    attacks = None
    if db_enemy.attacks:
        attacks_data = json.loads(db_enemy.attacks)
        attacks = [schemas.Attack(**a) for a in attacks_data]
    
    return schemas.Enemy(
        id=db_enemy.id,
        campaign_id=db_enemy.campaign_id,
        name=db_enemy.name,
        max_hp=db_enemy.max_hp,
        ac=db_enemy.ac,
        initiative_modifier=db_enemy.initiative_modifier,
        attacks=attacks,
        created_at=db_enemy.created_at
    )


# @app.get("/campaigns/{campaign_id}/enemies", response_model=List[schemas.Enemy])
def list_enemies_endpoint(
    campaign_id: int,
    db: Session,
    tg_user_id: int,
):
    """Получить всех врагов из библиотеки кампании (GM only)"""
    campaign = crud.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Кампания не найдена")
    
    if campaign.owner_id != tg_user_id:
        raise HTTPException(status_code=403, detail="Только GM может просматривать библиотеку")
    
    enemies = crud.get_enemies_by_campaign(db, campaign_id)
    
    result = []
    for e in enemies:
        attacks = None
        if e.attacks:
            attacks_data = json.loads(e.attacks)
            attacks = [schemas.Attack(**a) for a in attacks_data]
        
        result.append(schemas.Enemy(
            id=e.id,
            campaign_id=e.campaign_id,
            name=e.name,
            max_hp=e.max_hp,
            ac=e.ac,
            initiative_modifier=e.initiative_modifier,
            attacks=attacks,
            created_at=e.created_at
        ))
    
    return result


# @app.delete("/campaigns/{campaign_id}/enemies/{enemy_id}")
def delete_enemy_endpoint(
    campaign_id: int,
    enemy_id: int,
    db: Session,
    tg_user_id: int,
):
    """Удалить врага из библиотеки (GM only)"""
    campaign = crud.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Кампания не найдена")
    
    if campaign.owner_id != tg_user_id:
        raise HTTPException(status_code=403, detail="Только GM может удалять врагов")
    
    enemy = crud.get_enemy(db, enemy_id)
    if not enemy or enemy.campaign_id != campaign_id:
        raise HTTPException(status_code=404, detail="Враг не найден")
    
    success = crud.delete_enemy(db, enemy_id)
    if not success:
        raise HTTPException(status_code=400, detail="Не удалось удалить")
    
    return {"status": "deleted"}