# app/schemas.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from enum import Enum


class EncounterStatus(str, Enum):
    draft = "draft"
    active = "active"
    finished = "finished"


class ParticipantType(str, Enum):
    pc = "pc"
    npc_unique = "npc_unique"
    npc_group = "npc_group"


# ----- Атаки -----

class Attack(BaseModel):
    name: str
    hit_bonus: int
    damage_bonus: int
    damage_type: str
    range: str


# ----- Кампании -----

class CampaignBase(BaseModel):
    name: str


class CampaignCreate(CampaignBase):
    pass


class Campaign(CampaignBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True


# ----- Персонажи (игроки кампании) -----

class CharacterBase(BaseModel):
    name: str
    ac: int
    base_initiative: int


class CharacterCreate(CharacterBase):
    campaign_id: int


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    ac: Optional[int] = None
    base_initiative: Optional[int] = None


class Character(CharacterBase):
    id: int
    campaign_id: int

    class Config:
        orm_mode = True


# ----- Участники схватки -----

class ParticipantBase(BaseModel):
    type: ParticipantType
    name: str
    max_hp: Optional[int] = None
    current_hp: Optional[int] = None
    ac: Optional[int] = None
    initiative_total: int
    is_enemy: bool = False
    group_id: Optional[int] = None
    character_id: Optional[int] = None


class ParticipantCreate(ParticipantBase):
    encounter_id: int


class Participant(ParticipantBase):
    id: int

    class Config:
        orm_mode = True


# ----- Состояние Encounter для выдачи наружу -----

class EncounterStateBase(BaseModel):
    encounter_id: int
    campaign_id: int
    status: EncounterStatus
    round: int
    current_index: int

    encounter_name: Optional[str] = None
    campaign_name: str


class EncounterParticipantGM(BaseModel):
    id: int
    type: ParticipantType
    name: str
    is_enemy: bool
    max_hp: Optional[int]
    current_hp: Optional[int]
    ac: Optional[int]
    initiative_total: int
    is_alive: bool
    attacks: Optional[List[Attack]] = None

    class Config:
        orm_mode = True


class EncounterStateGM(EncounterStateBase):
    participants: List[EncounterParticipantGM]


class EncounterParticipantPlayer(BaseModel):
    id: int
    type: ParticipantType
    name: str
    is_enemy: bool
    max_hp: Optional[int]  # для мобов будем делать None
    current_hp: Optional[int]  # для мобов тоже None
    ac: Optional[int]
    initiative_total: int
    is_alive: bool
    attacks: Optional[List[Attack]] = None

    class Config:
        orm_mode = True


class EncounterStatePlayer(EncounterStateBase):
    participants: List[EncounterParticipantPlayer]


class EncounterMyItem(BaseModel):
    id: int
    name: Optional[str] = None
    status: EncounterStatus
    campaign_id: int
    campaign_name: str

    class Config:
        orm_mode = True


class EncounterCreate(BaseModel):
    campaign_id: int
    name: Optional[str] = None


class Encounter(BaseModel):
    id: int
    campaign_id: int
    name: Optional[str] = None
    status: EncounterStatus
    gm_id: int

    class Config:
        orm_mode = True


class PlayerInEncounter(BaseModel):
    character_id: int
    initiative_total: int


class UniqueMonsterInput(BaseModel):
    name: str
    max_hp: int
    ac: int
    initiative_mod: int  # модификатор инициативы, сам бросок сделаем на бэке
    is_enemy: bool = True
    attacks: Optional[List[Attack]] = None


class GroupMonsterInput(BaseModel):
    name: str
    count: int
    max_hp: int
    ac: int
    initiative_mod: int
    is_enemy: bool = True
    attacks: Optional[List[Attack]] = None


class EncounterParticipantsCreate(BaseModel):
    players: List[PlayerInEncounter]
    unique_monsters: List[UniqueMonsterInput] = []
    group_monsters: List[GroupMonsterInput] = []


class EncounterStartRequest(BaseModel):
    as_active: bool = True  # пока просто флаг, можно не менять


class NextTurnRequest(BaseModel):
    # на будущее можно добавить проверку, кто нажал
    pass


class HpChangeRequest(BaseModel):
    delta: int  # отрицательное значение = урон, положительное = хил
