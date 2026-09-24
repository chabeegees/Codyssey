/* ==========================================================================
   nav.js — 네비게이션과 스크롤 관련 인터랙션
   --------------------------------------------------------------------------
   여기서 다루는 것
     1. 햄버거 메뉴 토글 (classList.toggle)
     2. 부드러운 스크롤 + 메뉴 클릭 시 자동 닫힘
     3. 스크롤 위치에 따른 헤더 스타일 변경  (임계값 60px)
     4. 스크롤 탑 버튼 노출/이동          (임계값 300px)
     5. IntersectionObserver 스크롤 애니메이션 (threshold 0.2)
     6. 현재 보고 있는 섹션의 메뉴 항목 강조
   ========================================================================== */

(() => {
  /* 임계값은 한 곳에 모아둡니다. README에도 같은 값을 적어두었습니다. */
  const HEADER_SCROLL_THRESHOLD = 60;   // px — 헤더 배경이 생기는 지점
  const SCROLL_TOP_THRESHOLD = 300;     // px — 맨 위로 버튼이 나타나는 지점
  const REVEAL_THRESHOLD = 0.2;         // 요소의 20%가 보이면 등장 애니메이션 실행

  const header = document.querySelector('#header');
  const navToggle = document.querySelector('#nav-toggle');
  const navMenu = document.querySelector('#nav-menu');
  const navLinks = document.querySelectorAll('.nav__link');
  const scrollTopButton = document.querySelector('#scroll-top');
  const revealTargets = document.querySelectorAll('.reveal');
  const sections = document.querySelectorAll('main section[id]');

  /* ---------------------------------------------------------------
     1. 햄버거 메뉴
     --------------------------------------------------------------- */
  const closeMenu = () => {
    navMenu.classList.remove('active');
    navToggle.classList.remove('active');
    navToggle.setAttribute('aria-expanded', 'false');
    navToggle.setAttribute('aria-label', '메뉴 열기');
  };

  navToggle.addEventListener('click', () => {
    const isOpen = navMenu.classList.toggle('active');
    navToggle.classList.toggle('active', isOpen);
    navToggle.setAttribute('aria-expanded', String(isOpen));
    navToggle.setAttribute('aria-label', isOpen ? '메뉴 닫기' : '메뉴 열기');
  });

  /* 메뉴 항목을 누르면 이동과 동시에 메뉴를 닫습니다.
     스크롤 자체는 CSS의 scroll-behavior: smooth가 처리합니다. */
  navLinks.forEach((link) => {
    link.addEventListener('click', closeMenu);
  });

  /* 메뉴 바깥을 누르거나 Esc를 누르면 닫습니다. */
  document.addEventListener('click', (event) => {
    const clickedInsideNav = event.target.closest('.nav');
    if (!clickedInsideNav) closeMenu();
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeMenu();
  });

  /* 데스크톱 폭으로 넓어지면 열려 있던 모바일 메뉴 상태를 정리합니다. */
  window.matchMedia('(min-width: 768px)').addEventListener('change', (event) => {
    if (event.matches) closeMenu();
  });

  /* ---------------------------------------------------------------
     2. 스크롤에 반응하는 헤더 & 맨 위로 버튼
     --------------------------------------------------------------- */
  const handleScroll = () => {
    const offset = window.scrollY;

    header.classList.toggle('is-scrolled', offset > HEADER_SCROLL_THRESHOLD);
    scrollTopButton.classList.toggle('is-visible', offset > SCROLL_TOP_THRESHOLD);
  };

  window.addEventListener('scroll', handleScroll, { passive: true });
  handleScroll(); // 새로고침으로 중간 위치에서 시작한 경우를 대비해 한 번 실행

  scrollTopButton.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  /* ---------------------------------------------------------------
     3. 스크롤 등장 애니메이션
     --------------------------------------------------------------- */
  const revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach(({ isIntersecting, target }) => {
        if (!isIntersecting) return;
        target.classList.add('is-visible');
        revealObserver.unobserve(target); // 한 번 보여준 뒤에는 더 관찰하지 않습니다
      });
    },
    { threshold: REVEAL_THRESHOLD }
  );

  revealTargets.forEach((target) => revealObserver.observe(target));

  /* ---------------------------------------------------------------
     4. 현재 섹션의 메뉴 항목 강조
     --------------------------------------------------------------- */
  const sectionObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach(({ isIntersecting, target }) => {
        if (!isIntersecting) return;

        navLinks.forEach((link) => {
          const isCurrent = link.getAttribute('href') === `#${target.id}`;
          link.classList.toggle('is-active', isCurrent);
        });
      });
    },
    { rootMargin: '-45% 0px -50% 0px' } // 화면 중앙을 지나는 섹션을 현재 섹션으로 봅니다
  );

  sections.forEach((section) => sectionObserver.observe(section));
})();
