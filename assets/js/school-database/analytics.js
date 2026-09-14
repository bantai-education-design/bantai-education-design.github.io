(function () {
  let dataset = null;
  let currentMetric = "elem_pop_per_school";
  let currentSortOrder = "desc";
  let currentViewMode = "chart";
  let projectionLoaded = false;

  const metricSelect = document.getElementById("metric-select");
  const sortOrderSelect = document.getElementById("sort-order");
  const viewBtns = document.querySelectorAll(".view-btn");
  const metricTitle = document.getElementById("metric-info-title");
  const metricDesc = document.getElementById("metric-info-desc");
  const metricBadge = document.getElementById("metric-info-badge");
  const metricNationalAvg = document.getElementById("metric-national-avg");
  const metricNationalAvgLabel = document.getElementById("metric-national-avg-label");

  const chartContainer = document.getElementById("bar-chart-container");
  const mapContainer = document.getElementById("japan-map-grid");
  const tableBody = document.getElementById("analytics-table-body");
  const tableThVal = document.getElementById("table-th-val");
  const btnCsv = document.getElementById("btn-export-csv");
  const errorNotice = document.getElementById("analytics-error-notice");

  const mergeProjectionData = (projection) => {
    if (!dataset || !projection || !Array.isArray(projection.prefectures)) return;

    const projectionByCode = new Map(
      projection.prefectures.map((item) => [item.prefecture_code, item])
    );
    if (projectionByCode.size !== 47) {
      throw new Error(`IPSS projection prefecture count mismatch: ${projectionByCode.size}`);
    }

    const sourceLabel = "国立社会保障・人口問題研究所（IPSS）『日本の地域別将来推計人口（令和5（2023）年推計）』";
    dataset.indicators_definition = dataset.indicators_definition || {};
    dataset.national_summary = dataset.national_summary || {};

    dataset.indicators_definition.child_population_index_2035 = {
      label: "2035年 0～14歳人口指数（2020年=100）",
      unit: "指数",
      description: "2020年の0～14歳人口を100としたときの2035年推計人口指数。値が100を下回るほど、2020年より子ども人口が減少する見込みを示します。",
      source: sourceLabel,
      base_date: "2020年=100／2035年推計"
    };
    dataset.indicators_definition.child_population_index_2050 = {
      label: "2050年 0～14歳人口指数（2020年=100）",
      unit: "指数",
      description: "2020年の0～14歳人口を100としたときの2050年推計人口指数。将来の学校規模・学校需要を考える際の地域人口動向の目安です。",
      source: sourceLabel,
      base_date: "2020年=100／2050年推計"
    };

    dataset.national_summary.child_population_index_2035 = projection.national.child_population_index_2035;
    dataset.national_summary.child_population_index_2050 = projection.national.child_population_index_2050;

    const projectionKeys = ["child_population_index_2035", "child_population_index_2050"];
    dataset.prefectures.forEach((pref) => {
      const source = projectionByCode.get(pref.code);
      if (!source) throw new Error(`IPSS projection missing prefecture: ${pref.code}`);
      projectionKeys.forEach((key) => {
        pref[key] = source[key];
      });
      pref.ranks = pref.ranks || {};
    });

    projectionKeys.forEach((key) => {
      const sorted = [...dataset.prefectures].sort((a, b) => b[key] - a[key]);
      sorted.forEach((pref, index) => {
        pref.ranks[key] = index + 1;
      });
    });
  };

  const appendSupplementalMetricOptions = () => {
    if (!metricSelect) return;

    const addOption = (group, value, label) => {
      if (metricSelect.querySelector(`option[value="${value}"]`)) return;
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      group.appendChild(option);
    };

    if (!metricSelect.querySelector('option[value="absenteeism_combined_rate"]')) {
      const absenteeismGroup = document.createElement("optgroup");
      absenteeismGroup.label = "🚸 教育課題・不登校（文部科学省 2024年度）";
      addOption(absenteeismGroup, "absenteeism_combined_rate", "🚸 小中学校 1,000人当たり不登校児童生徒数");
      addOption(absenteeismGroup, "absenteeism_combined_count", "📊 小中学校 不登校児童生徒数（総数）");
      addOption(absenteeismGroup, "elem_absenteeism_rate", "🎒 小学校 1,000人当たり不登校児童数");
      addOption(absenteeismGroup, "jhs_absenteeism_rate", "🏫 中学校 1,000人当たり不登校生徒数");
      metricSelect.appendChild(absenteeismGroup);
    }

    if (projectionLoaded && !metricSelect.querySelector('option[value="child_population_index_2035"]')) {
      const projectionGroup = document.createElement("optgroup");
      projectionGroup.label = "🔮 将来の子ども人口（IPSS 2023年推計・2020年=100）";
      addOption(projectionGroup, "child_population_index_2035", "🔮 2035年 0～14歳人口指数（2020年=100）");
      addOption(projectionGroup, "child_population_index_2050", "🔭 2050年 0～14歳人口指数（2020年=100）");
      metricSelect.appendChild(projectionGroup);
    }
  };

  const init = async () => {
    try {
      const res = await fetch("/data/school-database/national-analytics-dataset.json");
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      dataset = await res.json();

      try {
        const projectionRes = await fetch("/data/school-database/ipss-child-population-projection-2023.json");
        if (!projectionRes.ok) throw new Error(`IPSS HTTP error ${projectionRes.status}`);
        const projection = await projectionRes.json();
        mergeProjectionData(projection);
        projectionLoaded = true;
      } catch (projectionError) {
        console.warn("IPSS future child population projection could not be loaded:", projectionError);
      }

      appendSupplementalMetricOptions();
      bindEvents();
      render();
    } catch (err) {
      console.error("Failed to load analytics dataset:", err);
      if (errorNotice) {
        errorNotice.style.display = "block";
        errorNotice.textContent = "統計データを読み込めませんでした。ページを再読み込みしてください。";
      } else if (chartContainer) {
        chartContainer.innerHTML = `<div style="background:#fef2f2; border:1px solid #fca5a5; color:#991b1b; padding:16px; border-radius:8px; margin:20px 0;">統計データを読み込めませんでした。ページを再読み込みしてください。</div>`;
      }
    }
  };

  const bindEvents = () => {
    if (metricSelect) {
      metricSelect.addEventListener("change", (e) => {
        currentMetric = e.target.value;
        render();
      });
    }

    if (sortOrderSelect) {
      sortOrderSelect.addEventListener("change", (e) => {
        currentSortOrder = e.target.value;
        render();
      });
    }

    viewBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        viewBtns.forEach((b) => {
          b.classList.remove("active");
          b.style.background = "transparent";
          b.style.color = "#475569";
        });
        btn.classList.add("active");
        btn.style.background = "#0c1b33";
        btn.style.color = "#fff";

        currentViewMode = btn.dataset.view;
        document.querySelectorAll(".view-panel").forEach((panel) => {
          panel.style.display = panel.id === `view-${currentViewMode}` ? "block" : "none";
        });
      });
    });

    if (btnCsv) {
      btnCsv.addEventListener("click", exportCSV);
    }
  };

  const formatNumber = (num) => {
    if (typeof num !== "number" || isNaN(num)) return num;
    return num.toLocaleString("ja-JP");
  };

  const getMetricMeta = (key) => {
    if (!dataset || !dataset.indicators_definition) return { label: key, unit: "", desc: "", description: "", source: "", base_date: "" };
    const def = dataset.indicators_definition[key] || {};
    return {
      label: def.label || key,
      unit: def.unit || "",
      desc: def.description || def.desc || "",
      description: def.description || def.desc || "",
      source: def.source || "",
      base_date: def.base_date || ""
    };
  };

  const render = () => {
    if (!dataset || !dataset.prefectures) return;

    const meta = getMetricMeta(currentMetric);
    const prefs = [...dataset.prefectures];

    prefs.sort((a, b) => {
      const rankA = a.ranks ? (a.ranks[currentMetric] ?? 999) : 999;
      const rankB = b.ranks ? (b.ranks[currentMetric] ?? 999) : 999;
      return currentSortOrder === "desc" ? rankA - rankB : rankB - rankA;
    });

    if (metricTitle) metricTitle.textContent = meta.label;
    if (metricDesc) metricDesc.textContent = meta.description || meta.desc || "";
    if (metricBadge) {
      const isCustom = ["elem_pop_per_school", "jhs_pop_per_school", "student_teacher_ratio", "elem_enrolled_per_school", "elem_enrolled_per_class", "jhs_enrolled_per_school", "jhs_enrolled_per_class", "jhs_student_teacher_ratio", "area_per_school", "private_elem_school_ratio", "special_needs_schools_per_100k_age_6_17", "waiting_children_per_10k_preschool"].includes(currentMetric);
      metricBadge.textContent = isCustom ? "独自算出指標" : "公的統計指標";
      metricBadge.style.background = isCustom ? "#3182ce" : "#059669";
    }

    const isRatioMetric = ["aging_rate", "student_teacher_ratio", "elem_pop_per_school", "jhs_pop_per_school", "elem_enrolled_per_school", "elem_enrolled_per_class", "jhs_enrolled_per_school", "jhs_enrolled_per_class", "jhs_student_teacher_ratio", "child_under_15_ratio", "pop_change_rate", "area_per_school", "ict_teaching_capability", "private_elem_school_ratio", "special_needs_schools_per_100k_age_6_17", "waiting_children_per_10k_preschool", "absenteeism_combined_rate", "elem_absenteeism_rate", "jhs_absenteeism_rate", "child_population_index_2035", "child_population_index_2050"].includes(currentMetric);

    if (metricNationalAvgLabel) {
      if (["child_population_index_2035", "child_population_index_2050"].includes(currentMetric)) {
        metricNationalAvgLabel.textContent = "全国指数（2020年=100）";
      } else if (["absenteeism_combined_rate", "elem_absenteeism_rate", "jhs_absenteeism_rate"].includes(currentMetric)) {
        metricNationalAvgLabel.textContent = "全国値（児童生徒1,000人あたり）";
      } else if (currentMetric === "ict_teaching_capability") {
        metricNationalAvgLabel.textContent = "全国平均（47都道府県単純平均）";
      } else {
        metricNationalAvgLabel.textContent = isRatioMetric ? "全国平均（全国総計より算出）" : "全国合計";
      }
    }

    if (metricNationalAvg) {
      let natVal = null;
      if (dataset.national_summary && dataset.national_summary[currentMetric] !== undefined) {
        natVal = dataset.national_summary[currentMetric];
      } else {
        const sum = dataset.prefectures.reduce((acc, p) => acc + (p[currentMetric] || 0), 0);
        natVal = isRatioMetric ? (sum / dataset.prefectures.length) : sum;
      }

      const displayVal = isRatioMetric
        ? natVal.toFixed(1)
        : Math.round(natVal).toLocaleString("ja-JP");
      metricNationalAvg.innerHTML = `${displayVal} <span style="font-size:0.85rem; font-weight:600;">${meta.unit}</span>`;
    }

    renderChart(prefs, meta);
    renderMap(prefs, meta);
    renderTable(prefs, meta);
  };

  const renderChart = (prefs, meta) => {
    if (!chartContainer) return;
    chartContainer.innerHTML = "";

    const maxVal = Math.max(...prefs.map((p) => p[currentMetric] || 0), 1);

    prefs.forEach((p, idx) => {
      const val = p[currentMetric] || 0;
      const rank = p.ranks ? p.ranks[currentMetric] : idx + 1;
      const pct = Math.max(4, (val / maxVal) * 100);

      const row = document.createElement("a");
      row.href = `/tools/school-database/${p.code}/`;
      row.className = "bar-row";

      const rankBadge = rank <= 3
        ? `<span style="background:#c5a059; color:#0c1b33; font-weight:800; padding:2px 8px; border-radius:99px; font-size:0.78rem;">${rank}位</span>`
        : `<span style="color:#64748b; font-weight:700; font-size:0.85rem;">${rank}位</span>`;

      row.innerHTML = `
        <div class="bar-rank">${rankBadge}</div>
        <div class="bar-pref">${p.name}</div>
        <div class="bar-track">
          <div class="bar-fill" style="width:${pct}%;"></div>
        </div>
        <div class="bar-value">
          ${formatNumber(val)} <span class="bar-unit">${meta.unit}</span>
        </div>
      `;

      chartContainer.appendChild(row);
    });
  };

  const renderMap = (prefs, meta) => {
    if (!mapContainer) return;
    mapContainer.innerHTML = "";

    const regions = [
      { name: "北海道・東北", codes: ["hokkaido", "aomori", "iwate", "miyagi", "akita", "yamagata", "fukushima"] },
      { name: "関東", codes: ["ibaraki", "tochigi", "gunma", "saitama", "chiba", "tokyo", "kanagawa"] },
      { name: "中部", codes: ["niigata", "toyama", "ishikawa", "fukui", "yamanashi", "nagano", "gifu", "shizuoka", "aichi"] },
      { name: "近畿", codes: ["mie", "shiga", "kyoto", "osaka", "hyogo", "nara", "wakayama"] },
      { name: "中国・四国", codes: ["tottori", "shimane", "okayama", "hiroshima", "yamaguchi", "tokushima", "kagawa", "ehime", "kochi"] },
      { name: "九州・沖縄", codes: ["fukuoka", "saga", "nagasaki", "kumamoto", "oita", "miyazaki", "kagoshima", "okinawa"] }
    ];

    const vals = prefs.map((p) => p[currentMetric] || 0);
    const maxVal = Math.max(...vals, 1);
    const minVal = Math.min(...vals);
    const range = Math.max(0.0001, maxVal - minVal);

    const prefMap = {};
    prefs.forEach((p) => (prefMap[p.code] = p));

    regions.forEach((reg) => {
      const box = document.createElement("div");
      box.style.cssText = "background:#f8fafc; border:1px solid #cbd5e1; border-radius:10px; padding:14px;";

      let html = `<h4 style="margin:0 0 10px; font-size:0.9rem; color:#0c1b33; border-bottom:2px solid #cbd5e1; padding-bottom:4px;">${reg.name}地方</h4>`;
      html += `<div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(105px, 1fr)); gap:8px;">`;

      reg.codes.forEach((code) => {
        const p = prefMap[code];
        if (!p) return;
        const val = p[currentMetric] || 0;
        const ratio = (val - minVal) / range;

        const bgAlpha = 0.15 + ratio * 0.85;
        const bgColor = `rgba(30, 58, 138, ${bgAlpha.toFixed(2)})`;
        const textColor = ratio > 0.5 ? "#ffffff" : "#0c1b33";

        html += `
          <a href="/tools/school-database/${p.code}/" style="display:block; background:${bgColor}; color:${textColor}; text-decoration:none; padding:8px 6px; border-radius:6px; font-size:0.8rem; text-align:center; transition:transform 0.15s; border:1px solid rgba(0,0,0,0.1);">
            <div style="font-weight:700;">${p.name}</div>
            <div style="font-size:0.75rem; margin-top:2px; opacity:0.9;">${formatNumber(val)} ${meta.unit}</div>
          </a>
        `;
      });

      html += `</div>`;
      box.innerHTML = html;
      mapContainer.appendChild(box);
    });
  };

  const renderTable = (prefs, meta) => {
    if (!tableBody) return;
    tableBody.innerHTML = "";

    if (tableThVal) {
      tableThVal.textContent = `${meta.label} (${meta.unit})`;
    }

    prefs.forEach((p, idx) => {
      const val = p[currentMetric] || 0;
      const rank = p.ranks ? p.ranks[currentMetric] : idx + 1;

      const tr = document.createElement("tr");
      tr.style.cssText = "border-bottom:1px solid #e2e8f0; transition:background 0.15s;";
      tr.addEventListener("mouseenter", () => (tr.style.background = "#f8fafc"));
      tr.addEventListener("mouseleave", () => (tr.style.background = "transparent"));

      const sourceText = meta.source ? `${meta.source}<br><span style="font-size:0.72rem; color:#94a3b8;">${meta.base_date || ''}</span>` : "e-Stat/学校DB統合";

      tr.innerHTML = `
        <td style="padding:10px 12px; font-weight:800; color:#0c1b33;">${rank}位</td>
        <td style="padding:10px 12px; font-weight:700;"><a href="/tools/school-database/${p.code}/" style="color:#1e3a8a; text-decoration:none;">${p.name}</a></td>
        <td style="padding:10px 12px; color:#64748b;">${p.region}</td>
        <td style="padding:10px 12px; text-align:right; font-weight:800; color:#0c1b33;">${formatNumber(val)} ${meta.unit}</td>
        <td style="padding:10px 12px; text-align:center; font-size:0.78rem; color:#475569;">${sourceText}</td>
        <td style="padding:10px 12px; text-align:center;">
          <a href="/tools/school-database/${p.code}/" style="background:#0c1b33; color:#fff; padding:3px 8px; border-radius:4px; font-size:0.74rem; text-decoration:none; font-weight:600;">詳細 →</a>
        </td>
      `;

      tableBody.appendChild(tr);
    });
  };

  const exportCSV = () => {
    if (!dataset || !dataset.prefectures) return;
    const meta = getMetricMeta(currentMetric);
    const prefs = [...dataset.prefectures];

    prefs.sort((a, b) => {
      const rankA = a.ranks ? (a.ranks[currentMetric] ?? 999) : 999;
      const rankB = b.ranks ? (b.ranks[currentMetric] ?? 999) : 999;
      return rankA - rankB;
    });

    let csvContent = `順位,都道府県名,地方区分,${meta.label}(${meta.unit}),出典,基準日
`;

    prefs.forEach((p) => {
      const val = p[currentMetric] || 0;
      const rank = p.ranks ? (p.ranks[currentMetric] ?? "") : "";
      const srcEscaped = (meta.source || "").replace(/,/g, " ");
      const dateEscaped = (meta.base_date || "").replace(/,/g, " ");
      csvContent += `${rank},${p.name},${p.region},${val},"${srcEscaped}","${dateEscaped}"
`;
    });

    const bom = "﻿";
    const blob = new Blob([bom + csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `bantai_school_db_${currentMetric}_ranking.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();