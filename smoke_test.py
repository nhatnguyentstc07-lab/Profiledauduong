"""Kiểm thử nhanh toàn bộ luồng nghiệp vụ, không cần mở giao diện.

Chạy: python smoke_test.py
Nếu chưa cấu hình OPENAI_API_KEY, kịch bản chạy ở chế độ ngoại tuyến.
"""

from __future__ import annotations

import re
import sys
import uuid

# Console Windows mặc định cp1252 -> ép UTF-8 để in được tiếng Việt
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from core import agents, config, debate, ingest, rag  # noqa: E402
from core import repository as repo  # noqa: E402
from core.auth import AuthError, login, register  # noqa: E402
from core.db import init_db  # noqa: E402
from core.repository import (  # noqa: E402
    ROLE_AI_REBUTTAL,
    ROLE_USER_ANSWER,
    ROLE_USER_REBUTTAL,
)

ok_count = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global ok_count
    mark = "PASS" if condition else "FAIL"
    print(f"[{mark}] {label}" + (f" — {detail}" if detail else ""))
    if not condition:
        sys.exit(1)
    ok_count += 1


def main() -> None:
    print(f"== Chế độ: {'NGOẠI TUYẾN' if config.offline_mode() else config.CHAT_MODEL} ==\n")

    init_db()
    stats = ingest.sync_all()
    check("Nạp ngữ liệu + ngân hàng đề", stats["chunks"] > 0,
          f"{stats['subjects']} môn, {stats['chapters']} chương, "
          f"{stats['chunks']} đoạn, {stats['questions']} câu hỏi")

    # Nạp lại lần hai phải không đổi (idempotent)
    stats2 = ingest.sync_all()
    check("Nạp lại idempotent",
          stats2["chunks"] == stats["chunks"]
          and stats2["questions"] == stats["questions"]
          and not stats2["pdf"]["changed"]
          and len(stats2["pdf"]["unchanged"]) == stats2["pdf"]["files"],
          f"{stats2['docx']['files']} docx + {stats2['pdf']['files']} pdf, "
          f"pdf bỏ qua {len(stats2['pdf']['unchanged'])}")

    # --- ghi vết tài liệu
    tracked = ingest.tracked_files()
    check("Ghi vết đủ tài liệu trong input/", len(tracked) >= 6,
          f"{len(tracked)} file")
    check("Mọi tài liệu ở trạng thái đã nạp",
          all(f["status"] == "đã nạp" for f in tracked),
          "; ".join(f"{f['name'][:28]}={f['status']}" for f in tracked[:3]))
    check("Có ghi tóm tắt kết quả nạp",
          all(f["summary"] for f in tracked),
          next((f["summary"][:60] for f in tracked), ""))

    if not config.offline_mode():
        n = rag.build_embeddings()
        check("Xây chỉ mục vector", rag.pending_embedding_count() == 0, f"{n} đoạn mới")

    # --- xác thực
    email = f"sv_{uuid.uuid4().hex[:8]}@sinhvien.edu.vn"
    user = register("Nguyễn Văn Test", email, "matkhau123", "matkhau123")
    check("Đăng ký", user["id"] > 0, email)

    try:
        register("Trùng", email, "matkhau123", "matkhau123")
        check("Chặn email trùng", False)
    except AuthError:
        check("Chặn email trùng", True)

    try:
        login(email, "sai-mat-khau")
        check("Chặn sai mật khẩu", False)
    except AuthError:
        check("Chặn sai mật khẩu", True)

    check("Đăng nhập", login(email, "matkhau123")["email"] == email.lower())

    # --- lớp đa tác tử
    specs = agents.describe()
    check("Khai báo đủ 4 tác tử", len(specs) == 4,
          ", ".join(a["name"] for a in specs))
    check("Mỗi tác tử có vai trò và mục tiêu riêng",
          all(a["role"] and a["goal"] for a in specs)
          and len({a["role"] for a in specs}) == 4)
    check("Chỉ trọng tài trả JSON",
          [a["key"] for a in specs if a["json"] == "có"] == ["judge"])
    check("Backend đang dùng hợp lệ",
          agents.active_backend() in ("native", "crewai"), agents.active_backend())
    check("System prompt dựng từ khai báo vai",
          agents.JUDGE.role in agents.system_prompt(agents.JUDGE)
          and agents.JUDGE.goal in agents.system_prompt(agents.JUDGE))
    check("Gán model riêng cho từng vai được",
          all(a["model"] for a in specs),
          " · ".join(f"{a['name']}={a['model']}" for a in specs[:2]))

    # --- môn học nạp từ thư mục input/
    subjects = repo.list_subjects()
    check("Liệt kê môn học", len(subjects) == 3, ", ".join(s["name"] for s in subjects))

    by_code = {s["code"]: s for s in subjects}
    expected_codes = {
        "PHAP_LUAT_DAI_CUONG",
        "THUONG_MAI_DIEN_TU_CAN_B",
        "UNG_DUNG_CONG_NGHE_THONG",
    }
    check("Nhận diện đủ 3 môn từ input/", expected_codes <= set(by_code),
          ", ".join(sorted(by_code)))
    check("Không còn ngữ liệu demo",
          not {"CSDL", "MMT", "AI"} & set(by_code))

    # Mỗi môn phải có cả ngân hàng câu hỏi lẫn giáo trình
    for code in sorted(expected_codes):
        chs = repo.list_chapters(by_code[code]["id"])
        questions = sum(c["question_count"] for c in chs)
        chunks = sum(c["chunk_count"] for c in chs)
        check(f"{code}: có đề + giáo trình", questions > 0 and chunks > 100,
              f"{len(chs)} chương, {questions} câu, {chunks} đoạn")

    # Giáo trình "Tin học quản lý" ghép vào môn Ứng dụng CNTT nhờ input/mapping.json
    cntt = repo.list_chapters(by_code["UNG_DUNG_CONG_NGHE_THONG"]["id"])
    check("mapping.json ghép giáo trình khác tên môn",
          sum(c["chunk_count"] for c in cntt) > 100,
          f"{sum(c['chunk_count'] for c in cntt)} đoạn")

    # Một file .docx chứa hai học phần -> phải tách thành hai môn
    tmdt = repo.list_chapters(by_code["THUONG_MAI_DIEN_TU_CAN_B"]["id"])
    check("Tách được 2 học phần trong cùng một file",
          sum(c["question_count"] for c in tmdt) > 0
          and sum(c["question_count"] for c in cntt) > 0,
          f"TMĐT {sum(c['question_count'] for c in tmdt)} câu, "
          f"CNTT {sum(c['question_count'] for c in cntt)} câu")

    # Câu trắc nghiệm giữ nguyên các phương án trên từng dòng
    mcq = [
        q for c in cntt
        for q in repo.chapter_question_samples(c["id"], limit=100)
        if chr(10) + "A." in q or chr(10) + "B." in q
    ]
    check("Giữ nguyên phương án của câu trắc nghiệm", len(mcq) > 5,
          f"{len(mcq)} câu nhiều dòng, ví dụ: {mcq[0].splitlines()[0][:60]!r}")

    # Tách đề bài / phương án để giao diện dựng ô chọn đáp án
    stem, options = debate.parse_choices(mcq[0])
    check("Tách được đề bài và phương án", len(options) >= 3 and len(stem) > 20,
          f"{len(options)} phương án: " + ", ".join(k for k, _ in options))
    check("Phương án đánh chữ cái liên tiếp",
          [k for k, _ in options] == ["A", "B", "C", "D"][: len(options)],
          str([k for k, _ in options]))
    check("Đề bài không lẫn phương án",
          not any(line.strip()[:2] in ("A.", "B.", "C.", "D.")
                  for line in stem.split(chr(10))),
          stem.splitlines()[0][:60])

    tu_luan = repo.chapter_question_samples(
        repo.list_chapters(by_code["PHAP_LUAT_DAI_CUONG"]["id"])[0]["id"], limit=1
    )[0]
    check("Câu tự luận không bị nhận nhầm là trắc nghiệm",
          debate.parse_choices(tu_luan)[1] == [], tu_luan[:60])

    # --- chọn một chương có đủ dữ liệu để chạy phiên tranh biện
    law_chapters = repo.list_chapters(by_code["PHAP_LUAT_DAI_CUONG"]["id"])
    check("Đủ 9 chương môn Pháp luật", len(law_chapters) == 9,
          f"tổng {sum(c['question_count'] for c in law_chapters)} câu hỏi")

    chapter = repo.get_chapter(
        max(law_chapters, key=lambda c: c["question_count"])["id"]
    )
    availability = repo.difficulty_availability(chapter["id"])
    check("Phân nhóm độ khó từ tài liệu", set(availability) <= set(config.DIFFICULTIES),
          str(availability))
    check("Tiêu đề chương lấy theo giáo trình",
          "Pháp luật 4" not in chapter["title"], chapter["title"])

    hits = rag.search(chapter["id"], "khái niệm và đặc điểm của trách nhiệm pháp lý")
    check("Truy hồi trúng mục trong giáo trình",
          bool(hits) and any(re.match(r"^\d+\.\d+", h.heading) for h in hits),
          f"top-1: {hits[0].heading[:60]!r}")

    # --- logic chọn chế độ nền kiến thức
    check("Có giáo trình -> chế độ corpus",
          debate.chapter_mode(chapter) == debate.MODE_CORPUS)
    check("Chỉ có ngân hàng đề -> chế độ bank",
          debate.chapter_mode({"chunk_count": 0, "question_count": 5}) == debate.MODE_BANK)
    check("Không có gì -> chế độ none",
          debate.chapter_mode({"chunk_count": 0, "question_count": 0}) == debate.MODE_NONE)

    picked = debate.generate_question(chapter, "easy")
    check("Bốc câu hỏi từ ngân hàng đề", picked["source"] == "bank",
          picked["question"][:90])

    # Mức 'khó' không có trong tài liệu -> AI phải tự sinh đề
    if not availability.get("hard"):
        made = debate.generate_question(chapter, "hard")
        check("Thiếu mức khó -> AI tự ra đề", made["source"] == "llm",
              made["question"][:90])

    # Không lặp lại câu đã hỏi khi còn câu mới
    easy_bank = repo.chapter_question_samples(chapter["id"], limit=100)
    first = debate.generate_question(chapter, "easy")["question"]
    second = debate.generate_question(chapter, "easy", avoid=[first])["question"]
    check("Tránh lặp câu vừa hỏi",
          second != first or len([q for q in easy_bank if q == first]) == len(easy_bank))

    # --- ra đề rồi chạy đủ 3 vòng tranh biện
    difficulty = "medium"
    generated = debate.generate_question(chapter, difficulty)
    check("Sinh câu hỏi", len(generated["question"]) > 10, generated["question"][:90])

    session_id = repo.create_session(
        user["id"], chapter["id"], difficulty, generated["question"], generated["context"]
    )
    check("Tạo phiên", session_id > 0)

    repo.add_turn(session_id, 0, ROLE_USER_ANSWER,
                  "Theo em, chỉ cần có hành vi trái pháp luật là đã đủ để truy cứu "
                  "trách nhiệm pháp lý, yếu tố lỗi chỉ dùng để giảm nhẹ mức phạt.")

    for rnd in range(1, config.MAX_ROUNDS + 1):
        turns = repo.get_turns(session_id)
        result = debate.generate_rebuttal(chapter, difficulty, generated["question"], turns, rnd)
        check(f"Phản biện vòng {rnd}", len(result["content"]) > 40,
              result["content"].replace(chr(10), " ")[:80] + "...")
        repo.add_turn(session_id, rnd, ROLE_AI_REBUTTAL, result["content"])
        repo.add_turn(session_id, rnd, ROLE_USER_REBUTTAL,
                      f"Em phản biện vòng {rnd}: em vẫn cho rằng việc xét lỗi làm "
                      "quá trình xử lý chậm, nên ưu tiên xử phạt theo hành vi.")

    turns = repo.get_turns(session_id)
    expected = 1 + config.MAX_ROUNDS * 2
    check("Số lượt tranh biện", len(turns) == expected, f"{len(turns)}/{expected}")

    # --- trọng tài
    verdict = debate.judge(chapter, difficulty, generated["question"], turns)
    check("Trọng tài chấm điểm", 0 <= verdict["diem_tong"] <= 10,
          f"tổng {verdict['diem_tong']}/10, thắng: {verdict['ben_thuyet_phuc_hon']}")
    check("Đủ 4 tiêu chí", len(verdict["diem"]) == 4, str(verdict["diem"]))

    repo.save_verdict(session_id, verdict)
    repo.close_session(session_id)
    saved = repo.get_verdict(session_id)
    check("Lưu/đọc kết luận", saved is not None and
          abs(saved["diem_tong"] - verdict["diem_tong"]) < 1e-6)

    # --- lịch sử cá nhân
    hist = repo.history(user["id"])
    check("Lịch sử cá nhân", len(hist) == 1 and hist[0]["status"] == "done")
    me = repo.user_stats(user["id"])
    check("Thống kê cá nhân", me["finished"] == 1 and me["avg_score"] is not None,
          f"điểm TB {me['avg_score']}")

    print(f"\n== {ok_count} kiểm thử đều PASS ==")
    if not config.offline_mode():
        print("\n--- Ví dụ phản biện vòng 1 ---")
        print(repo.get_turns(session_id)[1]["content"])
        print("\n--- Nhận xét trọng tài ---")
        print(verdict["nhan_xet_chung"])


if __name__ == "__main__":
    main()
