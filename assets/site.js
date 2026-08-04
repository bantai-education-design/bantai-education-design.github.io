(function () {
  const toggle = document.querySelector(".menu-toggle");
  const menu = document.getElementById("global-menu");

  if (!toggle || !menu) return;

  const closeMenu = () => {
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "メニューを開く");
    document.body.classList.remove("menu-open");
  };

  const openMenu = () => {
    toggle.setAttribute("aria-expanded", "true");
    toggle.setAttribute("aria-label", "メニューを閉じる");
    document.body.classList.add("menu-open");
  };

  toggle.addEventListener("click", () => {
    const isOpen = toggle.getAttribute("aria-expanded") === "true";
    if (isOpen) {
      closeMenu();
    } else {
      openMenu();
    }
  });

  menu.addEventListener("click", (event) => {
    if (event.target.closest("a")) closeMenu();
  });

  document.addEventListener("click", (event) => {
    if (!document.body.classList.contains("menu-open")) return;
    if (event.target.closest(".site-header")) return;
    closeMenu();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeMenu();
  });
})();

(function () {
  const cards = document.querySelectorAll(
    "#products .product[data-href]"
  );

  cards.forEach((card) => {
    const navigate = () => {
      const href = card.dataset.href;
      if (href) window.location.href = href;
    };

    card.addEventListener("click", (event) => {
      if (event.target.closest("a, button")) return;
      navigate();
    });

    card.addEventListener("keydown", (event) => {
      if (event.target.closest("a, button")) return;

      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        navigate();
      }
    });
  });
})();

(function () {
  const page = document.querySelector(".textbook-resources-page");
  if (!page) return;

  const input = document.getElementById("textbook-search-input");
  const subject = document.getElementById("textbook-subject-filter");
  const type = document.getElementById("textbook-type-filter");
  const reset = document.getElementById("textbook-search-reset");
  const count = document.getElementById("textbook-result-count");
  const empty = document.getElementById("textbook-no-results");
  const form = document.querySelector(".textbook-search-panel");
  const cards = Array.from(document.querySelectorAll(".textbook-publisher-card"));

  if (!input || !subject || !type || !reset || !count || !empty || !form || cards.length === 0) return;

  const normalize = (value) => value.toLocaleLowerCase("ja-JP").normalize("NFKC");

  const applyFilters = () => {
    const keyword = normalize(input.value.trim());
    const subjectValue = normalize(subject.value);
    const typeValue = normalize(type.value);
    let visibleCount = 0;

    cards.forEach((card) => {
      const text = normalize(card.textContent || "");
      const matchesKeyword = !keyword || text.includes(keyword);
      const matchesSubject = !subjectValue || text.includes(subjectValue);
      const matchesType = !typeValue || text.includes(typeValue);
      const isVisible = matchesKeyword && matchesSubject && matchesType;

      card.hidden = !isVisible;
      if (isVisible) visibleCount += 1;
    });

    count.textContent = String(visibleCount);
    empty.hidden = visibleCount !== 0;
  };

  [input, subject, type].forEach((control) => {
    control.addEventListener("input", applyFilters);
    control.addEventListener("change", applyFilters);
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    applyFilters();
  });

  reset.addEventListener("click", () => {
    input.value = "";
    subject.value = "";
    type.value = "";
    applyFilters();
    input.focus();
  });

  applyFilters();
})();
