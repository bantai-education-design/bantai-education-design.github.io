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

/* Global audience/context navigation: keeps visitors oriented after leaving the homepage. */
(function () {
  if (document.querySelector(".global-context-bar")) return;

  const header = document.querySelector(".site-header");
  const main = document.querySelector("main");
  if (!header || !main) return;

  const oldAudienceTier = header.querySelector(".audience-tier");
  if (oldAudienceTier) oldAudienceTier.hidden = true;

  const style = document.createElement("style");
  style.id = "global-context-nav-style";
  style.textContent = `
    .global-context-bar{position:sticky;top:80px;z-index:44;background:rgba(9,25,47,.97);color:#fff;border-bottom:1px solid rgba(197,160,89,.5);box-shadow:0 5px 18px rgba(5,18,35,.12);backdrop-filter:blur(10px)}
    .global-context-inner{width:min(1140px,90vw);margin:auto;display:flex;align-items:center;gap:18px;min-height:58px}
    .global-context-label{flex:0 0 auto;font-size:.72rem;font-weight:800;letter-spacing:.08em;color:#edd996;white-space:nowrap}
    .global-audience-nav{display:flex;gap:7px;align-items:center;flex-wrap:wrap}
    .global-audience-nav a{display:inline-flex;align-items:center;min-height:34px;padding:6px 12px;border:1px solid rgba(255,255,255,.22);border-radius:999px;color:rgba(255,255,255,.88);text-decoration:none;font-size:.8rem;font-weight:700;line-height:1.2;background:rgba(255,255,255,.05);transition:.2s}
    .global-audience-nav a:hover{background:rgba(255,255,255,.12);border-color:#c5a059;color:#fff}
    .global-audience-nav a.is-current{background:linear-gradient(135deg,#c5a059,#edd996);border-color:#edd996;color:#071b36;box-shadow:0 3px 10px rgba(197,160,89,.22)}
    .global-breadcrumb{margin-left:auto;display:flex;align-items:center;gap:6px;min-width:0;color:rgba(255,255,255,.64);font-size:.72rem;white-space:nowrap;overflow:hidden}
    .global-breadcrumb a{color:rgba(255,255,255,.76);text-decoration:none}.global-breadcrumb a:hover{color:#edd996}.global-breadcrumb .crumb-current{color:#fff;font-weight:700;overflow:hidden;text-overflow:ellipsis}.global-breadcrumb .crumb-sep{color:#c5a059}
    @media(max-width:860px){.global-context-bar{top:64px}.global-context-inner{width:100%;padding:8px 14px;display:grid;grid-template-columns:auto 1fr;gap:6px 10px;min-height:auto}.global-context-label{grid-column:1}.global-audience-nav{grid-column:2;flex-wrap:nowrap;overflow-x:auto;padding-bottom:2px;scrollbar-width:none}.global-audience-nav::-webkit-scrollbar{display:none}.global-audience-nav a{white-space:nowrap;font-size:.76rem;padding:6px 10px}.global-breadcrumb{grid-column:1/-1;margin-left:0;border-top:1px solid rgba(255,255,255,.1);padding-top:6px;font-size:.68rem}}
    @media(max-width:520px){.global-context-label{display:none}.global-audience-nav{grid-column:1/-1}.global-context-inner{grid-template-columns:1fr}.global-breadcrumb{grid-column:1}}
  `;
  document.head.appendChild(style);

  const path = window.location.pathname.replace(/\/+/g, "/");
  const isTeacher = path.startsWith("/for-teachers/") || path.startsWith("/products/school-work/");
  const isParent = path.startsWith("/for-parents/") || path.startsWith("/products/family-learning/");
  const isData = path.startsWith("/databases/") || path.startsWith("/tools/school-database/") || path.startsWith("/resources/textbook-plans/");
  const isProducts = path.startsWith("/products/") && !isTeacher && !isParent;

  const bar = document.createElement("div");
  bar.className = "global-context-bar";
  bar.setAttribute("aria-label", "対象者と現在地");

  const inner = document.createElement("div");
  inner.className = "global-context-inner";

  const label = document.createElement("span");
  label.className = "global-context-label";
  label.textContent = "対象者を選ぶ";
  inner.appendChild(label);

  const nav = document.createElement("nav");
  nav.className = "global-audience-nav";
  nav.setAttribute("aria-label", "対象者・目的別ナビゲーション");
  const navItems = [
    ["先生", "/for-teachers/", isTeacher],
    ["保護者・ご家庭", "/for-parents/", isParent],
    ["DB・情報検索", "/databases/", isData],
    ["商品カテゴリー", "/products/categories/", isProducts]
  ];
  navItems.forEach(([text, href, current]) => {
    const a = document.createElement("a");
    a.href = href;
    a.textContent = text;
    if (current) {
      a.classList.add("is-current");
      a.setAttribute("aria-current", "page");
    }
    nav.appendChild(a);
  });
  inner.appendChild(nav);

  const breadcrumb = document.createElement("nav");
  breadcrumb.className = "global-breadcrumb";
  breadcrumb.setAttribute("aria-label", "現在地");

  const addCrumb = (text, href) => {
    if (breadcrumb.children.length) {
      const sep = document.createElement("span");
      sep.className = "crumb-sep";
      sep.textContent = "›";
      breadcrumb.appendChild(sep);
    }
    if (href) {
      const a = document.createElement("a");
      a.href = href;
      a.textContent = text;
      breadcrumb.appendChild(a);
    } else {
      const span = document.createElement("span");
      span.className = "crumb-current";
      span.textContent = text;
      breadcrumb.appendChild(span);
    }
  };

  const h1 = document.querySelector("main h1");
  const pageTitle = (h1 ? h1.textContent : document.title.split("|")[0]).replace(/\s+/g, " ").trim();
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
  } else if (path.startsWith("/resources/textbook-plans/")) {
    addCrumb("DB・情報検索", "/databases/");
    addCrumb(pageTitle || "教科書・年間学習計画", null);
  } else if (path === "/products/" || path === "/products") {
    addCrumb("全商品", null);
  } else if (path.startsWith("/products/categories/")) {
    addCrumb("商品カテゴリー", null);
  } else if (path.startsWith("/products/")) {
    addCrumb("商品カテゴリー", "/products/categories/");
    addCrumb(pageTitle || "商品詳細", null);
  } else if (path !== "/" && path !== "/index.html" && path !== "/index-new.html") {
    addCrumb(pageTitle || "現在のページ", null);
  }

  inner.appendChild(breadcrumb);
  bar.appendChild(inner);
  header.insertAdjacentElement("afterend", bar);
})();
