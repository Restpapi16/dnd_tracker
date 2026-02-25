-- Миграция: Добавление поля attacks в таблицу participants
-- Дата: 2026-02-25
-- Описание: Поле attacks хранит информацию об атаках мобов в формате JSON

-- Проверяем, есть ли уже поле (SQLite не поддерживает IF NOT EXISTS для ALTER TABLE)
-- Если поле уже есть, этот запрос выдаст ошибку - это нормально

ALTER TABLE participants ADD COLUMN attacks TEXT;

-- Проверка успешности миграции
SELECT 
    'Migration completed successfully!' as status,
    COUNT(*) as total_participants,
    SUM(CASE WHEN attacks IS NOT NULL THEN 1 ELSE 0 END) as participants_with_attacks
FROM participants;
