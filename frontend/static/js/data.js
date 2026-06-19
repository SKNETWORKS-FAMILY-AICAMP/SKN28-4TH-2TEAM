/* ============================================================
   Icons — lucide-style 24x24 stroke paths
   ============================================================ */
const ICONS = {
  plus:'<path d="M12 5v14M5 12h14"/>',
  search:'<circle cx="11" cy="11" r="7"/><path d="m20 20-3.2-3.2"/>',
  send:'<path d="M11 13 21 3M21 3l-6.5 18-3.5-8L3 9z"/>',
  message:'<path d="M21 11.5a8.4 8.4 0 0 1-8.5 8.5 8.9 8.9 0 0 1-3.9-.9L3 21l1.9-5.6A8.4 8.4 0 0 1 4 11.5 8.4 8.4 0 0 1 12.5 3 8.4 8.4 0 0 1 21 11.5z"/>',
  thumbUp:'<path d="M7 10v11M2 12.5A2.5 2.5 0 0 1 4.5 10H7v11H4.5A2.5 2.5 0 0 1 2 18.5zM7 10l4.2-7a2 2 0 0 1 3.8.9V8h4.3a2 2 0 0 1 2 2.4l-1.5 7A2 2 0 0 1 17.8 19H7"/>',
  thumbDown:'<path d="M17 14V3M22 11.5A2.5 2.5 0 0 0 19.5 14H17V3h2.5A2.5 2.5 0 0 1 22 5.5zM17 14l-4.2 7a2 2 0 0 1-3.8-.9V16H4.7a2 2 0 0 1-2-2.4l1.5-7A2 2 0 0 1 6.2 5H17"/>',
  copy:'<rect x="9" y="9" width="11" height="11" rx="2.5"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
  refresh:'<path d="M21 12a9 9 0 1 1-2.6-6.4M21 3v5h-5"/>',
  book:'<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z"/><path d="M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5"/>',
  calendar:'<rect x="3" y="4.5" width="18" height="17" rx="2.5"/><path d="M3 9.5h18M8 2.5v4M16 2.5v4"/>',
  cap:'<path d="M22 9 12 4 2 9l10 5 10-5z"/><path d="M6 10.5V16c0 1.3 2.7 3 6 3s6-1.7 6-3v-5.5"/>',
  users:'<circle cx="9" cy="8" r="3.5"/><path d="M2.5 21a6.5 6.5 0 0 1 13 0M17 5.2a3.5 3.5 0 0 1 0 5.6M22 21a6.2 6.2 0 0 0-4-5.8"/>',
  sparkle:'<path d="M12 3l1.9 5.6L19.5 10l-5.6 1.4L12 17l-1.9-5.6L4.5 10l5.6-1.4z"/>',
  sources:'<path d="M4 5.5A1.5 1.5 0 0 1 5.5 4H14l4 4v6.5"/><circle cx="14.5" cy="16.5" r="3.5"/><path d="m20 22-2.6-2.6"/><path d="M4 5.5V19a1.5 1.5 0 0 0 1.5 1.5H9"/>',
  home:'<path d="M3 11 12 3l9 8M5 9.5V20a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V9.5"/>',
  arrowLeft:'<path d="M19 12H5M12 19l-7-7 7-7"/>',
  mail:'<rect x="2.5" y="4.5" width="19" height="15" rx="2.5"/><path d="m3 6 9 6.5L21 6"/>',
  lock:'<rect x="4.5" y="10.5" width="15" height="10.5" rx="2.5"/><path d="M8 10.5V7a4 4 0 0 1 8 0v3.5"/>',
  user:'<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  eye:'<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
  eyeOff:'<path d="M10.7 5.1A10.6 10.6 0 0 1 12 5c6.5 0 10 7 10 7a14 14 0 0 1-2.3 3.1M6.6 6.6A14 14 0 0 0 2 12s3.5 7 10 7a10 10 0 0 0 4-.8M3 3l18 18M9.9 9.9a3 3 0 0 0 4.2 4.2"/>',
  logout:'<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
  chart:'<path d="M3 3v17a1 1 0 0 0 1 1h17"/><path d="M7 15l3.5-4 3 2.5L19 7"/>',
  check:'<path d="M20 6 9 17l-5-5"/>',
  x:'<path d="M18 6 6 18M6 6l12 12"/>',
  menu:'<path d="M3 12h18M3 6h18M3 18h18"/>',
  sidebar:'<rect x="3" y="4" width="18" height="16" rx="2.5"/><path d="M9 4v16"/>',
  settings:'<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-2.7 1.1V21a2 2 0 0 1-4 0v-.1A1.6 1.6 0 0 0 6.6 19l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1A1.6 1.6 0 0 0 3 13.4H3a2 2 0 0 1 0-4h.1A1.6 1.6 0 0 0 4.6 6.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1A1.6 1.6 0 0 0 10 4.1V4a2 2 0 0 1 4 0v.1a1.6 1.6 0 0 0 2.7 1.1l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8V9a1.6 1.6 0 0 0 1.5 1H21a2 2 0 0 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1z"/>',
  sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  moon:'<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
  building:'<rect x="5" y="3" width="14" height="18" rx="1.5"/><path d="M9 7h2M13 7h2M9 11h2M13 11h2M9 15h2M13 15h2M10 21v-3h4v3"/>',
  bolt:'<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
  layers:'<path d="m12 2 9 5-9 5-9-5z"/><path d="m3 12 9 5 9-5M3 17l9 5 9-5"/>',
  flask:'<path d="M9 3h6M10 3v6.5L4.5 18A2 2 0 0 0 6.2 21h11.6a2 2 0 0 0 1.7-3L14 9.5V3"/><path d="M7.5 15h9"/>',
  cpu:'<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M1 9h3M1 15h3M20 9h3M20 15h3"/>',
  atom:'<circle cx="12" cy="12" r="1.4"/><ellipse cx="12" cy="12" rx="10" ry="4.4"/><ellipse cx="12" cy="12" rx="10" ry="4.4" transform="rotate(60 12 12)"/><ellipse cx="12" cy="12" rx="10" ry="4.4" transform="rotate(120 12 12)"/>',
  dna:'<path d="M5 3c0 5 14 6 14 12M19 3c0 5-14 6-14 12M5 21c0-3 14-4 14-9M19 21c0-3-14-4-14-9"/>',
  chevR:'<path d="m9 6 6 6-6 6"/>',
  database:'<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
  link:'<path d="M10 13a5 5 0 0 0 7 0l2-2a5 5 0 0 0-7-7l-1 1M14 11a5 5 0 0 0-7 0l-2 2a5 5 0 0 0 7 7l1-1"/>',
};
function svg(name, cls){ return `<svg class="${cls||''}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICONS[name]||''}</svg>`; }
function googleG(){ return `<svg class="gG" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="#4285F4" d="M23.5 12.27c0-.79-.07-1.54-.2-2.27H12v4.51h6.47a5.53 5.53 0 0 1-2.4 3.62v3h3.86c2.26-2.08 3.57-5.15 3.57-8.86z"/><path fill="#34A853" d="M12 24c3.24 0 5.96-1.08 7.95-2.91l-3.86-3c-1.07.72-2.45 1.16-4.09 1.16-3.14 0-5.8-2.12-6.76-4.98H1.26v3.09A12 12 0 0 0 12 24z"/><path fill="#FBBC05" d="M5.24 14.27a7.2 7.2 0 0 1 0-4.54V6.64H1.26a12 12 0 0 0 0 10.72l3.98-3.09z"/><path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42A11.97 11.97 0 0 0 12 0 12 12 0 0 0 1.26 6.64l3.98 3.09C6.2 6.87 8.86 4.75 12 4.75z"/></svg>`; }

