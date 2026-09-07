"""Hệ thống AI giả lập người phản biện — giao diện Streamlit.

Chạy:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from core import agents, auth, config, debate, ingest, rag, repository as repo
from core.auth import AuthError, login, register
from core.db import init_db
from core.llm import LLMError
from core.repository import ROLE_AI_REBUTTAL, ROLE_USER_ANSWER, ROLE_USER_REBUTTAL

st.set_page_config(page_title="Learnbuddy AI", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

# --------------------------------------------------------------------- giao diện
# Custom CSS: giữ nguyên toàn bộ logic AI/RAG/CrewAI, chỉ thay lớp trình bày.
# Thiết kế theo hướng EdTech/startup: sạch, hiện đại, tập trung vào phiên phản biện.

st.markdown(
    """
<style>
/* ---------- nền & typography ---------- */
:root {
    --lb-red: #b91c1c;
    --lb-red-dark: #991b1b;
    --lb-red-soft: #fef2f2;
    --lb-ink: #111827;
    --lb-muted: #6b7280;
    --lb-border: #e5e7eb;
    --lb-surface: #ffffff;
    --lb-bg: #f8fafc;
}

.stApp {
    background: var(--lb-bg);
}

[data-testid="stAppViewContainer"] .main {
    background: var(--lb-bg);
}

[data-testid="stHeader"] {
    background: rgba(248, 250, 252, .88);
}

.block-container {
    max-width: 1180px;
    padding-top: 2.2rem;
    padding-bottom: 4rem;
}

h1, h2, h3, h4 {
    color: var(--lb-ink) !important;
    letter-spacing: -0.025em;
}

h1 {
    font-weight: 800 !important;
}

p, li, label, .stCaption {
    color: #374151;
}

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] {
    background: #111827;
    border-right: 0;
}

section[data-testid="stSidebar"] > div {
    background: #111827;
}

section[data-testid="stSidebar"] * {
    color: #f9fafb;
}

section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] small {
    color: #9ca3af !important;
}

section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,.12);
}

section[data-testid="stSidebar"] button {
    border: 1px solid rgba(255,255,255,.10);
    background: rgba(255,255,255,.055);
    color: #f9fafb !important;
    border-radius: 10px;
    min-height: 42px;
    transition: .15s ease;
}

section[data-testid="stSidebar"] button:hover {
    border-color: rgba(255,255,255,.25);
    background: rgba(255,255,255,.11);
}

/* ---------- buttons ---------- */
.stButton > button,
.stFormSubmitButton > button {
    border-radius: 10px;
    min-height: 42px;
    font-weight: 700;
    border: 1px solid var(--lb-border);
    transition: transform .12s ease, box-shadow .12s ease, background .12s ease;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 5px 16px rgba(17,24,39,.08);
}

.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    background: var(--lb-red);
    border-color: var(--lb-red);
    color: white;
}

.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover {
    background: var(--lb-red-dark);
}

/* ---------- inputs ---------- */
[data-baseweb="input"],
[data-baseweb="textarea"],
[data-baseweb="select"] > div {
    border-radius: 10px !important;
}

[data-baseweb="input"]:focus-within,
[data-baseweb="textarea"]:focus-within,
[data-baseweb="select"] > div:focus-within {
    border-color: var(--lb-red) !important;
    box-shadow: 0 0 0 1px var(--lb-red) !important;
}

textarea {
    border-radius: 10px !important;
}

/* ---------- cards / metrics ---------- */
[data-testid="stMetric"] {
    background: var(--lb-surface);
    border: 1px solid var(--lb-border);
    border-radius: 14px;
    padding: 14px 16px;
}

[data-testid="stMetricLabel"] {
    color: var(--lb-muted) !important;
}

[data-testid="stMetricValue"] {
    color: var(--lb-ink) !important;
    font-weight: 800;
}

/* ---------- alerts ---------- */
[data-testid="stAlert"] {
    border-radius: 12px;
    border-width: 1px;
}

/* ---------- chat transcript ---------- */
[data-testid="stChatMessage"] {
    border: 1px solid var(--lb-border);
    border-radius: 14px;
    margin-bottom: 10px;
    padding: 4px 8px;
    background: white;
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    border-left: 4px solid var(--lb-red);
}

/* ---------- tabs ---------- */
button[data-baseweb="tab"] {
    font-weight: 700;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--lb-red) !important;
}

[role="tablist"] {
    gap: 4px;
}

/* ---------- progress ---------- */
[data-testid="stProgressBar"] > div > div {
    background: var(--lb-red);
}

/* ---------- expanders ---------- */
details {
    border: 1px solid var(--lb-border) !important;
    border-radius: 12px !important;
    background: white;
}

details summary {
    font-weight: 700;
}

/* ---------- divider ---------- */
hr {
    border-color: var(--lb-border) !important;
}

