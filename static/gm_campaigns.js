const tg = window.Telegram.WebApp;
const API_BASE = "";

function authHeaders() {
    const initData = tg?.initData || "";
    return initData ? { "Authorization": "tma " + initData } : {};
}

let toastTimeout = null;
function showToast(text) {
    const el = document.getElementById("toast");
    if (!el) return;
    el.innerText = text;
    el.classList.add("show");
    if (toastTimeout) clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => el.classList.remove("show"), 2200);
}

async function apiGet(path) {
    const res = await fetch(API_BASE + path, { headers: { ...authHeaders() } });
    if (!res.ok) throw new Error("HTTP " + res.status);
    return await res.json();
}

async function apiPost(path, body) {
    const res = await fetch(API_BASE + path, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: body ? JSON.stringify(body) : "{}",
    });
    if (!res.ok) throw new Error("HTTP " + res.status);
    return await res.json();
}

async function apiPut(path, body) {
    const res = await fetch(API_BASE + path, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error("HTTP " + res.status);
    return await res.json();
}

async function apiDelete(path) {
    const res = await fetch(API_BASE + path, {
        method: "DELETE",
        headers: { ...authHeaders() },
    });
    if (!res.ok) throw new Error("HTTP " + res.status);
    return await res.json();
}

function goHome() { window.location.href = '/static/index.html'; }

const screenCampaigns = document.getElementById("screenCampaigns");
const screenCharacters = document.getElementById("screenCharacters");
const screenEncounterSetup = document.getElementById("screenEncounterSetup");

let currentCampaignId = null, currentCampaignName = "", setupPlayers = [], setupUniqueMonsters = [], setupGroupMonsters = [];
let uniqueMonsterAttacks = [], groupMonsterAttacks = [];

// Helper: форматирование урона в XdY+Z
function formatDamage(numDice, dieSize, bonus) {
    let result = '';
    if (numDice > 0 && dieSize > 0) {
        result = `${numDice}d${dieSize}`;
        if (bonus !== 0) {
            result += bonus > 0 ? `+${bonus}` : `${bonus}`;
        }
    } else if (bonus !== 0) {
        result = `${bonus}`;
    } else {
        result = '0';
    }
    return result;
}

// === ATTACKS MANAGEMENT - UNIQUE ===
const toggleUniqueAttacksBtn = document.getElementById("toggleUniqueAttacksBtn");
const uniqueAttacksSection = document.getElementById("uniqueAttacksSection");
const addUniqueAttackBtn = document.getElementById("addUniqueAttackBtn");
const uniqueAttacksList = document.getElementById("uniqueAttacksList");
const uniqueAttacksHint = document.getElementById("uniqueAttacksHint");

toggleUniqueAttacksBtn.onclick = () => {
    const isVisible = uniqueAttacksSection.style.display !== 'none';
    uniqueAttacksSection.style.display = isVisible ? 'none' : 'block';
};

function updateUniqueAttacksButton() {
    const count = uniqueMonsterAttacks.length;
    toggleUniqueAttacksBtn.innerText = `⚔️ Атаки (${count})`;
    
    if (count > 0) {
        toggleUniqueAttacksBtn.classList.add('has-attacks');
        uniqueAttacksHint.style.display = 'block';
        uniqueAttacksHint.className = 'hint warning';
        uniqueAttacksHint.innerText = `⚠️ ${count} атак будут добавлены следующему мобу`;
    } else {
        toggleUniqueAttacksBtn.classList.remove('has-attacks');
        uniqueAttacksHint.style.display = 'none';
    }
}

function renderUniqueAttacksList() {
    uniqueAttacksList.innerHTML = '';
    if (uniqueMonsterAttacks.length === 0) {
        uniqueAttacksList.innerHTML = '<div class="hint">Атак пока нет</div>';
        return;
    }

    uniqueMonsterAttacks.forEach((attack, idx) => {
        const attackDiv = document.createElement('div');
        attackDiv.className = 'attack-item';

        const infoDiv = document.createElement('div');
        infoDiv.className = 'attack-info';

        const nameDiv = document.createElement('div');
        nameDiv.className = 'attack-name';
        nameDiv.innerText = attack.name;

        const statsDiv = document.createElement('div');
        statsDiv.className = 'attack-stats';
        const dmgStr = formatDamage(attack.damage_dice || 0, attack.damage_die || 0, attack.damage_bonus || 0);
        statsDiv.innerText = `+${attack.hit_bonus} попадание, ${dmgStr} урон (${attack.damage_type}), ${attack.range} футов`;

        infoDiv.appendChild(nameDiv);
        infoDiv.appendChild(statsDiv);

        const delBtn = document.createElement('button');
        delBtn.className = 'btn danger';
        delBtn.style.height = '36px';
        delBtn.style.padding = '0 12px';
        delBtn.style.fontSize = '12px';
        delBtn.innerText = '✕';
        delBtn.onclick = () => {
            uniqueMonsterAttacks.splice(idx, 1);
            renderUniqueAttacksList();
            updateUniqueAttacksButton();
        };

        attackDiv.appendChild(infoDiv);
        attackDiv.appendChild(delBtn);
        uniqueAttacksList.appendChild(attackDiv);
    });
}

addUniqueAttackBtn.onclick = () => {
    const name = document.getElementById('uniqueAttackName').value.trim();
    const hitBonus = parseInt(document.getElementById('uniqueAttackHitBonus').value) || 0;
    const dmgDice = parseInt(document.getElementById('uniqueAttackDmgDice').value) || 0;
    const dmgDie = parseInt(document.getElementById('uniqueAttackDmgDie').value) || 0;
    const dmgBonus = parseInt(document.getElementById('uniqueAttackDmgBonus').value) || 0;
    const dmgType = document.getElementById('uniqueAttackDmgType').value.trim() || 'физический';
    const range = document.getElementById('uniqueAttackRange').value.trim() || 'ближний бой';

    if (!name) {
        showToast('Введите название атаки');
        return;
    }

    uniqueMonsterAttacks.push({
        name,
        hit_bonus: hitBonus,
        damage_dice: dmgDice,
        damage_die: dmgDie,
        damage_bonus: dmgBonus,
        damage_type: dmgType,
        range
    });

    document.getElementById('uniqueAttackName').value = '';
    document.getElementById('uniqueAttackHitBonus').value = '';
    document.getElementById('uniqueAttackDmgDice').value = '';
    document.getElementById('uniqueAttackDmgDie').value = '';
    document.getElementById('uniqueAttackDmgBonus').value = '';
    document.getElementById('uniqueAttackDmgType').value = '';
    document.getElementById('uniqueAttackRange').value = '';

    renderUniqueAttacksList();
    updateUniqueAttacksButton();
};

function clearUniqueAttacks() {
    uniqueMonsterAttacks = [];
    renderUniqueAttacksList();
    updateUniqueAttacksButton();
}

function getUniqueAttacks() {
    return uniqueMonsterAttacks.length > 0 ? [...uniqueMonsterAttacks] : null;
}

// === ATTACKS MANAGEMENT - GROUPS ===
const toggleGroupAttacksBtn = document.getElementById("toggleGroupAttacksBtn");
const groupAttacksSection = document.getElementById("groupAttacksSection");
const addGroupAttackBtn = document.getElementById("addGroupAttackBtn");
const groupAttacksList = document.getElementById("groupAttacksList");
const groupAttacksHint = document.getElementById("groupAttacksHint");

toggleGroupAttacksBtn.onclick = () => {
    const isVisible = groupAttacksSection.style.display !== 'none';
    groupAttacksSection.style.display = isVisible ? 'none' : 'block';
};

function updateGroupAttacksButton() {
    const count = groupMonsterAttacks.length;
    toggleGroupAttacksBtn.innerText = `⚔️ Атаки (${count})`;
    
    if (count > 0) {
        toggleGroupAttacksBtn.classList.add('has-attacks');
        groupAttacksHint.style.display = 'block';
        groupAttacksHint.className = 'hint warning';
        groupAttacksHint.innerText = `⚠️ ${count} атак будут добавлены следующей группе`;
    } else {
        toggleGroupAttacksBtn.classList.remove('has-attacks');
        groupAttacksHint.style.display = 'none';
    }
}

function renderGroupAttacksList() {
    groupAttacksList.innerHTML = '';
    if (groupMonsterAttacks.length === 0) {
        groupAttacksList.innerHTML = '<div class="hint">Атак пока нет</div>';
        return;
    }

    groupMonsterAttacks.forEach((attack, idx) => {
        const attackDiv = document.createElement('div');
        attackDiv.className = 'attack-item';

        const infoDiv = document.createElement('div');
        infoDiv.className = 'attack-info';

        const nameDiv = document.createElement('div');
        nameDiv.className = 'attack-name';
        nameDiv.innerText = attack.name;

        const statsDiv = document.createElement('div');
        statsDiv.className = 'attack-stats';
        const dmgStr = formatDamage(attack.damage_dice || 0, attack.damage_die || 0, attack.damage_bonus || 0);
        statsDiv.innerText = `+${attack.hit_bonus} попадание, ${dmgStr} урон (${attack.damage_type}), ${attack.range} футов`;

        infoDiv.appendChild(nameDiv);
        infoDiv.appendChild(statsDiv);

        const delBtn = document.createElement('button');
        delBtn.className = 'btn danger';
        delBtn.style.height = '36px';
        delBtn.style.padding = '0 12px';
        delBtn.style.fontSize = '12px';
        delBtn.innerText = '✕';
        delBtn.onclick = () => {
            groupMonsterAttacks.splice(idx, 1);
            renderGroupAttacksList();
            updateGroupAttacksButton();
        };

        attackDiv.appendChild(infoDiv);
        attackDiv.appendChild(delBtn);
        groupAttacksList.appendChild(attackDiv);
    });
}

addGroupAttackBtn.onclick = () => {
    const name = document.getElementById('groupAttackName').value.trim();
    const hitBonus = parseInt(document.getElementById('groupAttackHitBonus').value) || 0;
    const dmgDice = parseInt(document.getElementById('groupAttackDmgDice').value) || 0;
    const dmgDie = parseInt(document.getElementById('groupAttackDmgDie').value) || 0;
    const dmgBonus = parseInt(document.getElementById('groupAttackDmgBonus').value) || 0;
    const dmgType = document.getElementById('groupAttackDmgType').value.trim() || 'физический';
    const range = document.getElementById('groupAttackRange').value.trim() || 'ближний бой';

    if (!name) {
        showToast('Введите название атаки');
        return;
    }

    groupMonsterAttacks.push({
        name,
        hit_bonus: hitBonus,
        damage_dice: dmgDice,
        damage_die: dmgDie,
        damage_bonus: dmgBonus,
        damage_type: dmgType,
        range
    });

    document.getElementById('groupAttackName').value = '';
    document.getElementById('groupAttackHitBonus').value = '';
    document.getElementById('groupAttackDmgDice').value = '';
    document.getElementById('groupAttackDmgDie').value = '';
    document.getElementById('groupAttackDmgBonus').value = '';
    document.getElementById('groupAttackDmgType').value = '';
    document.getElementById('groupAttackRange').value = '';

    renderGroupAttacksList();
    updateGroupAttacksButton();
};

function clearGroupAttacks() {
    groupMonsterAttacks = [];
    renderGroupAttacksList();
    updateGroupAttacksButton();
}

function getGroupAttacks() {
    return groupMonsterAttacks.length > 0 ? [...groupMonsterAttacks] : null;
}

// === CAMPAIGNS LOGIC ===
async function loadCampaigns() {
    try {
        const campaigns = await apiGet("/campaigns");
        renderCampaigns(campaigns);
    } catch (e) {
        console.error(e);
        showToast("Не удалось загрузить кампании");
    }
}

async function loadMyEncounters() {
    try {
        const encs = await apiGet("/encounters/my");
        renderMyEncounters(encs);
    } catch (e) {
        console.error(e);
    }
}

function renderCampaigns(campaigns) {
    const list = document.getElementById('campaignList');
    list.innerHTML = '';
    if (!campaigns || campaigns.length === 0) {
        list.innerHTML = '<div class="item"><div><div class="item-title">Пока пусто</div><div class="item-sub">Создай первую кампанию снизу</div></div><div class="pill warn">Нет кампаний</div></div>';
        return;
    }
    campaigns.forEach(c => {
        const row = document.createElement('div');
        row.className = 'item';
        const left = document.createElement('div');
        const title = document.createElement('div');
        title.className = 'item-title';
        title.innerText = c.name;
        const sub = document.createElement('div');
        sub.className = 'item-sub';
        sub.innerText = `ID: ${c.id}`;
        left.appendChild(title);
        left.appendChild(sub);
        const right = document.createElement('div');
        right.style.display = 'flex';
        right.style.gap = '8px';
        const shareBtn = document.createElement('button');
        shareBtn.className = 'btn secondary';
        shareBtn.style.height = '44px';
        shareBtn.style.padding = '0 14px';
        shareBtn.innerText = '📤';
        shareBtn.onclick = (e) => {
            e.stopPropagation();
            window.location.href = `/static/share_campaign.html?campaign_id=${c.id}`;
        };
        const openBtn = document.createElement('div');
        openBtn.className = 'pill';
        openBtn.innerText = 'Открыть';
        openBtn.onclick = () => openCampaign(c.id, c.name);
        right.appendChild(shareBtn);
        right.appendChild(openBtn);
        row.appendChild(left);
        row.appendChild(right);
        list.appendChild(row);
    });
}

function renderMyEncounters(encs) {
    const list = document.getElementById('myEncountersList');
    list.innerHTML = '';
    if (!encs || encs.length === 0) {
        list.innerHTML = '<div class="item"><div><div class="item-title">Нет незавершённых схваток</div><div class="item-sub">Когда начнёшь бой — он появится здесь</div></div><div class="pill">OK</div></div>';
        return;
    }
    encs.forEach(e => {
        const row = document.createElement('div');
        row.className = 'item';
        row.onclick = () => {
            window.location.href = `/static/gm_encounter.html?encounter_id=${e.id}`;
        };
        const left = document.createElement('div');
        const title = document.createElement('div');
        title.className = 'item-title';
        title.innerText = e.name || `Схватка #${e.id}`;
        const sub = document.createElement('div');
        sub.className = 'item-sub';
        sub.innerText = `Кампания "${e.campaign_name}" • ${e.status}`;
        left.appendChild(title);
        left.appendChild(sub);
        const pill = document.createElement('div');
        pill.className = 'pill ' + (e.status === 'active' ? 'ok' : 'warn');
        pill.innerText = 'Продолжить';
        row.appendChild(left);
        row.appendChild(pill);
        list.appendChild(row);
    });
}

document.getElementById('createCampaignBtn').onclick = async () => {
    const name = document.getElementById('newCampaignName').value.trim();
    if (!name) {
        showToast('Введите название кампании');
        return;
    }
    try {
        await apiPost('/campaigns', { name });
        document.getElementById('newCampaignName').value = '';
        showToast('Кампания создана');
        await loadCampaigns();
    } catch (e) {
        console.error(e);
        showToast('Ошибка создания кампании');
    }
};

async function openCampaign(id, name) {
    currentCampaignId = id;
    currentCampaignName = name;
    document.getElementById('campaignTitle').innerText = name;
    document.getElementById('campaignSubtitle').innerText = `Персонажи кампании #${id}`;
    screenCampaigns.style.display = 'none';
    screenEncounterSetup.style.display = 'none';
    screenCharacters.style.display = 'block';
    await loadCharacters();
}

async function loadCharacters() {
    if (!currentCampaignId) return;
    try {
        const chars = await apiGet(`/campaigns/${currentCampaignId}/characters`);
        renderCharacters(chars);
    } catch (e) {
        console.error(e);
        showToast('Не удалось загрузить персонажей');
    }
}

function renderCharacters(chars) {
    const list = document.getElementById('characterList');
    list.innerHTML = '';
    if (!chars || chars.length === 0) {
        list.innerHTML = '<div class="item"><div><div class="item-title">Персонажей нет</div><div class="item-sub">Добавь первого снизу</div></div><div class="pill warn">Пусто</div></div>';
        return;
    }
    chars.forEach(ch => {
        const row = document.createElement('div');
        row.className = 'item';
        const left = document.createElement('div');
        const name = document.createElement('div');
        name.className = 'item-title';
        name.innerText = ch.name;
        const sub = document.createElement('div');
        sub.className = 'item-sub';
        sub.innerText = `КД: ${ch.ac}, ИНИЦ: ${ch.base_initiative}`;
        left.appendChild(name);
        left.appendChild(sub);
        const right = document.createElement('div');
        right.style.display = 'flex';
        right.style.gap = '8px';
        const editBtn = document.createElement('button');
        editBtn.className = 'btn secondary';
        editBtn.style.height = '44px';
        editBtn.style.padding = '0 14px';
        editBtn.innerText = '✎';
        editBtn.onclick = (e) => {
            e.stopPropagation();
            editCharacterPrompt(ch);
        };
        const delBtn = document.createElement('button');
        delBtn.className = 'btn danger';
        delBtn.style.height = '44px';
        delBtn.style.padding = '0 14px';
        delBtn.innerText = '✕';
        delBtn.onclick = async (e) => {
            e.stopPropagation();
            await deleteCharacter(ch.id);
        };
        right.appendChild(editBtn);
        right.appendChild(delBtn);
        row.appendChild(left);
        row.appendChild(right);
        list.appendChild(row);
    });
}

document.getElementById('createCharBtn').onclick = async () => {
    if (!currentCampaignId) return;
    const name = document.getElementById('newCharName').value.trim();
    const ac = parseInt(document.getElementById('newCharAC').value, 10);
    const init = parseInt(document.getElementById('newCharInit').value, 10);
    if (!name || isNaN(ac) || isNaN(init)) {
        showToast('Имя, КД и ИНИЦ обязательны');
        return;
    }
    try {
        await apiPost('/characters', {
            campaign_id: currentCampaignId,
            name,
            ac,
            base_initiative: init
        });
        document.getElementById('newCharName').value = '';
        document.getElementById('newCharAC').value = '';
        document.getElementById('newCharInit').value = '';
        showToast('Персонаж добавлен');
        await loadCharacters();
    } catch (e) {
        console.error(e);
        showToast('Ошибка добавления персонажа');
    }
};

document.getElementById('backToCampaignsBtn').onclick = () => {
    screenCharacters.style.display = 'none';
    screenEncounterSetup.style.display = 'none';
    screenCampaigns.style.display = 'block';
    currentCampaignId = null;
    currentCampaignName = '';
};

document.getElementById('startSetupBtn').onclick = () => openEncounterSetup();
document.getElementById('backToCharsBtn').onclick = () => {
    screenEncounterSetup.style.display = 'none';
    screenCharacters.style.display = 'block';
};

async function openEncounterSetup() {
    if (!currentCampaignId) {
        showToast('Сначала выберите кампанию');
        return;
    }
    try {
        const chars = await apiGet(`/campaigns/${currentCampaignId}/characters`);
        setupPlayers = chars.map(ch => ({
            character_id: ch.id,
            name: ch.name,
            ac: ch.ac,
            base_initiative: ch.base_initiative,
            include: false,
            initiative_total: ch.base_initiative
        }));
    } catch (e) {
        console.error(e);
        showToast('Не удалось загрузить персонажей для схватки');
        return;
    }
    setupUniqueMonsters = [];
    setupGroupMonsters = [];
    clearUniqueAttacks();
    clearGroupAttacks();
    renderSetupPlayers();
    renderSetupUnique();
    renderSetupGroups();
    screenCharacters.style.display = 'none';
    screenCampaigns.style.display = 'none';
    screenEncounterSetup.style.display = 'block';
    document.getElementById('encSetupTitle').innerText = 'Подготовка схватки';
    document.getElementById('encSetupSubtitle').innerText = `Кампания: ${currentCampaignName}`;
}

function renderSetupPlayers() {
    const list = document.getElementById('encPlayersList');
    list.innerHTML = '';
    if (setupPlayers.length === 0) {
        list.innerHTML = '<div class="item"><div><div class="item-title">Нет персонажей</div><div class="item-sub">Вернись и добавь хотя бы одного</div></div><div class="pill warn">Пусто</div></div>';
        return;
    }
    setupPlayers.forEach((p, idx) => {
        const row = document.createElement('div');
        row.className = 'item pick' + (p.include ? ' selected' : '');
        const left = document.createElement('div');
        const name = document.createElement('div');
        name.className = 'item-title';
        name.innerText = p.name;
        const sub = document.createElement('div');
        sub.className = 'item-sub';
        sub.innerText = `КД: ${p.ac}, баз. ИНИЦ: ${p.base_initiative}`;
        left.appendChild(name);
        left.appendChild(sub);
        const right = document.createElement('div');
        right.style.display = 'flex';
        right.style.alignItems = 'center';
        right.style.gap = '10px';
        const pill = document.createElement('div');
        pill.className = 'pill ' + (p.include ? 'ok' : '');
        pill.innerText = p.include ? 'В бою' : 'Не в бою';
        const initInput = document.createElement('input');
        initInput.className = 'input small';
        initInput.type = 'number';
        initInput.value = p.initiative_total;
        initInput.onclick = (e) => e.stopPropagation();
        initInput.onchange = () => {
            const val = parseInt(initInput.value, 10);
            if (!isNaN(val)) setupPlayers[idx].initiative_total = val;
        };
        right.appendChild(pill);
        right.appendChild(initInput);
        row.appendChild(left);
        row.appendChild(right);
        row.onclick = () => {
            setupPlayers[idx].include = !setupPlayers[idx].include;
            renderSetupPlayers();
        };
        list.appendChild(row);
    });
}

function renderSetupUnique() {
    const list = document.getElementById('encUniqueMonsters');
    list.innerHTML = '';
    if (setupUniqueMonsters.length === 0) {
        list.innerHTML = '<div class="item"><div><div class="item-title">Пока нет уникальных мобов</div><div class="item-sub">Добавь ниже (имя, ХП, КД, ИНИЦ+)</div></div><div class="pill warn">0</div></div>';
        return;
    }
    setupUniqueMonsters.forEach((m, idx) => {
        const row = document.createElement('div');
        row.className = 'item';
        const left = document.createElement('div');
        const name = document.createElement('div');
        name.className = 'item-title';
        name.innerText = m.name;
        const sub = document.createElement('div');
        sub.className = 'item-sub';
        sub.innerText = `ХП: ${m.max_hp}, КД: ${m.ac}, ИНИЦ+: ${m.initiative_mod}`;
        if (m.attacks && m.attacks.length > 0) {
            sub.innerText += ` • ⚔️ ${m.attacks.length} атак`;
        }
        left.appendChild(name);
        left.appendChild(sub);
        const delBtn = document.createElement('button');
        delBtn.className = 'btn danger';
        delBtn.style.height = '44px';
        delBtn.style.padding = '0 14px';
        delBtn.innerText = '✕';
        delBtn.onclick = () => {
            setupUniqueMonsters.splice(idx, 1);
            renderSetupUnique();
        };
        row.appendChild(left);
        row.appendChild(delBtn);
        list.appendChild(row);
    });
}

function renderSetupGroups() {
    const list = document.getElementById('encGroupMonsters');
    list.innerHTML = '';
    if (setupGroupMonsters.length === 0) {
        list.innerHTML = '<div class="item"><div><div class="item-title">Пока нет групп</div><div class="item-sub">Добавь ниже (имя, xN, ХП, КД, ИНИЦ+)</div></div><div class="pill warn">0</div></div>';
        return;
    }
    setupGroupMonsters.forEach((g, idx) => {
        const row = document.createElement('div');
        row.className = 'item';
        const left = document.createElement('div');
        const name = document.createElement('div');
        name.className = 'item-title';
        name.innerText = `${g.name} (x${g.count})`;
        const sub = document.createElement('div');
        sub.className = 'item-sub';
        sub.innerText = `ХП: ${g.max_hp}, КД: ${g.ac}, ИНИЦ+: ${g.initiative_mod}`;
        if (g.attacks && g.attacks.length > 0) {
            sub.innerText += ` • ⚔️ ${g.attacks.length} атак`;
        }
        left.appendChild(name);
        left.appendChild(sub);
        const delBtn = document.createElement('button');
        delBtn.className = 'btn danger';
        delBtn.style.height = '44px';
        delBtn.style.padding = '0 14px';
        delBtn.innerText = '✕';
        delBtn.onclick = () => {
            setupGroupMonsters.splice(idx, 1);
            renderSetupGroups();
        };
        row.appendChild(left);
        row.appendChild(delBtn);
        list.appendChild(row);
    });
}

document.getElementById('addUniqueBtn').onclick = () => {
    const name = document.getElementById('uniqueName').value.trim();
    const hp = parseInt(document.getElementById('uniqueHP').value, 10);
    const ac = parseInt(document.getElementById('uniqueAC').value, 10);
    const initMod = parseInt(document.getElementById('uniqueInitMod').value, 10);
    if (!name || isNaN(hp) || isNaN(ac) || isNaN(initMod)) {
        showToast('Заполни имя, ХП, КД и ИНИЦ+');
        return;
    }
    const attacks = getUniqueAttacks();
    const attacksCount = attacks ? attacks.length : 0;
    setupUniqueMonsters.push({
        name,
        max_hp: hp,
        ac,
        initiative_mod: initMod,
        is_enemy: true,
        attacks: attacks
    });
    document.getElementById('uniqueName').value = '';
    document.getElementById('uniqueHP').value = '';
    document.getElementById('uniqueAC').value = '';
    document.getElementById('uniqueInitMod').value = '';
    clearUniqueAttacks();
    renderSetupUnique();
    if (attacksCount > 0) {
        showToast(`Моб '${name}' добавлен с ${attacksCount} атаками ⚔️`);
    } else {
        showToast(`Моб '${name}' добавлен`);
    }
};

document.getElementById('addGroupBtn').onclick = () => {
    const name = document.getElementById('groupName').value.trim();
    const count = parseInt(document.getElementById('groupCount').value, 10);
    const hp = parseInt(document.getElementById('groupHP').value, 10);
    const ac = parseInt(document.getElementById('groupAC').value, 10);
    const initMod = parseInt(document.getElementById('groupInitMod').value, 10);
    if (!name || isNaN(count) || isNaN(hp) || isNaN(ac) || isNaN(initMod)) {
        showToast('Заполни имя, xN, ХП, КД и ИНИЦ+');
        return;
    }
    const attacks = getGroupAttacks();
    const attacksCount = attacks ? attacks.length : 0;
    setupGroupMonsters.push({
        name,
        count,
        max_hp: hp,
        ac,
        initiative_mod: initMod,
        is_enemy: true,
        attacks: attacks
    });
    document.getElementById('groupName').value = '';
    document.getElementById('groupCount').value = '';
    document.getElementById('groupHP').value = '';
    document.getElementById('groupAC').value = '';
    document.getElementById('groupInitMod').value = '';
    clearGroupAttacks();
    renderSetupGroups();
    if (attacksCount > 0) {
        showToast(`Группа '${name}' (x${count}) добавлена с ${attacksCount} атаками ⚔️`);
    } else {
        showToast(`Группа '${name}' (x${count}) добавлена`);
    }
};

document.getElementById('startEncounterBtn').onclick = async () => {
    if (!currentCampaignId) {
        showToast('Нет выбранной кампании');
        return;
    }
    const playersForEncounter = setupPlayers
        .filter(p => p.include)
        .map(p => ({
            character_id: p.character_id,
            initiative_total: p.initiative_total
        }));
    if (playersForEncounter.length === 0) {
        showToast('Выбери хотя бы одного игрока');
        return;
    }
    try {
        let encName = prompt('Название схватки:', 'Засада у моста');
        if (encName === null) return;
        encName = encName.trim();
        if (!encName) encName = 'Схватка';
        const enc = await apiPost('/encounters', {
            campaign_id: currentCampaignId,
            name: encName
        });
        const encounterId = enc.id;
        await apiPost(`/encounters/${encounterId}/participants`, {
            players: playersForEncounter,
            unique_monsters: setupUniqueMonsters,
            group_monsters: setupGroupMonsters
        });
        await apiPost(`/encounters/${encounterId}/start`, {});
        showToast('Схватка началась');
        window.location.href = `/static/gm_encounter.html?encounter_id=${encounterId}`;
    } catch (e) {
        console.error(e);
        showToast('Ошибка при запуске схватки');
    }
};

async function editCharacterPrompt(ch) {
    const name = prompt('Имя персонажа:', ch.name);
    if (name === null) return;
    const acStr = prompt('КД:', ch.ac);
    if (acStr === null) return;
    const initStr = prompt('ИНИЦ:', ch.base_initiative);
    if (initStr === null) return;
    const ac = parseInt(acStr, 10);
    const init = parseInt(initStr, 10);
    if (!name || isNaN(ac) || isNaN(init)) {
        showToast('Некорректные данные');
        return;
    }
    try {
        await apiPut(`/characters/${ch.id}`, { name, ac, base_initiative: init });
        showToast('Персонаж обновлён');
        await loadCharacters();
    } catch (e) {
        console.error(e);
        showToast('Ошибка обновления персонажа');
    }
}

async function deleteCharacter(id) {
    if (!confirm('Удалить персонажа?')) return;
    try {
        await apiDelete(`/characters/${id}`);
        showToast('Персонаж удалён');
        await loadCharacters();
    } catch (e) {
        console.error(e);
        showToast('Ошибка удаления персонажа');
    }
}

if (tg && tg.ready) tg.ready();
loadCampaigns();
loadMyEncounters();