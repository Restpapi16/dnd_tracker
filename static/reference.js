// static/reference.js

const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

const API_BASE = '';
let currentTab = 'spells';
let searchTimeout;

// =========================
// Инициализация
// =========================

document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupSearch();
    loadContent();
});

// =========================
// Вкладки
// =========================

function setupTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentTab = tab.dataset.tab;
            loadContent();
        });
    });
}

// =========================
// Поиск с автодополнением
// =========================

function setupSearch() {
    const searchInput = document.getElementById('search');
    const suggestionsDropdown = document.getElementById('suggestions');

    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();

        if (query.length < 2) {
            hideSuggestions();
            return;
        }

        // Debounce: ждем 300мс после последнего ввода
        searchTimeout = setTimeout(async () => {
            await fetchSuggestions(query);
        }, 300);
    });

    // Закрытие подсказок при клике вне области
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !suggestionsDropdown.contains(e.target)) {
            hideSuggestions();
        }
    });
}

async function fetchSuggestions(query) {
    try {
        const response = await fetch(
            `${API_BASE}/reference/search/suggestions?q=${encodeURIComponent(query)}&limit=5`,
            {
                headers: {
                    'Authorization': `tma ${tg.initData}`
                }
            }
        );

        if (!response.ok) throw new Error('Failed to fetch suggestions');

        const data = await response.json();
        showSuggestions(data);
    } catch (error) {
        console.error('Error fetching suggestions:', error);
        tg.showAlert('Ошибка поиска');
    }
}

function showSuggestions(data) {
    const dropdown = document.getElementById('suggestions');
    let html = '';

    const hasResults = data.spells?.length || data.items?.length || data.creatures?.length;

    if (!hasResults) {
        dropdown.classList.remove('show');
        return;
    }

    // Заклинания
    if (data.spells?.length) {
        html += '<div class="suggestion-group-title">Заклинания</div>';
        data.spells.forEach(spell => {
            html += `
                <div class="suggestion-item" onclick="selectItem('spell', ${spell.id})">
                    <span class="suggestion-type">✨</span>
                    <span class="suggestion-name">${spell.name}</span>
                    <span class="suggestion-meta">${spell.level} ур.</span>
                </div>
            `;
        });
    }

    // Предметы
    if (data.items?.length) {
        html += '<div class="suggestion-group-title">Предметы</div>';
        data.items.forEach(item => {
            html += `
                <div class="suggestion-item" onclick="selectItem('item', ${item.id})">
                    <span class="suggestion-type">🗡️</span>
                    <span class="suggestion-name">${item.name}</span>
                    ${item.category ? `<span class="suggestion-meta">${item.category}</span>` : ''}
                </div>
            `;
        });
    }

    // Существа
    if (data.creatures?.length) {
        html += '<div class="suggestion-group-title">Существа</div>';
        data.creatures.forEach(creature => {
            html += `
                <div class="suggestion-item" onclick="selectItem('creature', ${creature.id})">
                    <span class="suggestion-type">🐉</span>
                    <span class="suggestion-name">${creature.name}</span>
                    ${creature.cr ? `<span class="suggestion-meta">CR ${creature.cr}</span>` : ''}
                </div>
            `;
        });
    }

    dropdown.innerHTML = html;
    dropdown.classList.add('show');
}

function hideSuggestions() {
    document.getElementById('suggestions').classList.remove('show');
}

async function selectItem(type, id) {
    hideSuggestions();
    await openDetail(type, id);
}

// =========================
// Загрузка контента
// =========================

async function loadContent() {
    const content = document.getElementById('content');
    content.innerHTML = '<div class="loading">Загрузка...</div>';

    try {
        let endpoint;
        switch (currentTab) {
            case 'spells':
                endpoint = '/reference/spells/search?limit=20';
                break;
            case 'items':
                endpoint = '/reference/items/search?limit=20';
                break;
            case 'creatures':
                endpoint = '/reference/creatures/search?limit=20';
                break;
        }

        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Authorization': `tma ${tg.initData}`
            }
        });

        if (!response.ok) throw new Error('Failed to load content');

        const data = await response.json();
        renderContent(data);
    } catch (error) {
        console.error('Error loading content:', error);
        content.innerHTML = '<div class="empty">Ошибка загрузки данных</div>';
    }
}

