"""GUIDE Phần 3 - Người tuyển chọn skill (skill curator): tự viết skill từ các lần chạy thất bại.

Pseudo-code: guides/pseudocode/04_curator.md
Kiểm tra:    pytest tests/test_04_curator.py
Chạy thật:   python -m lab.curator
"""
import json
from pathlib import Path
import re

from .model import make_model
from .tasks import ROOT, eval_markers   # có sẵn: định danh của tác vụ đánh giá, tính lúc chạy

# ---- CÓ SẴN, KHÔNG SỬA: kiểm tra và tách khối skill (phần dễ sai và liên quan bảo mật) ----------------
SAFE_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def validate_skill(text: str, expected_name: str | None = None) -> list[str]:
    """Kiểm tra nội dung một SKILL.md. Trả về danh sách vấn đề (rỗng = hợp lệ).

    Quy tắc: có khối YAML frontmatter; `name` chữ thường/số/gạch ngang (tối đa 64 ký tự) và bằng `expected_name`
    nếu được truyền; có `description` (tối đa 1024 ký tự); phần thân tối đa 80 dòng; không chứa chuỗi nào của
    `eval_markers()`. Quy tắc về `name` cũng là biện pháp bảo mật: tên khối do LLM sinh ra được dùng để tạo
    đường dẫn, nên `../evil` không được lọt qua.
    """
    problems = []
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text.strip() + "\n", re.S)
    if not m:
        return ["missing YAML frontmatter"]
    front, body = m.groups()
    name = re.search(r"^name:\s*(.+)$", front, re.M)
    desc = re.search(r"^description:\s*(.+)$", front, re.M)
    n = name.group(1).strip() if name else ""
    if not SAFE_NAME.fullmatch(n) or len(n) > 64:
        problems.append("invalid name")
    elif expected_name is not None and n != expected_name:
        problems.append("name differs from the block name")
    if not desc or len(desc.group(1).strip()) > 1024:
        problems.append("missing or too long description")
    if len(body.strip().splitlines()) > 80:
        problems.append("body longer than 80 lines")
    low = text.lower()
    for marker in eval_markers():
        if marker in low:
            problems.append(f"mentions evaluation material: {marker}")
    return problems


def parse_skill_blocks(reply: str) -> list[tuple[str, str]]:
    """Tách câu trả lời của LLM thành danh sách (name, nội dung SKILL.md).

    Khuôn dạng: `=== SKILL: <name> ===` ... `=== END ===`. Một khối kết thúc ở điểm nào đến trước trong ba điểm:
    `=== END ===`, tiêu đề `=== SKILL:` kế tiếp, hoặc cuối văn bản (LLM đôi khi quên dòng END).
    """
    pattern = re.compile(r"^=== SKILL: (\S+) ===[ \t]*\n(.*?)(?=^=== END ===|^=== SKILL: |\Z)", re.S | re.M)
    return [(name, text.strip()) for name, text in pattern.findall(str(reply))]
# --------------------------------------------------------------------------------------------------


