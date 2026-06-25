/* ============================================================
   Community UI views — board, inquiry, detail, write screens.
   Data is loaded from Django JSON APIs under /api/community/.
   ============================================================ */
(function(){
  const PAGE_SIZE = 5;
  const inquiryStatuses = [
    { value:'wait', label:'답변 대기' },
    { value:'progress', label:'처리중' },
    { value:'done', label:'답변 완료' },
  ];

  const boardCategories = ['학사', '수강', '장학', '졸업', '연구', '생활', '자유'];
  const inquiryCategories = ['계정 및 로그인', '데이터 오류', '답변 품질', '게시판 기능', '기타'];

  const Community = {
    activePostId:null,
    activeInquiryId:null,
    boardQuery:'',
    boardPage:1,
    boardTotal:0,
    boardPages:1,
    boardPosts:[],
    inquiryQuery:'',
    inquiryPage:1,
    inquiryTotal:0,
    inquiryPages:1,
    inquiries:[],
    myPosts:[],
    myInquiries:[],
    searchTimer:null,
    railCollapsed:window.sessionStorage?.getItem('communityRailCollapsed') === '1',

    esc(value){
      return String(value ?? '').replace(/[&<>"']/g, ch=>({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[ch]));
    },

    attr(value){
      return this.esc(value).replace(/`/g, '&#96;');
    },

    paragraphHTML(value){
      const text = String(value || '').trim();
      if(!text) return '<p>내용이 없습니다.</p>';
      return text
        .split(/\n{2,}/)
        .map(block=>`<p>${this.esc(block).replace(/\n/g, '<br>')}</p>`)
        .join('');
    },

    isGuest(){
      return CURRENT_USER.role === 'guest';
    },

    isAdmin(){
      return CURRENT_USER.role === 'admin';
    },

    loadingHTML(label='불러오는 중입니다.'){
      return `<div class="community-empty">${svg('refresh')}<strong>${this.esc(label)}</strong><span>잠시만 기다려주세요.</span></div>`;
    },

    errorHTML(message){
      return `<div class="community-empty">${svg('x')}<strong>요청을 처리하지 못했습니다.</strong><span>${this.esc(message || '다시 시도해 주세요.')}</span></div>`;
    },

    metaHTML(item){
      return `<div class="community-meta">
        <span>${svg('eye')}${Number(item.views || 0)}</span>
        <span>${svg('message')}${Number(item.comments || 0)}</span>
        <span>${svg('calendar')}${this.esc(item.date || '')}</span>
      </div>`;
    },

    detailMetaHTML(item){
      return `조회 ${Number(item.views || 0)} · 댓글 ${Number(item.comments || 0)} · 작성일 ${this.esc(item.date || '')}`;
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

    paginationHTML(total, page, pages, type){
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

    async loadMine(){
      if(this.isGuest()){
        this.myPosts = [];
        this.myInquiries = [];
        return;
      }

      try{
        const data = await Api.communityMine();
        this.myPosts = data.posts || [];
        this.myInquiries = data.inquiries || [];
      }catch(err){
        this.myPosts = [];
        this.myInquiries = [];
      }
    },

    async fetchPosts(){
      const data = await Api.communityPosts({
        q:this.boardQuery,
        page:this.boardPage,
        page_size:PAGE_SIZE,
      });
      this.boardPosts = data.posts || [];
      this.boardTotal = data.count || 0;
      this.boardPage = data.page || 1;
      this.boardPages = data.pages || 1;
    },

    async fetchInquiries(){
      const data = await Api.communityInquiries({
        q:this.inquiryQuery,
        page:this.inquiryPage,
        page_size:PAGE_SIZE,
      });
      this.inquiries = data.inquiries || [];
      this.inquiryTotal = data.count || 0;
      this.inquiryPage = data.page || 1;
      this.inquiryPages = data.pages || 1;
    },

    mount(html){
      document.getElementById('app').innerHTML = html;
      this.init();
      App.applyTweaks();
      App.syncProtoNav();
    },

    railItemHTML(item, mode){
      if(mode === 'inquiry'){
        return `
          <div class="sess" data-community-inquiry="${item.id}" data-title="${this.attr(item.title)}">
            <div class="sess-ic">${svg('mail')}</div>
            <div class="sess-body">
              <div class="sess-title">${this.esc(item.title)}</div>
              <div class="sess-meta">${this.esc(item.statusText)} · ${this.esc(item.date)}</div>
            </div>
          </div>`;
      }

      return `
        <div class="sess" data-community-post="${item.id}" data-title="${this.attr(item.title)}">
          <div class="sess-ic">${svg(item.icon || 'book')}</div>
          <div class="sess-body">
            <div class="sess-title">${this.esc(item.title)}</div>
            <div class="sess-meta">${this.esc(item.date)} · 댓글 ${Number(item.comments || 0)}개</div>
          </div>
        </div>`;
    },

    railHTML(active='board'){
      const mode = active === 'inquiry' ? 'inquiry' : 'board';
      const items = mode === 'inquiry' ? this.myInquiries : this.myPosts;
      const list = items.length
        ? items.map(item=>this.railItemHTML(item, mode)).join('')
        : `<div class="community-empty community-empty-compact"><span>${this.isGuest() ? '로그인 후 확인할 수 있습니다.' : '작성한 글이 없습니다.'}</span></div>`;
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

    boardHTML(state='ready', message=''){
      const listHTML = state === 'loading'
        ? this.loadingHTML('게시글을 불러오는 중입니다.')
        : state === 'error'
          ? this.errorHTML(message)
          : this.postsHTML(this.boardPosts);
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
              <label class="community-search">${svg('search')}<input id="board-search" value="${this.attr(this.boardQuery)}" placeholder="검색어를 입력하세요. 예: 졸업, 수강신청, 장학금"></label>
            </div>

            <div class="community-list-head">
              <strong id="board-count">게시글 ${this.boardTotal}개</strong>
              <span>한 페이지에 5개씩 표시</span>
            </div>
            <div class="community-list" id="board-list">${listHTML}</div>
            <div id="board-pages">${this.paginationHTML(this.boardTotal, this.boardPage, this.boardPages, 'board')}</div>
          </div>
        </section>`;
      return this.shell('board', '게시판', '검색과 페이지 선택으로 게시글을 확인합니다.', content);
    },

    inquiryHTML(state='ready', message=''){
      const listHTML = state === 'loading'
        ? this.loadingHTML('문의글을 불러오는 중입니다.')
        : state === 'error'
          ? this.errorHTML(message)
          : this.inquiriesHTML(this.inquiries);
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
              <label class="community-search">${svg('search')}<input id="inquiry-search" value="${this.attr(this.inquiryQuery)}" placeholder="검색어를 입력하세요. 예: 로그인, 답변 완료, 모바일"></label>
            </div>

            <div class="community-list-head">
              <strong id="inquiry-count">문의 ${this.inquiryTotal}개</strong>
              <span>한 페이지에 5개씩 표시</span>
            </div>
            <div class="community-list" id="inquiry-list">${listHTML}</div>
            <div id="inquiry-pages">${this.paginationHTML(this.inquiryTotal, this.inquiryPage, this.inquiryPages, 'inquiry')}</div>
          </div>
        </section>`;
      return this.shell('inquiry', '문의사항', '검색과 페이지 선택으로 문의를 확인합니다.', content);
    },

    postsHTML(posts){
      if(!posts.length) return `<div class="community-empty">${svg('search')}<strong>게시글이 없습니다.</strong><span>첫 글을 작성하거나 다른 검색어를 입력해보세요.</span></div>`;
      return posts.map(p=>this.postRow(p)).join('');
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

    inquiriesHTML(items){
      if(!items.length) return `<div class="community-empty">${svg('search')}<strong>문의글이 없습니다.</strong><span>첫 문의를 작성하거나 다른 검색어를 입력해보세요.</span></div>`;
      return items.map(item=>`
        <button class="community-post" data-community-inquiry="${item.id}" type="button">
          <div class="community-post-ic">${svg('mail')}</div>
          <div class="community-post-body">
            <div class="community-row-top">
              <span class="community-status ${this.esc(item.status)}">${this.esc(item.statusText)}</span>
              <span class="badge badge-blue">${this.esc(item.category)}</span>
              <span class="badge badge-gray">${this.esc(item.author)}</span>
            </div>
            <div class="community-post-title">${this.esc(item.title)}</div>
            <div class="community-post-summary">${this.esc(item.summary)}</div>
          </div>
          ${this.metaHTML(item)}
        </button>`).join('');
    },

    detailActionsHTML(item, type){
      if(!item.canManage) return '';
      return `<div class="community-actions">
        <button class="btn btn-soft btn-sm" id="${type}-edit" type="button">${svg('settings')} 수정</button>
        <button class="btn btn-ghost btn-sm" id="${type}-delete" type="button">${svg('x')} 삭제</button>
      </div>`;
    },

    replyActionsHTML(reply){
      if(!reply.canManage) return '';
      return `<div class="community-reply-actions">
        <button class="community-reply-action" data-comment-edit="${reply.id}" type="button">${svg('settings')} 수정</button>
        <button class="community-reply-action" data-comment-delete="${reply.id}" type="button">${svg('x')} 삭제</button>
      </div>`;
    },

    replyHTML(reply){
      return `<div class="community-reply">
        <div class="community-reply-head">
          <strong>${this.esc(reply.author)}</strong>
          ${this.replyActionsHTML(reply)}
        </div>
        <p>${this.esc(reply.body)}</p>
      </div>`;
    },

    commentBoxHTML(type, item){
      if(this.isGuest()){
        return `<div class="community-comment-box"><input disabled placeholder="로그인 후 댓글을 작성할 수 있습니다"><button class="btn btn-primary btn-sm" type="button" data-community-go="login">${svg('send')} 로그인</button></div>`;
      }

      if(type === 'post' && (item.isCommentBlocked || item.canComment === false)){
        return `<div class="community-comment-box"><input disabled placeholder="댓글이 차단된 게시글입니다"><button class="btn btn-primary btn-sm" disabled type="button">${svg('send')} 등록</button></div>`;
      }

      return `<form class="community-comment-box" id="${type}-comment-form">
        <input id="${type}-comment-input" placeholder="댓글을 입력하세요">
        <button class="btn btn-primary btn-sm" type="submit">${svg('send')} 등록</button>
      </form>`;
    },

    postDetailHTML(post, state='ready', message=''){
      const content = state === 'loading'
        ? `<section class="community-page scroll"><div class="community-wrap">${this.loadingHTML('게시글을 불러오는 중입니다.')}</div></section>`
        : state === 'error'
          ? `<section class="community-page scroll"><div class="community-wrap">${this.errorHTML(message)}</div></section>`
          : `
        <section class="community-page scroll">
          <div class="community-wrap">
            <div class="community-hero">
              <div>
                <button class="btn btn-ghost btn-sm" id="back-board">${svg('arrowLeft')} 목록으로</button>
              </div>
              ${this.detailActionsHTML(post, 'post')}
            </div>

            <div class="community-detail">
              <article class="community-article">
                <header class="community-article-head">
                  <div class="community-row-top">
                    <span class="badge badge-blue">${this.esc(post.category)}</span>
                    ${post.isNotice ? `<span class="badge badge-amber">공지</span>` : ''}
                    ${post.isCommentBlocked ? `<span class="badge badge-gray">댓글 차단</span>` : ''}
                  </div>
                  <h1 class="community-detail-title">${this.esc(post.title)}</h1>
                  <div class="community-author">
                    <div class="avatar">${this.esc((post.author || '?').slice(0,1))}</div>
                    <div>
                      <strong>${this.esc(post.author)}</strong>
                      <span>${this.detailMetaHTML(post)}</span>
                    </div>
                  </div>
                </header>
                <div class="community-article-body">
                  ${this.paragraphHTML(post.content)}
                  ${post.referenceUrl ? `<div class="community-note"><strong>참고 링크</strong><br><a href="${this.attr(post.referenceUrl)}" target="_blank" rel="noopener">${this.esc(post.referenceUrl)}</a></div>` : ''}
                </div>
                <section class="community-comment">
                  <div class="community-comment-title">댓글 ${Number(post.comments || 0)}개</div>
                  ${(post.replies || []).map(reply=>this.replyHTML(reply)).join('')}
                  ${this.commentBoxHTML('post', post)}
                </section>
              </article>
            </div>
          </div>
        </section>`;
      return this.shell('post', '게시글 상세', '게시글 본문과 댓글을 확인합니다.', content);
    },

    inquiryStatusControlHTML(item){
      if(!item.canChangeStatus) return '';
      return `<div class="community-admin-status">
        <label for="inquiry-status-select">문의 상태</label>
        <select id="inquiry-status-select" data-inquiry-status-id="${this.esc(item.id)}">
          ${inquiryStatuses.map(option=>`
            <option value="${option.value}" ${option.value === item.status ? 'selected' : ''}>${option.label}</option>
          `).join('')}
        </select>
      </div>`;
    },

    inquiryDetailHTML(item, state='ready', message=''){
      const content = state === 'loading'
        ? `<section class="community-page scroll"><div class="community-wrap">${this.loadingHTML('문의글을 불러오는 중입니다.')}</div></section>`
        : state === 'error'
          ? `<section class="community-page scroll"><div class="community-wrap">${this.errorHTML(message)}</div></section>`
          : `
        <section class="community-page scroll">
          <div class="community-wrap">
            <div class="community-hero">
              <div>
                <button class="btn btn-ghost btn-sm" id="back-inquiry">${svg('arrowLeft')} 목록으로</button>
              </div>
              ${this.detailActionsHTML(item, 'inquiry')}
            </div>

            <div class="community-detail">
              <article class="community-article">
                <header class="community-article-head">
                  <div class="community-row-top">
                    <span class="community-status ${this.esc(item.status)}">${this.esc(item.statusText)}</span>
                    <span class="badge badge-blue">${this.esc(item.category)}</span>
                    ${item.isPrivate ? `<span class="badge badge-gray">비공개</span>` : ''}
                  </div>
                  ${this.inquiryStatusControlHTML(item)}
                  <h1 class="community-detail-title">${this.esc(item.title)}</h1>
                  <div class="community-author">
                    <div class="avatar">${this.esc((item.author || '?').slice(0,1))}</div>
                    <div>
                      <strong>${this.esc(item.author)}</strong>
                      <span>${this.detailMetaHTML(item)}</span>
                    </div>
                  </div>
                </header>
                <div class="community-article-body">
                  ${this.paragraphHTML(item.content)}
                </div>
                <section class="community-comment">
                  <div class="community-comment-title">답변 및 댓글 ${Number(item.comments || 0)}개</div>
                  ${(item.replies || []).map(reply=>this.replyHTML(reply)).join('')}
                  ${this.commentBoxHTML('inquiry', item)}
                </section>
              </article>
            </div>
          </div>
        </section>`;
      return this.shell('inquiry', '문의 상세', '문의 내용과 답변을 확인합니다.', content);
    },

    boardWriteHTML(post=null, state='ready', message=''){
      const editing = Boolean(post);
      const canManagePostOptions = this.isAdmin();
      const content = state === 'loading'
        ? `<section class="community-page scroll"><div class="community-wrap">${this.loadingHTML('게시글 정보를 불러오는 중입니다.')}</div></section>`
        : state === 'error'
          ? `<section class="community-page scroll"><div class="community-wrap">${this.errorHTML(message)}</div></section>`
          : `
        <section class="community-page scroll">
          <div class="community-wrap">
            <div class="community-hero">
              <div>
                <button class="btn btn-ghost btn-sm" id="back-board">${svg('arrowLeft')} 목록으로</button>
                <h1 class="community-title">게시판 ${editing ? '글 수정' : '글쓰기'}</h1>
                <p class="community-desc">학사 정보, 수강신청, 장학, 졸업 요건 등 공유할 내용을 작성합니다.</p>
              </div>
              <div class="community-actions">
                <button class="btn btn-primary btn-sm" form="board-form" type="submit">${svg('send')} ${editing ? '수정 완료' : '등록'}</button>
              </div>
            </div>

            <article class="community-article community-form-card">
              <form class="community-form" id="board-form" data-post-id="${editing ? this.attr(post.id) : ''}">
                <label class="community-field">
                  <span>카테고리</span>
                  <select name="category">
                    ${boardCategories.map(category=>`<option value="${this.attr(category)}" ${post?.category === category ? 'selected' : ''}>${this.esc(category)}</option>`).join('')}
                  </select>
                </label>
                <label class="community-field">
                  <span>제목</span>
                  <input name="title" value="${this.attr(post?.title || '')}" placeholder="제목을 입력하세요">
                </label>
                <label class="community-field">
                  <span>본문</span>
                  <textarea name="content" rows="10" placeholder="공유할 내용을 입력하세요">${this.esc(post?.content || '')}</textarea>
                </label>
                <label class="community-field">
                  <span>참고 링크</span>
                  <input name="referenceUrl" value="${this.attr(post?.referenceUrl || '')}" placeholder="공식 페이지나 참고 링크를 입력하세요">
                </label>
                ${canManagePostOptions ? `
                <div class="community-check-row">
                  <label><input name="isNotice" type="checkbox" ${post?.isNotice ? 'checked' : ''}> 공지로 표시</label>
                  <label><input name="isCommentBlocked" type="checkbox" ${post?.isCommentBlocked ? 'checked' : ''}> 댓글 차단</label>
                </div>` : ''}
              </form>
            </article>
          </div>
        </section>`;
      return this.shell('board', editing ? '게시판 글 수정' : '게시판 글쓰기', '게시판에 글을 작성합니다.', content);
    },

    inquiryWriteHTML(item=null, state='ready', message=''){
      const editing = Boolean(item);
      const content = state === 'loading'
        ? `<section class="community-page scroll"><div class="community-wrap">${this.loadingHTML('문의글 정보를 불러오는 중입니다.')}</div></section>`
        : state === 'error'
          ? `<section class="community-page scroll"><div class="community-wrap">${this.errorHTML(message)}</div></section>`
          : `
        <section class="community-page scroll">
          <div class="community-wrap">
            <div class="community-hero">
              <div>
                <button class="btn btn-ghost btn-sm" id="back-inquiry">${svg('arrowLeft')} 목록으로</button>
                <h1 class="community-title">문의 ${editing ? '글 수정' : '글쓰기'}</h1>
                <p class="community-desc">계정, 데이터, 화면 오류, 답변 품질과 관련된 문의를 남깁니다.</p>
              </div>
              <div class="community-actions">
                <button class="btn btn-primary btn-sm" form="inquiry-form" type="submit">${svg('send')} ${editing ? '수정 완료' : '문의 등록'}</button>
              </div>
            </div>

            <article class="community-article community-form-card">
              <form class="community-form" id="inquiry-form" data-inquiry-id="${editing ? this.attr(item.id) : ''}">
                <label class="community-field">
                  <span>문의 유형</span>
                  <select name="category">
                    ${inquiryCategories.map(category=>`<option value="${this.attr(category)}" ${item?.category === category ? 'selected' : ''}>${this.esc(category)}</option>`).join('')}
                  </select>
                </label>
                <label class="community-field">
                  <span>제목</span>
                  <input name="title" value="${this.attr(item?.title || '')}" placeholder="문의 제목을 입력하세요">
                </label>
                <label class="community-field">
                  <span>문의 내용</span>
                  <textarea name="content" rows="10" placeholder="오류 상황, 기대 동작, 재현 순서를 함께 입력하세요">${this.esc(item?.content || '')}</textarea>
                </label>
                <div class="community-check-row">
                  <label><input name="isPrivate" type="checkbox" ${item?.isPrivate === false ? '' : 'checked'}> 비공개 문의</label>
                  <label><input name="emailOnAnswer" type="checkbox" ${item?.emailOnAnswer ? 'checked' : ''}> 답변 완료 시 이메일 알림</label>
                </div>
              </form>
            </article>
          </div>
        </section>`;
      return this.shell('inquiry', editing ? '문의 글 수정' : '문의 글쓰기', '문의사항에 글을 작성합니다.', content);
    },

    async showBoard(){
      this.mount(this.boardHTML('loading'));
      await this.loadMine();
      try{
        await this.fetchPosts();
        this.mount(this.boardHTML());
      }catch(err){
        this.mount(this.boardHTML('error', err.message));
      }
    },

    async showInquiry(){
      this.mount(this.inquiryHTML('loading'));
      await this.loadMine();
      try{
        await this.fetchInquiries();
        this.mount(this.inquiryHTML());
      }catch(err){
        this.mount(this.inquiryHTML('error', err.message));
      }
    },

    async reloadBoardList(){
      const list = document.getElementById('board-list');
      if(list) list.innerHTML = this.loadingHTML('게시글을 불러오는 중입니다.');
      try{
        await this.fetchPosts();
        document.getElementById('board-count').textContent = `게시글 ${this.boardTotal}개`;
        document.getElementById('board-list').innerHTML = this.postsHTML(this.boardPosts);
        document.getElementById('board-pages').innerHTML = this.paginationHTML(this.boardTotal, this.boardPage, this.boardPages, 'board');
        this.wirePostClicks();
        this.wirePagination();
      }catch(err){
        if(list) list.innerHTML = this.errorHTML(err.message);
      }
    },

    async reloadInquiryList(){
      const list = document.getElementById('inquiry-list');
      if(list) list.innerHTML = this.loadingHTML('문의글을 불러오는 중입니다.');
      try{
        await this.fetchInquiries();
        document.getElementById('inquiry-count').textContent = `문의 ${this.inquiryTotal}개`;
        document.getElementById('inquiry-list').innerHTML = this.inquiriesHTML(this.inquiries);
        document.getElementById('inquiry-pages').innerHTML = this.paginationHTML(this.inquiryTotal, this.inquiryPage, this.inquiryPages, 'inquiry');
        this.wireInquiryClicks();
        this.wirePagination();
      }catch(err){
        if(list) list.innerHTML = this.errorHTML(err.message);
      }
    },

    async showPost(id=this.activePostId){
      if(!id){ App.go('board'); return; }
      this.activePostId = id;
      this.mount(this.postDetailHTML(null, 'loading'));
      await this.loadMine();
      try{
        const data = await Api.communityPost(id);
        this.activePostId = data.post.id;
        this.mount(this.postDetailHTML(data.post));
      }catch(err){
        this.mount(this.postDetailHTML(null, 'error', err.message));
      }
    },

    async showInquiryPost(id=this.activeInquiryId){
      if(!id){ App.go('inquiry'); return; }
      this.activeInquiryId = id;
      this.mount(this.inquiryDetailHTML(null, 'loading'));
      await this.loadMine();
      try{
        const data = await Api.communityInquiry(id);
        this.activeInquiryId = data.inquiry.id;
        this.mount(this.inquiryDetailHTML(data.inquiry));
      }catch(err){
        this.mount(this.inquiryDetailHTML(null, 'error', err.message));
      }
    },

    async showBoardWrite(id=null){
      if(this.isGuest()){ App.go('login'); return; }
      await this.loadMine();
      if(!id){
        this.mount(this.boardWriteHTML());
        return;
      }

      this.mount(this.boardWriteHTML(null, 'loading'));
      try{
        const data = await Api.communityPost(id);
        this.mount(this.boardWriteHTML(data.post));
      }catch(err){
        this.mount(this.boardWriteHTML(null, 'error', err.message));
      }
    },

    async showInquiryWrite(id=null){
      if(this.isGuest()){ App.go('login'); return; }
      await this.loadMine();
      if(!id){
        this.mount(this.inquiryWriteHTML());
        return;
      }

      this.mount(this.inquiryWriteHTML(null, 'loading'));
      try{
        const data = await Api.communityInquiry(id);
        this.mount(this.inquiryWriteHTML(data.inquiry));
      }catch(err){
        this.mount(this.inquiryWriteHTML(null, 'error', err.message));
      }
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
            this.reloadBoardList();
          }else{
            this.inquiryPage = page;
            this.reloadInquiryList();
          }
        });
      });
    },

    wireTopNav(){
      document.querySelectorAll('[data-community-go]').forEach(btn=>{
        btn.addEventListener('click', ()=>App.go(btn.dataset.communityGo));
      });
    },

    async submitBoardForm(form){
      const payload = {
        category:form.elements.category.value,
        title:form.elements.title.value,
        content:form.elements.content.value,
        referenceUrl:form.elements.referenceUrl.value,
        isNotice:Boolean(form.elements.isNotice?.checked),
        isCommentBlocked:Boolean(form.elements.isCommentBlocked?.checked),
      };
      const id = form.dataset.postId;
      const result = id
        ? await Api.updateCommunityPost(id, payload)
        : await Api.createCommunityPost(payload);
      this.activePostId = result.post.id;
      await this.loadMine();
      await this.showPost(result.post.id);
    },

    async submitInquiryForm(form){
      const payload = {
        category:form.elements.category.value,
        title:form.elements.title.value,
        content:form.elements.content.value,
        isPrivate:Boolean(form.elements.isPrivate.checked),
        emailOnAnswer:Boolean(form.elements.emailOnAnswer.checked),
      };
      const id = form.dataset.inquiryId;
      const result = id
        ? await Api.updateCommunityInquiry(id, payload)
        : await Api.createCommunityInquiry(payload);
      this.activeInquiryId = result.inquiry.id;
      await this.loadMine();
      await this.showInquiryPost(result.inquiry.id);
    },

    async submitComment(type){
      const input = document.getElementById(`${type}-comment-input`);
      const content = input?.value.trim();
      if(!content) return;

      if(type === 'post'){
        await Api.createPostComment(this.activePostId, content);
        await this.showPost(this.activePostId);
      }else{
        await Api.createInquiryComment(this.activeInquiryId, content);
        await this.showInquiryPost(this.activeInquiryId);
      }
    },

    async editComment(commentId){
      const next = window.prompt('댓글을 수정하세요.');
      if(next === null) return;
      if(!next.trim()) return window.alert('댓글 내용을 입력해 주세요.');
      await Api.updateCommunityComment(commentId, next.trim());
      if(App.current === 'post') await this.showPost(this.activePostId);
      else await this.showInquiryPost(this.activeInquiryId);
    },

    async deleteComment(commentId){
      if(!window.confirm('댓글을 삭제할까요?')) return;
      await Api.deleteCommunityComment(commentId);
      if(App.current === 'post') await this.showPost(this.activePostId);
      else await this.showInquiryPost(this.activeInquiryId);
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
      document.getElementById('community-user-card')?.addEventListener('click', ()=>App.go(this.isGuest() ? 'login' : 'chat'));
      document.getElementById('back-board')?.addEventListener('click', ()=>App.go('board'));
      document.getElementById('back-inquiry')?.addEventListener('click', ()=>App.go('inquiry'));

      this.wireTopNav();
      this.wirePostClicks();
      this.wireInquiryClicks();
      this.wirePagination();

      const boardSearch = document.getElementById('board-search');
      if(boardSearch){
        boardSearch.addEventListener('input', ()=>{
          clearTimeout(this.searchTimer);
          this.searchTimer = setTimeout(()=>{
            this.boardQuery = boardSearch.value;
            this.boardPage = 1;
            this.reloadBoardList();
          }, 250);
        });
      }

      const inquirySearch = document.getElementById('inquiry-search');
      if(inquirySearch){
        inquirySearch.addEventListener('input', ()=>{
          clearTimeout(this.searchTimer);
          this.searchTimer = setTimeout(()=>{
            this.inquiryQuery = inquirySearch.value;
            this.inquiryPage = 1;
            this.reloadInquiryList();
          }, 250);
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

      const boardForm = document.getElementById('board-form');
      if(boardForm){
        boardForm.addEventListener('submit', async event=>{
          event.preventDefault();
          try{ await this.submitBoardForm(boardForm); }
          catch(err){ window.alert(err.message || '게시글 저장에 실패했습니다.'); }
        });
      }

      const inquiryForm = document.getElementById('inquiry-form');
      if(inquiryForm){
        inquiryForm.addEventListener('submit', async event=>{
          event.preventDefault();
          try{ await this.submitInquiryForm(inquiryForm); }
          catch(err){ window.alert(err.message || '문의글 저장에 실패했습니다.'); }
        });
      }

      document.getElementById('post-edit')?.addEventListener('click', ()=>this.showBoardWrite(this.activePostId));
      document.getElementById('inquiry-edit')?.addEventListener('click', ()=>this.showInquiryWrite(this.activeInquiryId));
      document.getElementById('post-delete')?.addEventListener('click', async ()=>{
        if(!window.confirm('게시글을 삭제할까요?')) return;
        try{
          await Api.deleteCommunityPost(this.activePostId);
          await this.loadMine();
          App.go('board');
        }catch(err){ window.alert(err.message || '게시글 삭제에 실패했습니다.'); }
      });
      document.getElementById('inquiry-delete')?.addEventListener('click', async ()=>{
        if(!window.confirm('문의글을 삭제할까요?')) return;
        try{
          await Api.deleteCommunityInquiry(this.activeInquiryId);
          await this.loadMine();
          App.go('inquiry');
        }catch(err){ window.alert(err.message || '문의글 삭제에 실패했습니다.'); }
      });

      const postCommentForm = document.getElementById('post-comment-form');
      if(postCommentForm){
        postCommentForm.addEventListener('submit', async event=>{
          event.preventDefault();
          try{ await this.submitComment('post'); }
          catch(err){ window.alert(err.message || '댓글 등록에 실패했습니다.'); }
        });
      }

      const inquiryCommentForm = document.getElementById('inquiry-comment-form');
      if(inquiryCommentForm){
        inquiryCommentForm.addEventListener('submit', async event=>{
          event.preventDefault();
          try{ await this.submitComment('inquiry'); }
          catch(err){ window.alert(err.message || '댓글 등록에 실패했습니다.'); }
        });
      }

      const inquiryStatusSelect = document.getElementById('inquiry-status-select');
      if(inquiryStatusSelect){
        inquiryStatusSelect.addEventListener('change', async event=>{
          try{
            await Api.updateInquiryStatus(event.currentTarget.dataset.inquiryStatusId, event.currentTarget.value);
            await this.showInquiryPost(this.activeInquiryId);
          }catch(err){ window.alert(err.message || '문의 상태 변경에 실패했습니다.'); }
        });
      }

      document.querySelectorAll('[data-comment-edit]').forEach(btn=>{
        btn.addEventListener('click', async ()=>{
          try{ await this.editComment(btn.dataset.commentEdit); }
          catch(err){ window.alert(err.message || '댓글 수정에 실패했습니다.'); }
        });
      });
      document.querySelectorAll('[data-comment-delete]').forEach(btn=>{
        btn.addEventListener('click', async ()=>{
          try{ await this.deleteComment(btn.dataset.commentDelete); }
          catch(err){ window.alert(err.message || '댓글 삭제에 실패했습니다.'); }
        });
      });
    },
  };

  const originalGo = App.go.bind(App);
  App.go = function(view){
    if(['board','inquiry','post','inquiry-post','board-write','inquiry-write'].includes(view)){
      this.current = view;
      if(typeof Chat !== 'undefined') clearTimeout(Chat.idleTimer);
      if(view === 'board') Community.showBoard();
      else if(view === 'inquiry') Community.showInquiry();
      else if(view === 'post') Community.showPost();
      else if(view === 'inquiry-post') Community.showInquiryPost();
      else if(view === 'board-write') Community.showBoardWrite();
      else Community.showInquiryWrite();
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
