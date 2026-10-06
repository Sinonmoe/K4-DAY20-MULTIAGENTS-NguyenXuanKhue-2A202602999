"""GUIDE Phần 1 - Dựng tác tử (agent) bằng Deep Agents.

Pseudo-code: guides/pseudocode/01_agent.md
Kiểm tra:    pytest tests/test_02_agent.py
"""
import os
from pathlib import Path
import subprocess
import sys
import uuid

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from deepagents.backends.protocol import ExecuteResponse
from .model import make_model
from .subagents import get_subagents

# ---- CÓ SẴN, KHÔNG SỬA: system prompt dùng chung cho mọi sinh viên (để đường cơ sở so sánh được) ----
PATHS_NOTE = (
    "PATHS: every path is relative to the sandbox root and never starts with '/'. "
    "The task files are in the folder workspace/ (for example workspace/app.log). "
    "Use exactly this relative form both in the file tools and in the shell (execute); "
    "the shell starts in the sandbox root. "
)
BASE_PROMPT = (
    "You are an engineering assistant working in a sandbox. "
    + PATHS_NOTE
    + "Use the shell to run Python and tests. "
    "When you are done, reply with a short summary that mentions only files you really created or changed."
)
SKILLS_NOTE = (
    " Skills are in the folder skills/ (one sub-folder per skill with a SKILL.md). "
    "As your FIRST action, read the SKILL.md of every skill whose description could apply to the task, "
    "then follow them. Never modify skills/."
)
SUBAGENTS_NOTE = (
    " You have specialised subagents (see the description of the task tool). "
    "For anything beyond a trivial step, delegate to a suitable subagent and put ALL the task rules and file paths "
    "in the delegation message, because a subagent sees only what you send. "
    "Check what a subagent returns before you rely on it."
)
# --------------------------------------------------------------------------------------------------


class WindowsPosixShellBackend(LocalShellBackend):
    """Subclass of LocalShellBackend that uses Git's sh.exe on Windows for POSIX compatibility."""

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        sh_exe = "C:\\Program Files\\Git\\bin\\sh.exe"
        if sys.platform == "win32" and Path(sh_exe).exists():
            if not command or not isinstance(command, str):
                return ExecuteResponse(
                    output="Error: Command must be a non-empty string.",
                    exit_code=1,
                    truncated=False,
                )
            effective_timeout = timeout if timeout is not None else self._default_timeout
            if effective_timeout <= 0:
                raise ValueError(f"timeout must be positive, got {effective_timeout}")

            try:
                result = subprocess.run(
                    [sh_exe, "-c", command],
                    check=False,
                    capture_output=True,
                    stdin=subprocess.DEVNULL,
                    text=True,
                    timeout=effective_timeout,
                    env=self._env,
                    cwd=str(self.cwd),
                )

                output_parts = []
                if result.stdout:
                    output_parts.append(result.stdout)
                if result.stderr:
                    stderr_lines = result.stderr.strip().split("\n")
                    output_parts.extend(f"[stderr] {line}" for line in stderr_lines)

                output = "\n".join(output_parts) if output_parts else "<no output>"
                truncated = False
                if len(output) > self._max_output_bytes:
                    output = output[: self._max_output_bytes] + f"\n\n... Output truncated at {self._max_output_bytes} bytes."
                    truncated = True

                if result.returncode != 0:
                    output = f"{output.rstrip()}\n\nExit code: {result.returncode}"

                return ExecuteResponse(
                    output=output,
                    exit_code=result.returncode,
                    truncated=truncated,
                )
            except subprocess.TimeoutExpired:
                msg = f"Error: Command timed out after {effective_timeout} seconds."
                return ExecuteResponse(output=msg, exit_code=124, truncated=False)
            except Exception as e:
                return ExecuteResponse(
                    output=f"Error executing command ({type(e).__name__}): {e}",
                    exit_code=1,
                    truncated=False,
                )

        return super().execute(command, timeout=timeout)


def make_backend(sandbox: Path):
    """Tạo backend (môi trường thực thi) cho tác tử.

    Yêu cầu:
      - Thư mục gốc (root_dir) là `sandbox`; đường dẫn tương đối `workspace/...` và `skills/...`
        phải dùng được ở CẢ công cụ tệp lẫn shell (shell chạy với thư mục làm việc = `sandbox`).
      - Tác tử chạy được lệnh shell và gọi được `python` (cần đặt PATH).
      - KHÔNG chuyển biến môi trường của bạn vào shell của tác tử (khóa API không được lộ).
    """
    py_dir = str(Path(sys.executable).parent)
    paths = [py_dir]
    if sys.platform == "win32":
        for p in ["C:\\Program Files\\Git\\usr\\bin", "C:\\Program Files\\Git\\bin", "C:\\Windows\\System32"]:
            if Path(p).exists():
                paths.append(p)
    paths.extend(["/usr/local/bin", "/usr/bin", "/bin"])

    env = {
        "PATH": os.pathsep.join(paths),
        "HOME": str(sandbox),
        "PYTHONDONTWRITEBYTECODE": "1",
    }

    backend_cls = WindowsPosixShellBackend if (sys.platform == "win32" and Path("C:\\Program Files\\Git\\bin\\sh.exe").exists()) else LocalShellBackend
    return backend_cls(
        root_dir=sandbox,
        virtual_mode=True,
        inherit_env=False,
        env=env,
        timeout=120,
    )


def build_agent(sandbox: Path, mode: str = "single", use_skills: bool = False, model=None):
    """Tạo tác tử Deep Agents.

    Tham số:
      sandbox:    thư mục chứa `workspace/` (và `skills/` nếu có).
      mode:       "single"    -> tác tử mặc định (có subagent `general-purpose` sẵn của Deep Agents)
                  "subagents" -> thêm các subagent từ `get_subagents()` (nối PATHS_NOTE vào `system_prompt` của MỖI subagent,
                                 vì subagent không nhận BASE_PROMPT) và thêm SUBAGENTS_NOTE vào prompt chính
      use_skills: True -> nạp thư mục "/skills/" qua tham số `skills=` của create_deep_agent
                  và thêm SKILLS_NOTE vào prompt.
      model:      mô hình ngôn ngữ; None -> dùng `make_model()`.
    mode không hợp lệ -> ném ValueError.
    Trả về: đồ thị (graph) đã biên dịch, gọi bằng `.invoke({"messages": [...]})`.
    """
    if mode not in ("single", "subagents"):
        raise ValueError(f"Unknown mode: {mode}")

    kwargs = {}
    prompt = BASE_PROMPT

    if mode == "subagents":
        kwargs["subagents"] = [
            {**sub, "system_prompt": sub["system_prompt"] + " " + PATHS_NOTE}
            for sub in get_subagents()
        ]
        prompt = prompt + SUBAGENTS_NOTE

    if use_skills:
        kwargs["skills"] = ["/skills/"]
        prompt = prompt + SKILLS_NOTE

    resolved_model = model if model is not None else make_model()
    return create_deep_agent(
        model=resolved_model,
        system_prompt=prompt,
        backend=make_backend(sandbox),
        **kwargs,
    )

