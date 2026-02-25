// attacks_addon.js - Модуль для управления атаками мобов

// Хранилище атак для текущего моба
let currentMonsterAttacks = [];

// Инициализация UI для атак
function initAttacksUI() {
    // Добавляем кнопку для атак после полей уникального моба
    const uniqueControls = document.querySelector('#addUniqueBtn').parentElement;
    
    const attacksToggle = document.createElement('button');
    attacksToggle.id = 'toggleAttacksBtn';
    attacksToggle.className = 'secondary';
    attacksToggle.innerText = '⚔️ Атаки (0)';
    attacksToggle.style.width = '100%';
    attacksToggle.style.marginTop = '8px';
    
    const attacksContainer = document.createElement('div');
    attacksContainer.id = 'attacksContainer';
    attacksContainer.style.display = 'none';
    attacksContainer.style.marginTop = '10px';
    attacksContainer.style.padding = '10px';
    attacksContainer.style.background = 'rgba(15, 23, 42, 0.5)';
    attacksContainer.style.borderRadius = '8px';
    attacksContainer.style.border = '1px solid #4b5563';
    
    attacksContainer.innerHTML = `
        <div class="section-title" style="margin-bottom: 8px;">Добавить атаку</div>
        <div style="display: flex; flex-direction: column; gap: 6px;">
            <input id="attackName" type="text" placeholder="Название атаки (напр. Укус)" 
                style="padding:6px 8px; border-radius:6px; border:1px solid #4b5563; background:#020617; color:#e5e7eb; font-size:13px;">
            <div style="display: flex; gap: 6px;">
                <input id="attackHitBonus" type="number" placeholder="+Попадание" 
                    style="flex:1; padding:6px 8px; border-radius:6px; border:1px solid #4b5563; background:#020617; color:#e5e7eb; font-size:13px;">
                <input id="attackDmgBonus" type="number" placeholder="+Урон" 
                    style="flex:1; padding:6px 8px; border-radius:6px; border:1px solid #4b5563; background:#020617; color:#e5e7eb; font-size:13px;">
            </div>
            <input id="attackDmgType" type="text" placeholder="Тип урона (напр. колющий)" 
                style="padding:6px 8px; border-radius:6px; border:1px solid #4b5563; background:#020617; color:#e5e7eb; font-size:13px;">
            <input id="attackRange" type="text" placeholder="Дальность (напр. ближний бой)" 
                style="padding:6px 8px; border-radius:6px; border:1px solid #4b5563; background:#020617; color:#e5e7eb; font-size:13px;">
            <button id="addAttackBtn" class="secondary">+ Добавить атаку</button>
        </div>
        <div id="attacksList" style="margin-top: 10px;"></div>
    `;
    
    uniqueControls.appendChild(attacksToggle);
    uniqueControls.appendChild(attacksContainer);
    
    // Обработчики
    attacksToggle.onclick = () => {
        const isVisible = attacksContainer.style.display !== 'none';
        attacksContainer.style.display = isVisible ? 'none' : 'block';
    };
    
    document.getElementById('addAttackBtn').onclick = addAttack;
}

// Добавить атаку
function addAttack() {
    const nameEl = document.getElementById('attackName');
    const hitEl = document.getElementById('attackHitBonus');
    const dmgEl = document.getElementById('attackDmgBonus');
    const typeEl = document.getElementById('attackDmgType');
    const rangeEl = document.getElementById('attackRange');
    
    const name = nameEl.value.trim();
    const hitBonus = parseInt(hitEl.value) || 0;
    const dmgBonus = parseInt(dmgEl.value) || 0;
    const dmgType = typeEl.value.trim() || 'физический';
    const range = rangeEl.value.trim() || 'ближний бой';
    
    if (!name) {
        showToast('Введите название атаки');
        return;
    }
    
    currentMonsterAttacks.push({
        name,
        hit_bonus: hitBonus,
        damage_bonus: dmgBonus,
        damage_type: dmgType,
        range
    });
    
    // Очистка полей
    nameEl.value = '';
    hitEl.value = '';
    dmgEl.value = '';
    typeEl.value = '';
    rangeEl.value = '';
    
    updateAttacksList();
    updateAttacksButton();
}

// Обновить список атак
function updateAttacksList() {
    const list = document.getElementById('attacksList');
    if (!list) return;
    
    list.innerHTML = '';
    
    if (currentMonsterAttacks.length === 0) {
        list.innerHTML = '<div class="hp-hint" style="margin-top: 8px;">Атак пока нет</div>';
        return;
    }
    
    currentMonsterAttacks.forEach((attack, idx) => {
        const attackRow = document.createElement('div');
        attackRow.className = 'row';
        attackRow.style.marginTop = '6px';
        attackRow.style.padding = '8px';
        
        const left = document.createElement('div');
        
        const name = document.createElement('div');
        name.className = 'name';
        name.innerText = attack.name;
        name.style.fontSize = '13px';
        left.appendChild(name);
        
        const meta = document.createElement('div');
        meta.className = 'meta';
        meta.innerText = `+${attack.hit_bonus} попадание, +${attack.damage_bonus} урон (${attack.damage_type}), ${attack.range}`;
        meta.style.fontSize = '11px';
        left.appendChild(meta);
        
        const right = document.createElement('div');
        const delBtn = document.createElement('button');
        delBtn.className = 'danger';
        delBtn.innerText = '✕';
        delBtn.style.padding = '4px 8px';
        delBtn.style.fontSize = '12px';
        delBtn.onclick = () => {
            currentMonsterAttacks.splice(idx, 1);
            updateAttacksList();
            updateAttacksButton();
        };
        right.appendChild(delBtn);
        
        attackRow.appendChild(left);
        attackRow.appendChild(right);
        list.appendChild(attackRow);
    });
}

// Обновить кнопку с количеством атак
function updateAttacksButton() {
    const btn = document.getElementById('toggleAttacksBtn');
    if (btn) {
        btn.innerText = `⚔️ Атаки (${currentMonsterAttacks.length})`;
    }
}

// Получить массив атак для отправки
function getAttacksForMonster() {
    return currentMonsterAttacks.length > 0 ? currentMonsterAttacks : null;
}

// Очистить атаки после создания моба
function clearAttacks() {
    currentMonsterAttacks = [];
    updateAttacksList();
    updateAttacksButton();
}

// Инициализация при загрузке
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAttacksUI);
} else {
    initAttacksUI();
}
