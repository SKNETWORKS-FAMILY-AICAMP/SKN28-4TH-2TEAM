/* ============================================================
   Mascot controller — reactive hero companion
   ============================================================ */
const MASCOT_IMG = {
  idle:    asset('images/mascot/nubzuki_idle.png'),
  thinking:asset('images/mascot/nubzuki_thinking.png'),
  done:    asset('images/mascot/nubzuki_done.png'),
  source:  asset('images/mascot/nubzuki_source.png'),
  warning: asset('images/mascot/nubzuki_warning.png'),
};
const MASCOT_COPY = {
  idle:    { line:'무엇이든 물어보세요. 학사 정보는 제가 도와드릴게요!', chip:'대기 중', tone:'var(--nub-soft)', fg:'var(--nub-deep)' },
  thinking:{ line:'음… 자료를 찾아보고 있어요. 잠시만요!', chip:'생각 중', tone:'var(--amber-soft)', fg:'#9a6212' },
  source:  { line:'관련 문서를 찾았어요! 출처도 함께 보여드릴게요.', chip:'출처 확인', tone:'var(--mint-soft)', fg:'#0c7a60' },
  done:    { line:'답변을 정리했어요. 도움이 되었으면 좋겠어요! 🙌', chip:'완료', tone:'var(--mint-soft)', fg:'#0c7a60' },
  warning: { line:'앗, 그건 아직 제가 잘 모르는 내용이에요. 😥', chip:'확인 필요', tone:'var(--danger-soft)', fg:'#c23' },
};

const Mascot = {
  el:null, img:null, line:null, chip:null,
  size:1, // tweakable scale

  panelHTML(){
    return `
    <aside class="mascot-panel mascot" data-state="idle" id="mascot">
      <div class="mascot-sky"><i></i><i></i><i></i><i></i></div>
      <div class="mascot-stage">
        <div class="mascot-aura"></div>
        <div class="mascot-disc"></div>
        <div class="mascot-fx">
          <div class="think"><b></b><b></b><b></b></div>
          <span class="spark s1"></span><span class="spark s2"></span><span class="spark s3"></span>
        </div>
        <img class="mascot-img" id="mascot-img" src="${MASCOT_IMG.idle}" alt="넙죽이">
      </div>
      <div class="mascot-speech">
        <div class="mascot-name">넙죽이</div>
        <div class="mascot-statuschip" id="mascot-chip"><span class="dot"></span><span id="mascot-chiptxt">대기 중</span></div>
        <div class="mascot-line" id="mascot-line">${MASCOT_COPY.idle.line}</div>
      </div>
      <div class="mascot-foot">
        <div class="tit">${svg('sparkle')} 넙죽이의 팁</div>
        <p id="mascot-tip">질문에 <b>학과 이름</b>을 함께 적으면 더 정확한 답을 찾을 수 있어요.</p>
      </div>
    </aside>`;
  },

  mount(container){
    container.insertAdjacentHTML('beforeend', this.panelHTML());
    this.el = document.getElementById('mascot');
    this.img = document.getElementById('mascot-img');
    this.line = document.getElementById('mascot-line');
    this.chip = document.getElementById('mascot-chip');
    this.chiptxt = document.getElementById('mascot-chiptxt');
    this.applySize();
  },

  applySize(){
    if(!this.img) return;
    this.img.style.width = (190 * this.size) + 'px';
  },
  setSize(s){ this.size = s; this.applySize(); },

  set(state, customLine){
    if(!this.el) return;
    const c = MASCOT_COPY[state] || MASCOT_COPY.idle;
    // swap image (retrigger animation)
    this.el.setAttribute('data-state', state);
    if(this.img && MASCOT_IMG[state]){
      this.img.style.opacity = '0';
      setTimeout(()=>{ this.img.src = MASCOT_IMG[state]; this.img.style.opacity = '1'; }, 130);
    }
    this.line.textContent = customLine || c.line;
    this.chiptxt.textContent = c.chip;
    this.chip.style.background = c.tone;
    this.chip.style.color = c.fg;
  },
};
