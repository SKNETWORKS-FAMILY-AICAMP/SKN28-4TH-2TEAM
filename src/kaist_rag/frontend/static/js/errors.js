/* ============================================================
   Error pages (400 / 403 / 500)
   ============================================================ */
const ERR = {
  '400': { mascot:'thinking', title:'잘못된 요청이에요', msg:'요청을 이해하지 못했어요. 주소를 다시 확인하거나, 넙죽이에게 다시 물어봐 주세요.', detail:'HTTP 400 · Bad Request' },
  '403': { mascot:'warning',  title:'접근 권한이 없어요', msg:'이 페이지를 볼 수 있는 권한이 없어요. KAIST 계정으로 로그인했는지 확인해 주세요.', detail:'HTTP 403 · Forbidden' },
  '500': { mascot:'warning',  title:'서버에 문제가 생겼어요', msg:'넙죽이가 잠시 정신을 잃었어요. 😵 잠시 후 다시 시도해 주세요. 문제가 계속되면 학사지원팀에 문의해 주세요.', detail:'HTTP 500 · Internal Server Error' },
};
const Errors = {
  html(code){
    const e=ERR[code]||ERR['500'];
    return `<div class="errpage view">
      <div class="errcard pop">
        <div class="err-mascot"><img src="${MASCOT_IMG[e.mascot]}" alt="넙죽이"></div>
        <div class="errcode">${code}</div>
        <h2>${e.title}</h2>
        <p>${e.msg}</p>
        <div class="err-actions">
          <button class="btn btn-primary" id="err-home">${svg('home')} 채팅으로 돌아가기</button>
          <button class="btn btn-ghost" id="err-back">${svg('arrowLeft')} 이전으로</button>
        </div>
        <div class="err-detail">${e.detail}</div>
      </div>
    </div>`;
  },
  init(){
    document.getElementById('err-home').addEventListener('click', ()=>App.go('chat'));
    document.getElementById('err-back').addEventListener('click', ()=>App.go('login'));
  },
};
