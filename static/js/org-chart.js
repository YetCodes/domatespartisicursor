(function () {
  const viewport = document.getElementById("org-viewport");
  const canvas = document.getElementById("org-canvas");
  if (!viewport || !canvas) return;

  let scale = 1;
  let panX = 0;
  let panY = 0;
  let dragging = false;
  let startX, startY;

  function applyTransform() {
    canvas.style.transform = `translate(${panX}px, ${panY}px) scale(${scale})`;
  }

  viewport.addEventListener("mousedown", (e) => {
    if (e.target.closest("button, input, textarea")) return;
    dragging = true;
    startX = e.clientX - panX;
    startY = e.clientY - panY;
    viewport.style.cursor = "grabbing";
  });
  window.addEventListener("mouseup", () => {
    dragging = false;
    viewport.style.cursor = "grab";
  });
  window.addEventListener("mousemove", (e) => {
    if (!dragging) return;
    panX = e.clientX - startX;
    panY = e.clientY - startY;
    applyTransform();
  });

  viewport.addEventListener("wheel", (e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.08 : 0.08;
    scale = Math.min(2, Math.max(0.4, scale + delta));
    applyTransform();
  }, { passive: false });

  document.getElementById("org-zoom-in")?.addEventListener("click", () => {
    scale = Math.min(2, scale + 0.15);
    applyTransform();
  });
  document.getElementById("org-zoom-out")?.addEventListener("click", () => {
    scale = Math.max(0.4, scale - 0.15);
    applyTransform();
  });
  document.getElementById("org-zoom-reset")?.addEventListener("click", () => {
    scale = 1;
    panX = 0;
    panY = 0;
    applyTransform();
  });

  const isChairman = document.body.dataset.chairman === "1";
  if (!isChairman) return;

  async function postOrg(data) {
    await fetch("/api/admin/org", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  }

  async function uploadImage(fileInput) {
    if (!fileInput?.files?.[0]) return null;
    const fd = new FormData();
    fd.append("file", fileInput.files[0]);
    const res = await fetch("/api/admin/upload", { method: "POST", body: fd });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "Yükleme hatası");
    return data.url;
  }

  const modal = document.getElementById("org-edit-modal");
  let currentNodeId = null;

  function openModal(id, name, desc, img) {
    currentNodeId = id;
    document.getElementById("org-edit-id").value = id;
    document.getElementById("org-modal-name").value = name || "";
    document.getElementById("org-modal-desc").value = desc || "";
    document.getElementById("org-modal-image").value = img || "";
    modal?.classList.add("open");
  }

  document.querySelectorAll(".org-edit-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const node = btn.closest(".org-node");
      openModal(
        btn.dataset.id,
        node.querySelector(".node-name")?.textContent,
        node.querySelector(".node-desc")?.textContent,
        node.querySelector("img")?.src || ""
      );
    });
  });

  document.querySelectorAll(".org-add-child-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      document.getElementById("org-parent-id").value = btn.dataset.id;
      document.getElementById("org-admin-panel")?.scrollIntoView({ behavior: "smooth" });
    });
  });

  document.getElementById("org-add-btn")?.addEventListener("click", async () => {
    const file = document.querySelector("#org-admin-panel .upload-file");
    let imageUrl = document.getElementById("org-image-url")?.value || "";
    if (file?.files?.[0]) imageUrl = (await uploadImage(file)) || imageUrl;

    const parentVal = document.getElementById("org-parent-id").value;
    const memberId = document.getElementById("org-member-id")?.value;
    await postOrg({
      action: "add",
      parent_id: parentVal ? parseInt(parentVal, 10) : null,
      title: document.getElementById("org-title").value,
      person_name: document.getElementById("org-person-name").value,
      description: document.getElementById("org-description").value,
      user_id: memberId ? parseInt(memberId, 10) : null,
      image_url: imageUrl
    });
    location.reload();
  });

  document.getElementById("org-modal-save")?.addEventListener("click", async () => {
    const file = document.querySelector("#org-edit-modal .upload-file");
    let imageUrl = document.getElementById("org-modal-image")?.value || "";
    if (file?.files?.[0]) imageUrl = (await uploadImage(file)) || imageUrl;

    const node = document.querySelector(`.org-node[data-id="${currentNodeId}"]`);
    const memberSel = document.getElementById("org-modal-member");
    await postOrg({
      action: "update",
      id: parseInt(currentNodeId, 10),
      title: node?.querySelector(".node-title")?.textContent,
      person_name: document.getElementById("org-modal-name").value,
      description: document.getElementById("org-modal-desc").value,
      user_id: memberSel?.value ? parseInt(memberSel.value, 10) : null,
      image_url: imageUrl
    });
    location.reload();
  });

  document.getElementById("org-modal-delete")?.addEventListener("click", async () => {
    if (!confirm("Kaldırılsın mı?")) return;
    await postOrg({ action: "delete", id: parseInt(currentNodeId, 10) });
    location.reload();
  });

  document.getElementById("org-modal-close")?.addEventListener("click", () => modal?.classList.remove("open"));
})();
