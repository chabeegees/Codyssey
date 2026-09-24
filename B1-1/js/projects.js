/* ==========================================================================
   projects.js — 흐름 ② GitHub API 연동 + 흐름 ④ 언어 필터
   --------------------------------------------------------------------------
   fetch  →  App.setState({ projectsStatus: 'loading' | 'success' | 'error' | 'empty' })
          →  renderProjects()가 네 가지 화면 중 하나를 그립니다.

   화면을 그리는 코드는 renderProjects() 하나뿐입니다.
   다른 함수들은 상태만 바꾸고, 무엇을 그릴지는 상태가 결정합니다.
   ========================================================================== */

(() => {
  /* 조회할 GitHub 계정. 배열에 아이디를 추가하면 그대로 합쳐서 보여줍니다. */
  const GITHUB_USERNAMES = ['chabeegees', 'junhyeok-cha'];
  const REPOS_PER_USER = 100;

  const viewElement = document.querySelector('#projects-view');
  const filtersElement = document.querySelector('#project-filters');

  /* ---------------------------------------------------------------
     1. 데이터 가져오기
     --------------------------------------------------------------- */

  /**
   * 한 계정의 저장소 목록을 가져옵니다.
   * 실패하면 호출한 쪽에서 잡을 수 있도록 에러를 던집니다.
   */
  const fetchReposOf = async (username) => {
    const endpoint =
      `https://api.github.com/users/${username}/repos` +
      `?per_page=${REPOS_PER_USER}&sort=updated`;

    const response = await fetch(endpoint, {
      headers: { Accept: 'application/vnd.github+json' },
    });

    if (!response.ok) {
      /* 인증 없이 호출하면 시간당 60회 제한이 있습니다. 초과 시 403이 옵니다. */
      if (response.status === 403) {
        throw new Error(
          'GitHub API 요청 한도(시간당 60회)를 초과했습니다. 잠시 후 다시 시도해 주세요.'
        );
      }
      if (response.status === 404) {
        throw new Error(`'${username}' 계정을 찾을 수 없습니다.`);
      }
      throw new Error(`GitHub API 응답 오류 (HTTP ${response.status})`);
    }

    return response.json();
  };

  /**
   * 카드에 필요한 값만 남깁니다. (구조분해 할당으로 필요한 키만 꺼냅니다)
   */
  const toProject = ({
    id,
    name,
    description,
    html_url: url,
    language,
    stargazers_count: stars,
    forks_count: forks,
    topics = [],
    updated_at: updatedAt,
    owner: { login: owner },
  }) => ({
    id,
    name,
    description,
    url,
    language: language ?? 'Other',
    stars,
    forks,
    topics: topics.slice(0, 4),
    updatedAt,
    owner,
  });

  /** 모든 계정의 저장소를 가져와 정리합니다. */
  const loadProjects = async () => {
    App.setState({ projectsStatus: 'loading', projectsError: '' });

    try {
      const responses = await Promise.all(GITHUB_USERNAMES.map(fetchReposOf));

      const projects = responses
        .flat()
        .filter(({ fork }) => !fork)                       // 포크한 저장소는 제외
        .map(toProject)
        .sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));

      if (projects.length === 0) {
        App.setState({ projectsStatus: 'empty', projects: [] });
        return;
      }

      App.setState({
        projectsStatus: 'success',
        projects,
        activeLanguage: 'All',
      });
    } catch (error) {
      /* fetch는 네트워크 자체가 끊기면 TypeError를 던집니다.
         이때의 기본 메시지('Failed to fetch')는 사용자에게 의미가 없으므로 바꿔줍니다. */
      const detail =
        error instanceof TypeError
          ? '네트워크에 연결할 수 없습니다. 인터넷 연결을 확인한 뒤 다시 시도해 주세요.'
          : error.message;

      App.setState({
        projectsStatus: 'error',
        projects: [],
        projectsError: detail,
      });
    }
  };

  /* ---------------------------------------------------------------
     2. HTML 조각 만들기 (템플릿 리터럴)
     --------------------------------------------------------------- */

  const formatDate = (isoString) =>
    new Date(isoString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });

  /* 사용자 입력이 아닌 API 응답이지만, 저장소 설명에 <나 &가 들어갈 수 있으므로
     innerHTML에 넣기 전에 이스케이프합니다. */
  const escapeHtml = (value) =>
    String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');

  const cardTemplate = ({
    name,
    description,
    url,
    language,
    stars,
    forks,
    topics,
    updatedAt,
    owner,
  }) => `
    <article class="card">
      <p class="card__owner">${escapeHtml(owner)}</p>
      <h3 class="card__title">
        <a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">
          ${escapeHtml(name)}
        </a>
      </h3>
      <p class="card__desc">
        ${escapeHtml(description) || '등록된 설명이 없는 저장소입니다.'}
      </p>
      ${
        topics.length > 0
          ? `<ul class="card__topics">
               ${topics.map((topic) => `<li class="card__topic">${escapeHtml(topic)}</li>`).join('')}
             </ul>`
          : ''
      }
      <div class="card__meta">
        <span class="card__meta-item">
          <span class="card__lang-dot" aria-hidden="true"></span>${escapeHtml(language)}
        </span>
        <span class="card__meta-item">★ ${stars}</span>
        <span class="card__meta-item">⑂ ${forks}</span>
        <span class="card__meta-item">${formatDate(updatedAt)} 업데이트</span>
      </div>
    </article>
  `;

  const loadingTemplate = () => `
    <div class="state">
      <div class="spinner" aria-hidden="true"></div>
      <p class="state__title">프로젝트를 불러오는 중...</p>
      <p class="state__desc">GitHub API에서 저장소 목록을 가져오고 있습니다.</p>
    </div>
    <div class="skeleton-grid" aria-hidden="true">
      <div class="skeleton"></div>
      <div class="skeleton"></div>
      <div class="skeleton"></div>
    </div>
  `;

  const errorTemplate = (detail) => `
    <div class="state">
      <p class="state__title">프로젝트를 불러올 수 없습니다</p>
      <p class="state__desc">${escapeHtml(detail)}</p>
      <button class="btn btn--primary btn--sm" id="projects-retry" type="button">다시 시도</button>
    </div>
  `;

  const emptyTemplate = () => `
    <div class="state">
      <p class="state__title">표시할 프로젝트가 없습니다</p>
      <p class="state__desc">공개된 저장소가 아직 없습니다. 새 저장소를 공개하면 이곳에 자동으로 나타납니다.</p>
    </div>
  `;

  const noMatchTemplate = (language) => `
    <div class="state">
      <p class="state__title">'${escapeHtml(language)}' 프로젝트가 없습니다</p>
      <p class="state__desc">다른 언어를 선택하거나 'All'을 눌러 전체 목록을 확인해 주세요.</p>
    </div>
  `;

  /* ---------------------------------------------------------------
     3. 렌더 — 상태 하나만 보고 화면 전체를 결정합니다
     --------------------------------------------------------------- */

  const renderFilters = (projects, activeLanguage) => {
    /* Set으로 중복 없는 언어 목록을 만듭니다. */
    const languages = ['All', ...new Set(projects.map(({ language }) => language))];

    filtersElement.innerHTML = languages
      .map(
        (language) => `
          <button class="filter ${language === activeLanguage ? 'is-active' : ''}"
                  type="button"
                  data-language="${escapeHtml(language)}"
                  aria-pressed="${language === activeLanguage}">
            ${escapeHtml(language)}
          </button>`
      )
      .join('');

    /* 언어가 한 종류뿐이면 필터가 의미 없으므로 감춥니다. */
    filtersElement.hidden = languages.length <= 2;
  };

  const renderProjects = ({ projectsStatus, projects, projectsError, activeLanguage }) => {
    viewElement.setAttribute('aria-busy', String(projectsStatus === 'loading'));

    if (projectsStatus === 'idle' || projectsStatus === 'loading') {
      filtersElement.hidden = true;
      viewElement.innerHTML = loadingTemplate();
      return;
    }

    if (projectsStatus === 'error') {
      filtersElement.hidden = true;
      viewElement.innerHTML = errorTemplate(projectsError);
      return;
    }

    if (projectsStatus === 'empty') {
      filtersElement.hidden = true;
      viewElement.innerHTML = emptyTemplate();
      return;
    }

    /* 성공 상태 */
    renderFilters(projects, activeLanguage);

    const visibleProjects =
      activeLanguage === 'All'
        ? projects
        : projects.filter(({ language }) => language === activeLanguage);

    viewElement.innerHTML =
      visibleProjects.length > 0
        ? `<div class="project-grid">${visibleProjects.map(cardTemplate).join('')}</div>`
        : noMatchTemplate(activeLanguage);
  };

  App.subscribe(renderProjects);

  /* ---------------------------------------------------------------
     4. 이벤트 — 다시 그려지는 요소라 상위 요소에 한 번만 연결합니다
     --------------------------------------------------------------- */

  viewElement.addEventListener('click', (event) => {
    if (event.target.closest('#projects-retry')) loadProjects();
  });

  filtersElement.addEventListener('click', (event) => {
    const button = event.target.closest('.filter');
    if (!button) return;

    App.setState({ activeLanguage: button.dataset.language });
  });

  /* 첫 로드 */
  loadProjects();
})();
