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
