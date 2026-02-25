# app/crud.py
from sqlalchemy import asc, desc
from typing import List
from sqlalchemy.orm import Session
from typing import Optional
from . import models, schemas
from sqlalchemy.orm import joinedload
import json

# ----- CAMPAIGNS -----


def get_campaign(db: Session, campaign_id: int):
    return db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()


def get_campaigns(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Campaign).offset(skip).limit(limit).all()


def get_campaigns_for_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Campaign)
        .filter(models.Campaign.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_campaign(db: Session, campaign: schemas.CampaignCreate, owner_id: int):
    db_campaign = models.Campaign(
        name=campaign.name,
        owner_id=owner_id,
    )
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign


# ----- CHARACTERS -----


def create_character(db: Session, character: schemas.CharacterCreate):
    db_character = models.Character(
        campaign_id=character.campaign_id,
        name=character.name,
        ac=character.ac,
        base_initiative=character.base_initiative,
    )
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    return db_character


def get_characters_by_campaign(db: Session, campaign_id: int):
    return (
        db.query(models.Character)
        .filter(models.Character.campaign_id == campaign_id)
        .all()
    )


def get_character(db: Session, character_id: int):
    return (
        db.query(models.Character)
        .filter(models.Character.id == character_id)
        .first()
    )


def update_character(db: Session, character_id: int, character_update: schemas.CharacterUpdate):
    db_character = get_character(db, character_id)
    if not db_character:
        return None

    if character_update.name is not None:
        db_character.name = character_update.name
    if character_update.ac is not None:
        db_character.ac = character_update.ac
    if character_update.base_initiative is not None:
        db_character.base_initiative = character_update.base_initiative

    db.commit()
    db.refresh(db_character)
    return db_character


def delete_character(db: Session, character_id: int):
    db_character = get_character(db, character_id)
    if not db_character:
        return False
    db.delete(db_character)
    db.commit()
    return True


# ----- ENCOUNTERS -----


def create_encounter(db: Session, data: schemas.EncounterCreate, gm_id: int):
    db_encounter = models.Encounter(
        campaign_id=data.campaign_id,
        name=data.name,
        status=models.EncounterStatus.draft,
        gm_id=gm_id,
    )
    db.add(db_encounter)
    db.commit()
    db.refresh(db_encounter)

    # Создаём стартовое состояние
    db_state = models.EncounterState(
        encounter_id=db_encounter.id,
        round=1,
        current_index=0,
    )
    db.add(db_state)
    db.commit()
    db.refresh(db_state)

    return db_encounter


def add_participants_to_encounter(
    db: Session,
    encounter_id: int,
    participants_data: schemas.EncounterParticipantsCreate,
):
    import random

    encounter = db.query(models.Encounter).filter(
        models.Encounter.id == encounter_id).first()
    if not encounter:
        return None

    # 1) Игроки
    for p in participants_data.players:
        db_part = models.Participant(
            encounter_id=encounter_id,
            type=models.ParticipantType.pc,
            character_id=p.character_id,
            name=_get_character_name(db, p.character_id),
            max_hp=None,
            current_hp=None,
            ac=None,
            initiative_total=p.initiative_total,
            is_enemy=False,
            attacks=None,
        )
        db.add(db_part)

    # 2) Уникальные мобы
    for m in participants_data.unique_monsters:
        roll = random.randint(1, 20) + m.initiative_mod
        
        # Сериализуем атаки в JSON, если они есть
        attacks_json = None
        if m.attacks:
            attacks_json = json.dumps([a.dict() for a in m.attacks])
        
        db_part = models.Participant(
            encounter_id=encounter_id,
            type=models.ParticipantType.npc_unique,
            character_id=None,
            name=m.name,
            max_hp=m.max_hp,
            current_hp=m.max_hp,
            ac=m.ac,
            initiative_total=roll,
            is_enemy=m.is_enemy,
            attacks=attacks_json,
        )
        db.add(db_part)

    # 3) Группы мобов
    group_id_counter = _get_next_group_id(db, encounter_id)
    for g in participants_data.group_monsters:
        group_id = group_id_counter
        group_id_counter += 1
        
        # Сериализуем атаки
        attacks_json = None
        if g.attacks:
            attacks_json = json.dumps([a.dict() for a in g.attacks])
        
        for i in range(g.count):
            roll = random.randint(1, 20) + g.initiative_mod
            db_part = models.Participant(
                encounter_id=encounter_id,
                type=models.ParticipantType.npc_group,
                character_id=None,
                name=f"{g.name} #{i+1}",
                max_hp=g.max_hp,
                current_hp=g.max_hp,
                ac=g.ac,
                initiative_total=roll,
                is_enemy=g.is_enemy,
                group_id=group_id,
                attacks=attacks_json,
            )
            db.add(db_part)

    db.commit()
    return encounter


def _get_character_name(db: Session, character_id: int) -> str:
    char = db.query(models.Character).filter(
        models.Character.id == character_id).first()
    return char.name if char else "Unknown"


def _get_next_group_id(db: Session, encounter_id: int) -> int:
    last = (
        db.query(models.Participant)
        .filter(models.Participant.encounter_id == encounter_id)
        .order_by(models.Participant.group_id.desc())
        .first()
    )
    if last and last.group_id:
        return last.group_id + 1
    return 1


# ----- ENCOUNTER LOGIC -----


def start_encounter(db: Session, encounter_id: int):
    encounter = db.query(models.Encounter).filter(
        models.Encounter.id == encounter_id).first()
    if not encounter:
        return None

    # сортируем участников по инициативе (убывание), при равенстве — по id
    participants: List[models.Participant] = (
        db.query(models.Participant)
        .filter(models.Participant.encounter_id == encounter_id)
        .order_by(models.Participant.initiative_total.desc(), models.Participant.id.asc())
        .all()
    )

    if not participants:
        return encounter  # пока просто не трогаем

    # делаем статус active и ставим текущий индекс = 0
    encounter.status = models.EncounterStatus.active

    state = encounter.state
    if state is None:
        state = models.EncounterState(
            encounter_id=encounter.id,
            round=1,
            current_index=0
        )
        db.add(state)
    else:
        state.round = 1
        state.current_index = 0

    db.commit()
    db.refresh(encounter)
    db.refresh(state)
    return encounter


def get_encounter_state_for_gm(db: Session, encounter_id: int) -> Optional[schemas.EncounterStateGM]:
    encounter = (db.query(models.Encounter)
                 .options(joinedload(models.Encounter.campaign))
                 .filter(models.Encounter.id == encounter_id)
                 .first())

    if not encounter:
        return None

    state = encounter.state
    if state is None:
        return None

    participants: List[models.Participant] = (
        db.query(models.Participant)
        .filter(models.Participant.encounter_id == encounter_id)
        .order_by(models.Participant.initiative_total.desc(), models.Participant.id.asc())
        .all()
    )

    items: List[schemas.EncounterParticipantGM] = []
    for p in participants:
        is_alive = p.current_hp is None or (
            p.current_hp is not None and p.current_hp > 0)
        
        # Десериализуем атаки из JSON
        attacks = None
        if p.attacks:
            attacks_data = json.loads(p.attacks)
            attacks = [schemas.Attack(**a) for a in attacks_data]
        
        items.append(
            schemas.EncounterParticipantGM(
                id=p.id,
                type=p.type.value,
                name=p.name,
                is_enemy=p.is_enemy,
                max_hp=p.max_hp,
                current_hp=p.current_hp,
                ac=p.ac,
                initiative_total=p.initiative_total,
                is_alive=is_alive,
                attacks=attacks,
            )
        )

    return schemas.EncounterStateGM(
        encounter_id=encounter.id,
        campaign_id=encounter.campaign_id,
        status=encounter.status.value,
        round=state.round,
        current_index=state.current_index,
        encounter_name=encounter.name,
        campaign_name=encounter.campaign.name,
        participants=items,
    )


def get_encounter_state_for_player(db: Session, encounter_id: int) -> Optional[schemas.EncounterStatePlayer]:
    encounter = (db.query(models.Encounter)
                 .options(joinedload(models.Encounter.campaign))
                 .filter(models.Encounter.id == encounter_id)
                 .first())
    if not encounter:
        return None

    state = encounter.state
    if state is None:
        return None

    participants: List[models.Participant] = (
        db.query(models.Participant)
        .filter(models.Participant.encounter_id == encounter_id)
        .order_by(models.Participant.initiative_total.desc(), models.Participant.id.asc())
        .all()
    )

    items: List[schemas.EncounterParticipantPlayer] = []
    for p in participants:
        is_alive = p.current_hp is None or (
            p.current_hp is not None and p.current_hp > 0)

        # игрокам HP мобов не показываем
        if p.is_enemy:
            max_hp = None
            current_hp = None
        else:
            max_hp = p.max_hp
            current_hp = p.current_hp
        
        # Десериализуем атаки из JSON
        attacks = None
        if p.attacks:
            attacks_data = json.loads(p.attacks)
            attacks = [schemas.Attack(**a) for a in attacks_data]

        items.append(
            schemas.EncounterParticipantPlayer(
                id=p.id,
                type=p.type.value,
                name=p.name,
                is_enemy=p.is_enemy,
                max_hp=max_hp,
                current_hp=current_hp,
                ac=p.ac,
                initiative_total=p.initiative_total,
                is_alive=is_alive,
                attacks=attacks,
            )
        )

    return schemas.EncounterStatePlayer(
        encounter_id=encounter.id,
        campaign_id=encounter.campaign_id,
        status=encounter.status.value,
        round=state.round,
        current_index=state.current_index,
        participants=items,
        encounter_name=encounter.name,
        campaign_name=encounter.campaign.name,
    )


def next_turn(db: Session, encounter_id: int):
    encounter = db.query(models.Encounter).filter(
        models.Encounter.id == encounter_id).first()
    if not encounter or not encounter.state:
        return None

    state = encounter.state

    participants_count = (
        db.query(models.Participant)
        .filter(models.Participant.encounter_id == encounter_id)
        .count()
    )
    if participants_count == 0:
        return encounter

    state.current_index += 1
    if state.current_index >= participants_count:
        state.current_index = 0
        state.round += 1

    db.commit()
    db.refresh(state)
    db.refresh(encounter)
    return encounter


# ----- HP CHANGE / FINISH / DELETE -----


def change_hp(db: Session, participant_id: int, delta: int):
    participant = (
        db.query(models.Participant)
        .filter(models.Participant.id == participant_id)
        .first()
    )
    if not participant:
        return None

    # если у участника нет хп (например, игроки без трекинга) — просто игнорируем
    if participant.current_hp is None:
        return participant

    new_hp = participant.current_hp + delta
    if new_hp < 0:
        new_hp = 0
    if participant.max_hp is not None and new_hp > participant.max_hp:
        new_hp = participant.max_hp

    participant.current_hp = new_hp
    db.commit()
    db.refresh(participant)
    return participant


def finish_encounter(db: Session, encounter_id: int):
    encounter = (
        db.query(models.Encounter)
        .filter(models.Encounter.id == encounter_id)
        .first()
    )
    if not encounter:
        return None

    encounter.status = models.EncounterStatus.finished
    db.commit()
    db.refresh(encounter)
    return encounter


def delete_encounter(db: Session, encounter_id: int):
    encounter = (
        db.query(models.Encounter)
        .filter(models.Encounter.id == encounter_id)
        .first()
    )
    if not encounter:
        return False

    db.delete(encounter)
    db.commit()
    return True
