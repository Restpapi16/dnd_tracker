# app/schemas_reference.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============ SPELL SCHEMAS ============

class SpellBase(BaseModel):
    name: str
    level: int
    school: Optional[str] = None
    casting_time: Optional[str] = None
    range: Optional[str] = None
    components: Optional[str] = None
    duration: Optional[str] = None
    concentration: bool = False
    ritual: bool = False
    description: Optional[str] = None
    at_higher_levels: Optional[str] = None
    classes: Optional[List[str]] = None


class SpellCreate(SpellBase):
    external_id: int
    slug: str
    source_url: str


class Spell(SpellBase):
    id: int
    external_id: int
    slug: str
    source_url: str
    updated_at: datetime

    class Config:
        from_attributes = True


class SpellSuggestion(BaseModel):
    id: int
    name: str
    level: int
    school: Optional[str] = None
    type: str = "spell"


# ============ ITEM SCHEMAS ============

class ItemBase(BaseModel):
    name: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    cost: Optional[str] = None
    weight: Optional[str] = None
    damage: Optional[str] = None
    ac: Optional[str] = None
    properties: Optional[List[str]] = None
    description: Optional[str] = None


class ItemCreate(ItemBase):
    external_id: int
    slug: str
    source_url: str


class Item(ItemBase):
    id: int
    external_id: int
    slug: str
    source_url: str
    updated_at: datetime

    class Config:
        from_attributes = True


class ItemSuggestion(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    type: str = "item"


# ============ CREATURE SCHEMAS ============

class CreatureBase(BaseModel):
    name: str
    size: Optional[str] = None
    creature_type: Optional[str] = None
    alignment: Optional[str] = None
    ac: Optional[int] = None
    hp: Optional[str] = None
    initiative: Optional[str] = None
    speed: Optional[Dict[str, str]] = None
    strength: Optional[int] = None
    dexterity: Optional[int] = None
    constitution: Optional[int] = None
    intelligence: Optional[int] = None
    wisdom: Optional[int] = None
    charisma: Optional[int] = None
    cr: Optional[str] = None
    xp: Optional[int] = None
    senses: Optional[str] = None
    languages: Optional[str] = None


class CreatureCreate(CreatureBase):
    external_id: int
    slug: str
    source_url: str
    features: Optional[List[Dict[str, Any]]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    legendary_actions: Optional[List[Dict[str, Any]]] = None


class Creature(CreatureBase):
    id: int
    external_id: int
    slug: str
    source_url: str
    features: Optional[List[Dict[str, Any]]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    legendary_actions: Optional[List[Dict[str, Any]]] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class CreatureSuggestion(BaseModel):
    id: int
    name: str
    cr: Optional[str] = None
    creature_type: Optional[str] = None
    type: str = "creature"


# ============ COMBINED SUGGESTIONS ============

class AllSuggestions(BaseModel):
    spells: List[SpellSuggestion]
    items: List[ItemSuggestion]
    creatures: List[CreatureSuggestion]