/* asset path helper — standalone uses "static/", Django sets window.ASSET_BASE */
function asset(p){ return (window.ASSET_BASE||'static/')+p; }

/* Real dataset statistics — computed live from window.KB_DATA (no fabricated numbers) */
function kbStats(){
  const D=window.KB_DATA||{courses:[],people:[],events:[],adm:[]};
  const cols={}; const depts=new Set();
  ['courses','people','events','adm'].forEach(t=>(D[t]||[]).forEach(r=>{
    depts.add(r.col+'|'+r.dp);
    cols[r.col]=cols[r.col]||{courses:0,people:0,events:0,adm:0,total:0,depts:new Set()};
    cols[r.col][t]++; cols[r.col].total++; cols[r.col].depts.add(r.dp);
  }));
  return {
    colleges:Object.keys(cols), cols,
    courses:(D.courses||[]).length, people:(D.people||[]).length,
    events:(D.events||[]).length, adm:(D.adm||[]).length,
    depts:depts.size,
    total:(D.courses||[]).length+(D.people||[]).length+(D.events||[]).length+(D.adm||[]).length,
  };
}
const COLLEGE_NAME={ ai:'AI대학', life:'생명과학기술대학', natsci:'자연과학대학' };
const COLLEGE_COLOR={ ai:'#9b6cf0', natsci:'var(--nub)', life:'var(--coral)' };

/* ============================================================
   Current user
   ============================================================ */
let   CURRENT_USER = { name:'이도현', mail:'dohyun.lee@kaist.ac.kr', initial:'이', role:'admin', via:'kaist' };
const GOOGLE_USER  = { name:'김민지', mail:'minji.kim@gmail.com', initial:'민', role:'user', via:'google' };

/* ============================================================
   Example conversations (grouped by college) — titles are real queries
   ============================================================ */
const SESSIONS = [
  { id:'s5', title:'단과대학·학과 목록', meta:'전체 학과 안내', icon:'building', day:'둘러보기' },
  { id:'s1', title:'AI컴퓨팅학과 전공 과목', meta:'AI대학', icon:'cpu', day:'AI대학' },
  { id:'s2', title:'AI대학 교수진', meta:'AI대학', icon:'users', day:'AI대학' },
  { id:'s3', title:'자연과학대학 입학 안내', meta:'자연과학대학', icon:'cap', day:'자연과학대학' },
  { id:'s4', title:'화학과 교수님 연구분야', meta:'자연과학대학 · 화학과', icon:'flask', day:'자연과학대학' },
  { id:'s6', title:'생명과학과 과목 안내', meta:'생명과학기술대학', icon:'dna', day:'생명과학기술대학' },
];

