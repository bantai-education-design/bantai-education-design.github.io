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
  const excludeSelector = "button, input, select, textarea, label, summary, [role='button'], a.image-source-link, a[download], a[target='_blank']";

  const getTargetHref = (container) => {
    if (!container) return null;
    if (container.dataset && container.dataset.href) return container.dataset.href;
    if (container.dataset && container.dataset.detailUrl) return container.dataset.detailUrl;

    const primaryLink = container.querySelector(
      "a.catalog-card-hit-area, a.btn-secondary, a.scene-link, a.card-detail-open, a.persona-product-card, a.product-showcase-card, a.column-read-more, a"
    );
    if (primaryLink) {
      const href = primaryLink.getAttribute("href");
      if (href && !href.startsWith("#") && !href.startsWith("javascript:")) {
        return href;
      }
    }
    return null;
  };

  const findCardContainer = (target) => {
    return target.closest(
      "[data-href], [data-detail-url], .product-card-v2, .scene-card, .catalog-card, .persona-product-card, .product-showcase-card, .column-card, .tokyo-card, .university-card, .school-card, .textbook-publisher-card, .textbook-grade-guide-card, .textbook-audience-card, article, .card"
    );
  };

  document.addEventListener("click", (event) => {
    if (event.target.closest(excludeSelector)) return;

    const card = findCardContainer(event.target);
    if (!card) return;

    const href = getTargetHref(card);
    if (!href || href.startsWith("#") || href.startsWith("javascript:")) return;

    const enclosingAnchor = event.target.closest("a");
    if (enclosingAnchor) {
      const anchorHref = enclosingAnchor.getAttribute("href");
      if (anchorHref === href || (anchorHref && !anchorHref.startsWith("#") && !anchorHref.startsWith("javascript:"))) {
        return;
      }
    }

    event.preventDefault();
    window.location.href = href;
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    if (event.target.closest(excludeSelector)) return;

    const card = findCardContainer(event.target);
    if (!card) return;

    if (document.activeElement === card || card.contains(document.activeElement)) {
      const href = getTargetHref(card);
      if (href && !href.startsWith("#") && !href.startsWith("javascript:")) {
        event.preventDefault();
        window.location.href = href;
      }
    }
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

(function () {
  const schoolDbLink = document.querySelector('#global-menu a[href="/tools/school-database/"]');
  if (schoolDbLink && schoolDbLink.textContent.trim() === "学校宛先DB") {
    schoolDbLink.textContent = "全国学校DB";
  }

  const teacherEntry = document.querySelector('.textbook-home-entry-actions a[href="/resources/textbook-plans/#for-teachers"]');
  if (teacherEntry) {
    teacherEntry.style.background = "#17345a";
    teacherEntry.style.border = "1px solid var(--gold)";
    teacherEntry.style.color = "#fff";
    teacherEntry.style.boxShadow = "0 4px 12px rgba(0,0,0,.22)";
  }
})();

/* Global navigation: breadcrumbs on subpages */
(function () {
  const path = window.location.pathname.replace(/\/+/g, "/");
  if (path === "/" || path === "/index.html" || path === "/index-new.html") return;

  const main = document.querySelector("main");
  if (!main || document.querySelector(".inline-breadcrumb")) return;

  const h1 = document.querySelector("main h1");
  const pageTitle = (h1 ? h1.textContent : document.title.split("|")[0]).replace(/\s+/g, " ").trim();

  const breadcrumb = document.createElement("nav");
  breadcrumb.className = "inline-breadcrumb";
  breadcrumb.setAttribute("aria-label", "現在地");
  breadcrumb.style.cssText = "width:min(1140px,90vw); margin:12px auto 0; padding:8px 0; font-size:0.8rem; color:#64748b; display:flex; align-items:center; gap:6px; flex-wrap:wrap;";

  const addCrumb = (text, href) => {
    if (breadcrumb.children.length) {
      const sep = document.createElement("span");
      sep.textContent = "›";
      sep.style.color = "#94a3b8";
      breadcrumb.appendChild(sep);
    }
    if (href) {
      const a = document.createElement("a");
      a.href = href;
      a.textContent = text;
      a.style.cssText = "color:#1e3a8a; text-decoration:none; font-weight:600;";
      breadcrumb.appendChild(a);
    } else {
      const span = document.createElement("span");
      span.textContent = text;
      span.style.cssText = "color:#475569; font-weight:700;";
      breadcrumb.appendChild(span);
    }
  };

  addCrumb("ホーム", "/");

  if (path.startsWith("/for-teachers/")) {
    addCrumb("先生向け", null);
  } else if (path.startsWith("/for-parents/")) {
    addCrumb("保護者・ご家庭", null);
  } else if (path === "/databases/" || path === "/databases") {
    addCrumb("DB・情報検索", null);
  } else if (path.startsWith("/tools/school-database/")) {
    addCrumb("DB・情報検索", "/databases/");
    addCrumb(path === "/tools/school-database/" ? "全国学校DB" : pageTitle || "全国学校DB", null);
  } else if (path.startsWith("/tools/university-database/")) {
    addCrumb("DB・情報検索", "/databases/");
    addCrumb(path === "/tools/university-database/" ? "全国大学DB" : pageTitle || "全国大学DB", null);
  } else if (path.startsWith("/resources/textbook-plans/")) {
    addCrumb("DB・情報検索", "/databases/");
    addCrumb(pageTitle || "教科書会社DB", null);
  } else if (path === "/products/" || path === "/products") {
    addCrumb("全商品", null);
  } else if (path.startsWith("/products/categories/")) {
    addCrumb("商品カテゴリー", null);
  } else if (path.startsWith("/products/")) {
    addCrumb("商品カテゴリー", "/products/categories/");
    addCrumb(pageTitle || "商品詳細", null);
  } else {
    addCrumb(pageTitle || "現在のページ", null);
  }

  main.insertBefore(breadcrumb, main.firstChild);
})();
