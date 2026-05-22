(function () {
  const navWrap = document.getElementById("floating-nav");
  const navToggle = document.getElementById("nav-toggle");
  const mainNav = document.getElementById("main-nav");

  window.addEventListener("scroll", () => {
    if (!navWrap) return;
    navWrap.classList.toggle("shrunk", window.scrollY > 80);
  });

  navToggle?.addEventListener("click", (e) => {
    e.stopPropagation();
    mainNav?.classList.toggle("open");
  });

  document.addEventListener("click", (e) => {
    if (mainNav?.classList.contains("open") && !mainNav.contains(e.target) && e.target !== navToggle) {
      mainNav.classList.remove("open");
    }
  });

  const reveals = document.querySelectorAll(".reveal");
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          e.target.classList.add("visible");
          observer.unobserve(e.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
  );
  reveals.forEach((el) => observer.observe(el));
})();
