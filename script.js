let allSearchableVideos = [];
// Alustetaan haku heti kun sivu latautuu
document.addEventListener("DOMContentLoaded", function() {
    // Haetaan data globaalista muuttujasta (joka on määritelty HTML:ssä)
    if (typeof videoData !== 'undefined') {
        Object.values(videoData).forEach(list => {
            allSearchableVideos = allSearchableVideos.concat(list);
        });
        allSearchableVideos = [...new Map(allSearchableVideos.map(item => [item.id, item])).values()];
    }

    if(document.getElementById('home-video-list')) {
        updateHomeSort();
    }
});

let currentCategory = null;

function formatDate(isoString) {
    if(!isoString) return "";
    const d = new Date(isoString);
    return d.getDate() + "." + (d.getMonth()+1) + "." + d.getFullYear();
}

function createVideoCard(v) {
    return `
        <div>
            <div class="lite-embed" style="background-image: url('https://img.youtube.com/vi/${v.id}/mqdefault.jpg');" onclick="loadVideo(this, '${v.id}')">
                <div class="play-btn"></div>
            </div>
            <div class="vid-info">
                <h4>${v.title}</h4>
                <div class="vid-meta">${v.channel} &bull; ${v.views.toLocaleString()} katselua &bull; ${formatDate(v.date)}</div>
            </div>
        </div>`;
}

function loadVideo(el, id) {
    el.innerHTML = `<iframe src="https://www.youtube.com/embed/${id}?autoplay=1" style="position:absolute; top:0; left:0; width:100%; height:100%; border:none;" allow="autoplay; encrypted-media" allowfullscreen></iframe>`;
}

function renderList(containerId, list) {
    const container = document.getElementById(containerId);
    if(!container) return;
    if(list.length === 0) {
        container.innerHTML = '<div style="padding:20px; color:var(--text-dim); text-align:center; grid-column: 1 / -1;">Ei hakutuloksia.</div>';
    } else {
        container.innerHTML = list.map(v => createVideoCard(v)).join('');
    }
}

function sortList(list, criteria) {
    return [...list].sort((a,b) => {
        if(criteria === 'views') return b.views - a.views;
        if(criteria === 'newest') return new Date(b.date) - new Date(a.date);
        return 0; 
    });
}

function searchVideos() {
    const query = document.getElementById('videoSearch').value.toLowerCase();
    const listTitle = document.getElementById('list-title');
    const sortSelect = document.getElementById('home-sort');

    if (query.length < 2) {
        listTitle.innerText = "🔥 Viikon katsotuimmat";
        sortSelect.style.display = 'block';
        updateHomeSort();
        return;
    }

    listTitle.innerText = "🔍 Hakutulokset";
    sortSelect.style.display = 'none';

    const results = allSearchableVideos.filter(v => 
        v.title.toLowerCase().includes(query) || 
        v.channel.toLowerCase().includes(query)
    );
    
    renderList('home-video-list', results);
}

function updateHomeSort() {
    // Varmistetaan että topVideos on olemassa (HTML:stä)
    if (typeof topVideos !== 'undefined') {
        const criteria = document.getElementById('home-sort').value;
        const sorted = sortList(topVideos, criteria);
        renderList('home-video-list', sorted);
    }
}

function showCategory(g) {
    currentCategory = g;
    document.getElementById('home-content').style.display='none';
    document.getElementById('view-container').classList.add('active');
    document.getElementById('cat-title').innerText = g;
    updateCatSort();
    window.scrollTo(0,0);
}

function updateCatSort() {
    if(!currentCategory || typeof videoData === 'undefined') return;
    const criteria = document.getElementById('cat-sort').value;
    const list = videoData[currentCategory] || [];
    const sorted = sortList(list, criteria);
    renderList('video-grid', sorted);
}

function showHome() { 
    document.getElementById('view-container').classList.remove('active'); 
    document.getElementById('home-content').style.display='block'; 
    document.getElementById('videoSearch').value = '';
    searchVideos(); 
}

// Kalenterin filtterit
let currentFilters = { sarja: 'all', laji: 'all' };
function updateFilters(type, value, btn) {
    btn.parentElement.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentFilters[type] = value;
    applyFilters();
}
function applyFilters() {
    const rows = document.querySelectorAll('#calendarTable tbody tr');
    rows.forEach(row => {
        const s = row.getAttribute('data-sarja');
        const l = row.getAttribute('data-laji');
        const sMatch = (currentFilters.sarja === 'all' || s === currentFilters.sarja);
        const lMatch = (currentFilters.laji === 'all' || l === currentFilters.laji);
        row.style.display = (sMatch && lMatch) ? '' : 'none';
    });
}