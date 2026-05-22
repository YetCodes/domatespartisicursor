async function postJson(url, data) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

document.getElementById("org-add-btn")?.addEventListener("click", async () => {
  const parentVal = document.getElementById("org-parent-id").value;
  await postJson("/api/admin/org", {
    action: "add",
    parent_id: parentVal ? parseInt(parentVal, 10) : null,
    title: document.getElementById("org-title").value,
    person_name: document.getElementById("org-person-name").value,
    description: document.getElementById("org-description").value,
  });
  location.reload();
});

document.querySelectorAll(".org-delete-btn").forEach((btn) => {
  btn.addEventListener("click", async () => {
    if (!confirm("Bu makam kaldırılsın mı?")) return;
    await postJson("/api/admin/org", { action: "delete", id: parseInt(btn.dataset.id, 10) });
    location.reload();
  });
});

document.querySelectorAll(".org-save-btn").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const id = btn.dataset.id;
    const node = btn.closest(".org-node");
    const name = node.querySelector(".org-edit-name").value;
    const desc = node.querySelector(".org-edit-desc").value;
    const title = node.querySelector(".node-title").textContent;
    await postJson("/api/admin/org", {
      action: "update",
      id: parseInt(id, 10),
      title,
      person_name: name,
      description: desc,
    });
    alert("Kadro kaydedildi");
    location.reload();
  });
});
