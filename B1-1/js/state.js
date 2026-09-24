/* ==========================================================================
   state.js — 아주 작은 상태 저장소
   --------------------------------------------------------------------------
   이 사이트의 모든 기능은 같은 흐름을 따릅니다.

       사용자 이벤트  →  App.setState({ ... })  →  등록된 렌더 함수 실행

   React의 useState가 하는 일을 최소한으로 흉내 낸 것입니다.
   화면을 직접 건드리는 코드는 언제나 렌더 함수 안에만 있고,
   이벤트 핸들러는 상태만 바꿉니다. 이 규칙 덕분에 "지금 화면이 왜 이런가"를
   상태 객체 하나만 보고 설명할 수 있습니다.

   defer로 불러오는 첫 번째 스크립트이므로, 뒤따르는 스크립트들은
   전역 App 객체를 그대로 사용할 수 있습니다.
   ========================================================================== */

const App = (() => {
  /* 앱 전체의 상태. 여기 있는 값이 화면의 "진실"입니다. */
  const state = {
    /* 흐름 ① 테마 */
    theme: 'light',              // 'light' | 'dark'

    /* 흐름 ② 프로젝트(GitHub API) */
    projectsStatus: 'idle',      // 'idle' | 'loading' | 'success' | 'error' | 'empty'
    projects: [],                // 성공 시 저장소 배열
    projectsError: '',           // 에러 상태에서 보여줄 메시지
    activeLanguage: 'All',       // 흐름 ④ 언어 필터

    /* 흐름 ③ 문의 폼 */
    formErrors: {},              // { name: '이름을 입력해 주세요', ... }
    formStatus: 'idle',          // 'idle' | 'success' | 'error'
    formMessage: '',
  };

  /* setState가 호출될 때마다 실행할 렌더 함수들 */
  const renderers = [];

  /**
   * 렌더 함수를 등록합니다. 등록 즉시 한 번 실행해 초기 화면을 그립니다.
   * @param {(state: object) => void} renderer
   */
  const subscribe = (renderer) => {
    renderers.push(renderer);
    renderer(state);
  };

  /**
   * 상태를 부분적으로 갱신하고 모든 렌더 함수를 다시 실행합니다.
   * @param {object} patch 바꾸고 싶은 키만 담은 객체
   */
  const setState = (patch) => {
    Object.assign(state, patch);
    renderers.forEach((renderer) => renderer(state));
  };

  /** 현재 상태의 사본을 돌려줍니다. (밖에서 직접 수정하지 못하도록) */
  const getState = () => ({ ...state });

  return { subscribe, setState, getState };
})();
