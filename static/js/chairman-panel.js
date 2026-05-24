(function () {
  document.querySelectorAll(".chairman-tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".chairman-tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".chairman-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(btn.dataset.panel)?.classList.add("active");
    });
  });

  document.getElementById("cms-save-all")?.addEventListener("click", async () => {
    const payload = {
      party_name: document.getElementById("cms-party_name").value,
      party_short: document.getElementById("cms-party_short").value,
      chairman: document.getElementById("cms-chairman").value,
      vision_text: document.getElementById("cms-vision_text").value,
      nav_home: document.getElementById("cms-nav_home").value,
      nav_news: document.getElementById("cms-nav_news").value,
      nav_complaint: document.getElementById("cms-nav_complaint").value,
      nav_members: document.getElementById("cms-nav_members").value,
      nav_promises: document.getElementById("cms-nav_promises").value,
      nav_org: document.getElementById("cms-nav_org").value,
      cta_member: document.getElementById("cms-cta_member").value,
      cta_donate: document.getElementById("cms-cta_donate").value,
      cta_volunteer: document.getElementById("cms-cta_volunteer").value,
      chairman_message_title: document.getElementById("cms-chairman_message_title").value,
      chairman_message_body: document.getElementById("cms-chairman_message_body").value,
      dop_tv_title: document.getElementById("cms-dop_tv_title").value,
      dop_tv_description: document.getElementById("cms-dop_tv_description").value,
    };
    document.querySelectorAll(".section-cb").forEach((cb) => {
      payload[cb.dataset.key] = cb.checked ? "1" : "0";
    });
    const res = await fetch("/api/admin/cms", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.ok) {
      alert("Site ayarları kaydedildi. Ana sayfayı yenileyerek bölüm değişikliklerini görün.");
    } else alert("Kayıt hatası");
  });

  async function changeRole(select) {
    const res = await fetch("/api/admin/user-role", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: parseInt(select.dataset.userId, 10),
        role: select.value,
      }),
    });
    const data = await res.json();
    if (data.ok) {
      alert(`Rütbe güncellendi: ${data.role_label}`);
      select.dataset.current = select.value;
    } else {
      alert(data.error || "Hata");
      select.value = select.dataset.current;
    }
  }

  document.querySelectorAll(".panel-role-select").forEach((sel) => {
    sel.addEventListener("change", () => changeRole(sel));
  });

  document.querySelectorAll(".user-delete").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm("Kullanıcıyı tamamen silmek istediğinize emin misiniz? Bu işlem geri alınamaz.")) return;
      const res = await fetch(`/api/admin/user/${btn.dataset.id}`, { method: "DELETE" });
      const data = await res.json();
      if (data.ok) {
        alert("Kullanıcı başarıyla silindi.");
        btn.closest("tr").remove();
      } else {
        alert(data.error || "Hata oluştu.");
      }
    });
  });
})();
