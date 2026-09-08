const cta = document.querySelector(".cta");
if (cta) {
  const reveal = () => cta.classList.add("is-visible");
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    reveal();
  } else {
    const observer = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            reveal();
            obs.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.35 }
    );
    observer.observe(cta);
  }
}