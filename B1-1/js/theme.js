/* ==========================================================================
   theme.js — 흐름 ① 다크 모드
   --------------------------------------------------------------------------
   토글 클릭  →  App.setState({ theme })  →  renderTheme()이
   <html data-theme="...">를 바꾸면, style.css의 변수 세트가 통째로 교체됩니다.
   선택한 테마는 로컬스토리지에 저장해 새로고침 후에도 유지합니다.
   ========================================================================== */

(() => {
  const STORAGE_KEY = 'chabee-portfolio-theme';

  const root = document.documentElement;
  const toggleButton = document.querySelector('#theme-toggle');

  /**
   * 처음 적용할 테마를 결정합니다.
   * 1순위: 사용자가 이전에 고른 값(로컬스토리지)
   * 2순위: 운영체제의 다크 모드 설정(prefers-color-scheme)
   */
  const getInitialTheme = () => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'light' || saved === 'dark') return saved;

    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    return prefersDark ? 'dark' : 'light';
  };

  /* ---- 렌더: 상태(theme)를 화면에 반영하는 유일한 함수 ---- */
  const renderTheme = ({ theme }) => {
    root.setAttribute('data-theme', theme);

    const isDark = theme === 'dark';
    toggleButton.setAttribute('aria-pressed', String(isDark));
    toggleButton.setAttribute('aria-label', isDark ? '라이트 모드 전환' : '다크 모드 전환');
  };

  App.subscribe(renderTheme);

  /* ---- 이벤트: 상태만 바꿉니다. DOM은 건드리지 않습니다. ---- */
  toggleButton.addEventListener('click', () => {
    const { theme } = App.getState();
    const nextTheme = theme === 'dark' ? 'light' : 'dark';

    localStorage.setItem(STORAGE_KEY, nextTheme);
    App.setState({ theme: nextTheme });
  });

  /* 사용자가 직접 고른 적이 없다면, 시스템 설정 변경을 그대로 따라갑니다. */
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (event) => {
    if (localStorage.getItem(STORAGE_KEY)) return;
    App.setState({ theme: event.matches ? 'dark' : 'light' });
  });

  /* 초기 테마 적용 */
  App.setState({ theme: getInitialTheme() });
})();
