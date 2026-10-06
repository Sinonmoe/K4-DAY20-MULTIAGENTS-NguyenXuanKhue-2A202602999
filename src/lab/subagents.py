"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    """
    return [
        {
            "name": "explorer",
            "description": (
                "Use proactively to inspect workspace files, read instruction.md, READMEs, docstrings, "
                "and analyze data formats before making modifications. Returns factual observations without editing files."
            ),
            "system_prompt": (
                "You are an exploratory research assistant. Read specifications, examine directory structures, "
                "and report objective facts. Never modify, create, or delete any files in the workspace."
            ),
        },
        {
            "name": "implementer",
            "description": (
                "Use to implement specific code changes, bug fixes, data parsing, or script executions. "
                "Always provide complete task rules and relative file paths in the delegation message."
            ),
            "system_prompt": (
                "You are an implementation specialist. Execute requested modifications, fix code errors, "
                "process data files, and use the shell to run tests and verify results. Report changes accurately."
            ),
        },
        {
            "name": "reviewer",
            "description": (
                "Use to independently evaluate and verify outputs against the task specification, "
                "checking edge cases and test results before concluding. Does not modify files."
            ),
            "system_prompt": (
                "You are an independent quality review specialist. Validate that output files strictly follow "
                "all formatting and functional requirements. Report any discrepancies or failed checks without editing files."
            ),
        },
    ]
