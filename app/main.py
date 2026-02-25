# app/main.py (фрагмент)
from fastapi.staticfiles import StaticFiles
from fastapi import Query
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import engine, Base, get_db
from . import models, schemas, crud
from typing import Optional
from typing import List
from .deps import get_current_tg_user_id
from sqlalchemy.orm import joinedload


Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/health")
def health_check():
    return {"status": "ok"}


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
    role: str = Query("gm", regex="^(gm|player)$"),
    db: Session = Depends(get_db),
    tg_user_id: int = Depends(get_current_tg_user_id),
):
    if role == "gm":
        state: Optional[schemas.EncounterStateGM] = crud.get_encounter_state_for_gm(
            db, encounter_id)
    else:
        state: Optional[schemas.EncounterStatePlayer] = crud.get_encounter_state_for_player(
            db, encounter_id)

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
