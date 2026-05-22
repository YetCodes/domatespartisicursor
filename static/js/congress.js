(function () {
  const banner = document.getElementById("congress-banner");
  const btnYes = document.getElementById("congress-vote-yes");
  const btnNo = document.getElementById("congress-vote-no");
  const role = document.body.dataset.userRole;
  const loggedIn = document.body.dataset.loggedIn === "1";
  const canVote = loggedIn && (role === "member" || role === "admin");

  async function checkCongress() {
    if (!canVote) return;
    const res = await fetch("/api/congress/active");
    const data = await res.json();
    if (data.active && !data.voted && !data.passed) {
      banner?.classList.add("visible");
    } else {
      banner?.classList.remove("visible");
    }
  }

  async function vote(v) {
    const res = await fetch("/api/congress/vote", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ vote: v }),
    });
    const data = await res.json();
    if (data.ok) {
      banner?.classList.remove("visible");
      if (data.passed) alert("Kurultay kararı GEÇTİ! Parti resmi olarak kurultaya gidiyor.");
      else alert(`Oy kaydedildi. Evet: ${data.yes_votes} · Hayır: ${data.no_votes}`);
    } else alert(data.error || "Oy kullanılamadı");
  }

  btnYes?.addEventListener("click", () => vote("yes"));
  btnNo?.addEventListener("click", () => vote("no"));
  window.addEventListener("congress-started", checkCongress);
  checkCongress();
  setInterval(checkCongress, 8000);
})();
