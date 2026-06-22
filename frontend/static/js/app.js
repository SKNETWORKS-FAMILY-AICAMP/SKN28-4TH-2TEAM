/* ============================================================
   App router · theme · prototype nav · Tweaks panel
   ============================================================ */
const App = {
  current:'login',
  tweaks: Object.assign({ accent:'#29a8e2', theme:'light', mascotSize:1, density:'comfortable', playful:true }, window.TWEAKS||{}),

  start(){
    this.applyTweaks();
    const r=window.__ROUTE;          // set by Django page templates
    if(r){ this.go(r); } else { this.go('login'); this.buildProtoNav(); }
    this.initTweakHost();
  },

  go(view){
    this.current=view; clearTimeout(Chat.idleTimer);
    const app=document.getElementById('app');
    if(view==='login'){ app.innerHTML=Auth.loginHTML(); Auth.initLogin(); }
    else if(view==='signup'){ app.innerHTML=Auth.signupHTML(); Auth.initSignup(); }
    else if(view==='chat'){ app.innerHTML=Chat.viewHTML(); Chat.init(); }
    else if(view==='admin'){ app.innerHTML=Dashboard.html(); Dashboard.init(); }
    else if(view.startsWith('e')){ const code=view.slice(1); app.innerHTML=Errors.html(code); Errors.init(); }
    this.applyTweaks();
    this.syncProtoNav();
  },

  toggleTheme(){
    this.tweaks.theme = this.tweaks.theme==='dark'?'light':'dark';
    this.applyTweaks(); this.persist({theme:this.tweaks.theme});
    const tb=document.getElementById('toggle-theme'); if(tb) tb.innerHTML=svg(this.tweaks.theme==='dark'?'sun':'moon');
  },

  applyTweaks(){
    const t=this.tweaks, r=document.documentElement;
    r.setAttribute('data-theme', t.theme);
    r.style.setProperty('--nub', t.accent);
    r.style.setProperty('--nub-deep', `color-mix(in srgb, ${t.accent} 78%, #00263f)`);
    r.style.setProperty('--nub-soft', `color-mix(in srgb, ${t.accent} 20%, ${t.theme==='dark'?'#0e1626':'#ffffff'})`);
    r.style.setProperty('--nub-tint', `color-mix(in srgb, ${t.accent} 9%, ${t.theme==='dark'?'#0e1626':'#ffffff'})`);
    r.style.setProperty('--font-brand', t.playful? `"Jua", var(--font-ui)` : `var(--font-ui)`);
    document.body.setAttribute('data-density', t.density);
    if(Mascot.el) Mascot.setSize(t.mascotSize);
    const tb=document.getElementById('toggle-theme'); if(tb) tb.innerHTML=svg(t.theme==='dark'?'sun':'moon');
  },

  /* ——— prototype screen jumper ——— */
  buildProtoNav(){
    const nav=document.createElement('div'); nav.id='proto-nav';
    const items=[['login','로그인'],['signup','회원가입'],['chat','채팅'],['admin','관리자']];
    nav.innerHTML='<span class="pn-label">화면</span>'+items.map(i=>`<button data-v="${i[0]}">${i[1]}</button>`).join('');
    document.body.appendChild(nav);
    nav.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>this.go(b.dataset.v)));
  },
  syncProtoNav(){ document.querySelectorAll('#proto-nav button').forEach(b=>b.classList.toggle('active', b.dataset.v===this.current)); },

  /* ——— Tweaks host protocol ——— */
  initTweakHost(){
    window.addEventListener('message', e=>{
      const d=e.data||{};
      if(d.type==='__activate_edit_mode') this.showTweaks();
      else if(d.type==='__deactivate_edit_mode') this.hideTweaks();
    });
    window.parent.postMessage({type:'__edit_mode_available'},'*');
  },
  persist(edits){ try{ window.parent.postMessage({type:'__edit_mode_set_keys', edits},'*'); }catch(e){} },

  showTweaks(){
    if(document.getElementById('tweaks-panel')){ document.getElementById('tweaks-panel').classList.remove('hidden'); return; }
    const t=this.tweaks;
    const accents=[['#29a8e2','넙죽이'],['#0b3f8c','네이비'],['#ff5b9e','코랄'],['#9b6cf0','바이올렛'],['#1fb894','민트']];
    const p=document.createElement('div'); p.id='tweaks-panel';
    p.innerHTML=`
      <div class="tw-head"><b>Tweaks</b><button id="tw-x">${svg('x')}</button></div>
      <div class="tw-body scroll">
        <div class="tw-sec"><label>테마</label>
          <div class="tw-seg" id="tw-theme">
            <button data-v="light" class="${t.theme==='light'?'on':''}">${svg('sun')} 라이트</button>
            <button data-v="dark" class="${t.theme==='dark'?'on':''}">${svg('moon')} 다크</button>
          </div></div>
        <div class="tw-sec"><label>강조 색</label>
          <div class="tw-swatches" id="tw-accent">
            ${accents.map(a=>`<button class="${t.accent===a[0]?'on':''}" data-v="${a[0]}" title="${a[1]}"><i style="background:${a[0]}"></i></button>`).join('')}
          </div></div>
        <div class="tw-sec"><label>넙죽이 크기 <span id="tw-msz-v">${Math.round(t.mascotSize*100)}%</span></label>
          <input type="range" id="tw-msz" min="0.8" max="1.35" step="0.05" value="${t.mascotSize}"></div>
        <div class="tw-sec"><label>메시지 밀도</label>
          <div class="tw-seg" id="tw-density">
            <button data-v="comfortable" class="${t.density==='comfortable'?'on':''}">여유</button>
            <button data-v="compact" class="${t.density==='compact'?'on':''}">조밀</button>
          </div></div>
        <div class="tw-sec"><label>제목 글꼴</label>
          <div class="tw-seg" id="tw-playful">
            <button data-v="1" class="${t.playful?'on':''}">둥글둥글</button>
            <button data-v="0" class="${!t.playful?'on':''}">깔끔하게</button>
          </div></div>
      </div>`;
    document.body.appendChild(p);
    document.getElementById('tw-x').addEventListener('click',()=>{ this.hideTweaks(); window.parent.postMessage({type:'__edit_mode_dismissed'},'*'); });
    const seg=(id,key,cast)=>{ p.querySelector('#'+id).querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{
      p.querySelector('#'+id).querySelectorAll('button').forEach(x=>x.classList.remove('on')); b.classList.add('on');
      this.tweaks[key]=cast?cast(b.dataset.v):b.dataset.v; this.applyTweaks(); this.persist({[key]:this.tweaks[key]});
    })); };
    seg('tw-theme','theme');
    seg('tw-density','density');
    seg('tw-playful','playful',v=>v==='1');
    p.querySelector('#tw-accent').querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{
      p.querySelector('#tw-accent').querySelectorAll('button').forEach(x=>x.classList.remove('on')); b.classList.add('on');
      this.tweaks.accent=b.dataset.v; this.applyTweaks(); this.persist({accent:b.dataset.v});
    }));
    const msz=p.querySelector('#tw-msz');
    msz.addEventListener('input',()=>{ this.tweaks.mascotSize=+msz.value; document.getElementById('tw-msz-v').textContent=Math.round(msz.value*100)+'%'; this.applyTweaks(); });
    msz.addEventListener('change',()=>this.persist({mascotSize:this.tweaks.mascotSize}));
  },
  hideTweaks(){ const p=document.getElementById('tweaks-panel'); if(p) p.classList.add('hidden'); },
};

window.addEventListener('DOMContentLoaded', ()=>App.start());
