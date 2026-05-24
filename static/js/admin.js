async function uploadImage(fileInput) {
  if (!fileInput?.files?.[0]) return null;
  const fd = new FormData();
  fd.append("file", fileInput.files[0]);
  const res = await fetch("/api/admin/upload", { method: "POST", body: fd });
  const data = await res.json();
  if (!data.ok) throw new Error(data.error || "Yükleme hatası");
  return data.url;
}

function bindUploadInputs() {
  document.querySelectorAll(".upload-file, input[type=file][data-target], input[type=file][data-target-img]").forEach((input) => {
    input.addEventListener("change", async () => {
      const isVideo = input.files[0]?.type.startsWith('video/');
      const sel = input.dataset.target;
      const target = sel ? document.querySelector(sel) : null;
      const targetImg = input.dataset.targetImg ? document.querySelector(input.dataset.targetImg) : null;
      const targetVid = input.dataset.targetVid ? document.querySelector(input.dataset.targetVid) : null;
      
      try {
        const url = await uploadImage(input);
        if (url) {
          if (targetImg && targetVid) {
             if (isVideo) targetVid.value = url;
             else targetImg.value = url;
          } else if (target) {
             target.value = url;
          }
          alert("Dosya yüklendi.");
        }
      } catch (e) {
        alert(e.message);
      }
      input.value = "";
    });
  });
}

bindUploadInputs();

async function postJson(url, data) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

const cmsSaveBtn = document.getElementById("cms-save-all");
if (cmsSaveBtn) {
  cmsSaveBtn.addEventListener("click", async () => {
    const data = {};
    
    // Tüm text ve textarea'ları topla
    document.querySelectorAll("input[id^='cms-'], textarea[id^='cms-']").forEach(el => {
      const key = el.id.replace("cms-", "");
      if (key && key !== "save-all") data[key] = el.value;
    });

    // Checkbox'ları topla
    document.querySelectorAll(".section-cb").forEach(cb => {
      data[cb.dataset.key] = cb.checked ? "1" : "0";
    });

    await postJson("/api/admin/cms", data);
    alert("Tüm site ayarları kaydedildi.");
  });
}

document.getElementById("new-slide-add")?.addEventListener("click", async () => {
  const file = document.getElementById("new-slide-file");
  let imageUrl = document.getElementById("new-slide-url").value;
  if (file?.files?.[0]) imageUrl = (await uploadImage(file)) || imageUrl;
  await postJson("/api/admin/carousel", {
    action: "add",
    image_url: imageUrl,
    headline: document.getElementById("new-slide-headline").value,
  });
  location.reload();
});

document.querySelectorAll(".slide-update").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const row = btn.closest(".form-row");
    await postJson("/api/admin/carousel", {
      action: "update",
      id: parseInt(btn.dataset.id, 10),
      image_url: row.querySelector(".slide-image").value,
      headline: row.querySelector(".slide-headline").value,
    });
    alert("Manşet güncellendi");
  });
});

document.querySelectorAll(".slide-delete").forEach((btn) => {
  btn.addEventListener("click", async () => {
    if (!confirm("Silinsin mi?")) return;
    await postJson("/api/admin/carousel", { action: "delete", id: parseInt(btn.dataset.id, 10) });
    location.reload();
  });
});

document.getElementById("new-promise-add")?.addEventListener("click", async () => {
  await postJson("/api/admin/promises", {
    action: "add",
    title: document.getElementById("new-promise-title").value,
    body: document.getElementById("new-promise-body").value,
  });
  location.reload();
});

document.querySelectorAll(".promise-update").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const id = btn.dataset.id;
    await postJson("/api/admin/promises", {
      action: "update",
      id: parseInt(id, 10),
      title: document.querySelector(`.promise-title[data-id="${id}"]`).value,
      body: document.querySelector(`.promise-body[data-id="${id}"]`).value,
    });
    alert("Vaat güncellendi");
  });
});

document.querySelectorAll(".promise-delete").forEach((btn) => {
  btn.addEventListener("click", async () => {
    if (!confirm("Silinsin mi?")) return;
    await postJson("/api/admin/promises", { action: "delete", id: parseInt(btn.dataset.id, 10) });
    location.reload();
  });
});

document.getElementById("mark-notifications-read")?.addEventListener("click", async () => {
  await postJson("/api/admin/notifications/read", {});
  location.reload();
});

document.getElementById("new-agenda-add")?.addEventListener("click", async () => {
  const file = document.getElementById("new-agenda-file");
  let imageUrl = document.getElementById("new-agenda-image").value;
  if (file?.files?.[0]) imageUrl = (await uploadImage(file)) || imageUrl;
  await postJson("/api/admin/agenda", {
    action: "add",
    title: document.getElementById("new-agenda-title").value,
    body: document.getElementById("new-agenda-body").value,
    image_url: imageUrl,
  });
  location.reload();
});

document.querySelectorAll(".agenda-update").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const id = btn.dataset.id;
    await postJson("/api/admin/agenda", {
      action: "update",
      id: parseInt(id, 10),
      title: document.querySelector(`.agenda-title[data-id="${id}"]`).value,
      body: document.querySelector(`.agenda-body[data-id="${id}"]`).value,
      image_url: document.querySelector(`.agenda-image[data-id="${id}"]`).value,
    });
    alert("Gündem güncellendi");
  });
});

