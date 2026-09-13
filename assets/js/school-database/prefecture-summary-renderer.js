(function () {
  const DATASET_URL = '/data/school-database/national-analytics-dataset.json';
  const container = document.querySelector('.pref-summary-section');

  if (!container) return;

  const pathParts = window.location.pathname.replace(/\/$/, '').split('/');
  const prefCode = pathParts[pathParts.length - 1];

  if (!prefCode || prefCode === 'school-database') return;

  fetch(DATASET_URL)
    .then((res) => {
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      return res.json();
    })
    .then((data) => {
      if (!data || !data.prefectures) return;
      const prefData = data.prefectures.find((p) => p.code === prefCode);
      if (!prefData) return;

      const rankBadge = container.querySelector('.pref-summary-card:nth-child(2) .pref-summary-value span:last-child');
      if (rankBadge && prefData.ranks && prefData.ranks.elem_pop_per_school) {
        rankBadge.textContent = `全国${prefData.ranks.elem_pop_per_school}位`;
      }
    })
    .catch((err) => {
      console.warn('Failed to load national-analytics-dataset.json for summary sync:', err);
    });
})();
