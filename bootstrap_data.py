"""Nạp dữ liệu và xây chỉ mục vector mà không cần mở giao diện.

Dùng khi triển khai lần đầu trên máy chủ, hoặc mỗi lần thêm/sửa tài liệu trong input/.

    python bootstrap_data.py             # chỉ xử lý file mới hoặc đã sửa
    python bootstrap_data.py --force     # nạp lại tất cả, kể cả file không đổi
    python bootstrap_data.py --reset     # xoá sạch học liệu cũ rồi nạp lại từ đầu
    python bootstrap_data.py --status    # chỉ xem trạng thái các tài liệu, không nạp
"""

from __future__ import annotations

import argparse
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from core import config, debate, ingest, rag  # noqa: E402
from core import repository as repo  # noqa: E402
from core.auth import purge_expired_tokens  # noqa: E402
from core.db import init_db  # noqa: E402
from core.llm import LLMError  # noqa: E402


def _print_files() -> None:
    files = ingest.tracked_files()
    if not files:
        print("Thư mục input/ chưa có tài liệu nào.")
        return
    print(f"\n{'TÀI LIỆU':58} {'LOẠI':5} {'TRẠNG THÁI':22} KẾT QUẢ NẠP")
    print("-" * 130)
    for f in files:
        size = f"{(f['size_bytes'] or 0)/1024:,.0f} KB"
        print(
            f"{f['name'][:56]:58} {(f['kind'] or ''):5} {f['status']:22} "
            f"{(f['summary'] or '')[:44]:46} {size:>10}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Nạp dữ liệu ôn tập và xây chỉ mục vector")
    parser.add_argument("--force", action="store_true",
                        help="nạp lại cả tài liệu không thay đổi")
    parser.add_argument("--reset", action="store_true",
                        help="xoá toàn bộ học liệu và chỉ mục cũ trước khi nạp lại "
                             "(giữ nguyên tài khoản người dùng)")
    parser.add_argument("--status", action="store_true",
                        help="chỉ xem trạng thái tài liệu, không nạp gì")
    args = parser.parse_args()

    init_db()

    if args.status:
        _print_files()
        print(f"\nHiện có: {rag.stats()}")
        return 0

    purge_expired_tokens()

    if args.reset:
        before = rag.stats()
        ingest.reset_content()
        print(
            f"Đã xoá học liệu cũ: {before['subjects']} môn · {before['chapters']} chương · "
            f"{before['chunks']} đoạn · {before['questions']} câu hỏi.\n"
        )

    force = args.force or args.reset
    stats = ingest.sync_all(force_docx=force, force_pdf=force)

    docx, pdf = stats["docx"], stats["pdf"]
    print("NGÂN HÀNG CÂU HỎI (.docx)")
    print(f"  {len(docx['changed'])} file nạp mới/cập nhật, "
          f"{len(docx['unchanged'])} file không đổi"
          + (f", {len(docx.get('removed', []))} file đã xoá" if docx.get("removed") else ""))
    print("GIÁO TRÌNH (.pdf)")
    print(f"  {len(pdf['changed'])} file nạp mới/cập nhật, "
          f"{len(pdf['unchanged'])} file không đổi"
          + (f", {len(pdf.get('removed', []))} file đã xoá" if pdf.get("removed") else ""))
    if stats["cleaned"]["subjects"] or stats["cleaned"]["chapters"]:
        print(f"  đã dọn {stats['cleaned']['chapters']} chương rỗng, "
              f"{stats['cleaned']['subjects']} môn rỗng")

    _print_files()

    print(
        f"\nTổng: {stats['subjects']} môn · {stats['chapters']} chương · "
        f"{stats['chunks']} đoạn ngữ liệu · {stats['questions']} câu hỏi"
    )
    for subject in repo.list_subjects():
        chapters = repo.list_chapters(subject["id"])
        print(
            f"  - {subject['name']}: {len(chapters)} chương, "
            f"{sum(c['question_count'] for c in chapters)} câu hỏi, "
            f"{sum(c['chunk_count'] for c in chapters)} đoạn"
        )

    if config.offline_mode():
        print("\nCHƯA cấu hình OPENAI_API_KEY -> bỏ qua bước xây chỉ mục vector.")
        return 0

    pending = rag.pending_embedding_count()
    if pending:
        print(f"\nĐang tạo embedding cho {pending} đoạn...")
        try:
            print(f"  xong {rag.build_embeddings()} đoạn.")
        except LLMError as exc:
            print(f"  LỖI: {exc}")
            return 1
    else:
        print("\nChỉ mục vector đã đầy đủ.")

    missing = repo.chapters_missing_topic()
    if missing:
        print(f"Đang đặt nhãn chủ đề cho {len(missing)} chương...")
        for chapter in missing:
            topic = debate.suggest_chapter_topic(chapter)
            if topic:
                repo.set_chapter_topic(chapter["id"], topic)
                print(f"  {chapter['title'][:44]} -> {topic}")

    final = rag.stats()
    print(f"\nSẵn sàng: {final['chunks']} đoạn / {final['embeddings']} vector.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
