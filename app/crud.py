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
    
    # Автоматически добавляем владельца как GM в campaign_members
    db_member = models.CampaignMember(
        campaign_id=db_campaign.id,
        user_id=owner_id,
        role=models.MemberRole.gm
    )
    db.add(db_member)
    db.commit()
    
    return db_campaign


# ----- ENEMY TEMPLATES FROM PAST ENCOUNTERS -----

def get_enemy_templates_from_past_encounters(db: Session, campaign_id: int):
    """
    Получить уникальных врагов из прошлых схваток кампании.
    Возвращает только npc_unique и npc_group (по одному на группу).
    """
    subquery = (
        db.query(models.Participant.name, models.Participant.id)
        .join(models.Encounter)
        .filter(models.Encounter.campaign_id == campaign_id)
        .filter(models.Participant.is_enemy == True)
        .filter(
            (models.Participant.type == models.ParticipantType.npc_unique) |
            (models.Participant.type == models.ParticipantType.npc_group)
        )
        .order_by(models.Participant.name, models.Participant.id.desc())
        .distinct(models.Participant.name)
        .subquery()
    )
    
    return (
        db.query(models.Participant)
        .filter(models.Participant.id.in_(db.query(subquery.c.id)))
        .all()
    )


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
            count=1,
            hp_array=None,
        )
        db.add(db_part)

    # 2) Уникальные мобы
    for m in participants_data.unique_monsters:
        roll = random.randint(1, 20) + m.initiative_mod
        
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
            count=1,
            hp_array=None,
        )
        db.add(db_part)

    # 3) Группы мобов - теперь ОДНА ЗАПИСЬ с count и hp_array
    for g in participants_data.group_monsters:
        roll = random.randint(1, 20) + g.initiative_mod
        
        attacks_json = None
        if g.attacks:
            attacks_json = json.dumps([a.dict() for a in g.attacks])
        
        # Создаём массив HP для каждого существа в группе
        hp_array = [g.max_hp] * g.count
        
        db_part = models.Participant(
            encounter_id=encounter_id,
            type=models.ParticipantType.npc_group,
            character_id=None,
            name=g.name,
            max_hp=g.max_hp,
            current_hp=None,  # Не используется для групп
            ac=g.ac,
            initiative_total=roll,
            is_enemy=g.is_enemy,
            count=g.count,
            hp_array=json.dumps(hp_array),
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
    """Deprecated - больше не нужно"""
    last = (
        db.query(models.Participant)
        .filter(models.Participant.encounter_id == encounter_id)
        .order_by(models.Participant.group_id.desc())
        .first()
    )
    if last and last.group_id:
        return last.group_id + 1
    return 1


# ----- НОВОЕ: Добавление участников в активную схватку -----

def add_participants_to_active_encounter(
    db: Session,
    encounter_id: int,
    participants_data: schemas.AddParticipantsToActiveEncounter,
):
    """
    Добавляет новых участников в активную схватку.
    Новые участники вставляются в порядок ходов согласно инициативе.
    """
    import random

    encounter = db.query(models.Encounter).filter(
        models.Encounter.id == encounter_id).first()
    if not encounter:
        return None

    state = encounter.state
    if not state:
        return None

    # 1) Из прошлых схваток (шаблоны)
    for template_data in participants_data.from_library:
        template = db.query(models.Participant).filter(
            models.Participant.id == template_data.enemy_id
        ).first()
        if not template:
            continue
        
        roll = random.randint(1, 20) + (template.initiative_total - 10)  # Примерная оценка модификатора
        
        if template_data.count == 1:
            # Уникальный
            db_part = models.Participant(
                encounter_id=encounter_id,
                type=models.ParticipantType.npc_unique,
                character_id=None,
                name=template.name,
                max_hp=template.max_hp,
                current_hp=template.max_hp,
                ac=template.ac,
                initiative_total=roll,
                is_enemy=True,
                attacks=template.attacks,
                count=1,
                hp_array=None,
            )
            db.add(db_part)
        else:
            # Группа
            hp_array = [template.max_hp] * template_data.count
            db_part = models.Participant(
                encounter_id=encounter_id,
                type=models.ParticipantType.npc_group,
                character_id=None,
                name=template.name,
                max_hp=template.max_hp,
                current_hp=None,
                ac=template.ac,
                initiative_total=roll,
                is_enemy=True,
                count=template_data.count,
                hp_array=json.dumps(hp_array),
                attacks=template.attacks,
            )
            db.add(db_part)

    # 2) Уникальные мобы
    for m in participants_data.unique_monsters:
        roll = random.randint(1, 20) + m.initiative_mod
        
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
            count=1,
            hp_array=None,
        )
        db.add(db_part)

    # 3) Группы мобов
    for g in participants_data.group_monsters:
        roll = random.randint(1, 20) + g.initiative_mod
        
        attacks_json = None
        if g.attacks:
            attacks_json = json.dumps([a.dict() for a in g.attacks])
        
        hp_array = [g.max_hp] * g.count
        
        db_part = models.Participant(
            encounter_id=encounter_id,
            type=models.ParticipantType.npc_group,
            character_id=None,
            name=g.name,
            max_hp=g.max_hp,
            current_hp=None,
            ac=g.ac,
            initiative_total=roll,
            is_enemy=g.is_enemy,
            count=g.count,
            hp_array=json.dumps(hp_array),
            attacks=attacks_json,
        )
        db.add(db_part)

    db.commit()
    db.refresh(encounter)
    return encounter


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
        return encounter

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
        # Для групп: разворачиваем в отдельные экземпляры
        if p.type == models.ParticipantType.npc_group and p.count > 1:
            hp_list = json.loads(p.hp_array) if p.hp_array else [p.max_hp] * p.count
            attacks = None
            if p.attacks:
                attacks_data = json.loads(p.attacks)
                attacks = [schemas.Attack(**a) for a in attacks_data]
            
            for i in range(p.count):
                current_hp = hp_list[i] if i < len(hp_list) else p.max_hp
                is_alive = current_hp > 0
                
                items.append(
                    schemas.EncounterParticipantGM(
                        id=p.id * 1000 + i,  # Виртуальный ID для фронта
                        type=p.type.value,
                        name=f"{p.name} #{i+1}",
                        is_enemy=p.is_enemy,
                        max_hp=p.max_hp,
                        current_hp=current_hp,
                        ac=p.ac,
                        initiative_total=p.initiative_total,
                        is_alive=is_alive,
                        attacks=attacks,
                        group_participant_id=p.id,  # Реальный ID записи
                        group_index=i,  # Индекс в группе
                    )
                )
        else:
            # Уникальные и игроки
            is_alive = p.current_hp is None or (p.current_hp is not None and p.current_hp > 0)
            
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
        # Для групп: разворачиваем
        if p.type == models.ParticipantType.npc_group and p.count > 1:
            hp_list = json.loads(p.hp_array) if p.hp_array else [p.max_hp] * p.count
            attacks = None
            if p.attacks:
                attacks_data = json.loads(p.attacks)
                attacks = [schemas.Attack(**a) for a in attacks_data]
            
            for i in range(p.count):
                current_hp = hp_list[i] if i < len(hp_list) else p.max_hp
                is_alive = current_hp > 0
                
                # Игрокам HP мобов не показываем
                if p.is_enemy:
                    max_hp = None
                    current_hp = None
                
                items.append(
                    schemas.EncounterParticipantPlayer(
                        id=p.id * 1000 + i,
                        type=p.type.value,
                        name=f"{p.name} #{i+1}",
                        is_enemy=p.is_enemy,
                        max_hp=max_hp if not p.is_enemy else None,
                        current_hp=current_hp if not p.is_enemy else None,
                        ac=p.ac,
                        initiative_total=p.initiative_total,
                        is_alive=is_alive,
                        attacks=attacks,
                    )
                )
        else:
            is_alive = p.current_hp is None or (p.current_hp is not None and p.current_hp > 0)

            # Игрокам HP мобов не показываем
            if p.is_enemy:
                max_hp = None
                current_hp = None
            else:
                max_hp = p.max_hp
                current_hp = p.current_hp
            
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


def change_hp(db: Session, participant_id: int, delta: int, group_index: int = None):
    """
    Изменить HP участника.
    Для групп: group_index указывает на конкретное существо в группе.
    """
    participant = (
        db.query(models.Participant)
        .filter(models.Participant.id == participant_id)
        .first()
    )
    if not participant:
        return None

    # Группа
    if participant.type == models.ParticipantType.npc_group and participant.count > 1:
        if group_index is None:
            return participant  # Не можем изменить HP без индекса
        
        hp_list = json.loads(participant.hp_array) if participant.hp_array else [participant.max_hp] * participant.count
        
        if group_index < 0 or group_index >= len(hp_list):
            return participant
        
        new_hp = hp_list[group_index] + delta
        if new_hp < 0:
            new_hp = 0
        if participant.max_hp is not None and new_hp > participant.max_hp:
            new_hp = participant.max_hp
        
        hp_list[group_index] = new_hp
        participant.hp_array = json.dumps(hp_list)
    else:
        # Уникальный или игрок
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
