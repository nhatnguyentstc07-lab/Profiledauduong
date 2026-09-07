"""Kiểm thử giao diện bằng streamlit.testing (không cần mở trình duyệt).

Chạy: python ui_test.py
"""

from __future__ import annotations

import sys
import uuid

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from streamlit.testing.v1 import AppTest  # noqa: E402

from core import config  # noqa: E402
from core.repository import get_turns as repo_turns  # noqa: E402

ok = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global ok
    print(f"[{'PASS' if condition else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not condition:
        sys.exit(1)
    ok += 1


def find_button(at: AppTest, text: str):
    """Nút thường và nút submit của form đều nằm trong at.button."""
    for btn in at.button:
        if text in btn.label:
            return btn
    raise AssertionError(
        f"Không tìm thấy nút chứa {text!r}. Hiện có: {[b.label for b in at.button]}"
    )


def main() -> None:
    at = AppTest.from_file("app.py", default_timeout=60).run()
    check("Tải trang đăng nhập", not at.exception, at.title[0].value)

    # --- đăng ký (tab thứ hai: 4 ô nhập cuối)
    email = f"ui_{uuid.uuid4().hex[:8]}@sinhvien.edu.vn"
    at.text_input[2].set_value("Trần Thị UI Test")
    at.text_input[3].set_value(email)
    at.text_input[4].set_value("matkhau123")
    at.text_input[5].set_value("matkhau123")
    find_button(at, "Đăng ký").click().run()
    check("Đăng ký qua UI", at.session_state["user"] is not None, email)

    # --- giữ phiên: token nằm trên URL, tải lại trang phải vẫn đăng nhập
    token = at.query_params.get("sid")
    if isinstance(token, list):
        token = token[0]
    check("Cấp token phiên", bool(token) and token == at.session_state["token"],
          f"sid={token[:12]}...")

    reloaded = AppTest.from_file("app.py", default_timeout=90)
    reloaded.query_params["sid"] = token
    reloaded.run()
    check("Tải lại trang vẫn giữ đăng nhập",
          reloaded.session_state["user"] is not None
          and reloaded.session_state["user"]["email"] == email.lower(),
          "không phải đăng nhập lại")

    # Token sai thì phải trả về màn hình đăng nhập và dọn URL
    bad = AppTest.from_file("app.py", default_timeout=90)
    bad.query_params["sid"] = "token-khong-hop-le"
    bad.run()
    check("Token sai -> quay về đăng nhập",
          bad.session_state["user"] is None and "sid" not in bad.query_params)

    # Đăng xuất phải thu hồi token: dùng lại token cũ không vào được nữa
    logged_out = AppTest.from_file("app.py", default_timeout=90)
    logged_out.query_params["sid"] = token
    logged_out.run()
    find_button(logged_out, "Đăng xuất").click().run()
    check("Đăng xuất xoá token khỏi URL",
          logged_out.session_state["user"] is None
          and "sid" not in logged_out.query_params)

    revisit = AppTest.from_file("app.py", default_timeout=90)
    revisit.query_params["sid"] = token
    revisit.run()
    check("Token đã thu hồi không dùng lại được",
          revisit.session_state["user"] is None)

    # Đăng nhập lại để chạy tiếp các kịch bản sau
    at = AppTest.from_file("app.py", default_timeout=90).run()
    at.text_input[0].set_value(email)
    at.text_input[1].set_value("matkhau123")
    find_button(at, "Đăng nhập").click().run()
    check("Đăng nhập lại sau khi đăng xuất", at.session_state["user"] is not None)

    # --- màn hình chọn môn / chương / mức độ
    check("Vào màn hình luyện tập", "Bắt đầu một phiên phản biện" in at.title[0].value)
    def label_of(value) -> str:
        if isinstance(value, dict):
            return str(value.get("name") or value.get("title") or value)
        return str(value)

    check("Có đủ 3 selectbox", len(at.selectbox) == 3,
          " | ".join(label_of(s.value) for s in at.selectbox))

    at.selectbox[2].set_value("hard").run()
    check("Đổi mức độ sang Khó", at.selectbox[2].value == "hard")

    # --- ra đề
    find_button(at, "Lấy câu hỏi ngẫu nhiên").click().run()
    d = at.session_state["debate"]
    check("Sinh câu hỏi + tạo phiên", d is not None and d["stage"] == "answer",
          d["question"][:80])

    # --- trả lời quá ngắn phải bị chặn
    at.text_area[0].set_value("ngắn quá")
    find_button(at, "Gửi").click().run()
    check("Chặn câu trả lời quá ngắn",
          at.session_state["debate"]["stage"] == "answer" and len(at.warning) > 0,
          at.warning[0].value)

    # --- trả lời hợp lệ -> AI phản biện vòng 1
    at.text_area[0].set_value(
        "Theo em, vấn đề này cần xét cả mặt lý thuyết lẫn chi phí triển khai thực tế, "
        "vì một giải pháp tối ưu trên giấy chưa chắc khả thi khi vận hành."
    )
    find_button(at, "Gửi").click().run()
    d = at.session_state["debate"]
    check("AI phản biện vòng 1", d["round"] == 1 and d["stage"] == "rebut")

    # --- các vòng phản biện còn lại
    for rnd in range(1, config.MAX_ROUNDS + 1):
        at.text_area[0].set_value(
            f"Em phản biện vòng {rnd}: lập luận của hệ thống chưa tính tới ràng buộc "
            "nguồn lực, nên kết luận đưa ra là chưa đầy đủ trong bối cảnh thực tế."
        )
        find_button(at, "Gửi").click().run()
        d = at.session_state["debate"]
        if rnd < config.MAX_ROUNDS:
            check(f"AI phản biện vòng {rnd + 1}", d["round"] == rnd + 1 and d["stage"] == "rebut")
        else:
            check("Kết thúc và gọi trọng tài", d["stage"] == "done")

    check("Hiển thị kết luận trọng tài",
          any("trọng tài" in s.value.lower() for s in at.subheader))

    session_id = d["session_id"]

    # --- sang trang lịch sử
    find_button(at, "Lịch sử của tôi").click().run()
    check("Mở trang lịch sử", "Lịch sử luyện tập" in at.title[0].value)
    check("Phiên vừa xong có trong lịch sử",
          any(f"#{session_id}" in e.label for e in at.expander))

    # --- kịch bản 2: môn nạp từ .docx, câu hỏi lấy từ ngân hàng đề
    find_button(at, "Luyện phản biện").click().run()
    options = at.selectbox[0].options
    check("Chỉ còn 3 môn thật", len(options) == 3, " | ".join(options))

    law_index = next(i for i, o in enumerate(options) if "Pháp luật" in o)
    at.selectbox[0].select_index(law_index).run()
    check("Chọn môn nạp từ .docx", at.selectbox[0].value["code"] == "PHAP_LUAT_DAI_CUONG",
          at.selectbox[1].options[0])
    check("Tiêu đề chương lấy theo giáo trình",
          not any("Pháp luật 1" in o for o in at.selectbox[1].options),
          at.selectbox[1].options[4])

    at.selectbox[2].select_index(0).run()  # mức Dễ
    captions = [c.value for c in at.caption]
    check("Hiển thị đủ cả ngân hàng đề lẫn ngữ liệu",
          any("Ngân hàng đề" in c and "Ngữ liệu tham khảo" in c for c in captions),
          next((c for c in captions if "Ngân hàng đề" in c), ""))
    check("Không còn cảnh báo thiếu tài liệu",
          not any("chưa có tài liệu giải thích" in w.value for w in at.warning))

    find_button(at, "Lấy câu hỏi ngẫu nhiên").click().run()
    d2 = at.session_state["debate"]
    check("Đề lấy từ ngân hàng, phản biện bám giáo trình",
          d2["source"] == "bank" and d2["mode"] == "corpus",
          d2["question"].splitlines()[0][:80])

    # --- kịch bản 3: môn có câu trắc nghiệm nhiều dòng
    find_button(at, "Luyện phản biện").click().run()
    at.session_state["debate"] = None
    at.run()
    cntt_index = next(i for i, o in enumerate(at.selectbox[0].options) if "công nghệ" in o)
    at.selectbox[0].select_index(cntt_index).run()
    check("Chọn được môn Ứng dụng CNTT",
          at.selectbox[0].value["code"] == "UNG_DUNG_CONG_NGHE_THONG")
    check("Giáo trình khác tên vẫn ghép đúng môn (mapping.json)",
          any("Ngữ liệu tham khảo" in c.value for c in at.caption),
          next((c.value for c in at.caption if "Ngân hàng đề" in c.value), ""))

    mcq_found = False
    for _ in range(6):  # bốc vài lần cho tới khi gặp câu trắc nghiệm
        find_button(at, "Lấy câu hỏi ngẫu nhiên").click().run()
        question = at.session_state["debate"]["question"]
        if "\n" in question:
            mcq_found = True
            break
        at.session_state["debate"] = None
        at.run()
    check("Câu trắc nghiệm giữ đủ các phương án", mcq_found,
          question.splitlines()[0][:70] if mcq_found else "không bốc trúng câu nhiều dòng")

    # --- ô chọn đáp án hiện ra kèm ô giải thích
    check("Hiện ô chọn đáp án", len(at.radio) == 1 and len(at.radio[0].options) >= 3,
          f"{len(at.radio[0].options)} phương án: {at.radio[0].options[0][:40]}")
    check("Vẫn còn ô nhập giải thích", len(at.text_area) == 1)

    at.text_area[0].set_value("Em chọn phương án này vì nó phản ánh đúng bản chất kỹ thuật "
                              "của vấn đề, các phương án còn lại đều sai ở điểm cốt lõi.")
    find_button(at, "Gửi").click().run()
    check("Chưa chọn đáp án thì bị chặn",
          at.session_state["debate"]["stage"] == "answer"
          and any("chọn một đáp án" in w.value for w in at.warning),
          at.warning[0].value if at.warning else "")

    at.radio[0].set_value(at.radio[0].options[2])
    at.text_area[0].set_value("Em chọn phương án này vì nó phản ánh đúng bản chất kỹ thuật "
                              "của vấn đề, các phương án còn lại đều sai ở điểm cốt lõi.")
    find_button(at, "Gửi").click().run()
    d3 = at.session_state["debate"]
    check("Gửi được đáp án kèm giải thích",
          d3["stage"] == "rebut" and d3["choice"] == at.radio[0].options[2]
          if at.radio else d3["stage"] == "rebut",
          str(d3.get("choice"))[:60])

    turns = repo_turns(d3["session_id"])
    check("Lưu đáp án đã chọn vào lượt trả lời",
          "Đáp án chọn:" in turns[0]["content"],
          turns[0]["content"].splitlines()[0][:60])

    # --- trang tài liệu nguồn chỉ dành cho quản trị viên
    check("Sinh viên thường không thấy nút Tài liệu nguồn",
          not any("Tài liệu nguồn" in b.label for b in at.button))

    at.session_state["page"] = "documents"  # thử vào thẳng bằng trạng thái phiên
    at.run()
    check("Vào thẳng cũng bị chặn",
          any("chỉ dành cho quản trị viên" in e.value for e in at.error))

    admin = AppTest.from_file("app.py", default_timeout=90).run()
    admin_email = "admin@gmail.com"
    admin.text_input[0].set_value(admin_email)
    admin.text_input[1].set_value("matkhau123")
    find_button(admin, "Đăng nhập").click().run()
    if admin.session_state["user"] is None:  # lần chạy đầu: tạo tài khoản admin
        admin = AppTest.from_file("app.py", default_timeout=90).run()
        admin.text_input[2].set_value("Quản trị viên")
        admin.text_input[3].set_value(admin_email)
        admin.text_input[4].set_value("matkhau123")
        admin.text_input[5].set_value("matkhau123")
        find_button(admin, "Đăng ký").click().run()
    check("Đăng nhập tài khoản quản trị",
          admin.session_state["user"] is not None
          and admin.session_state["user"]["email"] == admin_email)

    find_button(admin, "Tài liệu nguồn").click().run()
    check("Quản trị viên mở được trang tài liệu",
          "Tài liệu nguồn" in admin.title[0].value)
    check("Báo mọi tài liệu đã nạp",
          any("đã được nạp" in s.value for s in admin.success),
          "; ".join(s.value[:50] for s in admin.success))

    print(f"\n== {ok} kiểm thử giao diện đều PASS ==")


if __name__ == "__main__":
    main()
