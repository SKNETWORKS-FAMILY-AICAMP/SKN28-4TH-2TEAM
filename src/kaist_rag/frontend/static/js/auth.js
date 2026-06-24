/* ============================================================
   Auth — login & signup
   ============================================================ */
const Auth = {
  hero(title, sub){
    const s=kbStats();
    return `
    <div class="auth-hero">
      <div class="auth-blob a"></div><div class="auth-blob b"></div>
      <div class="brand"><span class="mark"><img src="${asset('images/mascot/nubzuki_idle.png')}" alt=""></span> 넙죽이 <small>KAIST 학과 안내 RAG</small></div>
      <div class="auth-hero-mid">
        <div class="auth-mascot"><div class="ring"></div><img src="${asset('images/mascot/nubzuki_done.png')}" alt="넙죽이"></div>
        <h2>${title}</h2>
        <p>${sub}</p>
      </div>
      <div class="auth-stats">
        <div class="st"><b class="tnum">${s.depts}</b><span>학과</span></div>
        <div class="st"><b class="tnum">${s.courses.toLocaleString()}</b><span>교과목</span></div>
        <div class="st"><b class="tnum">${s.people.toLocaleString()}</b><span>교수·연구진</span></div>
      </div>
    </div>`;
  },

  loginHTML(){
    return `<div class="auth view">
      ${this.hero('무엇이든 물어보세요.','넙죽이가 KAIST 학사 정보를 찾아 출처와 함께 알려드려요. 입학부터 졸업까지, 함께해요!')}
      <div class="auth-form-wrap scroll">
        <div class="auth-card pop">
          <div class="auth-mobile-brand"><div class="brand"><span class="mark"><img src="${asset('images/mascot/nubzuki_idle.png')}" alt=""></span> 넙죽이</div></div>
          <h3>다시 만나서 반가워요 👋</h3>
          <p class="sub">KAIST 계정으로 로그인하고 넙죽이와 대화를 이어가세요.</p>
          <form id="login-form" novalidate>
            <div class="field" id="f-email">
              <label>이메일</label>
              <div class="inp">${svg('mail')}<input type="email" id="li-email" placeholder="you@example.com"></div>
              <div class="err">올바른 이메일을 입력해 주세요.</div>
            </div>
            <div class="field" id="f-pw">
              <label>비밀번호</label>
              <div class="inp">${svg('lock')}<input type="password" id="li-pw" placeholder="비밀번호"><span class="eye" id="li-eye">${svg('eye')}</span></div>
              <div class="err">비밀번호는 6자 이상이에요.</div>
            </div>
            <div class="auth-row">
              <label class="check"><input type="checkbox" checked> 로그인 상태 유지</label>
              <span class="link">비밀번호 찾기</span>
            </div>
            <button type="submit" class="btn btn-primary btn-block btn-lg">로그인</button>
          </form>
          <div class="auth-or">또는</div>
          <button class="btn btn-google btn-block" id="li-google">${googleG()} Google 계정으로 계속하기</button>
          <button type="button" class="btn btn-ghost btn-block" id="li-sso" style="margin-top:10px" title="발표용 데모 버튼">${svg('cap')} KAIST SSO로 계속하기</button>
          <p class="auth-alt">아직 계정이 없으신가요? <span class="link" id="to-signup">회원가입</span></p>
        </div>
      </div>
    </div>`;
  },

  signupHTML(){
    return `<div class="auth view">
      ${this.hero('넙죽이와 함께 시작해요.','계정을 만들면 대화 기록을 저장하고, 자주 묻는 학사 정보를 더 빠르게 받아볼 수 있어요.')}
      <div class="auth-form-wrap scroll">
        <div class="auth-card pop">
          <div class="auth-mobile-brand"><div class="brand"><span class="mark"><img src="${asset('images/mascot/nubzuki_idle.png')}" alt=""></span> 넙죽이</div></div>
          <h3>회원가입</h3>
          <p class="sub">KAIST 구성원이라면 누구나 무료로 이용할 수 있어요.</p>
          <form id="signup-form" novalidate>
            <div class="field" id="s-name">
              <label>이름</label>
              <div class="inp">${svg('user')}<input id="su-name" placeholder="홍길동"></div>
              <div class="err">이름을 입력해 주세요.</div>
            </div>
            <div class="field" id="s-email">
              <label>이메일</label>
              <div class="inp">${svg('mail')}<input id="su-email" placeholder="you@example.com"></div>
              <div class="err">올바른 이메일을 입력해 주세요.</div>
            </div>
            <div class="field" id="s-pw">
              <label>비밀번호</label>
              <div class="inp">${svg('lock')}<input type="password" id="su-pw" placeholder="6자 이상"><span class="eye" id="su-eye">${svg('eye')}</span></div>
              <div class="err">비밀번호는 6자 이상이에요.</div>
            </div>
            <div class="field" id="s-pw2">
              <label>비밀번호 확인</label>
              <div class="inp">${svg('lock')}<input type="password" id="su-pw2" placeholder="비밀번호 재입력"></div>
              <div class="err">비밀번호가 일치하지 않아요.</div>
            </div>
            <div class="auth-row" style="margin-top:4px">
              <label class="check"><input type="checkbox" id="su-agree"> <span>이용약관과 개인정보 처리방침에 동의해요.</span></label>
            </div>
            <button type="submit" class="btn btn-primary btn-block btn-lg">계정 만들기</button>
          </form>
          <div class="auth-or">또는</div>
          <button class="btn btn-google btn-block" id="su-google">${googleG()} Google로 빠르게 가입하기</button>
          <p class="auth-alt">이미 계정이 있으신가요? <span class="link" id="to-login">로그인</span></p>
        </div>
      </div>
    </div>`;
  },

  initLogin(){
    const eye=document.getElementById('li-eye'), pw=document.getElementById('li-pw');
    eye.addEventListener('click', ()=>{ const t=pw.type==='password'; pw.type=t?'text':'password'; eye.innerHTML=svg(t?'eyeOff':'eye'); });
    document.getElementById('to-signup').addEventListener('click', ()=>App.go('signup'));
    /* KAIST SSO: presentation-only, intentionally non-functional */
    document.getElementById('li-google').addEventListener('click', e=>this.googleSignIn(e.currentTarget));
    document.getElementById('login-form').addEventListener('submit', async e=>{
      e.preventDefault();
      const em=document.getElementById('li-email'), p=document.getElementById('li-pw');
      let ok=true;
      ok = this.validate('f-email', /\S+@\S+\.\S+/.test(em.value)) && ok;
      ok = this.validate('f-pw', p.value.length>=6) && ok;
      if(!ok) return;
      const btn=e.submitter || e.currentTarget.querySelector('button[type="submit"]');
      this.busy(btn, true, '로그인 중…');
      try{
        const res = await Api.login(em.value.trim(), p.value, e.currentTarget.querySelector('input[type="checkbox"]').checked);
        Api.applyUser(res);
        window.location.replace('/chat/');
      }catch(err){
        this.setError('f-pw', err.message || '로그인에 실패했어요.');
      }finally{
        this.busy(btn, false, '로그인');
      }
    });
  },

  initSignup(){
    const eye=document.getElementById('su-eye'), pw=document.getElementById('su-pw');
    eye.addEventListener('click', ()=>{ const t=pw.type==='password'; pw.type=t?'text':'password'; eye.innerHTML=svg(t?'eyeOff':'eye'); });
    document.getElementById('to-login').addEventListener('click', ()=>App.go('login'));
    document.getElementById('su-google').addEventListener('click', e=>this.googleSignIn(e.currentTarget));
    document.getElementById('signup-form').addEventListener('submit', async e=>{
      e.preventDefault();
      const name=document.getElementById('su-name').value.trim();
      const em=document.getElementById('su-email').value.trim();
      const p=document.getElementById('su-pw').value, p2=document.getElementById('su-pw2').value;
      const agree=document.getElementById('su-agree').checked;
      let ok=true;
      ok = this.validate('s-name', !!name) && ok;
      ok = this.validate('s-email', /\S+@\S+\.\S+/.test(em)) && ok;
      ok = this.validate('s-pw', p.length>=6) && ok;
      ok = this.validate('s-pw2', p2===p && p2.length>=6) && ok;
      if(!agree){ ok=false; document.getElementById('su-agree').parentElement.style.color='var(--danger)'; }
      if(!ok) return;
      const btn=e.submitter || e.currentTarget.querySelector('button[type="submit"]');
      this.busy(btn, true, '계정 생성 중…');
      try{
        const res = await Api.signup(name, em, p);
        Api.applyUser(res);
        window.location.replace('/chat/');
      }catch(err){
        this.setError('s-email', err.message || '회원가입에 실패했어요.');
      }finally{
        this.busy(btn, false, '계정 만들기');
      }
    });
  },

  googleSignIn(btn){
    // OAuth/SSO is intentionally out of scope for this iteration.
    const orig = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `아직 준비 중이에요`;
    setTimeout(()=>{ btn.disabled = false; btn.innerHTML = orig; }, 1100);
  },

  validate(fieldId, cond){
    document.getElementById(fieldId).classList.toggle('invalid', !cond);
    return cond;
  },

  setError(fieldId, message){
    const field = document.getElementById(fieldId);
    field.classList.add('invalid');
    const err = field.querySelector('.err');
    if(err) err.textContent = message;
  },

  busy(btn, on, label){
    if(!btn) return;
    btn.disabled = on;
    btn.textContent = label;
  },
};
