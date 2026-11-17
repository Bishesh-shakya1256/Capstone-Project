const API_URL = "/api/plants";

const tableBody = document.querySelector("tbody");
const totalPlants = document.querySelector(".stat-value");
const plantSearchInput = document.getElementById("plant-search");

let allPlants = [];

function escapeHtml(str) {
  return String(str ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// Rendering the plants table;
function renderPlants(plants) {
    const rows = plants.map(plant => `
        <tr>
            <td>
                <img src="${escapeHtml(plant.image_url || 'images/recomended-img01.jpg')}"
                width="60" style="border-radius:6px;object-fit:cover" onerror="this.src='images/recomended-img01.jpg'">
            </td>
            <td><div class="plant-name">${escapeHtml(plant.plant_name)}</div></td>
            <td><span class="badge badge-medium">${escapeHtml(plant.maintenance_level || 'Medium')}</span></td>
            <td>
                <div class="actions">
                    <button class="action-btn" title="Edit" onclick="editPlant(${plant.plant_id})">
                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M9.5 2.5l2 2-7 7H2.5V9l7-6.5z"/></svg>
                    </button>
                    <button class="action-btn del" title="Delete" onclick="deletePlant(${plant.plant_id})">
                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 4h10M5 4V2.5h4V4M5.5 6.5v4M8.5 6.5v4M3 4l.8 8h6.4l.8-8"/></svg>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');

    tableBody.innerHTML = rows || '<tr><td colspan="4" style="text-align:center;padding:32px;color:var(--muted)">No plants found.</td></tr>';
    totalPlants.textContent = allPlants.length;

    const footer = document.getElementById('plant-table-footer');
    if (footer) footer.textContent = `${plants.length} plant${plants.length !== 1 ? 's' : ''}`;
}

// Loading all plants section;
async function loadPlants() {
    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error('Server error');
        const data = await response.json();
        allPlants = data.plants || [];
        renderPlants(filterPlants(plantSearchInput ? plantSearchInput.value : ''));

    } catch(error){
        console.error(error);
        tableBody.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:32px;color:var(--muted)">Failed to load plants.</td></tr>';
    }
}

// Filtering plants by name/category/care level;
function filterPlants(query) {
    const q = query.trim().toLowerCase();
    if (!q) return allPlants;
    return allPlants.filter(plant =>
        (plant.plant_name || '').toLowerCase().includes(q) ||
        (plant.category_name || '').toLowerCase().includes(q) ||
        (plant.maintenance_level || '').toLowerCase().includes(q)
    );
}

if (plantSearchInput) {
    plantSearchInput.addEventListener('input', e => {
        renderPlants(filterPlants(e.target.value));
    });
}


// Add plant section;
async function addPlant(data){
    const res = await fetch(API_URL,{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify(data)
    });
    if(!res.ok) throw new Error('Add failed');
}


// Delete plant section;
async function deletePlant(id){
    const confirmed = await confirmToast("Delete this plant?");
    if(!confirmed) return;
    try{
        const res = await fetch(`${API_URL}/${id}`,{method:"DELETE"});
        if(!res.ok) throw new Error('Delete failed');
        loadPlants();
        showToast('Plant deleted.', 'success');
    }catch(error){
        console.error(error);
        showToast('Failed to delete plant. Please try again.', 'error');
    }
}


// Edit plant section;
function editPlant(id){
    const plant = allPlants.find(p => p.plant_id === id);
    if(!plant) return;

    document.getElementById('ep-plant-id').value = id;
    document.getElementById('ep-plant-name').value = plant.plant_name || '';
    document.getElementById('ep-category-name').value = plant.category_name || '';
    document.getElementById('ep-category-id').value = plant.category_id || '';
    document.getElementById('ep-growth-rate').value = plant.growth_rate || '';
    document.getElementById('ep-humidity').value = plant.humidity_requirement || '';
    document.getElementById('ep-light').value = plant.light_requirement || '';
    document.getElementById('ep-maintenance').value = plant.maintenance_level || '';
    document.getElementById('ep-size').value = plant.size_category || '';
    document.getElementById('ep-temperature').value = plant.temperature_range || '';
    document.getElementById('ep-toxicity').value = plant.toxicity_level || '';
    document.getElementById('ep-watering').value = plant.watering_frequency || '';

    document.getElementById('edit-plant-error').style.display = 'none';
    document.getElementById('edit-plant-modal').classList.add('open');
    document.body.style.overflow = 'hidden';
}

function closeEditPlantModal(){
    document.getElementById('edit-plant-modal').classList.remove('open');
    document.body.style.overflow = '';
}

document.getElementById('edit-plant-close').addEventListener('click', closeEditPlantModal);
document.getElementById('edit-plant-cancel').addEventListener('click', closeEditPlantModal);
document.getElementById('edit-plant-modal').addEventListener('click', e=>{
    if(e.target === document.getElementById('edit-plant-modal')) closeEditPlantModal();
});

document.getElementById('edit-plant-form').addEventListener('submit', async function(e){
    e.preventDefault();

    const errEl = document.getElementById('edit-plant-error');
    const submitBtn = this.querySelector('[type="submit"]');
    function showErr(msg){ errEl.textContent = msg; errEl.style.display = 'block'; }
    errEl.style.display = 'none';

    const plantId = document.getElementById('ep-plant-id').value;
    const plantName = document.getElementById('ep-plant-name').value.trim();
    if(!plantName) return showErr('Please enter a plant name.');

    const data = {
        plant_name: plantName,
        category_name: document.getElementById('ep-category-name').value.trim(),
        category_id: document.getElementById('ep-category-id').value ? Number(document.getElementById('ep-category-id').value) : undefined,
        growth_rate: document.getElementById('ep-growth-rate').value.trim(),
        humidity_requirement: document.getElementById('ep-humidity').value.trim(),
        light_requirement: document.getElementById('ep-light').value.trim(),
        maintenance_level: document.getElementById('ep-maintenance').value.trim(),
        size_category: document.getElementById('ep-size').value.trim(),
        temperature_range: document.getElementById('ep-temperature').value.trim(),
        toxicity_level: document.getElementById('ep-toxicity').value.trim(),
        watering_frequency: document.getElementById('ep-watering').value.trim(),
    };

    submitBtn.disabled = true;
    submitBtn.textContent = 'Updating…';

    try{
        const res = await fetch(`${API_URL}/${plantId}`,{
            method:"PUT",
            headers:{"Content-Type":"application/json"},
            body: JSON.stringify(data)
        });
        if(!res.ok) throw new Error('Edit failed');
        closeEditPlantModal();
        loadPlants();
        showToast('Plant updated.', 'success');
    }catch(error){
        console.error(error);
        showErr('Failed to update plant. Please try again.');
    }finally{
        submitBtn.disabled = false;
        submitBtn.textContent = 'Update Plant';
    }
});


// Add Plant modal section;
function openAddPlantModal(){
    document.getElementById('add-plant-form').reset();
    document.getElementById('add-plant-error').style.display = 'none';
    document.getElementById('add-plant-modal').classList.add('open');
    document.body.style.overflow = 'hidden';
    document.getElementById('ap-plant-name').focus();
}

function closeAddPlantModal(){
    document.getElementById('add-plant-modal').classList.remove('open');
    document.body.style.overflow = '';
}

document.querySelector(".add-btn").addEventListener("click", openAddPlantModal);
document.getElementById('add-plant-close').addEventListener('click', closeAddPlantModal);
document.getElementById('add-plant-cancel').addEventListener('click', closeAddPlantModal);
document.getElementById('add-plant-modal').addEventListener('click', e=>{
    if(e.target === document.getElementById('add-plant-modal')) closeAddPlantModal();
});

document.getElementById('add-plant-form').addEventListener('submit', async function(e){
    e.preventDefault();

    const errEl = document.getElementById('add-plant-error');
    const submitBtn = this.querySelector('[type="submit"]');
    function showErr(msg){ errEl.textContent = msg; errEl.style.display = 'block'; }
    errEl.style.display = 'none';

    const plantName = document.getElementById('ap-plant-name').value.trim();
    if(!plantName) return showErr('Please enter a plant name.');

    const data = {
        plant_name: plantName,
        category_name: document.getElementById('ap-category-name').value.trim(),
        category_id: document.getElementById('ap-category-id').value ? Number(document.getElementById('ap-category-id').value) : undefined,
        growth_rate: document.getElementById('ap-growth-rate').value.trim(),
        humidity_requirement: document.getElementById('ap-humidity').value.trim(),
        light_requirement: document.getElementById('ap-light').value.trim(),
        maintenance_level: document.getElementById('ap-maintenance').value.trim(),
        size_category: document.getElementById('ap-size').value.trim(),
        temperature_range: document.getElementById('ap-temperature').value.trim(),
        toxicity_level: document.getElementById('ap-toxicity').value.trim(),
        watering_frequency: document.getElementById('ap-watering').value.trim(),
    };

    submitBtn.disabled = true;
    submitBtn.textContent = 'Adding…';

    try{
        await addPlant(data);
        closeAddPlantModal();
        loadPlants();
        showToast('Plant added.', 'success');
    }catch(error){
        console.error(error);
        showErr('Failed to add plant. Please try again.');
    }finally{
        submitBtn.disabled = false;
        submitBtn.textContent = 'Save Plant';
    }
});


loadPlants();


async function loadPlantStats() {
    try {
        var res = await fetch('/api/admin/plant-stats', { credentials: 'same-origin' });
        if (!res.ok) return;
        var s = await res.json();
        var el;
        el = document.getElementById('stat-total-plants');
        if (el) el.textContent = s.total_plants;
    } catch (e) {}

    var counts = {};
    for (var i = 0; i < localStorage.length; i++) {
        var key = localStorage.key(i);
        if (key.indexOf('gsSaved_') !== 0) continue;
        try {
            var plants = JSON.parse(localStorage.getItem(key) || '[]');
            plants.forEach(function(p) {
                var name = p.plant_name || ('Plant #' + p.plant_id);
                counts[name] = (counts[name] || 0) + 1;
            });
        } catch {}
    }
    var best = null, bestCount = 0;
    for (var name in counts) {
        if (counts[name] > bestCount) { best = name; bestCount = counts[name]; }
    }
    var ms = document.getElementById('stat-most-saved');
    var mc = document.getElementById('stat-most-saved-count');
    if (ms) ms.textContent = best || '—';
    if (mc) mc.textContent = best ? bestCount + ' saves' : 'No saves yet';
}

loadPlantStats();