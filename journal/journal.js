// DOM Elements
const editor = document.getElementById('editor');
const dateStamp = document.getElementById('dateStamp');
const savedIndicator = document.getElementById('savedIndicator');
const entryCount = document.getElementById('entryCount');
const fontBtn = document.getElementById('fontBtn');
const fontPicker = document.getElementById('fontPicker');
const fontGrid = document.getElementById('fontGrid');
const archiveBtn = document.getElementById('archiveBtn');
const archivePanel = document.getElementById('archivePanel');
const entriesList = document.getElementById('entriesList');
const entryView = document.getElementById('entryView');
const limitModal = document.getElementById('limitModal');
const shortcutHint = document.getElementById('shortcutHint');
const newEntryBtn = document.getElementById('newEntryBtn');

// Storage keys
const ENTRIES_KEY = "boredJournalEntries";
const USES_KEY = "boredJournalUses";
const FONT_KEY = "boredJournalFont";

// State
let entries = JSON.parse(localStorage.getItem(ENTRIES_KEY) || "[]");
let uses = Number(localStorage.getItem(USES_KEY) || 0);
let currentFont = localStorage.getItem(FONT_KEY) || 'font-sf-pro';
let autoSaveTimer;
let currentEntryId = Date.now();

// Font options
const fonts = [
    { id: 'font-sf-pro', name: 'SF Pro', preview: 'Clear and focused' },
    { id: 'font-ia-mono', name: 'Monospace', preview: 'Technical precision' },
    { id: 'font-merriweather', name: 'Merriweather', preview: 'Literary elegance' },
    { id: 'font-space', name: 'Space Grotesk', preview: 'Modern energy' },
    { id: 'font-crimson', name: 'Crimson Pro', preview: 'Sophisticated depth' },
    { id: 'font-system-mono', name: 'System Mono', preview: 'Raw authenticity' },
    { id: 'font-georgia', name: 'Georgia', preview: 'Classic warmth' },
    { id: 'font-charter', name: 'Charter', preview: 'Timeless clarity' }
];

// Initialize on load
function init() {
    editor.className = `editor ${currentFont}`;
    editor.focus();
    updateDateStamp();
    updateEntryCount();
    renderFontPicker();
}

// Render font picker options
function renderFontPicker() {
    fonts.forEach(font => {
        const option = document.createElement('div');
        option.className = `font-option ${font.id === currentFont ? 'active' : ''}`;
        option.innerHTML = `
            <div class="font-name">${font.name}</div>
            <div class="font-preview ${font.id}">${font.preview}</div>
        `;
        option.onclick = () => selectFont(font.id, option);
        fontGrid.appendChild(option);
    });
}

// Font selection
function selectFont(fontId, element) {
    currentFont = fontId;
    editor.className = `editor ${fontId}`;
    localStorage.setItem(FONT_KEY, fontId);
    
    document.querySelectorAll('.font-option').forEach(opt => {
        opt.classList.remove('active');
    });
    element.classList.add('active');
    
    fontPicker.classList.remove('show');
    editor.focus();
}

// Update date stamp
function updateDateStamp() {
    const now = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    dateStamp.textContent = now.toLocaleDateString('en-US', options);
}

// Update entry counter
function updateEntryCount() {
    entryCount.textContent = `${uses}/2 free`;
    if (uses >= 2) {
        entryCount.style.color = '#ff8fa3';
        entryCount.style.fontWeight = '600';
    }
}

// Show saved indicator
function showSavedIndicator() {
    savedIndicator.classList.add('show');
    setTimeout(() => {
        savedIndicator.classList.remove('show');
    }, 2000);
}

// Auto-save functionality
function autoSave() {
    clearTimeout(autoSaveTimer);
    autoSaveTimer = setTimeout(() => {
        const content = editor.value.trim();
        if (content && uses < 2) {
            showSavedIndicator();
        }
    }, 2000);
}