def curate_skills(results_dir="results", source_condition="baseline", out_dir=None, model=None, max_skills: int = 3) -> list[Path]:
    """Đọc các lần chạy của TÁC VỤ HỌC (role == "learn") trong `source_condition`, nhờ LLM viết skill, ghi file.

    Các bước: nạp run.json + trace.md -> (nếu không có check nào thất bại: in cảnh báo và trả về [] mà KHÔNG gọi LLM)
    -> dựng prompt -> model.invoke(prompt) -> parse_skill_blocks -> validate_skill(text, expected_name=name)
    -> ghi `<out_dir>/<name>/SKILL.md`. Mặc định `out_dir` = <gốc lab>/skills/auto (dùng `ROOT` từ lab.tasks).
    Giữ tối đa `max_skills` skill hợp lệ; skill không hợp lệ bị bỏ qua.
    Prompt chứa, với mỗi check thất bại, TÊN và trường `detail` (lời nhận xét của bot đánh giá: phát biểu quy tắc bị vi phạm)
    cùng phần cuối của vết (trace). Với tác vụ học, `detail` chỉ phát biểu quy tắc, không chứa đáp án.
    Tuyệt đối KHÔNG đưa dữ liệu của tác vụ đánh giá (role == "eval") vào prompt.
    model mặc định: make_model() (lab.model).
    Trả về: danh sách đường dẫn SKILL.md đã ghi.
    """
    if out_dir is None:
        out_dir = ROOT / "skills" / "auto"
    else:
        out_dir = Path(out_dir)

    results_path = Path(results_dir) / source_condition
    if not results_path.exists():
        print(f"Warning: Results directory {results_path} does not exist.")
        return []

    runs = []
    for task_dir in sorted(results_path.iterdir()):
        run_file = task_dir / "run.json"
        if not run_file.is_file():
            continue
        try:
            r = json.loads(run_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        # Tuyệt đối không đưa dữ liệu của tác vụ đánh giá (role == "eval") vào prompt
        if r.get("role") != "learn":
            continue

        failed_checks = []
        for c in r.get("checks", []):
            if not c.get("passed"):
                failed_checks.append({
                    "name": c.get("name", ""),
                    "detail": c.get("detail", ""),
                })

        trace_file = task_dir / "trace.md"
        trace_text = ""
        if trace_file.is_file():
            try:
                full_trace = trace_file.read_text(encoding="utf-8")
                trace_text = full_trace[-6000:]
            except Exception:
                pass

        if failed_checks:
            runs.append({
                "task": r.get("task", task_dir.name),
                "failed_checks": failed_checks,
                "trace": trace_text,
            })

    if not runs:
        print("Warning: không có check thất bại ở tác vụ học.")
        return []

    runs_descriptions = []
    for run in runs:
        checks_str = "\n".join(
            f"  - Check: {fc['name']}\n    Feedback detail: {fc['detail']}"
            for fc in run["failed_checks"]
        )
        runs_descriptions.append(
            f"### Task: {run['task']}\n"
            f"Failed checks:\n{checks_str}\n\n"
            f"Trace excerpt:\n{run['trace']}\n"
        )
    runs_block = "\n---\n".join(runs_descriptions)

    prompt = (
        "You are writing reusable SKILL files for an engineering assistant agent working in a sandbox.\n"
        "Below are the failed checks (check names and review feedback) along with execution traces from learning runs.\n"
        f"Identify common procedural errors and organizational rules, then write up to {max_skills} concise skills "
        "to prevent these failures on new tasks of the same kind.\n\n"
        "Rules:\n"
        "- Skills must be general: DO NOT mention specific task IDs, specific private test filenames, or hardcoded answers.\n"
        "- Each skill MUST have YAML frontmatter with `name` (lowercase letters, numbers, hyphens only) and "
        "`description` (one sentence stating WHEN the agent should read and use this skill).\n"
        "- Body must be at most 40 lines of imperative guidelines and checklists.\n"
        "- Format output exactly as blocks:\n\n"
        "=== SKILL: <name> ===\n"
        "---\n"
        "name: <name>\n"
        "description: <when to use>\n"
        "---\n"
        "<instructions>\n"
        "=== END ===\n\n"
        f"{runs_block}"
    )

    resolved_model = model if model is not None else make_model()
    reply = resolved_model.invoke(prompt)
    content = reply.content if hasattr(reply, "content") else str(reply)

    blocks = parse_skill_blocks(content)
    written = []
    for name, text in blocks:
        if len(written) >= max_skills:
            break
        problems = validate_skill(text, expected_name=name)
        if problems:
            print(f"Skipping skill {name} due to problems: {problems}")
            continue

        skill_file = out_dir / name / "SKILL.md"
        skill_file.parent.mkdir(parents=True, exist_ok=True)
        skill_file.write_text(text.strip() + "\n", encoding="utf-8")
        written.append(skill_file)

    return written


if __name__ == "__main__":
    for p in curate_skills():
        print("wrote", p)
