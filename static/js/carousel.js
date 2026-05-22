(function () {
  const track = document.getElementById("carousel-track");
  const dotsContainer = document.getElementById("carousel-dots");
  const headlineEl = document.getElementById("hero-headline");
  if (!track) return;

  const slides = track.querySelectorAll(".carousel-slide");
  const headlines = Array.from(slides).map((s) => {
    const img = s.querySelector("img");
    return img?.getAttribute("data-headline") || img?.getAttribute("alt") || "";
  });

  let index = 0;
  let timer;

  function goTo(i) {
    index = (i + slides.length) % slides.length;
    track.style.transform = `translateX(-${index * 100}%)`;
    slides.forEach((s, j) => s.classList.toggle("active", j === index));
    dotsContainer?.querySelectorAll(".carousel-dot").forEach((d, j) => {
      d.classList.toggle("active", j === index);
    });
    if (headlineEl && headlines[index]) {
      headlineEl.style.opacity = "0";
      setTimeout(() => {
        headlineEl.textContent = headlines[index] || headlineEl.textContent;
        headlineEl.style.opacity = "1";
      }, 200);
    }
  }

  slides.forEach((slide, i) => {
    const dot = document.createElement("button");
    dot.type = "button";
    dot.className = "carousel-dot" + (i === 0 ? " active" : "");
    dot.setAttribute("aria-label", `Slide ${i + 1}`);
    dot.addEventListener("click", () => {
      goTo(i);
      resetTimer();
    });
    dotsContainer?.appendChild(dot);
  });

  function resetTimer() {
    clearInterval(timer);
    timer = setInterval(() => goTo(index + 1), 5500);
  }

  resetTimer();
})();
