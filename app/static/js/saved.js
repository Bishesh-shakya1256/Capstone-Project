// Per-user saved-plants helpers (localStorage)

function _savedKey() {
  try {
    const u = JSON.parse(sessionStorage.getItem('gsUser') || 'null');
    return 'gsSaved_' + (u ? u.email : 'guest');
  } catch { return 'gsSaved_guest'; }
}

function getSavedPlants() {
  try { return JSON.parse(localStorage.getItem(_savedKey()) || '[]'); } catch { return []; }
}

function isSaved(plantId) {
  return getSavedPlants().some(p => p.plant_id === plantId);
}

function toggleSaved(plant) {
  const list = getSavedPlants();
  const idx  = list.findIndex(p => p.plant_id === plant.plant_id);
  if (idx >= 0) { list.splice(idx, 1); }
  else          { list.push(plant); }
  localStorage.setItem(_savedKey(), JSON.stringify(list));
  return idx < 0; // true = now saved
}

function removeSaved(plantId) {
  const list = getSavedPlants().filter(p => p.plant_id !== plantId);
  localStorage.setItem(_savedKey(), JSON.stringify(list));
}
