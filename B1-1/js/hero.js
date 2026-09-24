/* ==========================================================================
   hero.js — 보너스: Hero 섹션 타이핑 효과
   --------------------------------------------------------------------------
   문구를 한 글자씩 쓰고, 잠시 멈췄다가, 한 글자씩 지우고 다음 문구로 넘어갑니다.
   setTimeout을 재귀적으로 호출해 단계마다 다른 속도를 줍니다.
   ========================================================================== */

(() => {
  const PHRASES = [
    '효율성을 지향하는 AI 서비스 빌더',
    '문제 정의 → 시장 이해 → AI 도입',
    '꼭 필요한 곳에만 AI를 씁니다',
    '운영까지 감당 가능한 설계를 합니다',
  ];

  const TYPING_SPEED = 90;    // ms — 한 글자 입력 간격
  const DELETING_SPEED = 40;  // ms — 한 글자 삭제 간격
  const HOLD_DURATION = 1600; // ms — 문구를 다 쓴 뒤 머무는 시간

  const target = document.querySelector('#typing-text');

  let phraseIndex = 0;
  let charCount = 0;
  let isDeleting = false;

  const tick = () => {
    const phrase = PHRASES[phraseIndex];

    charCount += isDeleting ? -1 : 1;
    target.textContent = phrase.slice(0, charCount);

    /* 다 썼으면 잠시 멈췄다가 삭제로 전환 */
    if (!isDeleting && charCount === phrase.length) {
      isDeleting = true;
      setTimeout(tick, HOLD_DURATION);
      return;
    }

    /* 다 지웠으면 다음 문구로 */
    if (isDeleting && charCount === 0) {
      isDeleting = false;
      phraseIndex = (phraseIndex + 1) % PHRASES.length;
    }

    setTimeout(tick, isDeleting ? DELETING_SPEED : TYPING_SPEED);
  };

  /* 움직임을 줄이도록 설정한 사용자에게는 첫 문구만 고정으로 보여줍니다. */
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    target.textContent = PHRASES[0];
    return;
  }

  tick();
})();