// Save entry
function saveEntry() {
    const content = editor.value.trim();
    if (!content) return false;

    if (uses >= 2) {
        limitModal.classList.add('show');
        return false;
    }

    const entry = {
        id: currentEntryId,
        content: content,
        date: new Date().toISOString(),
        font: currentFont
    };

    entries.unshift(entry);
    uses++;
    
    localStorage.setItem(ENTRIES_KEY, JSON.stringify(entries));
    localStorage.setItem(USES_KEY, uses);
    
    editor.value = '';
    currentEntryId = Date.now();
    showSavedIndicator();
    updateEntryCount();
    loadEntries();
    
    return true;
}

// Load entries into archive
function loadEntries() {
    entriesList.innerHTML = '';
    
    if (entries.length === 0) {
        entriesList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">✨</div>
                <div class="empty-state-text">Your thoughts will appear here.<br>Start with what's on your mind right now.</div>
            </div>
        `;
        return;
    }

    entries.forEach(entry => {
        const item = document.createElement('div');
        item.className = 'entry-item';
        
        const preview = entry.content.substring(0, 100) + (entry.content.length > 100 ? '...' : '');
        const timeAgo = getTimeAgo(new Date(entry.date));
        
        item.innerHTML = `
            <div class="entry-title">${preview}</div>
            <div class="entry-meta">${timeAgo}</div>
        `;
        
        item.onclick = () => viewEntry(entry);
        entriesList.appendChild(item);
    });
}

// View single entry
function viewEntry(entry) {
    document.getElementById('entryViewDate').textContent = new Date(entry.date).toLocaleDateString('en-US', {
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: 'numeric', minute: 'numeric'
    });
    document.getElementById('entryViewContent').textContent = entry.content;
    entryView.classList.add('show');
}

// Get relative time
function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`;
    return date.toLocaleDateString();
}

// Show keyboard shortcut hint
function showShortcutHint(text) {
    shortcutHint.textContent = text;
    shortcutHint.classList.add('show');
    setTimeout(() => shortcutHint.classList.remove('show'), 2000);
}

// Event Listeners
editor.addEventListener('input', autoSave);

fontBtn.onclick = () => fontPicker.classList.add('show');
document.getElementById('closeFontPicker').onclick = () => fontPicker.classList.remove('show');

archiveBtn.onclick = () => {
    archivePanel.classList.add('open');
    loadEntries();
};
document.getElementById('closeArchive').onclick = () => archivePanel.classList.remove('open');

document.getElementById('closeEntryView').onclick = () => entryView.classList.remove('show');
document.getElementById('closeLimit').onclick = () => limitModal.classList.remove('show');

newEntryBtn.onclick = () => {
    if (editor.value.trim()) {
        if (saveEntry()) {
            showShortcutHint('Entry saved ✨');
        }
    }
    editor.focus();
};

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // CMD/CTRL + K - Toggle archive
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        archivePanel.classList.toggle('open');
        if (archivePanel.classList.contains('open')) {
            loadEntries();
        }
    }
    
    // CMD/CTRL + F - Font picker
    if ((e.metaKey || e.ctrlKey) && e.key === 'f') {
        e.preventDefault();
        fontPicker.classList.add('show');
    }
    
    // CMD/CTRL + N - New entry (save current)
    if ((e.metaKey || e.ctrlKey) && e.key === 'n') {
        e.preventDefault();
        if (editor.value.trim()) {
            if (saveEntry()) {
                showShortcutHint('⌘N New entry');
            }
        }
    }
    
    // CMD/CTRL + Enter - Save and clear
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        if (saveEntry()) {
            showShortcutHint('⌘↵ Saved');
        }
    }
    
    // ESC - Close all modals
    if (e.key === 'Escape') {
        fontPicker.classList.remove('show');
        archivePanel.classList.remove('open');
        entryView.classList.remove('show');
        limitModal.classList.remove('show');
    }
});

// Click outside to close modals
[fontPicker, entryView, limitModal].forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.remove('show');
    });
});

// Initialize app
init();
