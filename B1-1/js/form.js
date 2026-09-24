/* ==========================================================================
   form.js — 흐름 ③ 문의 폼 유효성 검사
   --------------------------------------------------------------------------
   입력/제출  →  App.setState({ formErrors, formStatus })
              →  renderForm()이 에러 메시지와 상태 문구를 그립니다.

   검사 규칙(validate)은 순수 함수입니다. 값을 받아 에러 객체를 돌려줄 뿐,
   화면은 건드리지 않습니다. 화면 반영은 renderForm() 한 곳에서만 합니다.
   ========================================================================== */

(() => {
  const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  const MIN_MESSAGE_LENGTH = 10;
  const CONTACT_EMAIL = 'chabee2027@gmail.com';

  const form = document.querySelector('#contact-form');
  const statusElement = document.querySelector('#form-status');

  /* 필드 이름 → 관련 DOM 요소를 한 번만 찾아 둡니다. */
  const fields = ['name', 'email', 'message'].map((name) => ({
    name,
    input: document.querySelector(`#${name}`),
    wrapper: document.querySelector(`#${name}`).closest('.field'),
    errorElement: document.querySelector(`#${name}-error`),
  }));

  /* ---------------------------------------------------------------
     1. 검사 규칙 — 값만 보고 에러 객체를 만듭니다
     --------------------------------------------------------------- */
  const validate = ({ name, email, message }) => {
    const errors = {};

    if (name.trim() === '') {
      errors.name = '이름을 입력해 주세요.';
    } else if (name.trim().length < 2) {
      errors.name = '이름은 2자 이상 입력해 주세요.';
    }

    if (email.trim() === '') {
      errors.email = '이메일을 입력해 주세요.';
    } else if (!EMAIL_PATTERN.test(email.trim())) {
      errors.email = '이메일 형식이 올바르지 않습니다. (예: you@example.com)';
    }

    if (message.trim() === '') {
      errors.message = '메시지를 입력해 주세요.';
    } else if (message.trim().length < MIN_MESSAGE_LENGTH) {
      errors.message = `메시지는 ${MIN_MESSAGE_LENGTH}자 이상 입력해 주세요.`;
    }

    return errors;
  };

  /** 지금 폼에 입력된 값을 읽어옵니다. */
  const readValues = () => {
    const formData = new FormData(form);
    return {
      name: formData.get('name') ?? '',
      email: formData.get('email') ?? '',
      message: formData.get('message') ?? '',
    };
  };

  /* ---------------------------------------------------------------
     2. 렌더 — 에러 상태를 화면에 반영하는 유일한 함수
     --------------------------------------------------------------- */
  const renderForm = ({ formErrors, formStatus, formMessage }) => {
    fields.forEach(({ name, input, wrapper, errorElement }) => {
      const message = formErrors[name] ?? '';

      wrapper.classList.toggle('has-error', message !== '');
      errorElement.textContent = message;
      input.setAttribute('aria-invalid', String(message !== ''));
    });

    statusElement.textContent = formMessage;
    statusElement.classList.toggle('is-success', formStatus === 'success');
    statusElement.classList.toggle('is-error', formStatus === 'error');
  };

  App.subscribe(renderForm);

  /* ---------------------------------------------------------------
     3. 이벤트 — 상태만 바꿉니다
     --------------------------------------------------------------- */

  /* 입력 중에는 "이미 에러가 떠 있는 필드"만 다시 검사합니다.
     아직 건드리지 않은 필드에 미리 에러를 띄우면 방해가 되기 때문입니다. */
  fields.forEach(({ name, input }) => {
    input.addEventListener('input', () => {
      const { formErrors } = App.getState();
      if (!(name in formErrors)) return;

      const nextErrors = { ...formErrors };
      const freshError = validate(readValues())[name];

      if (freshError) {
        nextErrors[name] = freshError;
      } else {
        delete nextErrors[name];
      }

      App.setState({ formErrors: nextErrors });
    });
  });

  form.addEventListener('submit', (event) => {
    event.preventDefault(); // 브라우저 기본 제출(페이지 이동)을 막습니다

    const values = readValues();
    const errors = validate(values);
    const hasError = Object.keys(errors).length > 0;

    if (hasError) {
      App.setState({
        formErrors: errors,
        formStatus: 'error',
        formMessage: '입력하신 내용을 다시 확인해 주세요.',
      });

      /* 첫 번째 에러 필드로 포커스를 옮겨 바로 고칠 수 있게 합니다. */
      const firstInvalid = fields.find(({ name }) => name in errors);
      firstInvalid.input.focus();
      return;
    }

    /* 통과 — 백엔드가 없는 정적 사이트이므로 메일 클라이언트를 엽니다. */
    const { name, email, message } = values;
    const subject = encodeURIComponent(`[포트폴리오 문의] ${name.trim()}님`);
    const body = encodeURIComponent(`${message.trim()}\n\n---\n보낸 사람: ${name.trim()} <${email.trim()}>`);

    window.location.href = `mailto:${CONTACT_EMAIL}?subject=${subject}&body=${body}`;

    App.setState({
      formErrors: {},
      formStatus: 'success',
      formMessage: `${name.trim()}님, 감사합니다! 메일 앱이 열리지 않으면 ${CONTACT_EMAIL}로 보내주세요.`,
    });

    form.reset();
  });

  /* 푸터 저작권 연도는 매년 바꾸지 않아도 되도록 자동으로 채웁니다. */
  document.querySelector('#year').textContent = String(new Date().getFullYear());
})();
