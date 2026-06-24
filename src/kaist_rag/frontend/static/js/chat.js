/* ============================================================
   Chat view — sessions + thread + composer
   Real retrieval (Search over KB_DATA) + optional LLM answer
   ============================================================ */
const SESSION_Q  = {
  s1:'AI컴퓨팅학과 전공 과목 알려줘',
  s2:'AI대학 교수님 알려줘',
  s3:'자연과학대학 입학은 어떻게 준비해?',
  s4:'화학과 교수님 연구분야 알려줘',
  s5:'단과대학이랑 학과 목록 알려줘',
  s6:'생명과학과 과목 알려줘',
};

const Chat = {
  msgSeq:0, busy:false, idleTimer:null, activeSession:null,

  railHTML(){
    const grouped = {};
    SESSIONS.forEach(s=>{ (grouped[s.day]=grouped[s.day]||[]).push(s); });
    let railList='';
    Object.keys(grouped).forEach(day=>{
      railList += `<div class="rail-sec">${day}</div>`;
      grouped[day].forEach(s=>{
        railList += `<div class="sess" data-sess="${s.id}" data-title="${s.title}">
          <div class="sess-ic">${svg(s.icon||'message')}</div>
          <div class="sess-body"><div class="sess-title">${this.esc(s.title)}</div><div class="sess-meta">${this.esc(s.meta||'')}</div></div>
        </div>`;
      });
    });
    return railList;
  },

  viewHTML(){
    const railList=this.railHTML();
    const railCollapsed = window.sessionStorage?.getItem('communityRailCollapsed') === '1' || Boolean(window.Community && Community.railCollapsed);

    return `
    <div class="chat-shell">
      <aside class="rail scroll${railCollapsed ? ' collapsed' : ''}" id="rail">
        <div class="rail-top">
          <div class="brand"><span class="mark"><img src="${asset('images/mascot/nubzuki_idle.png')}" alt=""></span> 넙죽이 <small>KAIST 학과 안내</small></div>
        </div>
        <button class="rail-new" id="new-chat">${svg('plus')} 새 대화 시작</button>
        <div class="rail-search">${svg('search')}<input placeholder="대화 검색" id="rail-search-inp"></div>
        <div class="rail-list scroll" id="rail-list">${railList}</div>
        <div class="rail-foot">
          <div class="user-card" id="user-card">
            <div class="avatar">${CURRENT_USER.initial}</div>
            <div class="uc-body"><div class="uc-name">${CURRENT_USER.name}</div><div class="uc-mail">${CURRENT_USER.mail}</div></div>
            ${svg('logout','')}
          </div>
        </div>
      </aside>

      <main class="chat-main">
        <header class="chat-head">
          <button class="iconbtn" id="rail-toggle" title="사이드바">${svg('sidebar')}</button>
          <div>
            <div class="ch-title" id="chat-title">새 대화</div>
            <div class="ch-sub">KAIST AI대학 · 자연과학대학 · 생명과학기술대학 안내</div>
          </div>
          <div class="spacer"></div>
          ${window.Community ? Community.topNav('chat') : ''}
          ${CURRENT_USER.role==='admin' ? `<button class="btn btn-soft btn-sm" id="go-admin">${svg('chart')} 관리자</button>`:''}
          <button class="iconbtn" id="toggle-theme" title="테마">${svg('moon')}</button>
        </header>

        <div class="thread scroll" id="thread"><div class="thread-inner" id="thread-inner"></div></div>

        <div class="composer-wrap">
          <div class="composer-inner">
            <div class="suggest" id="suggest"></div>
            <div class="composer">
              <textarea id="composer-input" rows="1" placeholder="넙죽이에게 학과 정보를 물어보세요…"></textarea>
              <button class="send" id="send-btn" disabled>${svg('send')}</button>
            </div>
            <div class="composer-hint">넙죽이는 수집된 KAIST 학과 데이터를 검색해 출처와 함께 답해요.</div>
          </div>
        </div>
      </main>
    </div>`;
  },

  init(){
    Mascot.mount(document.querySelector('.chat-shell'));
    this.thread = document.getElementById('thread');
    this.inner = document.getElementById('thread-inner');
    this.input = document.getElementById('composer-input');
    this.sendBtn = document.getElementById('send-btn');

    this.showWelcome();
    this.loadSessionList();

    const grow=()=>{ this.input.style.height='auto'; this.input.style.height=Math.min(this.input.scrollHeight,140)+'px'; this.sendBtn.disabled=!this.input.value.trim()||this.busy; };
    this.input.addEventListener('input', grow);
    this.input.addEventListener('keydown', e=>{ if(e.key==='Enter'&&!e.shiftKey){ e.preventDefault(); this.submit(); } });
    this.sendBtn.addEventListener('click', ()=>this.submit());

    document.getElementById('new-chat').addEventListener('click', ()=>this.newChat());
    this.wireRailSessions();
    document.getElementById('rail-toggle').addEventListener('click', ()=>{
      if(window.Community) Community.toggleRail();
      else {
        const collapsed = document.getElementById('rail').classList.toggle('collapsed');
        window.sessionStorage?.setItem('communityRailCollapsed', collapsed ? '1' : '0');
      }
    });
    document.getElementById('toggle-theme').addEventListener('click', ()=>App.toggleTheme());
    const ga=document.getElementById('go-admin'); if(ga) ga.addEventListener('click', ()=>App.go('admin'));
    if(window.Community) Community.wireTopNav();
    document.getElementById('user-card').addEventListener('click', ()=>this.logout());

    // sidebar search filter (functional)
    const rs=document.getElementById('rail-search-inp');
    rs.addEventListener('input', ()=>{
      const q=rs.value.trim().toLowerCase();
      document.querySelectorAll('#rail-list .sess').forEach(el=>{
        const hit=!q || (el.dataset.title||'').toLowerCase().includes(q);
        el.style.display=hit?'':'none';
      });
      document.querySelectorAll('#rail-list .rail-sec').forEach(sec=>{
        let n=sec.nextElementSibling, any=false;
        while(n && n.classList.contains('sess')){ if(n.style.display!=='none')any=true; n=n.nextElementSibling; }
        sec.style.display=any?'':'none';
      });
    });
  },

  wireRailSessions(){
    document.querySelectorAll('.sess').forEach(el=>el.addEventListener('click', ()=>this.loadSession(el.dataset.sess)));
    if(this.activeSession){
      document.querySelectorAll('.sess').forEach(s=>s.classList.toggle('active', String(s.dataset.sess)===String(this.activeSession)));
    }
  },

  async loadSessionList(){
    try{
      const res = await Api.sessions();
      SESSIONS = res.sessions || [];
      const list=document.getElementById('rail-list');
      if(list) list.innerHTML = this.railHTML();
      this.wireRailSessions();
    }catch(e){ /* session rail remains empty */ }
  },

  async logout(){
    if(CURRENT_USER.role==='guest'){ App.go('login'); return; }
    try{ await Api.logout(); }catch(e){}
    CURRENT_USER = { name:'게스트', mail:'temporary@session', initial:'게', role:'guest', via:'guest' };
    SESSIONS = [];
    App.go('login');
  },

  renderSuggest(list){
    const box=document.getElementById('suggest'); if(!box) return;
    box.innerHTML = list.map(s=>`<button class="chip" data-kb="${s.id||''}" data-q="${s.q||s.t}">${s.ic?svg(s.ic):''}${s.t}</button>`).join('');
    box.querySelectorAll('.chip').forEach(b=>b.addEventListener('click', ()=>{ this.submit(b.dataset.q, b.dataset.kb||null); }));
  },

  showWelcome(){
    this.inner.innerHTML = `
      <div class="welcome pop">
        <div style="width:120px;margin-bottom:6px"><img src="${asset('images/mascot/nubzuki_idle.png')}" alt="넙죽이" style="width:100%;animation:bob 3.4s var(--ease) infinite"></div>
        <h1>안녕하세요, 넙죽이예요!</h1>
        <p>KAIST <strong>AI대학·자연과학대학·생명과학기술대학</strong>의 학과 정보를 안내해 드려요.<br>교과목·교수진·입학·세미나까지 무엇이든 물어보세요.</p>
        <div class="welcome-grid">
          ${WELCOME_CARDS.map(c=>`
            <button class="wcard" data-q="${c.q}">
              <div class="wc-ic" style="background:${c.bg};color:${c.tint}">${svg(c.ic)}</div>
              <div class="wc-t">${c.t}</div><div class="wc-d">${c.d}</div>
            </button>`).join('')}
        </div>
      </div>`;
    this.inner.querySelectorAll('.wcard').forEach(b=>b.addEventListener('click', ()=>this.submit(b.dataset.q)));
    this.renderSuggest(SUGGESTED);
    Mascot.set('idle');
  },

  newChat(){
    this.activeSession=null;
    document.querySelectorAll('.sess').forEach(s=>s.classList.remove('active'));
    document.getElementById('chat-title').textContent='새 대화';
    this.showWelcome();
  },

  async loadSession(id){
    if(this.busy) return;
    try{
      const res = await Api.session(id);
      this.activeSession=String(res.session.id);
      document.querySelectorAll('.sess').forEach(s=>s.classList.toggle('active', String(s.dataset.sess)===this.activeSession));
      document.getElementById('chat-title').textContent = res.session.title || '대화';
      this.inner.innerHTML='';
      document.getElementById('suggest').innerHTML='';
      (res.messages||[]).forEach(m=>{
        if(m.role==='user') this.addUser(m.content||'');
        else this.addBot(this.apiMessageToBot(m), true);
      });
      if(!(res.messages||[]).length) this.showWelcome();
      Mascot.set('idle');
      this.scroll();
    }catch(e){
      Mascot.set('warning','대화를 불러오지 못했어요.');
    }
  },

  /* resolve a query to a bot object deterministically (no LLM) */
  resolve(query, kbId, instant){
    if(kbId && KB[kbId]) return KB[kbId];
    const m = kbId || matchKB(query);
    if(m && KB[m]) return KB[m];
    const r = Search.retrieve(query);
    if(!r) return KB.fallback;
    return { answer:Search.fallbackAnswer(r), sources:Search.sourcesFor(r), mascot:r.mascot, chips:Search.chipsFor(r) };
  },

  submit(text, kbId){
    if(this.busy) return;
    const val = (text!==undefined? text : this.input.value).trim();
    if(!val) return;
    if(this.inner.querySelector('.welcome')) this.inner.innerHTML='';
    if(text===undefined){ this.input.value=''; this.input.style.height='auto'; }
    this.sendBtn.disabled=true;
    if(!this.activeSession) document.getElementById('chat-title').textContent = val.length>22? val.slice(0,22)+'…' : val;
    this.addUser(val);
    this.scroll();
    this.ask(val, kbId);
  },

  async ask(query, kbId){
    this.busy=true; this.sendBtn.disabled=true;
    clearTimeout(this.idleTimer);
    Mascot.set('thinking');
    const typing = this.addTyping();
    this.scroll();

    try{
      const res = await Api.chat({ session_id:this.activeSession, question:query });
      typing.remove();
      this.activeSession = String(res.session_id);
      Mascot.set(res.warning ? 'warning' : 'source');
      this.finish(this.apiResponseToBot(res));
      this.loadSessionList();
    }catch(e){
      typing.remove();
      this.finish(this.localFallback(query, kbId));
    }
  },

  finish(kb){
    Mascot.set(kb.mascot);
    this.addBot(kb, false);
    this.busy=false;
    this.sendBtn.disabled = !this.input.value.trim();
    if(kb.mascot==='source') setTimeout(()=>Mascot.set('done','출처까지 확인 완료! 또 궁금한 게 있나요?'),1400);
    this.idleTimer=setTimeout(()=>Mascot.set('idle'), 7000);
    this.scroll();
  },

  apiResponseToBot(res){
    return {
      answer:this.fmt(res.answer||''),
      sources:this.apiSources(res.sources||[]),
      mascot:res.warning ? 'warning' : 'source',
      chips:res.warning ? ['AI컴퓨팅학과 전공 과목 알려줘','단과대학이랑 학과 목록 알려줘'] : null,
    };
  },

  apiMessageToBot(message){
    return {
      answer:this.fmt(message.content||''),
      sources:this.apiSources(message.sources||[]),
      mascot:message.warning ? 'warning' : 'source',
      chips:null,
    };
  },

  apiSources(sources){
    return (sources||[]).map(s=>{
      const bits=[];
      if(s.department) bits.push(s.department);
      if(s.score!==null && s.score!==undefined && s.score!=='') bits.push(`score ${s.score}`);
      return {
        title:s.title || 'Retrieved Source',
        doc:bits.join(' · ') || 'RAG Source',
        url:s.url || '',
        snippet:'',
        score:s.score,
      };
    });
  },

  localFallback(query, kbId){
    const m = kbId || matchKB(query);
    if(m && KB[m]) return KB[m];
    const result = Search.retrieve(query);
    if(!result) return KB.fallback;
    return {
      answer:Search.fallbackAnswer(result),
      sources:Search.sourcesFor(result),
      mascot:result.mascot,
      chips:Search.chipsFor(result),
    };
  },

  /* ——— renderers ——— */
  addUser(text){
    this.inner.insertAdjacentHTML('beforeend', `<div class="msg user pop">
      <div class="msg-av user">${CURRENT_USER.initial}</div>
      <div class="msg-col"><div class="bubble user"><p>${this.esc(text)}</p></div></div>
    </div>`);
  },

  addTyping(){
    const wrap=document.createElement('div');
    wrap.className='msg bot pop';
    wrap.innerHTML=`<div class="msg-av bot"><img src="${MASCOT_IMG.thinking}" alt=""></div>
      <div class="msg-col"><div class="bubble bot"><div class="typing"><b></b><b></b><b></b></div></div></div>`;
    this.inner.appendChild(wrap);
    return wrap;
  },

  srcCard(s,i){
    const href = s.url || ((s.snippet||'').match(/https?:\/\/[^\s"']+/)||[])[0] || '';
    const tag = href? 'a':'div';
    const snip = s.snippet ? (/^https?:/.test(s.snippet)
        ? `<div class="src-snip"><span class="mono">${s.snippet}</span></div>`
        : `<div class="src-snip">“${s.snippet}”</div>`) : '';
    return `<${tag} class="src"${href?` href="${href}" target="_blank" rel="noopener"`:''}>
      <div class="src-num">${i+1}</div>
      <div class="src-body">
        <div class="src-title">${s.title} ${svg('chevR','')}</div>
        <div class="src-doc">${s.doc}</div>
        ${snip}
      </div>
      ${href?`<span class="src-open">${svg('link')}</span>`:''}
    </${tag}>`;
  },

  addBot(kb, instant){
    const id = ++this.msgSeq;
    const srcHTML = (kb.sources&&kb.sources.length)? `
      <div class="sources" data-srcfor="${id}">
        <div class="sources-head">${svg('sources')} 참고한 자료 ${kb.sources.length}건 · 클릭하면 원문이 열려요</div>
        ${kb.sources.map((s,i)=>this.srcCard(s,i)).join('')}
      </div>`:'';

    const wrap=document.createElement('div');
    wrap.className='msg bot'+(instant?'':' pop');
    wrap.innerHTML=`<div class="msg-av bot"><img src="${MASCOT_IMG[kb.mascot]||MASCOT_IMG.idle}" alt=""></div>
      <div class="msg-col">
        <div class="bubble bot">${kb.answer}</div>
        ${srcHTML}
        <div class="fb" data-fbfor="${id}">
          <button class="fb-btn up" title="도움이 됐어요">${svg('thumbUp')}</button>
          <button class="fb-btn down" title="아쉬워요">${svg('thumbDown')}</button>
          <div class="fb-sep"></div>
          <button class="fb-btn copy" title="복사">${svg('copy')}</button>
          <button class="fb-btn regen" title="다시 생성">${svg('refresh')}</button>
          <span class="fb-note"></span>
        </div>
      </div>`;
    this.inner.appendChild(wrap);

    if(!instant && srcHTML){
      const sb=wrap.querySelector('.sources'); sb.style.opacity='0'; sb.style.transform='translateY(6px)'; sb.style.transition='all .35s var(--ease)';
      setTimeout(()=>{ sb.style.opacity='1'; sb.style.transform='none'; this.scroll(); }, 260);
    }
    wrap.querySelectorAll('.ref').forEach(r=>r.addEventListener('click',()=>{
      const n=+r.dataset.src; const card=wrap.querySelectorAll('.src')[n-1];
      if(card){ card.style.boxShadow='inset 0 0 0 2px var(--nub), var(--sh)'; setTimeout(()=>card.style.boxShadow='',1200);} }));
    this.wireFeedback(wrap, kb);
    if(kb.chips){ this.renderSuggest(kb.chips.map(c=>({t:c}))); }
    return wrap;
  },

  wireFeedback(wrap, kb){
    const fb=wrap.querySelector('.fb');
    const up=fb.querySelector('.up'), down=fb.querySelector('.down'), note=fb.querySelector('.fb-note');
    const copyBtn=fb.querySelector('.copy'), regen=fb.querySelector('.regen');
    up.addEventListener('click', ()=>{
      const on=up.classList.toggle('on'); down.classList.remove('on');
      note.textContent = on? '소중한 의견 감사해요! 🙌':'';
      if(on){ Mascot.set('done','도움이 됐다니 기뻐요! 또 물어보세요 😊'); clearTimeout(this.idleTimer); this.idleTimer=setTimeout(()=>Mascot.set('idle'),5000); }
    });
    down.addEventListener('click', ()=>{
      const on=down.classList.toggle('on'); up.classList.remove('on');
      note.textContent = on? '알려줘서 고마워요. 더 정확히 답하도록 배울게요.':'';
      if(on){ Mascot.set('warning','앗, 아쉬웠군요. 더 나은 답을 찾아볼게요!'); clearTimeout(this.idleTimer); this.idleTimer=setTimeout(()=>Mascot.set('idle'),5000); }
    });
    copyBtn.addEventListener('click', ()=>{
      const txt=wrap.querySelector('.bubble').innerText;
      if(navigator.clipboard) navigator.clipboard.writeText(txt).catch(()=>{});
      note.textContent='답변을 복사했어요.'; setTimeout(()=>{ if(!up.classList.contains('on')&&!down.classList.contains('on')) note.textContent=''; },1800);
    });
    regen.addEventListener('click', ()=>{ note.textContent='같은 자료로 다시 정리했어요.'; setTimeout(()=>{ if(!up.classList.contains('on')&&!down.classList.contains('on')) note.textContent=''; },1800); });
  },

  /* plain LLM text -> safe HTML */
  fmt(t){
    t=(t||'').trim().replace(/^#{1,6}\s*/gm,'');
    t=this.esc(t).replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>');
    const lines=t.split(/\n+/); let html='', inList=false;
    const close=()=>{ if(inList){html+='</ul>';inList=false;} };
    for(let ln of lines){ ln=ln.trim(); if(!ln)continue;
      if(/^[•\-*]\s+/.test(ln)){ if(!inList){html+='<ul class="b-list">';inList=true;} html+='<li>'+ln.replace(/^[•\-*]\s+/,'')+'</li>'; }
      else if(/^[A-Z]{2,3}\s?\d{3,5}\b/.test(ln)){ if(!inList){html+='<ul class="b-list">';inList=true;} const m=ln.match(/^([A-Z]{2,3}\s?\d{3,5})\s*(.*)$/); html+='<li><strong>'+m[1]+'</strong>'+(m[2]?' '+m[2]:'')+'</li>'; }
      else { close(); html+='<p>'+ln+'</p>'; } }
    close();
    return html;
  },

  wait(ms){ return new Promise(r=>setTimeout(r,ms)); },
  scroll(){ requestAnimationFrame(()=>{ this.thread.scrollTop=this.thread.scrollHeight; }); },
  esc(s){ return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); },
};
