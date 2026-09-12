/**
 * Ban.Tai Education Design - Columns & Interactive Utilities
 */
(function() {
  'use strict';

  let allColumns = [];
  let currentCategory = 'all';

  function getCategoryTagClass(slug) {
    switch (slug) {
      case 'ict': return 'badge-ict';
      case 'ai': return 'badge-ai';
      case 'trends': return 'badge-trends';
      case 'practice': return 'badge-practice';
      case 'history': return 'badge-history';
      case 'thoughts': return 'badge-thoughts';
      default: return 'badge-default';
    }
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Load column data from /data/columns.json
  async function fetchColumns() {
    try {
      const response = await fetch('/data/columns.json');
      if (!response.ok) throw new Error('Failed to fetch columns data');
      allColumns = await response.json();
      initHomeColumns();
      initColumnsPage();
      checkUrlQuery();
    } catch (err) {
      console.warn('Columns data loading error:', err);
    }
  }

  // Render top 3 columns on Home Page
  function initHomeColumns() {
    const container = document.getElementById('home-columns-grid');
    if (!container) return;

    const topColumns = allColumns.slice(0, 3);
    container.innerHTML = topColumns.map((column, idx) => renderColumnCard(column, idx)).join('');
  }

  // Render Column List Page
  function initColumnsPage() {
    const container = document.getElementById('columns-grid');
    if (!container) return;

    renderFilteredColumns();
    setupCategoryTabs();
  }

  function renderFilteredColumns() {
    const container = document.getElementById('columns-grid');
    if (!container) return;

    const filtered = currentCategory === 'all'
      ? allColumns
      : allColumns.filter(c => c.categorySlug === currentCategory);

    if (filtered.length === 0) {
      container.innerHTML = '<div class="column-empty"><p>該当するコラムが見つかりませんでした。</p></div>';
      return;
    }

    container.innerHTML = filtered.map((column, idx) => renderColumnCard(column, currentCategory === 'all' ? idx : -1)).join('');
  }

  function renderColumnCard(item, index) {
    const tagClass = getCategoryTagClass(item.categorySlug || '');
    const isNew = (index === 0);
    const newBadgeHtml = isNew ? '<span class="column-badge-new">NEW 新着</span>' : '';
    
    return `
      <article class="column-card ${isNew ? 'is-new-card' : ''}" tabindex="0" data-column-id="${item.id}" onclick="window.openColumnModal('${item.id}')">
        <div class="column-card-media">
          <img src="${item.thumbnail}" alt="${escapeHtml(item.title)}" loading="lazy">
          <span class="column-badge ${tagClass}">${escapeHtml(item.category)}</span>
          ${newBadgeHtml}
        </div>
        <div class="column-card-body">
          <div class="column-meta">
            <time datetime="${item.date.replace(/\./g, '-')}">${item.date}</time>
            <span class="column-read-time">${item.readTime || ''}</span>
          </div>
          <h3 class="column-title">${escapeHtml(item.title)}</h3>
          <p class="column-excerpt">${escapeHtml(item.excerpt)}</p>
          <div class="column-card-footer">
            <span class="column-read-more">続きを読む <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg></span>
          </div>
        </div>
      </article>
    `;
  }

  function setupCategoryTabs() {
    const tabs = document.querySelectorAll('.category-filter-tabs .filter-tab');
    if (!tabs || tabs.length === 0) return;

    tabs.forEach(tab => {
      tab.addEventListener('click', (e) => {
        tabs.forEach(t => t.classList.remove('active'));
        e.currentTarget.classList.add('active');
        currentCategory = e.currentTarget.getAttribute('data-category') || 'all';
        renderFilteredColumns();
      });
    });
  }

  function formatColumnBody(content) {
    if (!content) return '';
    
    // Remove ** asterisks
    let cleaned = content.replace(/\*\*/g, '');
    
    // Split into lines
    const lines = cleaned.split('\n');
    const resultHtml = [];
    let i = 0;
    
    while (i < lines.length) {
      let line = lines[i].trim();
      
      if (!line) {
        i++;
        continue;
      }
      
      // Horizontal Rule
      if (line === '---') {
        resultHtml.push('<hr class="column-content-hr">');
        i++;
        continue;
      }
      
      // Headings
      if (line.startsWith('#')) {
        const headingText = line.replace(/^#+\s*/, '');
        const match = line.match(/^#+/);
        const level = match ? match[0].length : 1;
        
        if (level <= 2) {
          const isYearHeading = /^(19\d{2}|20\d{2}|前史)/.test(headingText.trim());
          const eraPill = isYearHeading ? '<span class="h2-era-pill">時代</span>' : '';
          resultHtml.push(`<h2 class="column-content-h2">${eraPill}${escapeHtml(headingText)}</h2>`);
        } else {
          let headingClass = 'column-content-heading';
          let icon = '📌';
          if (headingText.includes('ポイント') || headingText.includes('主な進化') || headingText.includes('改良')) {
            headingClass = 'column-content-heading-point';
            icon = '✨';
          } else if (headingText.includes('歴史的意味') || headingText.includes('この年の意味')) {
            headingClass = 'column-content-heading-meaning';
            icon = '🏛️';
          } else if (headingText.includes('問題') || headingText.includes('決戦')) {
            headingClass = 'column-content-heading-warning';
            icon = '⚠️';
          }
          resultHtml.push(`<h3 class="${headingClass}"><span class="heading-icon">${icon}</span> ${escapeHtml(headingText)}</h3>`);
        }
        i++;
        continue;
      }
      
      // Bullet List Block (* or -)
      if (line.startsWith('* ') || line.startsWith('- ')) {
        const listItems = [];
        while (i < lines.length && (lines[i].trim().startsWith('* ') || lines[i].trim().startsWith('- '))) {
          const itemText = lines[i].trim().replace(/^[*-\s]+/, '');
          listItems.push(itemText);
          i++;
        }
        
        if (listItems.length > 0) {
          let listHtml = '<ul class="column-feature-list">';
          listItems.forEach(item => {
            listHtml += `<li class="column-feature-item">${escapeHtml(item)}</li>`;
          });
          listHtml += '</ul>';
          resultHtml.push(listHtml);
        }
        continue;
      }
      
      // Markdown Table Start
      if (line.startsWith('|')) {
        const tableLines = [];
        while (i < lines.length && lines[i].trim().startsWith('|')) {
          tableLines.push(lines[i].trim());
          i++;
        }
        
        if (tableLines.length > 0) {
          let tableHtml = '<div class="column-table-responsive"><table class="column-table">';
          let isHeader = true;
          
          tableLines.forEach(tline => {
            if (tline.includes('---')) return;
            
            const rawCells = tline.split('|');
            const cells = rawCells.slice(1, rawCells.length - 1).map(c => c.trim());
            if (isHeader) {
              tableHtml += '<thead><tr>' + cells.map(c => `<th>${escapeHtml(c)}</th>`).join('') + '</tr></thead><tbody>';
              isHeader = false;
            } else {
              tableHtml += '<tr>' + cells.map(c => `<td>${escapeHtml(c)}</td>`).join('') + '</tr>';
            }
          });
          
          tableHtml += '</tbody></table></div>';
          resultHtml.push(tableHtml);
        }
        continue;
      }
      
      // Image HTML
      if (line.startsWith('<img') || line.startsWith('<figure')) {
        resultHtml.push(`<div class="column-content-image">${line}</div>`);
        i++;
        continue;
      }
      
      // Regular Paragraph: Ensure leading full-width space 　
      let text = line;
      if (!text.startsWith('　')) {
        text = '　' + text;
      }
      resultHtml.push(`<p class="column-paragraph">${escapeHtml(text)}</p>`);
      i++;
    }
    
    return resultHtml.join('\n');
  }

  // Modal logic
  window.openColumnModal = function(id) {
    const item = allColumns.find(c => c.id === id);
    if (!item) return;

    let modal = document.getElementById('column-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'column-modal';
      modal.className = 'column-modal-backdrop';
      document.body.appendChild(modal);
    }

    const tagClass = getCategoryTagClass(item.categorySlug || '');
    const tagsHtml = (item.tags || []).map(t => `<span class="column-modal-tag">#${escapeHtml(t)}</span>`).join(' ');

    modal.innerHTML = `
      <div class="column-modal-dialog" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <button class="column-modal-close" aria-label="閉じる" onclick="window.closeColumnModal()">&times;</button>
        <div class="column-modal-content">
          <div class="column-modal-header">
            <div class="column-meta" style="margin-bottom:8px;">
              <span class="column-badge ${tagClass}">${escapeHtml(item.category)}</span>
              <time datetime="${item.date.replace(/\./g, '-')}">${item.date}</time>
              <span class="column-read-time">${item.readTime || ''}</span>
            </div>
            <h2 id="modal-title" class="column-modal-title">${escapeHtml(item.title)}</h2>
            <div class="column-modal-tags">${tagsHtml}</div>
          </div>
          <div class="column-modal-media">
            <img src="${item.thumbnail}" alt="${escapeHtml(item.title)}">
          </div>
          <div class="column-modal-body">
            <p class="column-modal-lead">${escapeHtml(item.excerpt)}</p>
            <hr class="column-modal-divider">
            <div class="column-modal-text">${formatColumnBody(item.content)}</div>
          </div>
          <div class="column-modal-footer">
            <button class="btn btn-secondary" onclick="window.closeColumnModal()">閉じる</button>
          </div>
        </div>
      </div>
    `;

    modal.classList.add('is-open');
    document.body.style.overflow = 'hidden';

    modal.onclick = function(e) {
      if (e.target === modal) {
        window.closeColumnModal();
      }
    };
  };

  window.closeColumnModal = function() {
    const modal = document.getElementById('column-modal');
    if (modal) {
      modal.classList.remove('is-open');
    }
    document.body.style.overflow = '';
  };

  function checkUrlQuery() {
    const params = new URLSearchParams(window.location.search);
    const articleId = params.get('article');
    if (articleId && allColumns.length > 0) {
      window.openColumnModal(articleId);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', fetchColumns);
  } else {
    fetchColumns();
  }
})();
