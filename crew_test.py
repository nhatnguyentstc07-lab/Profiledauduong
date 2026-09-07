"""Kiểm thử bộ chạy CrewAI (chạy bằng môi trường .venv-crewai).

    .venv-crewai/Scripts/python.exe crew_test.py        # Windows
    .venv-crewai/bin/python crew_test.py                # Linux

So sánh cùng một nghiệp vụ chạy qua hai backend để chắc chắn CrewAI không làm đổi
luồng: vẫn ra đề được, vẫn phản biện đúng bố cục, trọng tài vẫn trả JSON hợp lệ.
"""

from __future__ import annotations

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Tắt telemetry của CrewAI cho khỏi gọi mạng ngoài ý muốn
os.environ.setdefault("CREWAI_TELEMETRY_OPT_OUT", "true")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ["AGENT_FRAMEWORK"] = "crewai"

from core import agents, debate  # noqa: E402
from core import repository as repo  # noqa: E402
from core.repository import ROLE_AI_REBUTTAL, ROLE_USER_ANSWER  # noqa: E402

ok = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global ok
    print(f"[{'PASS' if condition else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not condition:
        sys.exit(1)
    ok += 1


def main() -> None:
    from core import crew_backend

    check("Đã cài CrewAI", crew_backend.available())
    check("Backend đang bật là crewai", agents.active_backend() == "crewai")

    subject = repo.list_subjects()[0]
    chapter = repo.get_chapter(repo.list_chapters(subject["id"])[4]["id"])
    print(f"\nMôn: {subject['name']} | {chapter['title']}\n")

    # Mức "khó" không có trong ngân hàng đề -> buộc phải qua LLM, không lấy sẵn
    generated = debate.generate_question(chapter, "hard")
    check("Ra đề qua CrewAI",
          generated["source"] == "llm" and not generated["offline"]
          and len(generated["question"]) > 10,
          generated["question"][:90])

    turns = [{
        "round_no": 0, "role": ROLE_USER_ANSWER,
        "content": "Theo em chỉ cần có hành vi trái pháp luật là đủ để truy cứu trách "
                   "nhiệm pháp lý, yếu tố lỗi chỉ để giảm nhẹ mức phạt.",
    }]
    rebuttal = debate.generate_rebuttal(
        chapter, "hard", generated["question"], turns, 1
    )
    check("Phản biện qua CrewAI",
          not rebuttal["offline"] and "Ghi nhận" in rebuttal["content"],
          rebuttal["content"].replace("\n", " ")[:90])

    turns.append({"round_no": 1, "role": ROLE_AI_REBUTTAL, "content": rebuttal["content"]})
    verdict = debate.judge(chapter, "hard", generated["question"], turns)
    check("Trọng tài qua CrewAI trả JSON hợp lệ",
          not verdict["offline"] and 0 <= verdict["diem_tong"] <= 10
          and len(verdict["diem"]) == 4,
          f"tổng {verdict['diem_tong']}/10, {verdict['diem']}")
    check("Trọng tài nêu được nhận xét",
          bool(verdict["nhan_xet_chung"]) and bool(verdict["dap_an_tham_khao"]),
          verdict["nhan_xet_chung"][:80])

    print(f"\n== {ok} kiểm thử CrewAI đều PASS ==")
    print("\n--- Ví dụ phản biện do CrewAI điều phối ---")
    print(rebuttal["content"][:700])


if __name__ == "__main__":
    main()