/* ============================================================
   Quick prompts (route through retrieval over real data)
   ============================================================ */
const SUGGESTED = [
  { t:'AI컴퓨팅학과 전공 과목 알려줘', ic:'cpu' },
  { t:'AI대학 교수님 알려줘', ic:'users' },
  { t:'자연과학대학 입학은 어떻게 준비해?', ic:'cap' },
  { t:'생명과학과 세미나 일정 알려줘', ic:'calendar' },
];
const WELCOME_CARDS = [
  { t:'학과·전공', d:'단과대학과 학과 편제 안내', ic:'building', tint:'var(--nub)', bg:'var(--nub-soft)', q:'단과대학이랑 학과 목록 알려줘' },
  { t:'교과목', d:'학과별 개설 교과목 검색', ic:'book', tint:'var(--mint)', bg:'var(--mint-soft)', q:'AI컴퓨팅학과 전공 과목 알려줘' },
  { t:'교수·연구실', d:'교수진과 연구 분야', ic:'users', tint:'#9b6cf0', bg:'#ece2fd', q:'AI대학 교수님 알려줘' },
  { t:'입학·일정', d:'입학·전형·세미나 안내', ic:'cap', tint:'var(--coral)', bg:'var(--coral-soft)', q:'자연과학대학 입학은 어떻게 준비해?' },
];

/* ============================================================
   Scripted KB — only meta answers (greeting / overview / fallback).
   Topic questions are answered by Search over real KB_DATA.
   ============================================================ */
const KB = {
  greeting: {
    mascot:'done',
    answer:`<p>안녕하세요! 저는 KAIST 학과 안내 챗봇 <strong>넙죽이</strong>예요 🙌 <strong>AI대학·자연과학대학·생명과학기술대학</strong>에서 수집한 교과목·교수진·입학·세미나 정보를 검색해 출처와 함께 알려드려요. 아래 추천 질문으로 시작해 보세요!</p>`,
    sources:[], chips:['AI컴퓨팅학과 전공 과목 알려줘','자연과학대학 입학은 어떻게 준비해?'],
  },
  departments: {
    mascot:'source',
    answer:`<p>넙죽이가 안내하는 KAIST 단과대학과 학과예요.</p>
      <ul class="b-list">
        <li><strong>AI대학</strong> · AI컴퓨팅학과 · AI시스템학과 · AX학과 · AI미래학과</li>
        <li><strong>자연과학대학</strong> · 화학과 · 수리과학과 · 물리학과 · 양자대학원</li>
        <li><strong>생명과학기술대학</strong> · 생명과학과 · 뇌인지과학과 · 의과학대학원 · 공학생물대학원 · 줄기세포및재생생물학대학원</li>
      </ul>
      <p>특정 학과의 교과목·교수진·입학 정보가 궁금하면 학과 이름과 함께 물어봐 주세요!</p>`,
    sources:[{ title:'단과대학·학과 편제', doc:'KAIST RAG 데이터셋 · rag_documents', snippet:'AI대학·자연과학대학·생명과학기술대학에서 수집한 학과 데이터', score:0 }],
    chips:['AI컴퓨팅학과 전공 과목 알려줘','생명과학과 교수님 알려줘'],
  },
  fallback: {
    mascot:'warning',
    answer:`<p>음… 그 질문은 제가 수집한 자료에서 정확한 근거를 찾지 못했어요. 😥 저는 지금 <strong>AI대학·자연과학대학·생명과학기술대학</strong>의 학과 정보를 안내하고 있어요. (수집되지 않은 학과나 KAIST 외부 정보, 개인별 합격 예측은 답변하지 않아요.)</p>
      <p>예를 들어 이렇게 물어보세요:</p>
      <ul class="b-list">
        <li>AI컴퓨팅학과 전공 과목 알려줘</li>
        <li>화학과 교수님 연구분야 알려줘</li>
        <li>자연과학대학 입학은 어떻게 준비해?</li>
      </ul>`,
    sources:[], chips:['AI대학 교수님 알려줘','단과대학이랑 학과 목록 알려줘'],
  },
};

/* keyword matcher -> scripted KB id (else null => Search retrieval) */
function matchKB(text){
  const t=(text||'').toLowerCase();
  const has=(...ks)=>ks.some(k=>t.includes(k));
  if(has('안녕','하이','hello','반가','누구야','누구세요','뭐 할 수','뭐할수','뭐 해줄','소개해','너 뭐')) return 'greeting';
  if(has('학과 목록','학과목록','단과대','어떤 학과','무슨 학과','대학 종류','전체 학과','학과 알려','어떤 대학')) return 'departments';
  return null;
}
