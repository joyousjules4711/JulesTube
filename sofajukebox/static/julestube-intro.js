(() => {
  "use strict";

  const STORAGE_KEY = "julestubeIntroPlayed";
  const intro = document.getElementById("jt-intro");

  if (!intro) return;

  const video = document.getElementById("jt-intro-video");
  const skipButton = document.getElementById("jt-intro-skip");
  const soundButton = document.getElementById("jt-intro-sound");

  let finished = false;
  let safetyTimer;

  const removeIntro = () => {
    intro.remove();
    document.body.classList.remove("jt-intro-active");
  };

  const finishIntro = () => {
    if (finished) return;
    finished = true;

    window.clearTimeout(safetyTimer);
    sessionStorage.setItem(STORAGE_KEY, "1");
    intro.classList.add("jt-intro-leaving");
    window.setTimeout(removeIntro, 720);
  };

  if (sessionStorage.getItem(STORAGE_KEY) === "1") {
    removeIntro();
    return;
  }

  document.body.classList.add("jt-intro-active");

  skipButton?.addEventListener("click", finishIntro);
  video?.addEventListener("ended", finishIntro);
  video?.addEventListener("error", finishIntro);

  soundButton?.addEventListener("click", async () => {
    if (!video) return;

    video.muted = !video.muted;
    soundButton.textContent = video.muted ? "Ton einschalten" : "Ton ausschalten";
    soundButton.setAttribute("aria-pressed", String(!video.muted));

    try {
      await video.play();
    } catch {
      // Der Browser kann die Wiedergabe blockieren.
    }
  });

  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") finishIntro();
  });

  safetyTimer = window.setTimeout(finishIntro, 20000);

  video?.play().catch(() => {
    // Bei blockiertem Autoplay bleibt "Überspringen" verfügbar.
  });
})();
