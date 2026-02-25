-- Миграция: Мультиплеер - система доступа к кампаниям
-- Дата: 2026-02-25
-- Описание: Добавление таблиц для управления доступом игроков к кампаниям GM

-- Таблица участников кампании (GM + observers)
CREATE TABLE IF NOT EXISTS campaign_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('gm', 'observer')),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
    UNIQUE(campaign_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_campaign_members_campaign ON campaign_members(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_members_user ON campaign_members(user_id);

-- Таблица инвайт-токенов для присоединения к кампаниям
CREATE TABLE IF NOT EXISTS campaign_invites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL,
    invite_token TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    max_uses INTEGER,
    current_uses INTEGER DEFAULT 0,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_campaign_invites_token ON campaign_invites(invite_token);
CREATE INDEX IF NOT EXISTS idx_campaign_invites_campaign ON campaign_invites(campaign_id);

-- Мигрируем существующих владельцев кампаний в campaign_members как GM
INSERT INTO campaign_members (campaign_id, user_id, role, joined_at)
SELECT id, owner_id, 'gm', CURRENT_TIMESTAMP
FROM campaigns
WHERE owner_id IS NOT NULL
ON CONFLICT(campaign_id, user_id) DO NOTHING;

-- Проверка успешности миграции
SELECT 
    'Migration completed successfully!' as status,
    (SELECT COUNT(*) FROM campaign_members) as total_members,
    (SELECT COUNT(*) FROM campaign_members WHERE role = 'gm') as gm_count,
    (SELECT COUNT(*) FROM campaign_members WHERE role = 'observer') as observer_count,
    (SELECT COUNT(*) FROM campaign_invites) as total_invites;
