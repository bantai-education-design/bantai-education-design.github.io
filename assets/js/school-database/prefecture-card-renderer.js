(function () {
  const DATA_URL = "/data/school-database/prefecture-card-metadata.json";
  const root = document.querySelector("[data-prefecture-card-root]");

  if (!root) {
    return;
  }

  const formatNumber = (value) => Number(value).toLocaleString("ja-JP");

  const createElement = (tag, className, text) => {
    const element = document.createElement(tag);
    if (className) {
      element.className = className;
    }
    if (text !== undefined) {
      element.textContent = text;
    }
    return element;
  };

  const createMetaRow = (label, value, unit) => {
    const row = createElement("div", "meta-row");
    row.append(createElement("span", "meta-label", label));
    const valueElement = createElement("span", "meta-value", value);
    if (unit) {
      valueElement.append(createElement("span", "meta-unit", unit));
    }
    row.append(valueElement);
    return row;
  };

  const establishmentLabel = (establishment) => {
    const labels = [
      ["national", "国"],
      ["public", "公"],
      ["private", "私"],
      ["other", "他"],
    ];
    const parts = labels
      .filter(([key]) => Number(establishment[key]) > 0)
      .map(([key, label]) => `${label}${formatNumber(establishment[key])}`);
    return parts.length ? parts.join("・") : "ー";
  };

  const appendPopulationSummary = (card, prefecture) => {
    const population = prefecture.population;
    if (!population || population.available !== true) {
      return;
    }

    const summary = createElement("div", "population-summary");
    summary.setAttribute("aria-label", `${prefecture.prefecture_name}の確認済み人口メタデータ`);

    const populationRow = createElement("div", "population-summary-row");
    populationRow.append(createElement("span", "population-summary-label", population.population_scope_label));
    const populationValue = createElement("strong", "", formatNumber(population.japanese_population));
    populationValue.append(createElement("span", "", "人"));
    populationRow.append(populationValue);
    summary.append(populationRow);

    const ageRow = createElement("div", "population-summary-row");
    ageRow.append(createElement("span", "population-summary-label", "3～17歳人口"));
    const ageValue = createElement("strong", "", formatNumber(population.japanese_age_3_17));
    ageValue.append(createElement("span", "", "人"));
    ageValue.append(createElement("span", "population-inline-share", `（${population.share_of_japanese_population_percent.toFixed(1)}%）`));
    ageRow.append(ageValue);
    summary.append(ageRow);

    card.append(summary);

    const details = createElement("details", "population-age-details");
    details.append(createElement("summary", "", "年齢別人口"));
    const list = createElement("dl", "");
    population.age_groups.forEach((group) => {
      const item = createElement("div", "");
      item.append(createElement("dt", "", `${group.label} ${group.age_range_label}`));
      item.append(
        createElement(
          "dd",
          "",
          `${formatNumber(group.population)}人・${group.share_of_japanese_population_percent.toFixed(1)}%`,
        ),
      );
      list.append(item);
    });
    details.append(list);
    details.append(createElement("p", "population-note", `基準日：${population.reference_date}`));
    if (population.summary_note) {
      details.append(createElement("p", "population-note", population.summary_note));
    }
    population.notes.forEach((note) => {
      details.append(createElement("p", "population-note", note));
    });
    card.append(details);
  };

  const createCard = (prefecture) => {
    const hasDetails = prefecture.population && prefecture.population.available === true;
    const card = createElement(hasDetails ? "article" : "a", `pref-card prefecture-card active-card region-${prefecture.region.code}`);
    if (hasDetails) {
      card.dataset.cardHref = prefecture.url;
      card.setAttribute("aria-label", `${prefecture.prefecture_name}学校データベース`);
      card.setAttribute("role", "link");
      card.tabIndex = 0;
    } else {
      card.href = prefecture.url;
      card.setAttribute("aria-label", `${prefecture.prefecture_name}学校データベースを開く`);
    }

    const header = createElement("div", "pref-card-header");
    const badge = createElement("span", "pref-badge", prefecture.status_label);
    badge.style.background = "#27ae60";
    header.append(badge);
    const edition = createElement("span", "", prefecture.edition);
    edition.style.fontSize = "0.8rem";
    edition.style.color = "#718096";
    header.append(edition);
    card.append(header);

    card.append(createElement("h2", "", prefecture.prefecture_name));

    const schoolDatabase = prefecture.school_database;
    const metaGrid = createElement("div", "pref-meta-grid");
    metaGrid.append(createMetaRow("収録校・園", formatNumber(schoolDatabase.record_count), "件"));
    metaGrid.append(createMetaRow("対象地域", formatNumber(schoolDatabase.municipality_count)));
    metaGrid.append(createMetaRow("設置区分", establishmentLabel(schoolDatabase.establishment)));
    metaGrid.append(createMetaRow("校種", formatNumber(schoolDatabase.school_type_count), "種類"));
    card.append(metaGrid);

    appendPopulationSummary(card, prefecture);

    return card;
  };

  const renderCards = (payload) => {
    root.textContent = "";
    let currentRegion = "";
    let currentSection = null;
    let currentGrid = null;

    payload.prefectures.forEach((prefecture) => {
      if (prefecture.region.code !== currentRegion) {
        currentRegion = prefecture.region.code;
        currentSection = createElement("section", `region-section region-${currentRegion}`);
        const heading = createElement("h3", `region-header region-title region-${currentRegion}`, prefecture.region.name);
        currentGrid = createElement("div", "prefectures-grid");
        currentSection.append(heading, currentGrid);
        root.append(currentSection);
      }

      currentGrid.append(createCard(prefecture));
    });
  };

  const enableStretchedCardLinks = () => {
    document.querySelectorAll("[data-card-href]").forEach((card) => {
      card.addEventListener("click", (event) => {
        if (event.target.closest("a, button, summary, details, input, select, textarea")) {
          return;
        }
        window.location.href = card.dataset.cardHref;
      });
      card.addEventListener("keydown", (event) => {
        if (event.target !== card || event.key !== "Enter") {
          return;
        }
        event.preventDefault();
        window.location.href = card.dataset.cardHref;
      });
    });
  };

  fetch(DATA_URL)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response.json();
    })
    .then((payload) => {
      renderCards(payload);
      enableStretchedCardLinks();
    })
    .catch((error) => {
      root.textContent = "都道府県カードを読み込めませんでした。時間をおいて再読み込みしてください。";
      console.error("Failed to render prefecture cards", error);
    });
}());
