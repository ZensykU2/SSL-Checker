function openDeleteModal(siteId) {
    const modal = document.getElementById('deleteModal');
    const form = document.getElementById('deleteWebsiteForm');
    form.action = `/my-websites/delete/${siteId}`;
    modal.classList.remove('hidden');
  }
  
  function closeDeleteModal() {
    document.getElementById('deleteModal').classList.add('hidden');
  }
  