/* ---------- dataframes ---------- */
[data-testid="stDataFrame"] {
    border: 1px solid var(--lb-border);
    border-radius: 12px;
    overflow: hidden;
}

/* ---------- utility classes rendered through markdown ---------- */
.lb-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 18px;
}

.lb-mark {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    display: grid;
    place-items: center;
    background: var(--lb-red);
    color: white;
    font-weight: 900;
    font-size: 19px;
    box-shadow: 0 8px 22px rgba(185,28,28,.20);
}

.lb-brand-name {
    font-size: 20px;
    font-weight: 850;
    color: var(--lb-ink);
    line-height: 1;
}

.lb-brand-sub {
    color: var(--lb-muted);
    font-size: 11px;
    margin-top: 4px;
}

.lb-hero {
    background: linear-gradient(135deg, #ffffff 0%, #fff7f7 100%);
    border: 1px solid #fee2e2;
    border-radius: 20px;
    padding: 28px 30px;
    margin-bottom: 24px;
    box-shadow: 0 12px 35px rgba(17,24,39,.05);
}

.lb-eyebrow {
    color: var(--lb-red);
    font-size: 12px;
    font-weight: 800;
    letter-spacing: .10em;
    text-transform: uppercase;
    margin-bottom: 7px;
}

.lb-hero-title {
    color: var(--lb-ink);
    font-size: 32px;
    font-weight: 850;
    line-height: 1.08;
    letter-spacing: -.04em;
}

.lb-hero-desc {
    color: #4b5563;
    font-size: 15px;
    margin-top: 8px;
    max-width: 760px;
}

.lb-section {
    color: var(--lb-ink);
    font-size: 18px;
    font-weight: 800;
    margin: 18px 0 10px;
}

.lb-chip {
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    background: var(--lb-red-soft);
    color: var(--lb-red-dark);
    font-size: 12px;
    font-weight: 750;
    margin-right: 6px;
    margin-bottom: 6px;
}

.lb-voice-card {
    border: 1px dashed #fca5a5;
    background: #fffafa;
    border-radius: 14px;
    padding: 14px 16px;
    margin-top: 10px;
}

.lb-voice-title {
    font-weight: 800;
    color: var(--lb-ink);
}

.lb-voice-desc {
    color: var(--lb-muted);
    font-size: 13px;
    margin-top: 3px;
}

/* ---------- hide Streamlit chrome ---------- */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
</style>
""",
    unsafe_allow_html=True,
)

MIN_ANSWER_CHARS = 30


# --------------------------------------------------------------------- khởi động


@st.cache_resource(show_spinner="Đang khởi tạo cơ sở dữ liệu và nạp tài liệu...")
def bootstrap() -> dict:
    init_db()
    auth.purge_expired_tokens()
    result = ingest.sync_all()

    if config.OPENAI_API_KEY:
        if rag.pending_embedding_count():
            try:
                result["embedded"] = rag.build_embeddings()
            except LLMError:
                result["embedded"] = 0
        # Đặt nhãn chủ đề cho các chương có tiêu đề chung chung ("Pháp luật 1"...)
        for chapter in repo.chapters_missing_topic():
            topic = debate.suggest_chapter_topic(chapter)
            if topic:
                repo.set_chapter_topic(chapter["id"], topic)
    return result


def question_block(text: str) -> str:
    """Khối trích dẫn cho câu hỏi.

    Câu trắc nghiệm được lưu nhiều dòng (đề bài + các phương án), nên phải thêm
    dấu trích dẫn cho từng dòng thay vì chỉ dòng đầu.
    """
    return "\n".join(f"> {line}" for line in text.strip().split("\n"))


def chapter_label(chapter: dict) -> str:
    """Nhãn hiển thị của chương, kèm chủ đề nếu tiêu đề gốc quá chung chung."""
    title = chapter["title"]
    topic = (chapter.get("topic") or "").strip()
    return f"{title} · {topic}" if topic and topic.lower() not in title.lower() else title


def init_state() -> None:
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("token", None)
    st.session_state.setdefault("page", "practice")
    st.session_state.setdefault("debate", None)
    st.session_state.setdefault("view_session", None)


# ------------------------------------------------------------------- giữ phiên
#
# st.session_state mất khi tải lại trang, nên token phiên được gửi kèm trên URL
# (?sid=...) và đối chiếu với bảng auth_tokens trong SQLite. Token là chuỗi ngẫu
# nhiên, tự hết hạn sau SESSION_TTL_DAYS ngày và thu hồi được khi đăng xuất.

SESSION_PARAM = "sid"


def start_session(user: dict) -> None:
    token = auth.create_token(user["id"])
    st.session_state.user = user
    st.session_state.token = token
    st.query_params[SESSION_PARAM] = token


def restore_session() -> None:
    """Khôi phục đăng nhập từ token trên URL sau khi tải lại trang."""
    if st.session_state.user is not None:
        return
    token = st.query_params.get(SESSION_PARAM)
    if isinstance(token, list):  # URL lặp tham số, hoặc môi trường kiểm thử
        token = token[0] if token else None
    if not token:
        return
    user = auth.user_from_token(token)
    if user:
        st.session_state.user = user
        st.session_state.token = token
    else:  # token sai hoặc đã hết hạn
        del st.query_params[SESSION_PARAM]


def end_session() -> None:
    auth.revoke_token(st.session_state.get("token") or "")
    st.session_state.user = None
    st.session_state.token = None
    st.session_state.debate = None
    st.session_state.view_session = None
    if SESSION_PARAM in st.query_params:
        del st.query_params[SESSION_PARAM]


# ------------------------------------------------------------------- xác thực UI


def render_auth() -> None:
    st.markdown(
        """
        <div class="lb-brand">
            <div class="lb-mark">L</div>
            <div>
                <div class="lb-brand-name">Learnbuddy AI</div>
                <div class="lb-brand-sub">AI GIẢ LẬP NGƯỜI PHẢN BIỆN</div>
            </div>
        </div>
        <div class="lb-hero">
            <div class="lb-eyebrow">AI thought partner · EdTech</div>
            <div class="lb-hero-title">Học để phản biện.<br>Không chỉ học để nhớ.</div>
            <div class="lb-hero-desc">Luyện vấn đáp, bảo vệ đồ án và tranh biện với AI theo phương pháp Socratic — mọi lúc, không phán xét.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.title("🎓 Hệ thống luyện phản biện học thuật")
    st.caption(
        "Trả lời câu hỏi ôn tập, tranh biện qua lại với AI trong "
        f"{config.MAX_ROUNDS} vòng, rồi nhận nhận xét từ trọng tài AI."
    )

    left, right = st.columns([1, 1], gap="large")
    with left:
        tab_login, tab_register = st.tabs(["Đăng nhập", "Đăng ký"])

        with tab_login:
            with st.form("form_login"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Mật khẩu", type="password", key="login_pwd")
                submitted = st.form_submit_button("Đăng nhập", type="primary", width="stretch")
            if submitted:
                try:
                    start_session(login(email, password))
                    st.rerun()
                except AuthError as exc:
                    st.error(str(exc))

        with tab_register:
            with st.form("form_register"):
                full_name = st.text_input("Tên sinh viên")
                email_r = st.text_input("Email", key="reg_email")
                pwd = st.text_input("Mật khẩu", type="password", key="reg_pwd")
                pwd2 = st.text_input("Nhập lại mật khẩu", type="password", key="reg_pwd2")
                submitted_r = st.form_submit_button("Đăng ký", type="primary", width="stretch")
            if submitted_r:
                try:
                    start_session(register(full_name, email_r, pwd, pwd2))
                    st.success("Đăng ký thành công, tài khoản đã được kích hoạt.")
                    st.rerun()
                except AuthError as exc:
                    st.error(str(exc))

    with right:
        st.subheader("Cách hoạt động")
        st.markdown(
            f"""
1. Chọn **môn học → chương → mức độ** (dễ / trung bình / khó).
2. Hệ thống dùng **RAG** bốc ngẫu nhiên nội dung trong chương và **LLM** ra một câu hỏi.
3. Bạn trả lời bằng kiến thức của mình.
4. AI đánh giá và **phản biện**. Bạn phản biện lại. Lặp **{config.MAX_ROUNDS} vòng**.
5. Một **trọng tài AI** độc lập chấm điểm, chỉ ra chỗ hổng và gợi ý cải thiện.
            """
        )
        if config.offline_mode():
            st.warning(
                "Đang ở **chế độ ngoại tuyến** (chưa có `OPENAI_API_KEY` trong file `.env`). "
                "Luồng nghiệp vụ vẫn chạy nhưng nội dung phản biện chỉ là mẫu dựng sẵn."
            )


# ---------------------------------------------------------------------- sidebar


def render_sidebar(stats: dict) -> None:
    user = st.session_state.user
    with st.sidebar:
        st.markdown(f"### 👤 {user['full_name']}")
        st.caption(user["email"])
        st.divider()

        if st.button("🥊 Luyện phản biện", width="stretch"):
            st.session_state.page = "practice"
            # Phiên đã chấm xong thì mở màn hình chọn đề mới; phiên đang dở thì giữ nguyên
            current = st.session_state.debate
            if current and current.get("stage") == "done":
                st.session_state.debate = None
            st.rerun()
        if st.button("📜 Lịch sử của tôi", width="stretch"):
            st.session_state.page = "history"
            st.session_state.view_session = None
            st.rerun()
        if config.is_admin(user["email"]):
            if st.button("📁 Tài liệu nguồn", width="stretch"):
                st.session_state.page = "documents"
                st.rerun()
        if st.button("🚪 Đăng xuất", width="stretch"):
            end_session()
            st.rerun()

        st.divider()
        me = repo.user_stats(user["id"])
        col_a, col_b = st.columns(2)
        col_a.metric("Phiên đã tạo", me["total"])
        col_b.metric("Đã hoàn tất", me["finished"])
        if me["avg_score"] is not None:
            st.metric("Điểm trung bình", f"{me['avg_score']:.1f}/10")

        st.divider()
        st.caption(
            f"Dữ liệu: {stats['subjects']} môn · {stats['chapters']} chương · "
            f"{stats['chunks']} đoạn ngữ liệu · {stats['questions']} câu hỏi ngân hàng"
        )
        pending = rag.pending_embedding_count()
        if config.offline_mode():
            st.warning("Chế độ ngoại tuyến — chưa cấu hình `OPENAI_API_KEY`.")
            st.caption("Truy hồi RAG đang dùng cơ chế từ vựng thay cho vector.")
        else:
            st.caption(
                f"Model: `{config.CHAT_MODEL}` · điều phối: `{agents.active_backend()}`"
            )
            if pending:
                st.info(f"Còn {pending} đoạn chưa có vector.")
                if st.button("⚙️ Xây chỉ mục vector", width="stretch"):
                    with st.spinner("Đang tạo embedding..."):
                        try:
                            n = rag.build_embeddings()
                            st.success(f"Đã xử lý {n} đoạn.")
                        except LLMError as exc:
                            st.error(str(exc))
            else:
                st.caption("✅ Chỉ mục vector sẵn sàng.")


# -------------------------------------------------------------- màn hình luyện tập


def render_setup() -> None:
    st.markdown(
        """
        <div class="lb-hero">
            <div class="lb-eyebrow">Learnbuddy AI · Practice room</div>
            <div class="lb-hero-title">Sẵn sàng để AI chất vấn?</div>
            <div class="lb-hero-desc">Chọn môn học, chương và mức độ. Learnbuddy sẽ tạo một phiên phản biện nhiều vòng và chỉ ra điểm mạnh, điểm yếu trong lập luận của bạn.</div>
            <div style="margin-top:12px">
                <span class="lb-chip">Socratic questioning</span>
                <span class="lb-chip">Feedback cá nhân hóa</span>
                <span class="lb-chip">24/7</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.title("🥊 Bắt đầu một phiên phản biện")

    subjects = repo.list_subjects()
    if not subjects:
        st.error("Chưa có ngữ liệu. Kiểm tra thư mục `data/corpus`.")
        return

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        subject = st.selectbox(
            "Môn học", subjects, format_func=lambda s: s["name"], key="sel_subject"
        )
    chapters = repo.list_chapters(subject["id"])
    with col2:
        chapter = st.selectbox(
            "Chương", chapters, format_func=chapter_label, key="sel_chapter"
        )
    with col3:
        difficulty = st.selectbox(
            "Mức độ",
            list(config.DIFFICULTIES.keys()),
            format_func=lambda d: config.DIFFICULTIES[d],
            index=1,
            key="sel_difficulty",
        )

    if not chapter:
        st.error("Môn học này chưa có chương nào.")
        return

    availability = repo.difficulty_availability(chapter["id"])
    bank_total = sum(availability.values())

    info_bits = []
    if bank_total:
        detail = ", ".join(
            f"{config.DIFFICULTIES[k].lower()}: {availability.get(k, 0)}"
            for k in config.DIFFICULTIES
            if availability.get(k)
        )
        info_bits.append(f"📕 Ngân hàng đề: {bank_total} câu ({detail})")
    if chapter["chunk_count"]:
        info_bits.append(f"📚 Ngữ liệu tham khảo: {chapter['chunk_count']} đoạn")
    st.caption(" · ".join(info_bits) if info_bits else "Chương này chưa có dữ liệu.")

    st.info(config.DIFFICULTY_SPEC[difficulty])

    if bank_total and not availability.get(difficulty):
        st.warning(
            f"Ngân hàng đề của chương này chưa có câu mức **{config.DIFFICULTIES[difficulty]}**. "
            "Hệ thống sẽ để AI tự ra một câu hỏi mới trong phạm vi chương."
        )
    if not chapter["chunk_count"] and bank_total:
        st.warning(
            "Chương này chỉ có ngân hàng câu hỏi, chưa có tài liệu giải thích để truy hồi. "
            "AI sẽ phản biện bằng kiến thức chuyên môn chung và không viện dẫn số hiệu điều luật. "
            "Muốn phản biện bám giáo trình, hãy bổ sung tài liệu vào `data/corpus`."
        )

    if st.button("🎲 Lấy câu hỏi ngẫu nhiên", type="primary"):
        if not chapter["chunk_count"] and not bank_total:
            st.error("Chương này chưa có dữ liệu ôn tập.")
            return
        user = st.session_state.user
        full_chapter = repo.get_chapter(chapter["id"])
        with st.spinner("Đang chọn câu hỏi và chuẩn bị ngữ cảnh..."):
            try:
                generated = debate.generate_question(
                    full_chapter,
                    difficulty,
                    avoid=repo.recent_questions(user["id"], chapter["id"]),
                )
            except LLMError as exc:
                st.error(str(exc))
                return
            session_id = repo.create_session(
                user["id"],
                chapter["id"],
                difficulty,
                generated["question"],
                generated["context"],
            )
        st.session_state.debate = {
            "session_id": session_id,
            "chapter": full_chapter,
            "difficulty": difficulty,
            "question": generated["question"],
            "source": generated["source"],
            "mode": generated["mode"],
            "choice": None,
            "round": 0,
            "stage": "answer",
        }
        st.rerun()


def _render_transcript(turns: list[dict]) -> None:
    for t in turns:
        if t["role"] == ROLE_AI_REBUTTAL:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(f"**Người phản biện — vòng {t['round_no']}**")
                st.markdown(t["content"])
        else:
            label = (
                "Câu trả lời của bạn"
                if t["role"] == ROLE_USER_ANSWER
                else f"Bạn phản biện — vòng {t['round_no']}"
            )
            with st.chat_message("user", avatar="🧑‍🎓"):
                st.markdown(f"**{label}**")
                st.markdown(t["content"])


def _advance(d: dict) -> None:
    """Sinh lượt tiếp theo của hệ thống, hoặc gọi trọng tài nếu đã đủ vòng."""
    turns = repo.get_turns(d["session_id"])
    next_round = d["round"] + 1

    if next_round <= config.MAX_ROUNDS:
        with st.spinner(f"AI đang phản biện (vòng {next_round}/{config.MAX_ROUNDS})..."):
            result = debate.generate_rebuttal(
                d["chapter"], d["difficulty"], d["question"], turns, next_round
            )
        repo.add_turn(d["session_id"], next_round, ROLE_AI_REBUTTAL, result["content"])
        d["round"] = next_round
        d["stage"] = "rebut"
    else:
        _run_judge(d)


def _run_judge(d: dict) -> None:
    turns = repo.get_turns(d["session_id"])
    with st.spinner("Trọng tài AI đang chấm phiên tranh biện..."):
        verdict = debate.judge(d["chapter"], d["difficulty"], d["question"], turns)
    repo.save_verdict(d["session_id"], verdict)
    repo.close_session(d["session_id"])
    d["stage"] = "done"


def _render_verdict(verdict: dict) -> None:
    st.subheader("⚖️ Kết luận của trọng tài")
    if verdict.get("offline"):
        st.warning("Kết quả mẫu ở chế độ ngoại tuyến.")

    winner_label = {
        "sinh_vien": "🏆 Sinh viên thuyết phục hơn",
        "ai": "🤖 Người phản biện thuyết phục hơn",
        "hoa": "🤝 Hai bên ngang nhau",
    }[verdict["ben_thuyet_phuc_hon"]]

    head_left, head_right = st.columns([1, 2])
    with head_left:
        st.metric("Điểm tổng", f"{verdict['diem_tong']:.1f}/10")
        st.markdown(f"**{winner_label}**")
    with head_right:
        labels = {
            "do_chinh_xac": "Độ chính xác",
            "do_day_du": "Độ đầy đủ",
            "chat_luong_lap_luan": "Chất lượng lập luận",
            "phan_hoi_phan_bien": "Phản hồi phản biện",
        }
        for key, label in labels.items():
            score = verdict["diem"][key]
            st.progress(score / 10, text=f"{label}: {score:.1f}/10")

    if verdict.get("nhan_xet_chung"):
        st.info(verdict["nhan_xet_chung"])

    col_a, col_b = st.columns(2)
    with col_a:
        if verdict["diem_manh"]:
            st.markdown("**✅ Điểm mạnh**")
            for item in verdict["diem_manh"]:
                st.markdown(f"- {item}")
        if verdict["goi_y_cai_thien"]:
            st.markdown("**🚀 Gợi ý cải thiện**")
            for item in verdict["goi_y_cai_thien"]:
                st.markdown(f"- {item}")
    with col_b:
        if verdict["diem_yeu"]:
            st.markdown("**⚠️ Điểm yếu**")
            for item in verdict["diem_yeu"]:
                st.markdown(f"- {item}")
        if verdict["kien_thuc_con_thieu"]:
            st.markdown("**📚 Kiến thức cần ôn lại**")
            for item in verdict["kien_thuc_con_thieu"]:
                st.markdown(f"- {item}")

    if verdict.get("dap_an_tham_khao"):
        with st.expander("📖 Đáp án tham khảo (dựa trên ngữ liệu)"):
            st.markdown(verdict["dap_an_tham_khao"])


def render_debate() -> None:
    d = st.session_state.debate
    chapter = d["chapter"]

    st.markdown(
        f"""
        <div class="lb-hero">
            <div class="lb-eyebrow">LIVE DEBATE · AI CRITIC</div>
            <div class="lb-hero-title">Đừng vội trả lời. Hãy bảo vệ lập luận.</div>
            <div class="lb-hero-desc">{chapter['subject_name']} · {chapter['title']} · Mức độ: {config.DIFFICULTIES[d['difficulty']]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.title("🥊 Phiên phản biện")
    st.caption(
        f"{chapter['subject_name']} · {chapter['title']} · "
        f"Mức độ: {config.DIFFICULTIES[d['difficulty']]} · Phiên #{d['session_id']}"
    )

    if d["stage"] != "done":
        done_rounds = d["round"] if d["stage"] == "answer" else d["round"] - 1
        st.progress(
            min(1.0, max(0.0, done_rounds / config.MAX_ROUNDS)),
            text=f"Tiến độ: vòng {min(d['round'] + 1, config.MAX_ROUNDS)}/{config.MAX_ROUNDS}"
            if d["stage"] != "answer"
            else "Tiến độ: chưa bắt đầu tranh biện",
        )

    stem, choices = debate.parse_choices(d["question"])

    st.markdown("#### ❓ Câu hỏi")
    st.markdown(question_block(stem))
    st.caption(
        ("📕 Lấy từ ngân hàng đề của giảng viên" if d.get("source") == "bank"
         else "✨ AI sinh mới trong phạm vi chương")
        + (" · 📚 phản biện bám ngữ liệu môn học" if d.get("mode") == debate.MODE_CORPUS
           else " · ⚠️ chương chưa có tài liệu tham khảo, AI phản biện bằng kiến thức chung")
    )
    st.divider()

    _render_transcript(repo.get_turns(d["session_id"]))

    if d["stage"] == "done":
        verdict = repo.get_verdict(d["session_id"])
        if verdict:
            st.divider()
            _render_verdict(verdict)
        st.divider()
        col1, col2 = st.columns(2)
        if col1.button("🔁 Luyện câu khác", type="primary", width="stretch"):
            st.session_state.debate = None
            st.rerun()
        if col2.button("📜 Xem lịch sử", width="stretch"):
            st.session_state.debate = None
            st.session_state.page = "history"
            st.rerun()
        return

    # --- khu vực nhập của sinh viên
    if d["stage"] == "answer":
        placeholder = (
            "Giải thích vì sao bạn chọn đáp án đó..."
            if choices
            else "Nhập câu trả lời của bạn..."
        )
    else:
        placeholder = f"Phản biện lại lập luận của AI (vòng {d['round']}/{config.MAX_ROUNDS})..."

    labels = [f"{letter}. {text}" for letter, text in choices]
    previous = d.get("choice")

    st.markdown(
        """
        <div class="lb-voice-card">
            <div class="lb-voice-title">🎙️ Voice Mode · mô phỏng vấn đáp</div>
            <div class="lb-voice-desc">Giao diện đã sẵn sàng cho luồng nói → chuyển giọng nói thành văn bản → AI phản biện. Có thể kết nối Speech-to-Text/TTS ở bước tích hợp voice.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("form_turn", clear_on_submit=True):
        picked = None
        if choices:
            picked = st.radio(
                "Chọn đáp án bạn cho là đúng"
                + ("" if d["stage"] == "answer" else " (có thể đổi sau khi nghe phản biện)"),
                labels,
                index=labels.index(previous) if previous in labels else None,
                key=f"choice_{d['session_id']}_{d['round']}_{d['stage']}",
            )
        text = st.text_area(placeholder, height=180, label_visibility="collapsed",
                            placeholder=placeholder)
        col_send, col_stop = st.columns([3, 1])
        send = col_send.form_submit_button("Gửi", type="primary", width="stretch")
        stop = col_stop.form_submit_button("Kết thúc sớm & chấm", width="stretch")

    if send:
        explanation = (text or "").strip()
        if choices and not picked:
            st.warning("Hãy chọn một đáp án trước khi gửi.")
            return
        if len(explanation) < MIN_ANSWER_CHARS:
            st.warning(
                "Hãy giải thích dài hơn "
                f"(tối thiểu {MIN_ANSWER_CHARS} ký tự) — hệ thống phản biện vào lập "
                "luận chứ không chỉ chấm đúng/sai."
                if choices
                else f"Hãy trình bày dài hơn (tối thiểu {MIN_ANSWER_CHARS} ký tự)."
            )
            return

        content = explanation
        if picked:
            changed = previous and picked != previous
            content = (
                f"**Đáp án chọn: {picked}**"
                + (f" _(đổi từ {previous.split('.')[0]})_" if changed else "")
                + f"\n\n{explanation}"
            )
            d["choice"] = picked

        role = ROLE_USER_ANSWER if d["stage"] == "answer" else ROLE_USER_REBUTTAL
        repo.add_turn(d["session_id"], d["round"], role, content)
        try:
            _advance(d)
        except LLMError as exc:
            st.error(str(exc))
            return
        st.rerun()

    if stop:
        turns = repo.get_turns(d["session_id"])
        if not turns:
            st.warning("Bạn cần trả lời ít nhất một lượt trước khi chấm điểm.")
            return
        try:
            _run_judge(d)
        except LLMError as exc:
            st.error(str(exc))
            return
        st.rerun()

    st.caption(
        "💡 Mẹo: chọn đáp án rồi giải thích vì sao các phương án còn lại sai — "
        "hệ thống chấm phần lập luận, không chỉ chấm đúng/sai."
        if choices
        else "💡 Mẹo: nêu rõ lập trường, dẫn khái niệm trong giáo trình và chỉ ra chỗ "
        "lập luận của AI chưa vững."
    )


# ----------------------------------------------------------- tài liệu nguồn


_STATUS_ICON = {
    "đã nạp": "✅",
    "file mới, chưa nạp": "🆕",
    "đã sửa, cần nạp lại": "✏️",
    "đã xoá khỏi input": "🗑️",
}


def render_documents() -> None:
    # Chặn ngay cả khi vào thẳng bằng trạng thái phiên, không chỉ ẩn nút ở thanh bên
    if not config.is_admin(st.session_state.user["email"]):
        st.error("Trang này chỉ dành cho quản trị viên.")
        if st.button("← Về màn hình luyện tập"):
            st.session_state.page = "practice"
            st.rerun()
        return

    st.title("📁 Tài liệu nguồn")
    st.caption(
        "Mọi file `.docx` (ngân hàng câu hỏi) và `.pdf` (giáo trình) trong thư mục "
        "`input/` đều được ghi vết theo mã băm nội dung. Thêm file mới hoặc sửa file "
        "cũ rồi bấm quét lại — hệ thống chỉ xử lý phần thay đổi."
    )

    files = ingest.tracked_files()
    pending_files = [f for f in files if f["status"] != "đã nạp"]

    if pending_files:
        st.warning(
            "Có "
            + ", ".join(
                f"**{len([f for f in pending_files if f['status'] == s])}** {s}"
                for s in {f["status"] for f in pending_files}
            )
            + ". Bấm *Quét lại thư mục input* để cập nhật."
        )
    else:
        st.success("Mọi tài liệu đều đã được nạp và còn khớp với nội dung trên đĩa.")

    col1, col2 = st.columns([1, 1])
    if col1.button("🔄 Quét lại thư mục input", type="primary", width="stretch"):
        with st.spinner("Đang đọc tài liệu và cập nhật ngữ liệu..."):
            result = ingest.sync_all()
            embedded = 0
            if not config.offline_mode():
                try:
                    embedded = rag.build_embeddings()
                except LLMError as exc:
                    st.error(str(exc))
        bootstrap.clear()
        st.success(
            f"Xong: {result['subjects']} môn · {result['chapters']} chương · "
            f"{result['questions']} câu hỏi · {result['chunks']} đoạn"
            + (f" · {embedded} vector mới" if embedded else "")
        )
        st.rerun()

    if col2.button("♻️ Nạp lại toàn bộ (kể cả file không đổi)", width="stretch"):
        with st.spinner("Đang nạp lại toàn bộ tài liệu..."):
            ingest.sync_all(force_docx=True, force_pdf=True)
            if not config.offline_mode():
                try:
                    rag.build_embeddings()
                except LLMError as exc:
                    st.error(str(exc))
        bootstrap.clear()
        st.rerun()

    st.divider()

    if not files:
        st.info("Thư mục `input/` chưa có tài liệu nào.")
        return

    st.dataframe(
        [
            {
                "": _STATUS_ICON.get(f["status"], "•"),
                "Tài liệu": f["name"],
                "Loại": f["kind"] or "",
                "Trạng thái": f["status"],
                "Đã nạp được": f["summary"] or "—",
                "Kích thước": f"{(f['size_bytes'] or 0) / 1024:,.0f} KB",
                "Cập nhật": (f["updated_at"] or "—")[:16],
            }
            for f in files
        ],
        width="stretch",
        hide_index=True,
    )

    st.divider()
    st.markdown("#### Các tác tử đang chạy")
    st.caption(
        f"Bộ điều phối: **{agents.active_backend()}** — đổi bằng `AGENT_FRAMEWORK` trong "
        "`.env` (`native` gọi thẳng OpenAI, `crewai` dựng Agent/Task/Crew). "
        "Mỗi vai gán được model riêng qua `QUESTION_MODEL` / `DEBATER_MODEL` / `JUDGE_MODEL`."
    )
    st.dataframe(
        [
            {
                "Tác tử": a["name"],
                "Vai trò": a["role"],
                "Mục tiêu": a["goal"],
                "Model": a["model"],
                "Trả JSON": a["json"],
            }
            for a in agents.describe()
        ],
        width="stretch",
        hide_index=True,
    )

    st.divider()
    st.markdown("#### Học liệu đang có")
    for subject in repo.list_subjects():
        chapters = repo.list_chapters(subject["id"])
        questions = sum(c["question_count"] for c in chapters)
        chunks = sum(c["chunk_count"] for c in chapters)
        with st.expander(
            f"{subject['name']} — {len(chapters)} chương · {questions} câu hỏi · "
            f"{chunks} đoạn ngữ liệu"
        ):
            for chapter in chapters:
                bits = []
                availability = repo.difficulty_availability(chapter["id"])
                if availability:
                    bits.append(
                        "đề: "
                        + ", ".join(
                            f"{config.DIFFICULTIES[k].lower()} {v}"
                            for k, v in availability.items()
                            if k in config.DIFFICULTIES
                        )
                    )
                if chapter["chunk_count"]:
                    bits.append(f"{chapter['chunk_count']} đoạn")
                st.markdown(
                    f"- **{chapter_label(chapter)}** — "
                    + (" · ".join(bits) if bits else "_chưa có dữ liệu_")
                )


# --------------------------------------------------------------------- lịch sử


def render_history() -> None:
    user = st.session_state.user

    if st.session_state.view_session:
        _render_history_detail(st.session_state.view_session)
        return

    st.title("📜 Lịch sử luyện tập")
    rows = repo.history(user["id"])
    if not rows:
        st.info("Bạn chưa có phiên nào. Hãy bắt đầu ở mục *Luyện phản biện*.")
        return

    stats = repo.user_stats(user["id"])
    if stats["by_subject"]:
        st.markdown("#### Theo môn học")
        cols = st.columns(min(4, len(stats["by_subject"])))
        for col, item in zip(cols, stats["by_subject"]):
            avg = f"{item['avg_score']:.1f}" if item["avg_score"] is not None else "—"
            col.metric(item["subject_name"], f"{avg}/10", f"{item['n']} phiên")
        st.divider()

    status_label = {"open": "⏳ Đang dở", "done": "✅ Hoàn tất", "abandoned": "✖️ Bỏ dở"}
    for row in rows:
        score = f"{row['total_score']:.1f}/10" if row["total_score"] is not None else "chưa chấm"
        title = (
            f"#{row['id']} · {row['subject_name']} — {row['chapter_title']} · "
            f"{config.DIFFICULTIES.get(row['difficulty'], row['difficulty'])} · "
            f"{status_label.get(row['status'], row['status'])} · {score}"
        )
        with st.expander(title):
            st.markdown("**Câu hỏi:**")
            st.markdown(question_block(row["question"]))
            st.caption(f"Tạo lúc {row['created_at']}")
            if st.button("Xem chi tiết", key=f"detail_{row['id']}"):
                st.session_state.view_session = row["id"]
                st.rerun()


def _render_history_detail(session_id: int) -> None:
    session = repo.get_session(session_id)
    if not session or session["user_id"] != st.session_state.user["id"]:
        st.error("Không tìm thấy phiên này.")
        st.session_state.view_session = None
        return

    if st.button("← Quay lại danh sách"):
        st.session_state.view_session = None
        st.rerun()

    st.title(f"Phiên #{session_id}")
    st.caption(
        f"{session['subject_name']} · {session['chapter_title']} · "
        f"{config.DIFFICULTIES.get(session['difficulty'], session['difficulty'])} · "
        f"{session['created_at']}"
    )
    st.markdown("#### ❓ Câu hỏi")
    st.markdown(question_block(session["question"]))
    st.divider()

    _render_transcript(repo.get_turns(session_id))

    verdict = repo.get_verdict(session_id)
    if verdict:
        st.divider()
        _render_verdict(verdict)
    elif session["status"] == "open":
        st.info("Phiên này chưa hoàn tất nên chưa có kết luận của trọng tài.")

    with st.expander("🔎 Ngữ liệu đã dùng để ra đề"):
        st.text(session["context"] or "(không có)")


# ------------------------------------------------------------------------- main


def main() -> None:
    init_state()
    bootstrap()
    restore_session()

    if st.session_state.user is None:
        render_auth()
        return

    render_sidebar(rag.stats())

    if st.session_state.page == "documents":
        render_documents()
    elif st.session_state.page == "history":
        render_history()
    elif st.session_state.debate is None:
        render_setup()
    else:
        render_debate()


main()
