# Инструкции по интеграции функционала атак

## Шаг 1: Подключить JavaScript модуль

В `static/campaigns.html` добавьте перед закрывающим тегом `</body>`:

```html
<script src="/static/attacks_addon.js"></script>
```

## Шаг 2: Обновить функцию addUniqueBtn.onclick

Найдите в campaigns.html строку:
```javascript
addUniqueBtn.onclick = () => {
```

И замените весь блок на:

```javascript
addUniqueBtn.onclick = () => {
    const name = uniqueNameInput.value.trim();
    const hp = parseInt(uniqueHPInput.value, 10);
    const ac = parseInt(uniqueACInput.value, 10);
    const initMod = parseInt(uniqueInitModInput.value, 10);

    if (!name || isNaN(hp) || isNaN(ac) || isNaN(initMod)) {
        showToast("Заполните имя, ХП, КД и мод ИНИЦ уникального моба");
        return;
    }

    // Получаем атаки из модуля
    const attacks = getAttacksForMonster();

    setupUniqueMonsters.push({
        name,
        max_hp: hp,
        ac,
        initiative_mod: initMod,
        is_enemy: true,
        attacks: attacks  // Добавляем атаки
    });

    uniqueNameInput.value = "";
    uniqueHPInput.value = "";
    uniqueACInput.value = "";
    uniqueInitModInput.value = "";
    
    // Очищаем атаки после добавления моба
    clearAttacks();

    renderSetupUnique();
};
```

## Шаг 3: Обновить renderSetupUnique() для отображения атак

В функции `renderSetupUnique()` после meta.innerText добавьте:

```javascript
const meta = document.createElement("div");
meta.className = "meta";
meta.innerText = `ХП: ${m.max_hp}, КД: ${m.ac}, ИНИЦ мод: ${m.initiative_mod}`;
left.appendChild(meta);

// Добавляем отображение атак
if (m.attacks && m.attacks.length > 0) {
    const attacksBadge = document.createElement("div");
    attacksBadge.className = "badges";
    attacksBadge.style.marginTop = "4px";
    
    const badge = document.createElement("span");
    badge.className = "badge";
    badge.style.background = "#7f1d1d";
    badge.innerText = `⚔️ ${m.attacks.length} атак(и)`;
    attacksBadge.appendChild(badge);
    
    left.appendChild(attacksBadge);
}
```

## Шаг 4: (Опционально) Добавить поддержку атак для групповых мобов

Если хотите добавить атаки и для групп мобов, аналогично обновите `addGroupBtn.onclick`:

```javascript
addGroupBtn.onclick = () => {
    const name = groupNameInput.value.trim();
    const count = parseInt(groupCountInput.value, 10);
    const hp = parseInt(groupHPInput.value, 10);
    const ac = parseInt(groupACInput.value, 10);
    const initMod = parseInt(groupInitModInput.value, 10);

    if (!name || isNaN(count) || isNaN(hp) || isNaN(ac) || isNaN(initMod)) {
        showToast("Заполните имя, кол-во, ХП, КД и мод ИНИЦ группы");
        return;
    }

    const attacks = getAttacksForMonster();

    setupGroupMonsters.push({
        name,
        count,
        max_hp: hp,
        ac,
        initiative_mod: initMod,
        is_enemy: true,
        attacks: attacks
    });

    groupNameInput.value = "";
    groupCountInput.value = "";
    groupHPInput.value = "";
    groupACInput.value = "";
    groupInitModInput.value = "";
    
    clearAttacks();

    renderSetupGroups();
};
```

## Что получится

После всех изменений:

1. Под полями уникального моба появится кнопка "⚔️ Атаки (0)"
2. При нажатии разворачивается форма для добавления атак
3. Можно добавить несколько атак к одному мобу
4. Добавленные атаки отображаются в списке с возможностью удаления
5. При добавлении моба атаки автоматически отправляются на бэкенд
6. В списке добавленных мобов отображается бедж с количеством атак

## Отображение атак во время боя (gm_encounter.html)

В `gm_encounter.html` при отрисовке участников добавьте после badges:

```javascript
// Отображение атак
if (p.attacks && p.attacks.length > 0) {
    const attacksBlock = document.createElement("div");
    attacksBlock.style.marginTop = "8px";
    attacksBlock.style.padding = "8px";
    attacksBlock.style.background = "rgba(127, 29, 29, 0.2)";
    attacksBlock.style.borderRadius = "6px";
    attacksBlock.style.border = "1px solid #7f1d1d";
    
    const attacksTitle = document.createElement("div");
    attacksTitle.className = "section-title";
    attacksTitle.style.fontSize = "11px";
    attacksTitle.innerText = "⚔️ Атаки:";
    attacksBlock.appendChild(attacksTitle);
    
    p.attacks.forEach(attack => {
        const attackDiv = document.createElement("div");
        attackDiv.style.marginTop = "4px";
        attackDiv.style.fontSize = "11px";
        
        const attackName = document.createElement("div");
        attackName.style.fontWeight = "600";
        attackName.innerText = attack.name;
        
        const attackStats = document.createElement("div");
        attackStats.className = "meta";
        attackStats.style.fontSize = "10px";
        attackStats.innerText = `+${attack.hit_bonus} попадание, +${attack.damage_bonus} урон (${attack.damage_type}), ${attack.range}`;
        
        attackDiv.appendChild(attackName);
        attackDiv.appendChild(attackStats);
        attacksBlock.appendChild(attackDiv);
    });
    
    left.appendChild(attacksBlock);
}
```

## Тестирование

1. Перезапустите сервер
2. Откройте Mini App
3. Перейдите к созданию схватки
4. Добавьте уникального моба
5. Нажмите "⚔️ Атаки (0)"
6. Добавьте атаку
7. Добавьте моба в схватку
8. Запустите схватку
9. Проверьте, что атаки отображаются в боевом экране
