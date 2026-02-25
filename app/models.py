# app/models.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy import Text
from .database import Base
import enum
import json


class EncounterStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    finished = "finished"


class ParticipantType(str, enum.Enum):
    pc = "pc"
    npc_unique = "npc_unique"
    npc_group = "npc_group"


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, index=True)

    characters = relationship("Character", back_populates="campaign")
    encounters = relationship("Encounter", back_populates="campaign")


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    name = Column(String, nullable=False)
    ac = Column(Integer, nullable=False)
    base_initiative = Column(Integer, nullable=False)

    campaign = relationship("Campaign", back_populates="characters")


class Encounter(Base):
    __tablename__ = "encounters"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    name = Column(String, nullable=True)
    status = Column(Enum(EncounterStatus), nullable=False,
                    default=EncounterStatus.draft)
    gm_id = Column(Integer, index=True)  # tg id ГМа

    campaign = relationship("Campaign", back_populates="encounters")
    participants = relationship(
        "Participant", back_populates="encounter", cascade="all, delete-orphan"
    )
    state = relationship(
        "EncounterState",
        back_populates="encounter",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
    )


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=False)
    type = Column(Enum(ParticipantType), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=True)

    name = Column(String, nullable=False)
    max_hp = Column(Integer, nullable=True)
    current_hp = Column(Integer, nullable=True)
    ac = Column(Integer, nullable=True)
    initiative_total = Column(Integer, nullable=False)
    group_id = Column(Integer, nullable=True)
    is_enemy = Column(Boolean, nullable=False, default=False)

    encounter = relationship("Encounter", back_populates="participants")


class EncounterState(Base):
    __tablename__ = "encounter_state"

    encounter_id = Column(Integer, ForeignKey(
        "encounters.id"), primary_key=True)
    round = Column(Integer, nullable=False, default=1)
    current_index = Column(Integer, nullable=False, default=0)

    encounter = relationship("Encounter", back_populates="state")
