/* ============================================================
   Community UI views
   Static-only board, inquiry, and post-detail screens.
   ============================================================ */
(function(){
  const PAGE_SIZE = 5;

  const boardPosts = [
    { id:'graduation-requirements', category:'학사', badge:'공지', title:'전산학부 졸업 요건이 어떻게 되나요?', summary:'전공 필수, 전공 선택, 연구 학점과 졸업 심사 체크 항목을 한 번에 정리했습니다.', author:'학사도우미', date:'오늘 09:42', views:128, comments:6, icon:'cap', isNotice:true, noticeAt:'2026-06-24T09:42:00+09:00' },
    { id:'spring-registration', category:'수강', badge:'공지', title:'2025 봄학기 수강신청 일정 알려줘', summary:'장바구니, 본수강, 정정 기간과 학사 시스템 확인 경로를 안내합니다.', author:'교학팀', date:'오늘 08:10', views:96, comments:4, icon:'calendar', isNotice:true, noticeAt:'2026-06-24T08:10:00+09:00' },
    { id:'ai-course-recommend', category:'교과목', badge:'추천', title:'인공지능 관련 과목 추천해줘', summary:'기초부터 프로젝트 과목까지 난이도별로 수강 순서를 비교했습니다.', author:'이도현', date:'어제 18:22', views:83, comments:8, icon:'cpu' },
    { id:'professor-office-hour', category:'교수님', badge:'정보', title:'전기및전자공학부 교수님 상담은 어디서 확인하나요?', summary:'학과 페이지, 교수 연구실, 메일 문의 전에 확인할 링크를 모았습니다.', author:'김민지', date:'어제 15:07', views:52, comments:5, icon:'users' },
    { id:'scholarship-apply', category:'장학', badge:'공지', title:'국가장학금 신청 방법과 제출 서류', summary:'신청 기간, 증빙서류, 학적 정보 입력 시 주의할 점을 정리했습니다.', author:'학사도우미', date:'5일 전', views:44, comments:2, icon:'book', isNotice:true, noticeAt:'2026-06-19T10:00:00+09:00' },
    { id:'orientation-guide', category:'신입생', badge:'안내', title:'신입생 오리엔테이션은 언제인가요?', summary:'학과별 오리엔테이션 일정과 참석 전 확인해야 할 준비물을 안내합니다.', author:'교학팀', date:'6일 전', views:39, comments:3, icon:'sparkle' },
    { id:'department-list', category:'학과', badge:'정보', title:'단과대학과 학과 목록을 한 번에 보고 싶어요', summary:'AI대학, 자연과학대학, 생명과학기술대학 소속 학과를 정리했습니다.', author:'학사도우미', date:'7일 전', views:71, comments:1, icon:'building' },
    { id:'lab-rotation', category:'연구', badge:'질문', title:'랩 로테이션 신청은 어떤 순서로 진행되나요?', summary:'희망 연구실 조사, 교수님 면담, 배정 결과 확인 흐름을 안내합니다.', author:'박서준', date:'8일 전', views:31, comments:4, icon:'flask' },
    { id:'ai-future-major', category:'전공', badge:'정보', title:'AI미래학과 전공 필수 과목을 알고 싶어요', summary:'전공 필수와 전공 선택 과목을 구분해서 수강 계획을 세울 수 있게 정리했습니다.', author:'정하린', date:'9일 전', views:58, comments:6, icon:'atom' },
    { id:'exam-period', category:'일정', badge:'공지', title:'중간고사와 기말고사 기간 확인 방법', summary:'학사 캘린더에서 시험 기간과 보강 기간을 확인하는 방법을 정리했습니다.', author:'교학팀', date:'10일 전', views:65, comments:2, icon:'calendar' },
    { id:'tuition-payment', category:'등록', badge:'안내', title:'등록금 납부 확인은 어디에서 하나요?', summary:'고지서 출력, 납부 확인, 장학 반영 여부를 확인하는 메뉴를 안내합니다.', author:'학사도우미', date:'12일 전', views:47, comments:3, icon:'database' },
    { id:'course-withdrawal', category:'수강', badge:'질문', title:'수강 철회 신청 기간과 유의사항', summary:'철회 가능 기간, 성적표 표기, 지도교수 확인이 필요한 경우를 정리했습니다.', author:'김민지', date:'14일 전', views:36, comments:2, icon:'book' },
    { id:'advisor-change', category:'학사', badge:'질문', title:'지도교수 변경 신청 절차가 궁금합니다', summary:'지도교수 변경 신청서, 학과 승인, 변경 가능 시점을 정리했습니다.', author:'이도현', date:'15일 전', views:28, comments:1, icon:'users' },
    { id:'dorm-application', category:'생활', badge:'안내', title:'생활관 신청 기간은 어디서 확인하나요?', summary:'생활관 신청 페이지와 선발 일정, 결과 확인 방법을 안내합니다.', author:'정하린', date:'16일 전', views:42, comments:4, icon:'home' },
    { id:'english-score', category:'졸업', badge:'정보', title:'영어 성적 제출 기준을 확인하고 싶어요', summary:'졸업 사정 전 제출해야 하는 공인 영어성적 기준과 제출 경로를 정리했습니다.', author:'학사도우미', date:'17일 전', views:59, comments:2, icon:'sources' },
    { id:'leave-return', category:'학적', badge:'안내', title:'휴학과 복학 신청은 어떻게 하나요?', summary:'휴학 신청, 복학 신청, 승인 처리 흐름과 주의사항을 한 번에 확인합니다.', author:'교학팀', date:'18일 전', views:33, comments:2, icon:'refresh' },
  ];

  const inquiries = [
    { id:'inq-1', status:'done', statusText:'답변 완료', title:'회원가입 후 Google 로그인 연동이 가능한가요?', summary:'기존 계정과 Google 계정을 같은 이메일 기준으로 연결할 수 있는지 문의합니다.', author:'이도현', date:'오늘 10:14', comments:1 },
    { id:'inq-2', status:'progress', statusText:'처리중', title:'검색 결과에 오래된 학사 일정이 먼저 보여요', summary:'최근 학기 자료를 우선 노출하는 정렬 기준을 확인하고 싶습니다.', author:'김민지', date:'오늘 09:02', comments:2 },
    { id:'inq-3', status:'wait', statusText:'답변 대기', title:'문의사항 게시글을 비공개로 등록할 수 있나요?', summary:'작성자와 관리자만 볼 수 있는 옵션이 필요한지 검토 요청드립니다.', author:'박서준', date:'어제 21:30', comments:0 },
    { id:'inq-4', status:'done', statusText:'답변 완료', title:'모바일에서 사이드바가 화면을 덮는 현상', summary:'작은 화면에서 게시글 목록과 사이드바 버튼 위치를 조정할 수 있을까요?', author:'정하린', date:'2일 전', comments:3 },
    { id:'inq-5', status:'wait', statusText:'답변 대기', title:'게시판 검색어가 띄어쓰기를 포함해도 검색되나요?', summary:'전공 필수, 전공필수처럼 띄어쓰기가 다른 키워드도 찾을 수 있으면 좋겠습니다.', author:'최유진', date:'3일 전', comments:0 },
    { id:'inq-6', status:'progress', statusText:'처리중', title:'관리자 답변 알림을 메일로 받을 수 있나요?', summary:'문의 답변이 등록되면 가입 이메일로 알림을 받는 기능을 검토 중인지 궁금합니다.', author:'오지훈', date:'4일 전', comments:1 },
    { id:'inq-7', status:'done', statusText:'답변 완료', title:'첨부파일 업로드는 몇 개까지 가능한가요?', summary:'오류 화면 캡처나 학사 자료 PDF를 문의글에 첨부할 수 있는지 문의합니다.', author:'한서연', date:'5일 전', comments:2 },
    { id:'inq-8', status:'wait', statusText:'답변 대기', title:'답변 품질 신고 기능도 문의사항에 넣을 수 있나요?', summary:'챗봇 답변이 부정확할 때 문의사항으로 바로 연결되는 흐름을 제안합니다.', author:'문태호', date:'6일 전', comments:0 },
    { id:'inq-9', status:'done', statusText:'답변 완료', title:'게시글 삭제 후 복구가 가능한가요?', summary:'실수로 삭제한 게시글을 관리자에게 요청해 복구할 수 있는지 문의합니다.', author:'김민지', date:'7일 전', comments:1 },
    { id:'inq-10', status:'progress', statusText:'처리중', title:'문의글 답변 순서를 정렬할 수 있나요?', summary:'최신 답변순, 답변 대기순 정렬이 가능한지 확인하고 싶습니다.', author:'이도현', date:'8일 전', comments:2 },
    { id:'inq-11', status:'wait', statusText:'답변 대기', title:'비공개 문의글 표시 아이콘이 필요합니다', summary:'목록에서 비공개 문의글을 구분할 수 있는 표시가 있으면 좋겠습니다.', author:'정하린', date:'9일 전', comments:0 },
    { id:'inq-12', status:'done', statusText:'답변 완료', title:'모바일 검색창에서 엔터 입력이 동작하지 않아요', summary:'모바일 키보드의 검색 버튼을 눌렀을 때 필터가 유지되는지 문의합니다.', author:'최유진', date:'10일 전', comments:1 },
    { id:'inq-13', status:'progress', statusText:'처리중', title:'관리자 페이지에서 문의 답변을 바로 달 수 있나요?', summary:'관리자 페이지와 문의사항 화면을 연결하는 흐름이 필요한지 확인합니다.', author:'오지훈', date:'11일 전', comments:1 },
    { id:'inq-14', status:'wait', statusText:'답변 대기', title:'문의 유형을 선택하는 드롭다운이 필요합니다', summary:'계정, 데이터 오류, 답변 품질 같은 문의 유형 분류를 제안합니다.', author:'박서준', date:'12일 전', comments:0 },
    { id:'inq-15', status:'done', statusText:'답변 완료', title:'댓글 알림은 어디에서 확인하나요?', summary:'게시글 댓글이 달렸을 때 사용자에게 알림을 줄 수 있는지 문의합니다.', author:'한서연', date:'13일 전', comments:2 },
    { id:'inq-16', status:'wait', statusText:'답변 대기', title:'문의글 작성 화면에서 임시저장을 지원하나요?', summary:'작성 중인 문의를 저장했다가 다시 이어서 쓸 수 있는 기능을 요청합니다.', author:'문태호', date:'14일 전', comments:0 },
  ];

  [42, 38, 27, 31, 44, 29, 23, 19, 36, 33, 21, 25, 28, 17, 30, 16]
    .forEach((views, index)=>{ inquiries[index].views = views; });

  const inquiryStatuses = [
    { value:'wait', label:'답변 대기' },
    { value:'progress', label:'처리중' },
    { value:'done', label:'답변 완료' },
  ];

  const myPostIds = ['ai-course-recommend', 'professor-office-hour', 'course-withdrawal'];
  const myInquiryIds = ['inq-1', 'inq-2', 'inq-5'];

  const Community = {
    activePostId:'graduation-requirements',
    activeInquiryId:'inq-1',
    boardQuery:'',
    boardPage:1,
    inquiryQuery:'',
    inquiryPage:1,
    railCollapsed:window.sessionStorage?.getItem('communityRailCollapsed') === '1',

    esc(value){
      return String(value ?? '').replace(/[&<>"']/g, ch=>({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[ch]));
    },

    post(id){
      return boardPosts.find(p=>p.id===id) || boardPosts[0];
    },

    inquiry(id){
      return inquiries.find(item=>item.id===id) || inquiries[0];
    },

    setInquiryStatus(id, status){
      const option = inquiryStatuses.find(item=>item.value === status);
      const inquiry = this.inquiry(id);
      if(!option || !inquiry) return;
      inquiry.status = option.value;
      inquiry.statusText = option.label;
    },

    metaHTML(item){
      return `<div class="community-meta">
        <span>${svg('eye')}${item.views}</span>
        <span>${svg('message')}${item.comments}</span>
        <span>${svg('calendar')}${this.esc(item.date)}</span>
      </div>`;
    },

    detailMetaHTML(item){
      return `조회 ${item.views} · 댓글 ${item.comments} · 작성일 ${this.esc(item.date)}`;
    },

    inquiryStatusControlHTML(item){
      if(!this.isAdmin()) return '';
      return `<div class="community-admin-status">
        <label for="inquiry-status-select">문의 상태</label>
        <select id="inquiry-status-select" data-inquiry-status-id="${this.esc(item.id)}">
          ${inquiryStatuses.map(option=>`
            <option value="${option.value}" ${option.value === item.status ? 'selected' : ''}>${option.label}</option>
          `).join('')}
        </select>
      </div>`;
    },

    filtered(items, query){
      const q = query.trim().toLowerCase();
      if(!q) return items;
      return items.filter(item=>{
        const values = [item.title, item.summary, item.category, item.badge, item.author, item.statusText];
        return values.some(value=>String(value || '').toLowerCase().includes(q));
      });
    },

    pageItems(items, page){
      const start = (page - 1) * PAGE_SIZE;
      return items.slice(start, start + PAGE_SIZE);
    },

    boardItems(items){
      const noticeItems = items
        .filter(item=>item.isNotice)
        .sort((a,b)=>String(b.noticeAt || '').localeCompare(String(a.noticeAt || '')))
        .slice(0, 3);
      const noticeIds = new Set(noticeItems.map(item=>item.id));
      return noticeItems.concat(items.filter(item=>!noticeIds.has(item.id)));
    },

    isAdmin(){
      return CURRENT_USER.role === 'admin';
    },

    canManage(author){
      return this.isAdmin() || CURRENT_USER.name === author;
    },

    detailActionsHTML(author){
      if(!this.canManage(author)) return '';
      return `<div class="community-actions">
        <button class="btn btn-soft btn-sm" type="button">${svg('settings')} 수정</button>
        <button class="btn btn-ghost btn-sm" type="button">${svg('x')} 삭제</button>
      </div>`;
    },

    replyActionsHTML(author){
      if(!this.canManage(author)) return '';
      return `<div class="community-reply-actions">
        <button class="community-reply-action" type="button">${svg('settings')} 수정</button>
        <button class="community-reply-action" type="button">${svg('x')} 삭제</button>
      </div>`;
    },

    replyHTML(reply){
      return `<div class="community-reply">
        <div class="community-reply-head">
          <strong>${this.esc(reply.author)}</strong>
          ${this.replyActionsHTML(reply.author)}
        </div>
        <p>${this.esc(reply.body)}</p>
      </div>`;
    },

    railClass(){
      this.railCollapsed = window.sessionStorage?.getItem('communityRailCollapsed') === '1';
      return `rail scroll${this.railCollapsed ? ' collapsed' : ''}`;
    },

    setRailCollapsed(collapsed){
      this.railCollapsed = Boolean(collapsed);
      window.sessionStorage?.setItem('communityRailCollapsed', this.railCollapsed ? '1' : '0');
      document.getElementById('rail')?.classList.toggle('collapsed', this.railCollapsed);
    },

    toggleRail(){
      this.setRailCollapsed(!this.railCollapsed);
    },

    clampPage(page, total){
      const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
      return Math.min(Math.max(1, page), pages);
    },

    paginationHTML(total, page, type){
      const pages = Math.ceil(total / PAGE_SIZE);
      if(pages <= 1) return '';
      const pageButton = (target, label, extra='', aria='') => `
        <button class="community-page-btn ${extra}" data-page-type="${type}" data-page="${target}" type="button" ${aria ? `aria-label="${aria}" title="${aria}"` : ''}>${label}</button>`;
      if(pages <= 3){
        return `<div class="community-pages" aria-label="페이지 선택">
          ${Array.from({ length: pages }, (_, index)=>{
            const n = index + 1;
            return pageButton(n, n, n === page ? 'active' : '', `${n}페이지`);
          }).join('')}
        </div>`;
      }

      const start = Math.min(Math.max(1, page - 1), pages - 2);
      const visiblePages = [start, start + 1, start + 2];
      return `<div class="community-pages" aria-label="페이지 선택">
        <button class="community-page-btn nav" data-page-type="${type}" data-page="1" type="button" ${page === 1 ? 'disabled' : ''} aria-label="처음 페이지" title="처음 페이지">&laquo;</button>
        <button class="community-page-btn nav" data-page-type="${type}" data-page="${Math.max(1, page - 1)}" type="button" ${page === 1 ? 'disabled' : ''} aria-label="이전 페이지" title="이전 페이지">&lsaquo;</button>
        ${visiblePages.map(n=>pageButton(n, n, n === page ? 'active' : '', `${n}페이지`)).join('')}
        <button class="community-page-btn nav" data-page-type="${type}" data-page="${Math.min(pages, page + 1)}" type="button" ${page === pages ? 'disabled' : ''} aria-label="다음 페이지" title="다음 페이지">&rsaquo;</button>
        <button class="community-page-btn nav" data-page-type="${type}" data-page="${pages}" type="button" ${page === pages ? 'disabled' : ''} aria-label="마지막 페이지" title="마지막 페이지">&raquo;</button>
      </div>`;
    },

    myPosts(){
      return boardPosts.filter(post=>myPostIds.includes(post.id));
    },

    myInquiries(){
      return inquiries.filter(item=>myInquiryIds.includes(item.id));
    },

    railItemHTML(item, mode){
      if(mode === 'inquiry'){
        return `
          <div class="sess" data-community-inquiry="${item.id}" data-title="${this.esc(item.title)}">
            <div class="sess-ic">${svg('mail')}</div>
            <div class="sess-body">
              <div class="sess-title">${this.esc(item.title)}</div>
              <div class="sess-meta">${this.esc(item.statusText)} · ${this.esc(item.date)}</div>
            </div>
          </div>`;
      }
      return `
        <div class="sess" data-community-post="${item.id}" data-title="${this.esc(item.title)}">
          <div class="sess-ic">${svg(item.icon || 'message')}</div>
          <div class="sess-body">
            <div class="sess-title">${this.esc(item.title)}</div>
            <div class="sess-meta">${this.esc(item.date)} · 댓글 ${item.comments}개</div>
          </div>
        </div>`;
    },

    railHTML(active='board'){
      const mode = active === 'inquiry' ? 'inquiry' : 'board';
      const items = mode === 'inquiry' ? this.myInquiries() : this.myPosts();
      const list = items.map(item=>this.railItemHTML(item, mode)).join('');
      const writeLabel = mode === 'inquiry' ? '새 문의 작성' : '새 글 작성';
      const searchLabel = mode === 'inquiry' ? '내가 쓴 문의글 검색' : '내가 쓴 글 검색';
      const listLabel = mode === 'inquiry' ? '내가 쓴 문의글' : '내가 쓴 글';
      const placeholder = mode === 'inquiry' ? '내 문의글 검색' : '내 게시글 검색';

      return `
        <aside class="${this.railClass()}" id="rail">
          <div class="rail-top">
            <div class="brand"><span class="mark"><img src="${asset('images/mascot/nubzuki_idle.png')}" alt=""></span> 넙죽이<small>KAIST 학사도우미</small></div>
          </div>
          <button class="rail-new" id="community-write" data-community-write="${mode}">${svg('plus')} ${writeLabel}</button>
          <div class="rail-sec">${searchLabel}</div>
          <div class="rail-search">${svg('search')}<input placeholder="${placeholder}" id="community-my-search"></div>
          <div class="rail-sec">${listLabel}</div>
          <div class="rail-list scroll" id="community-my-list">${list}</div>
          <div class="rail-foot">
            <div class="user-card" id="community-user-card">
              <div class="avatar">${this.esc(CURRENT_USER.initial)}</div>
              <div class="uc-body"><div class="uc-name">${this.esc(CURRENT_USER.name)}</div><div class="uc-mail">${this.esc(CURRENT_USER.mail)}</div></div>
              ${svg('settings')}
            </div>
          </div>
        </aside>`;
    },

    topNav(active){
      const items = [
        ['chat','채팅','message'],
        ['board','게시판','book'],
        ['inquiry','문의','mail'],
      ];
      return `<nav class="community-nav" aria-label="주요 메뉴">
        ${items.map(([view,label,icon])=>`
          <button class="community-nav-btn ${active===view?'active':''}" data-community-go="${view}" type="button" title="${label}">
            ${svg(icon)} <span>${label}</span>
          </button>`).join('')}
      </nav>`;
    },

    shell(active, title, subtitle, content){
      return `
      <div class="chat-shell">
        ${this.railHTML(active)}
        <main class="chat-main community-main">
          <header class="chat-head">
            <button class="iconbtn" id="rail-toggle" title="사이드바">${svg('sidebar')}</button>
            <div>
              <div class="ch-title">${title}</div>
              <div class="ch-sub">${subtitle}</div>
            </div>
            <div class="spacer"></div>
            ${this.topNav(active)}
            ${CURRENT_USER.role==='admin' ? `<button class="btn btn-soft btn-sm" id="go-admin">${svg('chart')} 관리자</button>`:''}
            <button class="iconbtn" id="toggle-theme" title="테마">${svg(App.tweaks.theme==='dark'?'sun':'moon')}</button>
          </header>
          ${content}
        </main>
      </div>`;
    },

    boardHTML(){
      const filtered = this.boardItems(this.filtered(boardPosts, this.boardQuery));
      this.boardPage = this.clampPage(this.boardPage, filtered.length);
      const content = `
        <section class="community-page scroll">
          <div class="community-wrap">
            <div class="community-hero">
              <div>
                <span class="community-kicker">${svg('book')} 게시판</span>
                <h1 class="community-title">학사 정보를 빠르게 찾는 게시판</h1>
                <p class="community-desc">키워드를 검색하면 제목, 내용, 카테고리, 작성자 기준으로 게시글을 찾습니다.</p>
              </div>
              <div class="community-actions">
                <button class="btn btn-primary btn-sm" id="board-write-main">${svg('plus')} 글쓰기</button>
              </div>
            </div>

            <div class="community-toolbar community-toolbar-single">
              <label class="community-search">${svg('search')}<input id="board-search" value="${this.esc(this.boardQuery)}" placeholder="검색어를 입력하세요. 예: 졸업, 수강신청, 장학금"></label>
            </div>

            <div class="community-list-head">
              <strong id="board-count">게시글 ${filtered.length}개</strong>
              <span>한 페이지에 5개씩 표시</span>
            </div>
            <div class="community-list" id="board-list">${this.postsHTML(this.pageItems(filtered, this.boardPage))}</div>
            <div id="board-pages">${this.paginationHTML(filtered.length, this.boardPage, 'board')}</div>
          </div>
        </section>`;
      return this.shell('board', '게시판', '검색과 페이지 선택으로 게시글을 확인합니다.', content);
    },

    inquiryHTML(){
      const filtered = this.filtered(inquiries, this.inquiryQuery);
      this.inquiryPage = this.clampPage(this.inquiryPage, filtered.length);
      const content = `
        <section class="community-page scroll">
          <div class="community-wrap">
            <div class="community-hero">
              <div>
                <span class="community-kicker">${svg('mail')} 문의사항</span>
                <h1 class="community-title">운영자에게 남기는 문의 게시판</h1>
                <p class="community-desc">문의 제목, 내용, 작성자, 답변 상태를 검색해서 필요한 문의를 찾을 수 있습니다.</p>
              </div>
              <div class="community-actions">
                <button class="btn btn-primary btn-sm" id="inquiry-write-main">${svg('plus')} 문의하기</button>
              </div>
            </div>

            <div class="community-toolbar community-toolbar-single">
              <label class="community-search">${svg('search')}<input id="inquiry-search" value="${this.esc(this.inquiryQuery)}" placeholder="검색어를 입력하세요. 예: 로그인, 답변 완료, 모바일"></label>
            </div>

            <div class="community-list-head">
              <strong id="inquiry-count">문의 ${filtered.length}개</strong>
              <span>한 페이지에 5개씩 표시</span>
            </div>
            <div class="community-list" id="inquiry-list">${this.inquiriesHTML(this.pageItems(filtered, this.inquiryPage))}</div>
            <div id="inquiry-pages">${this.paginationHTML(filtered.length, this.inquiryPage, 'inquiry')}</div>
          </div>
        </section>`;
      return this.shell('inquiry', '문의사항', '검색과 페이지 선택으로 문의를 확인합니다.', content);
    },

    postHTML(){
      const p = this.post(this.activePostId);
      const replies = [
        { author:'김민지', body:'졸업 요건은 학번별로 차이가 있을 수 있어서 입학연도 필터가 있으면 좋겠습니다.' },
        { author:'학사도우미', body:'좋은 의견입니다. 백엔드 연결 시 학번/학과 기준 필터를 함께 검토하겠습니다.' },
      ];
      const content = `
        <section class="community-page scroll">
          <div class="community-wrap">
            <div class="community-hero">
              <div>
                <button class="btn btn-ghost btn-sm" id="back-board">${svg('arrowLeft')} 목록으로</button>
              </div>
              ${this.detailActionsHTML(p.author)}
            </div>

            <div class="community-detail">
              <article class="community-article">
                <header class="community-article-head">
                  <div class="community-row-top">
                    <span class="badge badge-blue">${this.esc(p.category)}</span>
                    <span class="badge badge-amber">${this.esc(p.badge)}</span>
                  </div>
                  <h1 class="community-detail-title">${this.esc(p.title)}</h1>
                  <div class="community-author">
                    <div class="avatar">${this.esc(p.author.slice(0,1))}</div>
                    <div>
                      <strong>${this.esc(p.author)}</strong>
                      <span>${this.detailMetaHTML(p)}</span>
                    </div>
                  </div>
                </header>
                <div class="community-article-body">
                  <p>이 화면은 게시글 상세 페이지 UI 예시입니다. 제목, 카테고리, 작성자, 본문, 첨부/출처, 댓글 영역이 한 흐름으로 읽히도록 구성했습니다.</p>
                  <p>실제 구현에서는 게시글 본문을 서버에서 받아오고, 수정/삭제 권한은 작성자 또는 관리자 권한에 맞춰 노출하면 됩니다. 현재는 화면 확인용 정적 콘텐츠만 배치했습니다.</p>
                  <div class="community-note">
                    <strong>학사 정보 확인 팁</strong><br>
                    공식 학사 정보는 게시글 내용과 함께 원문 링크를 제공하면 사용자가 최신 정보를 다시 검증하기 쉽습니다.
                  </div>
                  <p>게시글 하단에는 댓글 입력만 배치해 원본 채팅 화면처럼 본문 흐름을 방해하지 않도록 했습니다.</p>
                </div>
                <section class="community-comment">
                  <div class="community-comment-title">댓글 ${replies.length}개</div>
                  ${replies.map(reply=>this.replyHTML(reply)).join('')}
                  <div class="community-comment-box">
                    <input placeholder="댓글을 입력하세요">
                    <button class="btn btn-primary btn-sm">${svg('send')} 등록</button>
                  </div>
                </section>
              </article>
            </div>
          </div>
        </section>`;
      return this.shell('post', '게시글 상세', '게시글 본문과 댓글을 확인합니다.', content);
    },

    inquiryDetailHTML(){
      const item = this.inquiry(this.activeInquiryId);
      const answer = {
        author:'관리자',
        body:item.status === 'wait'
          ? '문의가 접수되었습니다. 확인 후 답변을 등록하겠습니다.'
          : '문의 내용을 확인했습니다. 동일한 문제가 반복되면 화면 캡처와 함께 다시 문의해주세요.',
      };
      const content = `
        <section class="community-page scroll">
          <div class="community-wrap">
            <div class="community-hero">
              <div>
                <button class="btn btn-ghost btn-sm" id="back-inquiry">${svg('arrowLeft')} 목록으로</button>
              </div>
              ${this.detailActionsHTML(item.author)}
            </div>

            <div class="community-detail">
              <article class="community-article">
                <header class="community-article-head">
                  <div class="community-row-top">
                    <span class="community-status ${item.status}">${this.esc(item.statusText)}</span>
                    <span class="badge badge-gray">문의사항</span>
                  </div>
                  ${this.inquiryStatusControlHTML(item)}
                  <h1 class="community-detail-title">${this.esc(item.title)}</h1>
                  <div class="community-author">
                    <div class="avatar">${this.esc(item.author.slice(0,1))}</div>
                    <div>
                      <strong>${this.esc(item.author)}</strong>
                      <span>${this.detailMetaHTML(item)}</span>
                    </div>
                  </div>
                </header>
                <div class="community-article-body">
                  <p>${this.esc(item.summary)}</p>
                  <div class="community-note">
                    <strong>문의 내용</strong><br>
                    로그인, 검색, 게시판 사용 중 문제가 발생한 화면과 재현 순서를 함께 남기면 답변을 더 빠르게 받을 수 있습니다.
                  </div>
                  <p>현재 화면은 문의 상세 UI 예시입니다. 실제 연결 후에는 문의 본문, 첨부파일, 공개 여부, 관리자 답변 상태를 서버 데이터로 채우면 됩니다.</p>
                </div>
                <section class="community-comment">
                  <div class="community-comment-title">관리자 답변</div>
                  ${this.replyHTML(answer)}
                  <div class="community-comment-box">
                    <input placeholder="추가 문의를 입력하세요">
                    <button class="btn btn-primary btn-sm">${svg('send')} 등록</button>
                  </div>
                </section>
              </article>
            </div>
          </div>
        </section>`;
      return this.shell('inquiry', '문의 상세', '문의 내용과 답변을 확인합니다.', content);
    },

    boardWriteHTML(){
      const canManagePostOptions = CURRENT_USER.role === 'admin';
      const content = `
        <section class="community-page scroll">
          <div class="community-wrap">
            <div class="community-hero">
              <div>
                <button class="btn btn-ghost btn-sm" id="back-board">${svg('arrowLeft')} 목록으로</button>
                <h1 class="community-title">게시판 글쓰기</h1>
                <p class="community-desc">학사 정보, 수강신청, 장학, 졸업 요건 등 공유할 내용을 작성하는 화면입니다.</p>
              </div>
              <div class="community-actions">
                <button class="btn btn-ghost btn-sm">${svg('copy')} 임시저장</button>
                <button class="btn btn-primary btn-sm">${svg('send')} 등록</button>
              </div>
            </div>

            <article class="community-article community-form-card">
              <div class="community-form">
                <label class="community-field">
                  <span>카테고리</span>
                  <select>
                    <option>학사</option>
                    <option>수강</option>
                    <option>장학</option>
                    <option>졸업</option>
                    <option>자유</option>
                  </select>
                </label>
                <label class="community-field">
                  <span>제목</span>
                  <input placeholder="제목을 입력하세요">
                </label>
                <label class="community-field">
                  <span>본문</span>
                  <textarea rows="10" placeholder="공유할 내용을 입력하세요"></textarea>
                </label>
                <label class="community-field">
                  <span>참고 링크</span>
                  <input placeholder="공식 페이지나 참고 링크를 입력하세요">
                </label>
                ${canManagePostOptions ? `
                <div class="community-check-row">
                  <label><input type="checkbox"> 공지로 표시</label>
                  <label><input type="checkbox"> 댓글 차단</label>
                </div>` : ''}
              </div>
            </article>
          </div>
        </section>`;
      return this.shell('board', '게시판 글쓰기', '게시판에 새 글을 작성합니다.', content);
    },

    inquiryWriteHTML(){
      const content = `
        <section class="community-page scroll">
          <div class="community-wrap">
            <div class="community-hero">
              <div>
                <button class="btn btn-ghost btn-sm" id="back-inquiry">${svg('arrowLeft')} 목록으로</button>
                <h1 class="community-title">문의 글쓰기</h1>
                <p class="community-desc">계정, 데이터, 화면 오류, 답변 품질과 관련된 문의를 남기는 화면입니다.</p>
              </div>
              <div class="community-actions">
                <button class="btn btn-ghost btn-sm">${svg('copy')} 임시저장</button>
                <button class="btn btn-primary btn-sm">${svg('send')} 문의 등록</button>
              </div>
            </div>

            <article class="community-article community-form-card">
              <div class="community-form">
                <label class="community-field">
                  <span>문의 유형</span>
                  <select>
                    <option>계정 및 로그인</option>
                    <option>데이터 오류</option>
                    <option>답변 품질</option>
                    <option>게시판 기능</option>
                    <option>기타</option>
                  </select>
                </label>
                <label class="community-field">
                  <span>제목</span>
                  <input placeholder="문의 제목을 입력하세요">
                </label>
                <label class="community-field">
                  <span>문의 내용</span>
                  <textarea rows="10" placeholder="오류 상황, 기대 동작, 재현 순서를 함께 입력하세요"></textarea>
                </label>
                <label class="community-field">
                  <span>첨부파일</span>
                  <input placeholder="파일 업로드 UI는 백엔드 연결 후 붙이면 됩니다">
                </label>
                <div class="community-check-row">
                  <label><input type="checkbox" checked> 비공개 문의</label>
                  <label><input type="checkbox"> 답변 완료 시 이메일 알림</label>
                </div>
              </div>
            </article>
          </div>
        </section>`;
      return this.shell('inquiry', '문의 글쓰기', '문의사항에 새 글을 작성합니다.', content);
    },

    postsHTML(posts){
      if(!posts.length) return `<div class="community-empty">${svg('search')}<strong>검색 결과가 없습니다.</strong><span>다른 키워드로 다시 검색해보세요.</span></div>`;
      return posts.map(p=>this.postRow(p)).join('');
    },

    inquiriesHTML(items){
      if(!items.length) return `<div class="community-empty">${svg('search')}<strong>검색 결과가 없습니다.</strong><span>다른 키워드로 다시 검색해보세요.</span></div>`;
      return items.map(item=>`
        <button class="community-post" data-community-inquiry="${item.id}" type="button">
          <div class="community-post-ic">${svg('mail')}</div>
          <div class="community-post-body">
            <div class="community-row-top">
              <span class="community-status ${item.status}">${this.esc(item.statusText)}</span>
              <span class="badge badge-gray">${this.esc(item.author)}</span>
            </div>
            <div class="community-post-title">${this.esc(item.title)}</div>
            <div class="community-post-summary">${this.esc(item.summary)}</div>
          </div>
          ${this.metaHTML(item)}
        </button>`).join('');
    },

    postRow(p){
      const noticeBadge = p.isNotice ? `<span class="badge badge-amber">${this.esc(p.badge)}</span>` : '';
      return `
        <button class="community-post ${p.isNotice ? 'notice' : ''}" data-community-post="${p.id}" type="button">
          <div class="community-post-ic">${svg(p.icon || 'book')}</div>
          <div class="community-post-body">
            <div class="community-row-top">
              <span class="badge badge-blue">${this.esc(p.category)}</span>
              ${noticeBadge}
              <span class="badge badge-gray">${this.esc(p.author)}</span>
            </div>
            <div class="community-post-title">${this.esc(p.title)}</div>
            <div class="community-post-summary">${this.esc(p.summary)}</div>
          </div>
          ${this.metaHTML(p)}
        </button>`;
    },

    renderBoard(){
      const filtered = this.boardItems(this.filtered(boardPosts, this.boardQuery));
      this.boardPage = this.clampPage(this.boardPage, filtered.length);
      const list = document.getElementById('board-list');
      const count = document.getElementById('board-count');
      const pages = document.getElementById('board-pages');
      if(list) list.innerHTML = this.postsHTML(this.pageItems(filtered, this.boardPage));
      if(count) count.textContent = `게시글 ${filtered.length}개`;
      if(pages) pages.innerHTML = this.paginationHTML(filtered.length, this.boardPage, 'board');
      this.wirePostClicks();
      this.wirePagination();
    },

    renderInquiry(){
      const filtered = this.filtered(inquiries, this.inquiryQuery);
      this.inquiryPage = this.clampPage(this.inquiryPage, filtered.length);
      const list = document.getElementById('inquiry-list');
      const count = document.getElementById('inquiry-count');
      const pages = document.getElementById('inquiry-pages');
      if(list) list.innerHTML = this.inquiriesHTML(this.pageItems(filtered, this.inquiryPage));
      if(count) count.textContent = `문의 ${filtered.length}개`;
      if(pages) pages.innerHTML = this.paginationHTML(filtered.length, this.inquiryPage, 'inquiry');
      this.wireInquiryClicks();
      this.wirePagination();
    },

    wirePostClicks(){
      document.querySelectorAll('[data-community-post]').forEach(btn=>{
        btn.addEventListener('click', ()=>{
          this.activePostId = btn.dataset.communityPost || this.activePostId;
          App.go('post');
        });
      });
    },

    wireInquiryClicks(){
      document.querySelectorAll('[data-community-inquiry]').forEach(btn=>{
        btn.addEventListener('click', ()=>{
          this.activeInquiryId = btn.dataset.communityInquiry || this.activeInquiryId;
          App.go('inquiry-post');
        });
      });
    },

    wirePagination(){
      document.querySelectorAll('[data-page-type]').forEach(btn=>{
        btn.addEventListener('click', ()=>{
          const page = Number(btn.dataset.page) || 1;
          if(btn.dataset.pageType === 'board'){
            this.boardPage = page;
            this.renderBoard();
          }else{
            this.inquiryPage = page;
            this.renderInquiry();
          }
        });
      });
    },

    wireTopNav(){
      document.querySelectorAll('[data-community-go]').forEach(btn=>{
        btn.addEventListener('click', ()=>App.go(btn.dataset.communityGo));
      });
    },

    init(){
      Mascot.mount(document.querySelector('.chat-shell'));
      this.setRailCollapsed(this.railCollapsed);
      document.getElementById('rail-toggle')?.addEventListener('click', ()=>this.toggleRail());
      document.getElementById('toggle-theme')?.addEventListener('click', ()=>App.toggleTheme());
      document.getElementById('go-admin')?.addEventListener('click', ()=>App.go('admin'));
      document.getElementById('community-write')?.addEventListener('click', event=>{
        App.go(event.currentTarget.dataset.communityWrite === 'inquiry' ? 'inquiry-write' : 'board-write');
      });
      document.getElementById('board-write-main')?.addEventListener('click', ()=>App.go('board-write'));
      document.getElementById('inquiry-write-main')?.addEventListener('click', ()=>App.go('inquiry-write'));
      document.getElementById('community-user-card')?.addEventListener('click', ()=>App.go(CURRENT_USER.role==='guest' ? 'login' : 'chat'));
      document.getElementById('back-board')?.addEventListener('click', ()=>App.go('board'));
      document.getElementById('back-inquiry')?.addEventListener('click', ()=>App.go('inquiry'));

      this.wireTopNav();
      this.wirePostClicks();
      this.wireInquiryClicks();
      this.wirePagination();

      const boardSearch = document.getElementById('board-search');
      if(boardSearch){
        boardSearch.addEventListener('input', ()=>{
          this.boardQuery = boardSearch.value;
          this.boardPage = 1;
          this.renderBoard();
        });
      }

      const inquirySearch = document.getElementById('inquiry-search');
      if(inquirySearch){
        inquirySearch.addEventListener('input', ()=>{
          this.inquiryQuery = inquirySearch.value;
          this.inquiryPage = 1;
          this.renderInquiry();
        });
      }

      const mySearch = document.getElementById('community-my-search');
      if(mySearch){
        mySearch.addEventListener('input', ()=>{
          const q = mySearch.value.trim().toLowerCase();
          document.querySelectorAll('#community-my-list .sess').forEach(el=>{
            const hit = !q || el.textContent.toLowerCase().includes(q);
            el.style.display = hit ? '' : 'none';
          });
        });
      }

      const inquiryStatusSelect = document.getElementById('inquiry-status-select');
      if(inquiryStatusSelect){
        inquiryStatusSelect.addEventListener('change', event=>{
          this.setInquiryStatus(event.currentTarget.dataset.inquiryStatusId, event.currentTarget.value);
          App.go('inquiry-post');
        });
      }
    },
  };

  const originalGo = App.go.bind(App);
  App.go = function(view){
    if(['board','inquiry','post','inquiry-post','board-write','inquiry-write'].includes(view)){
      this.current = view;
      if(typeof Chat !== 'undefined') clearTimeout(Chat.idleTimer);
      const app = document.getElementById('app');
      if(view === 'board') app.innerHTML = Community.boardHTML();
      else if(view === 'inquiry') app.innerHTML = Community.inquiryHTML();
      else if(view === 'post') app.innerHTML = Community.postHTML();
      else if(view === 'inquiry-post') app.innerHTML = Community.inquiryDetailHTML();
      else if(view === 'board-write') app.innerHTML = Community.boardWriteHTML();
      else app.innerHTML = Community.inquiryWriteHTML();
      Community.init();
      this.applyTweaks();
      this.syncProtoNav();
      return;
    }
    originalGo(view);
  };

  App.buildProtoNav = function(){
    const old = document.getElementById('proto-nav');
    if(old) old.remove();
    if(CURRENT_USER.role !== 'admin') return;
    const nav = document.createElement('div');
    nav.id = 'proto-nav';
    const items = [
      ['login','로그인'],
      ['signup','회원가입'],
      ['chat','채팅'],
      ['board','게시판'],
      ['inquiry','문의'],
      ['admin','관리자'],
    ];
    nav.innerHTML = '<span class="pn-label">화면</span>' + items.map(i=>`<button data-v="${i[0]}">${i[1]}</button>`).join('');
    document.body.appendChild(nav);
    nav.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>this.go(b.dataset.v)));
    this.syncProtoNav();
  };

  window.Community = Community;
})();
