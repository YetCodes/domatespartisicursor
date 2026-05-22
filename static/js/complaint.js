(function () {
  const body = document.body;
  const logo = document.getElementById("dop-logo");
  const eyesWrap = document.getElementById("dop-eyes");
  const eyeLeft = document.querySelector("#eye-left .pupil");
  const eyeRight = document.querySelector("#eye-right .pupil");
  const textarea = document.getElementById("complaint-body");
  const form = document.getElementById("complaint-form");
  const priorityValue = document.getElementById("priority-value");
  const modal = document.getElementById("kurultay-modal");
  const flameCanvas = document.getElementById("flame-canvas");
  const cornerCanvas = document.getElementById("corner-flame-canvas");
  const identityInputs = document.querySelectorAll('input[name="identity"]');

  let flameAnim = null;
  let cornerAnim = null;
  let eyesVisible = false;

  function activateDarkTheme() {
    body.classList.add("theme-dark");
    setTimeout(morphToEyes, 350);
  }

  function morphToEyes() {
    if (!logo || !eyesWrap) return;
    logo.classList.add("hidden");
    eyesWrap.classList.add("visible");
    eyesVisible = true;
  }

  function getPriority(identity) {
    return identity === "anonim" ? 3 : 5;
  }

  function updateIdentityMode() {
    const selected = document.querySelector('input[name="identity"]:checked');
    const identity = selected ? selected.value : "vatandas";
    const priority = getPriority(identity);
    if (priorityValue) priorityValue.textContent = String(priority);

    if (identity === "uye") {
      body.classList.add("theme-void");
      startFlameEffect(flameCanvas);
      startCornerFlames();
    } else {
      body.classList.remove("theme-void");
      stopFlameEffect(flameCanvas);
      stopCornerFlames();
      if (body.classList.contains("theme-dark")) {
        body.style.background = "#0a0a0a";
      }
    }
  }

  function movePupils(clientX, clientY) {
    if (!eyesVisible || !eyeLeft || !eyeRight) return;
    [eyeLeft, eyeRight].forEach((pupil) => {
      const eye = pupil.parentElement;
      const rect = eye.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const dx = (clientX - cx) / rect.width;
      const dy = (clientY - cy) / rect.height;
      const max = 14;
      const x = Math.max(-max, Math.min(max, dx * max * 2));
      const y = Math.max(-max, Math.min(max, dy * max * 2));
      pupil.style.transform = `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`;
    });
  }

  document.addEventListener("mousemove", (e) => movePupils(e.clientX, e.clientY));

  textarea?.addEventListener("keydown", () => {
    const len = textarea.value.length;
    movePupils(window.innerWidth / 2 + Math.sin(len * 0.5) * 100, window.innerHeight / 2 + Math.cos(len * 0.35) * 50);
  });

  textarea?.addEventListener("input", () => {
    const len = textarea.value.length;
    movePupils(220 + len * 4, 280 + (len % 12) * 6);
  });

  identityInputs.forEach((input) => input.addEventListener("change", updateIdentityMode));

  function startFlameEffect(canvas) {
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const particles = [];
    let running = true;

    function spawn() {
      for (let i = 0; i < 4; i++) {
        particles.push({
          x: canvas.width / 2 + (Math.random() - 0.5) * 60,
          y: canvas.height - 10,
          vx: (Math.random() - 0.5) * 2,
          vy: -1.5 - Math.random() * 2.5,
          life: 1,
          size: 5 + Math.random() * 10,
        });
      }
    }

    function draw() {
      if (!running) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      if (Math.random() > 0.25) spawn();
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        p.life -= 0.018;
        p.size *= 0.985;
        const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.size);
        g.addColorStop(0, `rgba(255, 200, 80, ${p.life})`);
        g.addColorStop(0.5, `rgba(255, 60, 20, ${p.life * 0.5})`);
        g.addColorStop(1, "transparent");
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
        if (p.life <= 0) particles.splice(i, 1);
      }
      flameAnim = requestAnimationFrame(draw);
    }
    stopFlameEffect(canvas);
    draw();
    canvas._stop = () => { running = false; };
  }

  function stopFlameEffect(canvas) {
    if (flameAnim) cancelAnimationFrame(flameAnim);
    flameAnim = null;
    if (canvas?._stop) canvas._stop();
    canvas?.getContext("2d")?.clearRect(0, 0, canvas.width, canvas.height);
  }

  function startCornerFlames() {
    if (!cornerCanvas) return;
    cornerCanvas.width = window.innerWidth;
    cornerCanvas.height = window.innerHeight;
    const ctx = cornerCanvas.getContext("2d");
    const sparks = [];
    let running = true;

    const corners = [
      [0, cornerCanvas.height],
      [cornerCanvas.width, cornerCanvas.height],
      [0, 0],
      [cornerCanvas.width, 0],
    ];

    function spawn() {
      const [cx, cy] = corners[Math.floor(Math.random() * corners.length)];
      const tx = cornerCanvas.width / 2;
      const ty = cornerCanvas.height / 2;
      const angle = Math.atan2(ty - cy, tx - cx);
      sparks.push({
        x: cx,
        y: cy,
        vx: Math.cos(angle) * (1 + Math.random() * 2),
        vy: Math.sin(angle) * (1 + Math.random() * 2),
        life: 1,
        size: 3 + Math.random() * 6,
      });
    }

    function draw() {
      if (!running) return;
      ctx.clearRect(0, 0, cornerCanvas.width, cornerCanvas.height);
      if (Math.random() > 0.4) spawn();
      for (let i = sparks.length - 1; i >= 0; i--) {
        const p = sparks[i];
        p.x += p.vx;
        p.y += p.vy;
        p.life -= 0.012;
        ctx.fillStyle = `rgba(255, ${80 + Math.random() * 100}, 20, ${p.life})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
        if (p.life <= 0) sparks.splice(i, 1);
      }
      cornerAnim = requestAnimationFrame(draw);
    }
    stopCornerFlames();
    draw();
    cornerCanvas._stop = () => { running = false; };
  }

  function stopCornerFlames() {
    if (cornerAnim) cancelAnimationFrame(cornerAnim);
    cornerAnim = null;
    if (cornerCanvas?._stop) cornerCanvas._stop();
    cornerCanvas?.getContext("2d")?.clearRect(0, 0, cornerCanvas.width, cornerCanvas.height);
  }

  function openModal() { modal?.classList.add("open"); }
  function closeModal() { modal?.classList.remove("open"); }

  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const selected = document.querySelector('input[name="identity"]:checked');
    const identity = selected ? selected.value : "anonim";
    const res = await fetch("/api/complaint", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identity_type: identity, body: textarea.value.trim() }),
    });
    const data = await res.json();
    if (!data.ok) {
      alert(data.error || "Hata");
      return;
    }
    if (data.show_congress_modal) openModal();
    else {
      alert("Şikayet kaydedildi. Öncelik: " + data.priority);
      form.reset();
      updateIdentityMode();
    }
  });

  document.getElementById("kurultay-hayir")?.addEventListener("click", closeModal);
  document.getElementById("kurultay-baskan")?.addEventListener("click", async () => {
    await fetch("/api/congress/ask-chairman", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: "Genel Başkana Sor seçildi." }),
    });
    closeModal();
    alert("Genel Başkana bildirim gönderildi.");
  });
  document.getElementById("kurultay-evet")?.addEventListener("click", async () => {
    const res = await fetch("/api/congress/start", { method: "POST", headers: { "Content-Type": "application/json" } });
    const data = await res.json();
    closeModal();
    if (data.ok) {
      alert("Kurultay çağrısı başlatıldı (%61 evet gerekli).");
      window.dispatchEvent(new CustomEvent("congress-started"));
    } else alert(data.error || "Üye girişi gerekli olabilir.");
  });

  activateDarkTheme();
  updateIdentityMode();
})();
