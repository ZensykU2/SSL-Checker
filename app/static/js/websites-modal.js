function openDeleteModal(websitesId) {
    const modal = document.getElementById('deleteModal');
    const form = document.getElementById('deleteWebsitesForm');
    form.action = `/delete/${websitesId}`;
    modal.classList.remove('hidden');
  }
  
  function closeDeleteModal() {
    document.getElementById('deleteModal').classList.add('hidden');
  }
  