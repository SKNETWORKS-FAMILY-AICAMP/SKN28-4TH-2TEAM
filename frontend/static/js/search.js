/* ============================================================
   Search / RAG retrieval over window.KB_DATA (real KAIST data)
   - retrieve(query)  -> {type, records, dept, college, label, mascot} | null
   - sourcesFor / contextFor / fallbackAnswer / chipsFor
   ============================================================ */
const Search = {
  COLLEGES:{
    ai:{ name:'AI대학', kw:['ai','인공지능','머신러닝','기계학습','딥러닝','컴퓨팅','데이터'] },
    life:{ name:'생명과학기술대학', kw:['생명','의과학','뇌','줄기세포','재생','바이오','생물'] },
    natsci:{ name:'자연과학대학', kw:['화학','물리','수리','수학','양자'] },
  },
  DEPTS:[
    { col:'ai', name:'AI컴퓨팅학과', kw:['ai컴퓨팅','컴퓨팅','aic'] },
    { col:'ai', name:'AI시스템학과', kw:['ai시스템','시스템학과'] },
    { col:'ai', name:'AX학과', kw:['ax학과','ax'] },
    { col:'ai', name:'AI미래학과', kw:['ai미래','미래학과'] },
    { col:'life', name:'뇌인지과학과', kw:['뇌인지','뇌과학','bcs'] },
    { col:'life', name:'생명과학과', kw:['생명과학과','생명과학'] },
    { col:'life', name:'의과학대학원', kw:['의과학'] },
    { col:'life', name:'줄기세포및재생생물학대학원', kw:['줄기세포','재생생물'] },
    { col:'life', name:'공학생물대학원', kw:['공학생물'] },
    { col:'natsci', name:'화학과', kw:['화학'] },
    { col:'natsci', name:'물리학과', kw:['물리','고전역학','전자기','양자역학','열물리'] },
    { col:'natsci', name:'수리과학과', kw:['수리','수학','대수','해석','미적분'] },
    { col:'natsci', name:'양자대학원', kw:['양자대학원','양자정보'] },
  ],
  AREA:{ ORG:'유기화학', ANAL:'분석화학', PHY:'물리화학', INO:'무기화학', BIO:'화학생물학', MAT:'재료화학', NANO:'나노과학' },

  norm(s){ return (s||'').toLowerCase().replace(/\s+/g,' ').trim(); },
  toks(q){ return this.norm(q).split(/[\s,.?!·]+/).filter(t=>t.length>=2); },
  host(u){ try{ return (u||'').replace(/^https?:\/\//,'').replace(/#\/?$/,'').split(/[?#]/)[0]; }catch(e){ return u; } },
  areaKo(a){ return (a||'').split(/[,\s]+/).filter(Boolean).map(c=>this.AREA[c]||c).join('·'); },
  credit(c){ return /\d\s*:\s*\d/.test(c||'') ? c : ''; },
  collegeName(id){ return (this.COLLEGES[id]||{}).name||''; },

  detectDept(q){ const n=this.norm(q); for(const d of this.DEPTS){ if(d.kw.some(k=>n.includes(k))) return d; } return null; },
  detectCollege(q){ const n=this.norm(q); for(const id in this.COLLEGES){ if(this.COLLEGES[id].kw.some(k=>n.includes(k))) return id; } return null; },

  rank(pool, tk, keyOf){
    if(!tk.length) return pool.slice();
    return pool.map(r=>{ const hay=this.norm(keyOf(r)); let s=0; tk.forEach(t=>{ if(hay.includes(t)) s+=(hay.split(t).length-1)*2+t.length; }); return {r,s}; })
      .filter(x=>x.s>0).sort((a,b)=>b.s-a.s).map(x=>x.r);
  },

  retrieve(query){
    const D=window.KB_DATA; if(!D) return null;
    const q=this.norm(query), tk=this.toks(query);
    const dept=this.detectDept(query), college=dept?dept.col:this.detectCollege(query);
    const inScope=(r)=> dept? r.dp===dept.name : (college? r.col===college : true);

    const code=(query.match(/[A-Za-z]{2,3}\s?\d{3,5}/)||[])[0];
    const wantCourse=/과목|강의|수업|교과목|학점|커리큘럼|전공|코드|course/.test(q)||code;
    const wantPeople=/교수|교수님|연구실|연구분야|연구 분야|faculty|지도교수|랩|연구진/.test(q);
    const wantEvent=/세미나|행사|특강|콜로퀴엄|소식|콜로키움|event|seminar/.test(q);
    const wantAdm=/입학|지원|장학|면접|모집|전형|admission|학위|대학원 과정|일정/.test(q);

    const mk=(type,records,label,mascot)=> records&&records.length? {type,records,dept,college,label,mascot:mascot||'source'} : null;
    const scope=this.collegeName(college)|| (dept?dept.name:'') || 'KAIST';
    const deptLabel=dept? dept.name : (this.collegeName(college)||'');

    if(code){
      const cc=code.replace(/\s/g,'').toUpperCase();
      const hit=D.courses.filter(c=>c.c.replace(/\s/g,'').toUpperCase().includes(cc));
      const r=mk('courses',hit.slice(0,8),'‘'+code.toUpperCase()+'’ 과목'); if(r) return r;
    }
    if(wantPeople){
      const pool=D.people.filter(inScope);
      const r=this.rank(pool,tk,p=>[p.n,this.areaKo(p.a),p.a,p.dp].join(' '));
      const list=(r.length?r:pool).slice(0,6);
      const out=mk('people',list,(deptLabel||'')+' 교수·연구진'); if(out) return out;
    }
    if(wantCourse){
      const pool=D.courses.filter(inScope);
      const r=this.rank(pool,tk,c=>[c.c,c.n,c.dp].join(' '));
      const list=(r.length?r:pool).slice(0,8);
      const out=mk('courses',list,(deptLabel||'')+' 교과목'); if(out) return out;
    }
    if(wantEvent){
      const pool=D.events.filter(inScope);
      const r=this.rank(pool,tk,e=>[e.t,e.c,e.dp].join(' '));
      const list=(r.length?r:pool).slice(0,6);
      const out=mk('events',list,(deptLabel||'')+' 세미나·행사','done'); if(out) return out;
    }
    if(wantAdm){
      const pool=D.adm.filter(inScope);
      const r=this.rank(pool,tk,a=>[a.t,a.c,a.dp].join(' '));
      const list=(r.length?r:pool).slice(0,4);
      const out=mk('adm',list,(deptLabel||'')+' 입학·장학','done'); if(out) return out;
    }
    // generic
    const gc=this.rank(D.courses.filter(inScope),tk,c=>[c.c,c.n,c.dp].join(' ')).slice(0,5);
    if(gc.length>=2) return mk('courses',gc,(deptLabel||'')+' 교과목');
    const gp=this.rank(D.people.filter(inScope),tk,p=>[p.n,this.areaKo(p.a),p.dp].join(' ')).slice(0,5);
    if(gp.length) return mk('people',gp,(deptLabel||'')+' 교수·연구진');
    const ge=this.rank(D.events.filter(inScope),tk,e=>[e.t,e.c].join(' ')).slice(0,5);
    if(ge.length) return mk('events',ge,(deptLabel||'')+' 세미나·행사','done');
    return null;
  },

  /* fallback deterministic HTML (used when LLM unavailable) */
  fallbackAnswer(R){
    const head=`<p><strong>${R.label}</strong> 검색 결과예요. 관련 자료 ${R.records.length}건을 찾았어요.</p>`;
    let li='';
    if(R.type==='people') li=R.records.map(p=>`<li><strong>${p.n}${p.r?' · '+p.r:''}</strong>${this.areaKo(p.a)?' · '+this.areaKo(p.a):''}${p.e?` · <span class="mono">${p.e}</span>`:''}</li>`).join('');
    else if(R.type==='courses') li=R.records.map(c=>`<li><strong>${c.c}${c.n?' '+c.n:''}</strong>${this.credit(c.cr)?' · '+this.credit(c.cr):''}${c.t?' · '+c.t:''}</li>`).join('');
    else if(R.type==='events') li=R.records.map(e=>`<li><strong>${e.d||'일정 미정'}</strong> · ${e.t}</li>`).join('');
    else li=R.records.map(a=>`<li><strong>${a.t}</strong>${a.c?` · <span class="muted">${a.c}</span>`:''}</li>`).join('');
    return head+`<ul class="b-list">${li}</ul>`;
  },

  /* context block for the LLM */
  contextFor(R){
    const lines=R.records.map((r,i)=>{
      if(R.type==='people') return `${i+1}. 교수 ${r.n}${r.r?' ('+r.r+')':''}${this.areaKo(r.a)?' / 연구분야: '+this.areaKo(r.a):''}${r.e?' / 이메일: '+r.e:''} [${r.dp}]`;
      if(R.type==='courses') return `${i+1}. ${r.c} ${r.n}${this.credit(r.cr)?' / 학점 '+this.credit(r.cr):''}${r.t?' / '+r.t:''} [${r.dp}]`;
      if(R.type==='events') return `${i+1}. ${r.d||'일정미정'} ${r.t}${r.c?' — '+r.c:''} [${r.dp}]`;
      return `${i+1}. ${r.t}${r.c?': '+r.c:''} [${r.dp}]`;
    });
    return lines.join('\n');
  },

  llmPrompt(query, R){
    return `너는 KAIST 학과 안내 챗봇 "넙죽이"야. 아래 [검색결과]만 근거로 사용자의 질문에 한국어로 간결하고 친절하게 답해.\n`+
      `규칙: 검색결과에 없는 사실은 지어내지 마. 핵심을 2~4문장으로 요약하고, 필요하면 항목을 •로 나열해. 학점/이메일/날짜 같은 구체 정보는 정확히 인용해. 출처 URL은 본문에 적지 마(별도 카드로 표시됨).\n\n`+
      `[질문]\n${query}\n\n[검색결과 — ${R.label}]\n${this.contextFor(R)}`;
  },

  sourcesFor(R){
    const sheet={people:'people_clean',courses:'courses_clean',events:'events_clean',adm:'admissions_clean'}[R.type];
    const label={people:'교수진',courses:'교과목',events:'세미나·행사',adm:'입학안내'}[R.type];
    const out=[], seen=new Set();
    // one card per distinct real URL among the matched records (links match the listed items)
    for(const r of R.records){
      if(!r.u || seen.has(r.u)) continue;
      seen.add(r.u);
      out.push({ title:(r.dp||this.collegeName(r.col)||'KAIST')+' '+label, doc:this.host(r.u)+' · 2026-06-17 수집', snippet:r.u, url:r.u, score:0 });
      if(out.length>=3) break;
    }
    const cn=this.collegeName(R.college);
    out.push({ title:(cn||'KAIST')+' RAG 데이터셋', doc:'rag · '+sheet, snippet:'KAIST 크롤링 데이터에서 검색된 결과예요.', score:0 });
    return out;
  },

  chipsFor(R){
    const dn=R.dept?R.dept.name:(this.collegeName(R.college)||'');
    if(R.type==='people') return [dn+' 교수님 더 보여줘', dn+' 전공 과목 알려줘'].filter(s=>s.trim());
    if(R.type==='courses') return [dn+' 필수 과목만 알려줘', dn+' 교수님 연구분야는?'].filter(s=>s.trim());
    if(R.type==='events') return [dn+' 다음 세미나 일정', dn+' 입학 안내 보여줘'].filter(s=>s.trim());
    return ['AI대학 학과 알려줘','자연과학대학 입학 안내'];
  },
};