document.querySelectorAll(".agenda-delete").forEach((btn) => {
  btn.addEventListener("click", async () => {
    if (!confirm("Silinsin mi?")) return;
    await postJson("/api/admin/agenda", { action: "delete", id: parseInt(btn.dataset.id, 10) });
    location.reload();
  });
});

document.getElementById("new-news-add")?.addEventListener("click", async () => {
  await postJson("/api/admin/news", {
    action: "add",
    title: document.getElementById("new-news-title").value,
    excerpt: document.getElementById("new-news-excerpt").value,
    image_url: document.getElementById("new-news-image").value,
  });
  location.reload();
});

document.querySelectorAll(".news-update").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const id = btn.dataset.id;
    await postJson("/api/admin/news", {
      action: "update",
      id: parseInt(id, 10),
      title: document.querySelector(`.news-title[data-id="${id}"]`).value,
      excerpt: document.querySelector(`.news-excerpt[data-id="${id}"]`).value,
      image_url: document.querySelector(`.news-image[data-id="${id}"]`).value,
    });
    alert("Haber güncellendi");
  });
});

document.querySelectorAll(".news-delete").forEach((btn) => {
  btn.addEventListener("click", async () => {
    if (!confirm("Silinsin mi?")) return;
    await postJson("/api/admin/news", { action: "delete", id: parseInt(btn.dataset.id, 10) });
    location.reload();
  });
});

document.getElementById("new-press-add")?.addEventListener("click", async () => {
  await postJson("/api/admin/press", {
    action: "add",
    title: document.getElementById("new-press-title").value,
    body: document.getElementById("new-press-body").value,
  });
  location.reload();
});

document.querySelectorAll(".press-update").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const id = btn.dataset.id;
    await postJson("/api/admin/press", {
      action: "update",
      id: parseInt(id, 10),
      title: document.querySelector(`.press-title[data-id="${id}"]`).value,
      body: document.querySelector(`.press-body[data-id="${id}"]`).value,
    });
    location.reload();
  });
});

document.querySelectorAll(".press-delete").forEach((btn) => {
  btn.addEventListener("click", async () => {
    if (!confirm("Silinsin mi?")) return;
    await postJson("/api/admin/press", { action: "delete", id: parseInt(btn.dataset.id, 10) });
    location.reload();
  });
});

document.getElementById("new-event-add")?.addEventListener("click", async () => {
  await postJson("/api/admin/events", {
    action: "add",
    title: document.getElementById("new-event-title").value,
    location: document.getElementById("new-event-loc").value,
    event_date: document.getElementById("new-event-date").value,
  });
  location.reload();
});

document.querySelectorAll(".event-update").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const id = btn.dataset.id;
    await postJson("/api/admin/events", {
      action: "update",
      id: parseInt(id, 10),
      title: document.querySelector(`.event-title[data-id="${id}"]`).value,
      location: document.querySelector(`.event-loc[data-id="${id}"]`).value,
      event_date: document.querySelector(`.event-date[data-id="${id}"]`).value,
    });
    location.reload();
  });
});

document.querySelectorAll(".event-delete").forEach((btn) => {
  btn.addEventListener("click", async () => {
    if (!confirm("Silinsin mi?")) return;
    await postJson("/api/admin/events", { action: "delete", id: parseInt(btn.dataset.id, 10) });
    location.reload();
  });
});

document.getElementById("new-media-add")?.addEventListener("click", async () => {
  const file = document.getElementById("new-media-file");
  let imageUrl = document.getElementById("new-media-image").value;
  if (file?.files?.[0]) imageUrl = (await uploadImage(file)) || imageUrl;
  await postJson("/api/admin/media", {
    action: "add",
    title: document.getElementById("new-media-title").value,
    image_url: imageUrl,
    video_url: document.getElementById("new-media-video").value,
    media_type: document.getElementById("new-media-type").value,
  });
  location.reload();
});

document.querySelectorAll(".media-update").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const id = btn.dataset.id;
    await postJson("/api/admin/media", {
      action: "update",
      id: parseInt(id, 10),
      title: document.querySelector(`.media-title[data-id="${id}"]`).value,
      media_type: document.querySelector(`.media-type[data-id="${id}"]`).value,
      image_url: document.querySelector(`.media-image[data-id="${id}"]`).value,
      video_url: document.querySelector(`.media-video[data-id="${id}"]`).value,
    });
    alert("Medya güncellendi");
  });
});

document.querySelectorAll(".media-delete").forEach((btn) => {
  btn.addEventListener("click", async () => {
    if (!confirm("Silinsin mi?")) return;
    await postJson("/api/admin/media", { action: "delete", id: parseInt(btn.dataset.id, 10) });
    location.reload();
  });
});

document.getElementById("org-add-btn")?.addEventListener("click", async () => {
  const file = document.getElementById("org-image-file");
  let imageUrl = document.getElementById("org-image-url")?.value || "";
  if (file?.files?.[0]) imageUrl = (await uploadImage(file)) || imageUrl;
  
  const parentVal = document.getElementById("org-parent-id").value;
  const memberId = document.getElementById("org-member-id")?.value;
  
  await postJson("/api/admin/org", {
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
