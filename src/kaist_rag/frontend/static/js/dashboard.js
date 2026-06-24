/* ============================================================
   Admin dashboard — REAL dataset coverage (no fabricated metrics)
   All figures computed live from window.KB_DATA
   ============================================================ */
const Dashboard = {
  donut(items){
    const total=items.reduce((a,b)=>a+b.n,0)||1;
    const C=2*Math.PI*52; let off=0;
    const segs=items.map(it=>{
      const len=(it.n/total)*C;
      const s=`<circle cx="75" cy="75" r="52" fill="none" stroke="${it.color}" stroke-width="20"
        stroke-dasharray="${len.toFixed(2)} ${(C-len).toFixed(2)}" stroke-dashoffset="${(-off).toFixed(2)}"
        transform="rotate(-90 75 75)" stroke-linecap="butt"/>`;
      off+=len; return s;
    }).join('');
    return `<svg viewBox="0 0 150 150">${segs}</svg>`;
  },

  perDept(){
    const D=window.KB_DATA, m={};
    const add=(r,k)=>{ const id=r.col+'|'+r.dp; (m[id]=m[id]||{col:r.col,dp:r.dp,courses:0,people:0,events:0,adm:0})[k]++; };
    D.courses.forEach(r=>add(r,'courses')); D.people.forEach(r=>add(r,'people'));
    D.events.forEach(r=>add(r,'events')); D.adm.forEach(r=>add(r,'adm'));
    const order={ai:0,natsci:1,life:2};
    return Object.values(m).sort((a,b)=>(order[a.col]-order[b.col])||(b.courses+b.people)-(a.courses+a.people));
  },

  html(){
    const s=kbStats();
    const kpi=[
      { lab:'단과대학', val:s.colleges.length, ic:'building', tint:'var(--nub)', bg:'var(--nub-soft)' },
      { lab:'학과·대학원', val:s.depts, ic:'layers', tint:'#9b6cf0', bg:'#ece2fd' },
      { lab:'수집 교과목', val:s.courses, ic:'book', tint:'var(--mint)', bg:'var(--mint-soft)' },
      { lab:'교수·연구진', val:s.people, ic:'users', tint:'var(--coral)', bg:'var(--coral-soft)' },
    ];
    const kpiHTML=kpi.map(c=>`<div class="kpi pop">
      <div class="kpi-ic" style="background:${c.bg};color:${c.tint}">${svg(c.ic)}</div>
      <div class="kpi-val tnum">${c.val.toLocaleString()}</div>
      <div class="kpi-lab">${c.lab}</div></div>`).join('');

    // college distribution (by total records)
    const colItems=s.colleges.map(id=>({ id, t:COLLEGE_NAME[id]||id, n:s.cols[id].total, color:COLLEGE_COLOR[id]||'var(--nub)' }))
      .sort((a,b)=>b.n-a.n);
    const totalRec=colItems.reduce((a,b)=>a+b.n,0)||1;
    const colLeg=colItems.map(c=>`<div class="dl"><i style="background:${c.color}"></i>${c.t}<b class="tnum">${c.n.toLocaleString()}</b><span class="faint" style="margin-left:6px">${Math.round(c.n/totalRec*100)}%</span></div>`).join('');

    // record-type composition
    const types=[
      { t:'교과목', n:s.courses, c:'var(--nub)' },
      { t:'교수·연구진', n:s.people, c:'#9b6cf0' },
      { t:'세미나·행사', n:s.events, c:'var(--mint)' },
      { t:'입학·장학 자료', n:s.adm, c:'var(--coral)' },
    ];
    const tmax=Math.max(...types.map(t=>t.n))||1;
    const typeHTML=types.map(t=>`<div class="barrow"><div class="bl-top"><b>${t.t}</b><span class="tnum">${t.n.toLocaleString()}건</span></div>
      <div class="track"><i style="width:0;background:${t.c}" data-w="${Math.round(t.n/tmax*100)}%"></i></div></div>`).join('');

    // per-department coverage table
    const rows=this.perDept().map(d=>`<tr>
      <td class="q">${d.dp}</td>
      <td><span class="badge badge-gray">${COLLEGE_NAME[d.col]||d.col}</span></td>
      <td class="tnum">${d.courses.toLocaleString()}</td>
      <td class="tnum">${d.people.toLocaleString()}</td>
      <td class="tnum">${d.events.toLocaleString()}</td>
      <td class="tnum">${d.adm.toLocaleString()}</td>
    </tr>`).join('');

    return `<div class="dash view">
      <header class="dash-head">
        <div class="brand"><span class="mark"><img src="${asset('images/mascot/nubzuki_idle.png')}" alt=""></span> 넙죽이 <small>관리자</small></div>
        <div class="spacer"></div>
        <span class="badge badge-blue">${svg('database')} 2026-06-17 크롤링 기준</span>
        <button class="btn btn-ghost btn-sm" id="back-chat">${svg('arrowLeft')} 채팅으로</button>
      </header>
      <div class="dash-body scroll">
        <div class="dash-inner">
          <div class="dash-title"><h1>수집 데이터 현황</h1>
            <div class="mini-mascot"><img src="${asset('images/mascot/nubzuki_done.png')}" alt=""></div>
          </div>
          <p class="dash-sub">RAG 챗봇이 검색하는 실제 수집 데이터셋의 규모와 구성이에요. 모든 수치는 적재된 레코드에서 집계돼요.</p>

          <div class="kpis">${kpiHTML}</div>

          <div class="dash-grid">
            <div class="panel pop"><div class="panel-h"><h3>데이터 구성</h3><div class="spacer"></div><span class="muted" style="font-size:13px">전체 ${s.total.toLocaleString()}건</span></div>
              <div class="barlist">${typeHTML}</div>
            </div>
            <div class="panel pop"><div class="panel-h"><h3>단과대학별 비중</h3></div>
              <div class="donut-wrap">
                <div class="donut">${this.donut(colItems)}<div class="ctr"><b class="tnum">${s.total.toLocaleString()}</b><span>레코드</span></div></div>
                <div class="donut-leg">${colLeg}</div>
              </div>
            </div>
          </div>

          <div class="panel pop">
            <div class="panel-h"><h3>학과별 수집 현황</h3><div class="spacer"></div><span class="muted" style="font-size:13px">${this.perDept().length}개 학과·대학원</span></div>
            <table class="tbl-feed"><thead><tr><th>학과·대학원</th><th>단과대학</th><th>교과목</th><th>교수·연구진</th><th>세미나·행사</th><th>입학·장학</th></tr></thead><tbody>${rows}</tbody></table>
          </div>
        </div>
      </div>
    </div>`;
  },

  init(){
    document.getElementById('back-chat').addEventListener('click', ()=>App.go('chat'));
    requestAnimationFrame(()=>setTimeout(()=>{
      document.querySelectorAll('.barrow .track i').forEach(i=>{ i.style.width=i.dataset.w; });
    },120));
  },
};
