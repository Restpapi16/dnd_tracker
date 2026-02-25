# app/crud_multiplayer.py
# CRUD операции для мультиплеерной системы доступа

from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from datetime import datetime, timedelta
import secrets
import json
from . import models, schemas


# ----- CAMPAIGN MEMBERS -----

def get_user_role_in_campaign(db: Session, campaign_id: int, user_id: int) -> Optional[models.MemberRole]:
    """Получить роль пользователя в кампании"""
    member = db.query(models.CampaignMember).filter(
        models.CampaignMember.campaign_id == campaign_id,
        models.CampaignMember.user_id == user_id
    ).first()
    
    return member.role if member else None


def is_campaign_gm(db: Session, campaign_id: int, user_id: int) -> bool:
    """Проверить, является ли пользователь GM кампании"""
    role = get_user_role_in_campaign(db, campaign_id, user_id)
    return role == models.MemberRole.gm


def has_campaign_access(db: Session, campaign_id: int, user_id: int) -> bool:
    """Проверить, имеет ли пользователь доступ к кампании (GM или observer)"""
    role = get_user_role_in_campaign(db, campaign_id, user_id)
    return role is not None


def get_campaign_members(db: Session, campaign_id: int) -> List[models.CampaignMember]:
    """Получить всех участников кампании"""
    return db.query(models.CampaignMember).filter(
        models.CampaignMember.campaign_id == campaign_id
    ).all()


def remove_campaign_member(db: Session, campaign_id: int, user_id: int) -> bool:
    """Удалить участника из кампании"""
    member = db.query(models.CampaignMember).filter(
        models.CampaignMember.campaign_id == campaign_id,
        models.CampaignMember.user_id == user_id
    ).first()
    
    if not member:
        return False
    
    # Нельзя удалить GM
    if member.role == models.MemberRole.gm:
        return False
    
    db.delete(member)
    db.commit()
    return True


def get_campaigns_for_observer(db: Session, user_id: int) -> List[models.Campaign]:
    """Получить список кампаний, где пользователь является observer"""
    campaigns = db.query(models.Campaign).join(
        models.CampaignMember
    ).filter(
        models.CampaignMember.user_id == user_id,
        models.CampaignMember.role == models.MemberRole.observer
    ).all()
    
    return campaigns


# ----- CAMPAIGN INVITES -----

def generate_invite_token() -> str:
    """Генерировать уникальный токен приглашения"""
    return secrets.token_urlsafe(16)


def create_campaign_invite(
    db: Session,
    campaign_id: int,
    expires_in_days: Optional[int] = None,
    max_uses: Optional[int] = None
) -> models.CampaignInvite:
    """Создать инвайт-токен для кампании"""
    token = generate_invite_token()
    
    expires_at = None
    if expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
    
    invite = models.CampaignInvite(
        campaign_id=campaign_id,
        invite_token=token,
        expires_at=expires_at,
        is_active=True,
        max_uses=max_uses,
        current_uses=0
    )
    
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


def get_invite_by_token(db: Session, token: str) -> Optional[models.CampaignInvite]:
    """Получить инвайт по токену"""
    return db.query(models.CampaignInvite).filter(
        models.CampaignInvite.invite_token == token
    ).first()


def validate_invite(invite: models.CampaignInvite) -> tuple[bool, Optional[str]]:
    """Проверить валидность инвайта. Возвращает (is_valid, error_message)"""
    if not invite.is_active:
        return False, "Приглашение деактивировано"
    
    if invite.expires_at and invite.expires_at < datetime.utcnow():
        return False, "Срок действия приглашения истёк"
    
    if invite.max_uses and invite.current_uses >= invite.max_uses:
        return False, "Достигнут лимит использований приглашения"
    
    return True, None


def join_campaign_by_invite(
    db: Session,
    invite_token: str,
    user_id: int
) -> tuple[Optional[models.Campaign], Optional[str]]:
    """Присоединиться к кампании по инвайт-токену. Возвращает (campaign, error)"""
    invite = get_invite_by_token(db, invite_token)
    
    if not invite:
        return None, "Неверный токен приглашения"
    
    # Проверяем валидность
    is_valid, error = validate_invite(invite)
    if not is_valid:
        return None, error
    
    campaign_id = invite.campaign_id
    
    # Проверяем, не является ли пользователь уже участником
    existing = db.query(models.CampaignMember).filter(
        models.CampaignMember.campaign_id == campaign_id,
        models.CampaignMember.user_id == user_id
    ).first()
    
    if existing:
        # Уже участник - просто возвращаем кампанию
        campaign = db.query(models.Campaign).filter(
            models.Campaign.id == campaign_id
        ).first()
        return campaign, None
    
    # Добавляем как observer
    member = models.CampaignMember(
        campaign_id=campaign_id,
        user_id=user_id,
        role=models.MemberRole.observer
    )
    db.add(member)
    
    # Увеличиваем счётчик использований
    invite.current_uses += 1
    
    db.commit()
    db.refresh(member)
    
    campaign = db.query(models.Campaign).filter(
        models.Campaign.id == campaign_id
    ).first()
    
    return campaign, None


def deactivate_invite(db: Session, invite_id: int) -> bool:
    """Деактивировать инвайт"""
    invite = db.query(models.CampaignInvite).filter(
        models.CampaignInvite.id == invite_id
    ).first()
    
    if not invite:
        return False
    
    invite.is_active = False
    db.commit()
    return True


def get_campaign_invites(db: Session, campaign_id: int) -> List[models.CampaignInvite]:
    """Получить все инвайты кампании"""
    return db.query(models.CampaignInvite).filter(
        models.CampaignInvite.campaign_id == campaign_id
    ).order_by(models.CampaignInvite.created_at.desc()).all()


# ----- ENCOUNTER STATE FOR OBSERVER -----

def get_encounter_state_for_observer(
    db: Session,
    encounter_id: int
) -> Optional[schemas.EncounterStateObserver]:
    """Получить состояние схватки для observer (минимальная информация + HP для эффектов)"""
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
    
    items: List[schemas.EncounterParticipantObserver] = []
    for p in participants:
        is_alive = p.current_hp is None or (
            p.current_hp is not None and p.current_hp > 0)
        
        # Для observer передаём HP для визуальных эффектов (трещины)
        # но не показываем числа в UI
        items.append(
            schemas.EncounterParticipantObserver(
                id=p.id,
                type=p.type.value,
                name=p.name,
                is_enemy=p.is_enemy,
                initiative_total=p.initiative_total,
                is_alive=is_alive,
                current_hp=p.current_hp,  # Добавлено для трещин
                max_hp=p.max_hp,          # Добавлено для трещин
            )
        )
    
    return schemas.EncounterStateObserver(
        encounter_id=encounter.id,
        campaign_id=encounter.campaign_id,
        status=encounter.status.value,
        round=state.round,
        current_index=state.current_index,
        encounter_name=encounter.name,
        campaign_name=encounter.campaign.name,
        participants=items,
    )


def get_active_encounters_for_campaign(
    db: Session,
    campaign_id: int
) -> List[models.Encounter]:
    """Получить активные схватки кампании"""
    return db.query(models.Encounter).filter(
        models.Encounter.campaign_id == campaign_id,
        models.Encounter.status == models.EncounterStatus.active
    ).all()
