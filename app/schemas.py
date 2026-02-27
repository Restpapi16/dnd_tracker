# app/schemas.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from enum import Enum
from datetime import datetime


class EncounterStatus(str, Enum):
    draft = "draft"
    active = "active"
    finished = "finished"


class ParticipantType(str, Enum):
    pc = "pc"
    npc_unique = "npc_unique"
    npc_group = "npc_group"


class MemberRole(str, Enum):
    gm = "gm"
    observer = "observer"


# ----- Атаки -----

class Attack(BaseModel):
    name: str
    hit_bonus: int
    damage_dice: int      # количество костей (например, 2 в 2d6)
    damage_die: int       # размер кости (например, 6 в 2d6)
    damage_bonus: int     # бонус к урону (например, +3)
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


class CampaignWithRole(Campaign):
    """Campaign with user's role (for observer view)"""
    user_role: MemberRole


# ----- Campaign Members -----

class CampaignMember(BaseModel):
    id: int
    campaign_id: int
    user_id: int
    role: MemberRole
    joined_at: datetime

    class Config:
        orm_mode = True


class CampaignMemberInfo(BaseModel):
    """Simplified member info for display"""
    user_id: int
    role: MemberRole
    joined_at: datetime


# ----- Campaign Invites -----

class CampaignInvite(BaseModel):
    id: int
    campaign_id: int
    invite_token: str
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    max_uses: Optional[int]
    current_uses: int

    class Config:
        orm_mode = True


class InviteGenerateResponse(BaseModel):
    invite_token: str
    invite_url: str
    expires_at: Optional[datetime]


class InviteJoinRequest(BaseModel):
    invite_token: str


# ----- НОВОЕ: Библиотека врагов -----

class EnemyBase(BaseModel):
    name: str
    max_hp: int
    ac: int
    initiative_modifier: int = 0
    attacks: Optional[List[Attack]] = None


class EnemyCreate(EnemyBase):
    campaign_id: int


class Enemy(EnemyBase):
    id: int
    campaign_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class EnemyUpdate(BaseModel):
    name: Optional[str] = None
    max_hp: Optional[int] = None
    ac: Optional[int] = None
    initiative_modifier: Optional[int] = None
    attacks: Optional[List[Attack]] = None


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


# Observer view - минимальная информация + HP для визуальных эффектов
class EncounterParticipantObserver(BaseModel):
    id: int
    type: ParticipantType
    name: str
    is_enemy: bool
    initiative_total: int
    is_alive: bool
    # HP добавлены для визуальных эффектов (трещины), но не показываем числа в UI
    current_hp: Optional[int] = None
    max_hp: Optional[int] = None
    # AC, attacks - скрыты

    class Config:
        orm_mode = True


class EncounterStateObserver(EncounterStateBase):
    participants: List[EncounterParticipantObserver]


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


# ----- НОВОЕ: схема для добавления участников в активную схватку -----

class AddParticipantsFromLibrary(BaseModel):
    """Добавление врагов из библиотеки"""
    enemy_id: int
    count: int = 1


class AddParticipantsToActiveEncounter(BaseModel):
    """Схема для добавления новых участников во время боя"""
    from_library: List[AddParticipantsFromLibrary] = []
    unique_monsters: List[UniqueMonsterInput] = []
    group_monsters: List[GroupMonsterInput] = []


class EncounterStartRequest(BaseModel):
    as_active: bool = True  # пока просто флаг, можно не менять


class NextTurnRequest(BaseModel):
    # на будущее можно добавить проверку, кто нажал
    pass


class HpChangeRequest(BaseModel):
    delta: int  # отрицательное значение = урон, положительное = хил