function renderContent(data) {
    const content = document.getElementById('content');

    if (!data || data.length === 0) {
        content.innerHTML = '<div class="empty">Данные не найдены</div>';
        return;
    }

    let html = '';

    data.forEach(item => {
        if (currentTab === 'spells') {
            html += renderSpellCard(item);
        } else if (currentTab === 'items') {
            html += renderItemCard(item);
        } else if (currentTab === 'creatures') {
            html += renderCreatureCard(item);
        }
    });

    content.innerHTML = html;
}

function renderSpellCard(spell) {
    return `
        <div class="card" onclick="openDetail('spell', ${spell.id})">
            <div class="card-title">✨ ${spell.name}</div>
            <div class="card-meta">
                <span class="card-badge">${spell.level} уровень</span>
                ${spell.school ? `<span class="card-badge">${spell.school}</span>` : ''}
                ${spell.concentration ? '<span class="card-badge">Концентрация</span>' : ''}
            </div>
            ${spell.description ? `<div class="card-description">${spell.description}</div>` : ''}
        </div>
    `;
}

function renderItemCard(item) {
    return `
        <div class="card" onclick="openDetail('item', ${item.id})">
            <div class="card-title">🗡️ ${item.name}</div>
            <div class="card-meta">
                ${item.category ? `<span class="card-badge">${item.category}</span>` : ''}
                ${item.cost ? `<span class="card-badge">${item.cost}</span>` : ''}
            </div>
            ${item.description ? `<div class="card-description">${item.description}</div>` : ''}
        </div>
    `;
}

function renderCreatureCard(creature) {
    return `
        <div class="card" onclick="openDetail('creature', ${creature.id})">
            <div class="card-title">🐉 ${creature.name}</div>
            <div class="card-meta">
                ${creature.cr ? `<span class="card-badge">CR ${creature.cr}</span>` : ''}
                ${creature.creature_type ? `<span class="card-badge">${creature.creature_type}</span>` : ''}
            </div>
            ${creature.size ? `<div class="card-description">${creature.size}, ${creature.alignment || ''}</div>` : ''}
        </div>
    `;
}

// =========================
// Детальный просмотр
// =========================

async function openDetail(type, id) {
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modalTitle');
    const modalContent = document.getElementById('modalContent');

    modalContent.innerHTML = '<div class="loading">Загрузка...</div>';
    modal.classList.add('show');

    try {
        let endpoint;
        switch (type) {
            case 'spell':
                endpoint = `/reference/spells/${id}`;
                break;
            case 'item':
                endpoint = `/reference/items/${id}`;
                break;
            case 'creature':
                endpoint = `/reference/creatures/${id}`;
                break;
        }

        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Authorization': `tma ${tg.initData}`
            }
        });

        if (!response.ok) throw new Error('Failed to load detail');

        const data = await response.json();
        modalTitle.textContent = data.name;

        if (type === 'spell') {
            modalContent.innerHTML = renderSpellDetail(data);
        } else if (type === 'item') {
            modalContent.innerHTML = renderItemDetail(data);
        } else if (type === 'creature') {
            modalContent.innerHTML = renderCreatureDetail(data);
        }
    } catch (error) {
        console.error('Error loading detail:', error);
        modalContent.innerHTML = '<div class="empty">Ошибка загрузки</div>';
    }
}

