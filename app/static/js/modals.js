function openDeleteModal(userId) {
    const modal = document.getElementById('deleteModal');
    const form = document.getElementById('deleteUserForm');
    form.action = `/users/delete/${userId}`;
    modal.classList.remove('hidden');
  }
  
  function closeDeleteModal() {
    document.getElementById('deleteModal').classList.add('hidden');
  }
  