# app/main.py (фрагмент)
from fastapi.staticfiles import StaticFiles
from fastapi import Query
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import engine, Base, get_db
from . import models, schemas, crud
from . import crud_multiplayer
from typing import Optional
from typing import List
from .deps import get_current_tg_user_id
from sqlalchemy.orm import joinedload


Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ----- USER INFO API -----

@app.get("/me/stats")
def get_my_stats(
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    """Получить статистику пользователя: количество GM-кампаний и Observer-кампаний"""
    # GM-кампании (где я владелец)
    gm_campaigns = db.query(models.Campaign).filter(
        models.Campaign.owner_id == tg_user_id
    ).count()
    
    # Observer-кампании (где я observer)
    observer_campaigns = db.query(models.CampaignMember).filter(
        models.CampaignMember.user_id == tg_user_id,
        models.CampaignMember.role == models.MemberRole.observer
    ).count()
    
    return {
        "gm_campaigns_count": gm_campaigns,
        "observer_campaigns_count": observer_campaigns
    }


# ----- CAMPAIGNS API -----

@app.post("/campaigns", response_model=schemas.Campaign)
def create_campaign(
    campaign: schemas.CampaignCreate,
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    return crud.create_campaign(db, campaign=campaign, owner_id=tg_user_id)


@app.get("/campaigns", response_model=List[schemas.Campaign])
def list_campaigns(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    campaigns = crud.get_campaigns_for_owner(
        db, owner_id=tg_user_id, skip=skip, limit=limit)
    return campaigns


@app.get("/campaigns/{campaign_id}", response_model=schemas.Campaign)
def read_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    db_campaign = crud.get_campaign(db, campaign_id=campaign_id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Кампании не найдены")
    return db_campaign


# ----- MULTIPLAYER: CAMPAIGNS API -----

@app.get("/campaigns/observer/my", response_model=List[schemas.Campaign])
def list_observer_campaigns(
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    """Получить список кампаний, где я observer"""
    campaigns = crud_multiplayer.get_campaigns_for_observer(db, tg_user_id)
    return campaigns


@app.post("/campaigns/{campaign_id}/invite")
def generate_campaign_invite(
    campaign_id: int,
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    """Сгенерировать инвайт-ссылку для кампании (GM only)"""
    # Проверка: является ли пользователь GM
    if not crud_multiplayer.is_campaign_gm(db, campaign_id, tg_user_id):
        raise HTTPException(status_code=403, detail="Только GM может создавать приглашения")
    
    # Создаём инвайт (бессрочный, без лимита)
    invite = crud_multiplayer.create_campaign_invite(db, campaign_id)
    
    bot_username = "d20_bot"
    invite_url = f"https://t.me/{bot_username}?start=invite_{invite.invite_token}"
    
    return schemas.InviteGenerateResponse(
        invite_token=invite.invite_token,
        invite_url=invite_url,
        expires_at=invite.expires_at
    )


@app.get("/campaigns/invite/{token}")
def check_campaign_invite(
    token: str,
    db: Session = Depends(get_db),
):
    """Проверить валидность инвайт-токена и получить информацию о кампании"""
    invite = crud_multiplayer.get_invite_by_token(db, token)
    
    if not invite:
        raise HTTPException(status_code=404, detail="Инвайт не найден")
    
    # Проверяем валидность
    is_valid, error = crud_multiplayer.validate_invite(invite)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Получаем кампанию
    campaign = db.query(models.Campaign).filter(
        models.Campaign.id == invite.campaign_id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Кампания не найдена")
    
    return {
        "campaign_id": campaign.id,
        "campaign_name": campaign.name,
        "valid": True
    }


@app.post("/campaigns/join")
def join_campaign(
    request: schemas.InviteJoinRequest,
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    """Присоединиться к кампании по инвайт-токену"""
    campaign, error = crud_multiplayer.join_campaign_by_invite(
        db, request.invite_token, tg_user_id
    )
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return {
        "status": "success",
        "campaign_id": campaign.id,
        "campaign_name": campaign.name
    }


@app.get("/campaigns/{campaign_id}/members", response_model=List[schemas.CampaignMemberInfo])
def get_campaign_members_list(
    campaign_id: int,
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    """Получить список участников кампании (GM only)"""
    if not crud_multiplayer.is_campaign_gm(db, campaign_id, tg_user_id):
        raise HTTPException(status_code=403, detail="Только GM может просматривать список участников")
    
    members = crud_multiplayer.get_campaign_members(db, campaign_id)
    return [
        schemas.CampaignMemberInfo(
            user_id=m.user_id,
            role=m.role,
            joined_at=m.joined_at
        )
        for m in members
    ]


@app.delete("/campaigns/{campaign_id}/members/{user_id}")
def remove_member(
    campaign_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    """Удалить участника из кампании (GM only)"""
    if not crud_multiplayer.is_campaign_gm(db, campaign_id, tg_user_id):
        raise HTTPException(status_code=403, detail="Только GM может удалять участников")
    
    success = crud_multiplayer.remove_campaign_member(db, campaign_id, user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Не удалось удалить участника")
    
    return {"status": "deleted"}


# ----- CHARACTERS API -----


@app.post("/characters", response_model=schemas.Character)
def create_character(
    character: schemas.CharacterCreate,
    db: Session = Depends(get_db),
):
    # опционально можно проверить, что кампания существует
    campaign = crud.get_campaign(db, character.campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Кампании не найдены")

    db_character = crud.create_character(db, character=character)
    return db_character


@app.get("/campaigns/{campaign_id}/characters", response_model=List[schemas.Character])
def list_characters_for_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
):
    campaign = crud.get_campaign(db, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Кампании не найдены")

    characters = crud.get_characters_by_campaign(db, campaign_id=campaign_id)
    return characters


@app.put("/characters/{character_id}", response_model=schemas.Character)
def update_character(
    character_id: int,
    character_update: schemas.CharacterUpdate,
    db: Session = Depends(get_db),
):
    db_character = crud.update_character(db, character_id, character_update)
    if db_character is None:
        raise HTTPException(status_code=404, detail="Персонажи не найдены")
    return db_character


@app.delete("/characters/{character_id}")
def delete_character(
    character_id: int,
    db: Session = Depends(get_db),
):
    ok = crud.delete_character(db, character_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Персонажи не найдены")
    return {"status": "deleted"}


# ----- ENCOUNTERS API -----


@app.post("/encounters", response_model=schemas.Encounter)
def create_encounter(
    data: schemas.EncounterCreate,
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    campaign = crud.get_campaign(db, data.campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Кампании не найдены")

    # запрет создавать encounter в чужой кампании
    if campaign.owner_id != tg_user_id:
        raise HTTPException(status_code=403, detail="Нет доступа")

    encounter = crud.create_encounter(db, data, gm_id=tg_user_id)
    return encounter


@app.post("/encounters/{encounter_id}/participants")
def add_participants(
    encounter_id: int,
    participants_data: schemas.EncounterParticipantsCreate,
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    encounter = crud.add_participants_to_encounter(
        db, encounter_id, participants_data)
    if encounter is None:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return {"status": "ok"}


# ----- НОВОЕ: Добавление участников в активную схватку -----

@app.post("/encounters/{encounter_id}/add_participants")
def add_participants_to_active(
    encounter_id: int,
    participants_data: schemas.AddParticipantsToActiveEncounter,
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    """
    Добавить новых участников в активную схватку (во время боя).
    Новые участники автоматически получают инициативу и встают в порядок ходов.
    """
    encounter = crud.add_participants_to_active_encounter(
        db, encounter_id, participants_data
    )
    if encounter is None:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return {"status": "ok", "message": "Участники добавлены"}


# ----- ENCOUNTERS CONTROL API -----


@app.post("/encounters/{encounter_id}/start")
def start_encounter(
    encounter_id: int,
    data: Optional[schemas.EncounterStartRequest] = None,
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    encounter = crud.start_encounter(db, encounter_id)
    if encounter is None:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return {"status": "started", "encounter_id": encounter_id}


@app.get("/encounters/{encounter_id}/state")
def get_encounter_state(
    encounter_id: int,
    role: str = Query("gm", regex="^(gm|player|observer)$"),
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    """Получить состояние схватки с учётом роли пользователя"""
    if role == "gm":
        state = crud.get_encounter_state_for_gm(db, encounter_id)
    elif role == "observer":
        state = crud_multiplayer.get_encounter_state_for_observer(db, encounter_id)
    else:
        state = crud.get_encounter_state_for_player(db, encounter_id)

    if state is None:
        raise HTTPException(
            status_code=404, detail="Encounter state not found")

    return state


@app.post("/encounters/{encounter_id}/next_turn")
def encounter_next_turn(
    encounter_id: int,
    data: Optional[schemas.NextTurnRequest] = None,
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    encounter = crud.next_turn(db, encounter_id)
    if encounter is None:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return {"status": "ok", "encounter_id": encounter_id}


@app.get("/encounters/my", response_model=List[schemas.EncounterMyItem])
def my_encounters(db: Session = Depends(get_db),
                  user_id: int = Depends(get_current_tg_user_id)):
    encs = (db.query(models.Encounter)
              .options(joinedload(models.Encounter.campaign))
              .filter(models.Encounter.gm_id == user_id)
              .filter(models.Encounter.status.in_([models.EncounterStatus.draft, models.EncounterStatus.active]))
              .order_by(models.Encounter.id.desc())
              .all())

    return [{
        "id": e.id,
        "name": e.name,
        "status": e.status,
        "campaign_id": e.campaign_id,
        "campaign_name": e.campaign.name
    } for e in encs]


# ----- MULTIPLAYER: OBSERVER ENCOUNTERS -----

@app.get("/campaigns/{campaign_id}/encounters/active")
def get_active_encounters(
    campaign_id: int,
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    """Получить активные схватки кампании (observers могут смотреть)"""
    # Проверяем доступ
    if not crud_multiplayer.has_campaign_access(db, campaign_id, tg_user_id):
        raise HTTPException(status_code=403, detail="Нет доступа")
    
    encounters = crud_multiplayer.get_active_encounters_for_campaign(db, campaign_id)
    
    return [{
        "id": e.id,
        "name": e.name,
        "status": e.status.value,
        "campaign_id": e.campaign_id
    } for e in encounters]


# ----- HP CHANGE / FINISH / DELETE API -----


@app.post("/participants/{participant_id}/hp_change")
def participant_hp_change(
    participant_id: int,
    data: schemas.HpChangeRequest,
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    participant = crud.change_hp(db, participant_id, data.delta)
    if participant is None:
        raise HTTPException(status_code=404, detail="Participant not found")
    return {"status": "ok", "participant_id": participant_id, "current_hp": participant.current_hp}


@app.post("/encounters/{encounter_id}/finish")
def encounter_finish(
    encounter_id: int,
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    encounter = crud.finish_encounter(db, encounter_id)
    if encounter is None:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return {"status": "finished", "encounter_id": encounter_id}


@app.delete("/encounters/{encounter_id}")
def encounter_delete(
    encounter_id: int,
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    ok = crud.delete_encounter(db, encounter_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return {"status": "deleted"}


app.mount("/static", StaticFiles(directory="static"), name="static")