function renderSpellDetail(spell) {
    let html = '';

    if (spell.level !== undefined) {
        html += `<div class="modal-section">
            <div class="modal-section-title">Уровень</div>
            <div class="modal-section-content">${spell.level} ${spell.school ? `(${spell.school})` : ''}</div>
        </div>`;
    }

    if (spell.casting_time) {
        html += `<div class="modal-section">
            <div class="modal-section-title">Время сотворения</div>
            <div class="modal-section-content">${spell.casting_time}</div>
        </div>`;
    }

    if (spell.range) {
        html += `<div class="modal-section">
            <div class="modal-section-title">Дистанция</div>
            <div class="modal-section-content">${spell.range}</div>
        </div>`;
    }

    if (spell.components) {
        html += `<div class="modal-section">
            <div class="modal-section-title">Компоненты</div>
            <div class="modal-section-content">${spell.components}</div>
        </div>`;
    }

    if (spell.duration) {
        html += `<div class="modal-section">
            <div class="modal-section-title">Длительность</div>
            <div class="modal-section-content">${spell.duration}</div>
        </div>`;
    }

    // Классы
    if (spell.classes && spell.classes.length > 0) {
        html += `<div class="modal-section">
            <div class="modal-section-title">Классы</div>
            <div class="modal-section-content">${spell.classes.join(', ')}</div>
        </div>`;
    }

    // Подклассы
    if (spell.subclasses && spell.subclasses.length > 0) {
        html += `<div class="modal-section">
            <div class="modal-section-title">Подклассы</div>
            <div class="modal-section-content">${spell.subclasses.join(', ')}</div>
        </div>`;
    }

    if (spell.description) {
        html += `<div class="modal-section">
            <div class="modal-section-title">Описание</div>
            <div class="modal-section-content">${spell.description}</div>
        </div>`;
    }

    if (spell.at_higher_levels) {
        html += `<div class="modal-section">
            <div class="modal-section-title">На более высоких уровнях</div>
            <div class="modal-section-content">${spell.at_higher_levels}</div>
        </div>`;
    }

    return html;
}

function renderItemDetail(item) {
    let html = '';

    if (item.category) {
        html += `<div class="modal-section">
            <div class="modal-section-title">Категория</div>
            <div class="modal-section-content">${item.category}</div>
        </div>`;
    }

    if (item.cost || item.weight) {
        html += `<div class="modal-section">
            <div class="modal-section-title">Характеристики</div>
            <div class="modal-section-content">
                ${item.cost ? `Стоимость: ${item.cost}<br>` : ''}
                ${item.weight ? `Вес: ${item.weight}` : ''}
            </div>
        </div>`;
    }

    if (item.damage) {
        html += `<div class="modal-section">
            <div class="modal-section-title">Урон</div>
            <div class="modal-section-content">${item.damage}</div>
        </div>`;
    }

    if (item.description) {
        html += `<div class="modal-section">
            <div class="modal-section-title">Описание</div>
            <div class="modal-section-content">${item.description}</div>
        </div>`;
    }

    return html;
}

function renderCreatureDetail(creature) {
    let html = '';

    if (creature.size || creature.creature_type) {
        html += `<div class="modal-section">
            <div class="modal-section-title">Тип</div>
            <div class="modal-section-content">${creature.size}, ${creature.creature_type}</div>
        </div>`;
    }

    if (creature.ac) {
        html += `<div class="modal-section">
            <div class="modal-section-title">КД</div>
            <div class="modal-section-content">${creature.ac}</div>
        </div>`;
    }

    if (creature.hp) {
        html += `<div class="modal-section">
            <div class="modal-section-title">Хиты</div>
            <div class="modal-section-content">${creature.hp}</div>
        </div>`;
    }

    if (creature.cr) {
        html += `<div class="modal-section">
            <div class="modal-section-title">Показатель опасности</div>
            <div class="modal-section-content">CR ${creature.cr}</div>
        </div>`;
    }

    if (creature.strength) {
        html += `<div class="modal-section">
            <div class="modal-section-title">Характеристики</div>
            <div class="modal-section-content">
                СИЛ: ${creature.strength}, ЛОВ: ${creature.dexterity}, ТЕЛ: ${creature.constitution}<br>
                ИНТ: ${creature.intelligence}, МДР: ${creature.wisdom}, ХАР: ${creature.charisma}
            </div>
        </div>`;
    }

    return html;
}

function closeModal() {
    document.getElementById('modal').classList.remove('show');
}
