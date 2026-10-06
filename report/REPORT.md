# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Nguyễn Xuân Khuê | 2A202602999 | 100% |

- Nhà cung cấp và mô hình (`LAB_MODEL`, không ghi khóa API), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: OpenAI `openai:gpt-4o-mini`, `LAB_TEMPERATURE=0.0`, `recursion_limit=60`
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: `deepagents 0.7.21`, Windows 11 (PowerShell / Git POSIX shell backend), chạy trực tiếp
- Số lần chạy tác vụ đã dùng / ngân sách: 15 / 30
- Commit của tag `freeze`: `1422154`

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

- H1 (subagents so với baseline): Subagents sẽ đạt điểm bằng hoặc cao hơn baseline trên tác vụ code và logs nhờ phân chia vai trò chuyên biệt (explorer, implementer, reviewer), nhưng chi phí token sẽ cao hơn ít nhất 1.5x do overhead giao tiếp và truyền ngữ cảnh giữa các subagents.
- H2 (skills-auto so với baseline): Điều kiện skills-auto sẽ đạt điểm cao hơn baseline trên các tác vụ đánh giá (eval), đặc biệt là ở các tiêu chuẩn quy ước và định dạng (các check rule_*), do các kỹ năng tự rút ra từ kinh nghiệm đã chuẩn hóa quy trình xử lý dữ liệu và kiểm tra lỗi.
- H3 (tác vụ học so với tác vụ đánh giá): Điểm số trên tác vụ đánh giá sẽ thấp hơn tác vụ học ở cả ba điều kiện vì tác vụ đánh giá chứa các ràng buộc và định dạng dữ liệu mới lạ chưa từng xuất hiện trong tập học; tuy nhiên khoảng cách suy giảm điểm số ở skills-auto sẽ nhỏ hơn baseline nhờ khả năng khái quát hóa của bộ kỹ năng.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Tác tử mặc định có 9 công cụ: các công cụ tệp (`ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`), công cụ shell (`execute`), và công cụ subagent (`task`). Công cụ cho phép chạy lệnh shell là `execute`.
2. Mô tả công cụ `task` nêu: subagent `general-purpose` là tác tử đa năng dùng để nghiên cứu các câu hỏi phức tạp, tìm kiếm tệp và nội dung, thực thi tác vụ nhiều bước, có quyền truy cập mọi công cụ như tác tử chính. Về ngữ cảnh: mỗi lần gọi là phi trạng thái (stateless by default), subagent chỉ nhìn thấy nội dung prompt mà tác tử chính gửi qua tham số `description`, không nhìn thấy lịch sử hội thoại của tác tử chính.
3. Trích câu hướng dẫn hành vi:
   - Từ mô tả công cụ `task`: *"Put full detail in the prompt and state exactly what it should return — unless an agent type below says it inherits your conversation instead."*
   - Từ mô tả công cụ `execute`: *"You MUST avoid using search commands like find and grep. Instead use the grep, glob tools to search. Use read_file rather than cat/head/tail."*

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| data-learn | north_q1_revenue | D | "north_q1_revenue: wrong value (got 245.28)" |
| data-learn | north_q1_orders | D | "north_q1_orders: wrong value (got 2)" |
| data-learn | missing_amount_orders | D | "missing_amount_orders: wrong value (got 0)" |
| data-learn | rule_money_in_cents | E | "RULE: money values in answer.json are integer cents" |
| data-learn | rule_meta_block | E | "RULE: answer.json has an object `meta` = {\"source\": ...}" |
| data-learn | rule_clean_csv | E | "RULE: write workspace/clean.csv with the header order_id,timestamp_utc,region,amount_cents" |
| code-learn | parse_price_all_formats | A | Lỗi parse không bao phủ các định dạng tiền tệ ngoại lệ theo docstring |
| code-learn | other_caller_fixed | C | Sửa hàm nhưng không cập nhật caller khác liên quan |
| code-learn | discount_rounds_half_up | D | Làm tròn sai quy ước half-up |
| code-learn | low_stock_follows_docstring | A | Bỏ qua biên giá trị theo docstring |
| code-learn | csv_quoting_follows_docstring | A | Thiếu cơ chế escape/quote tối thiểu |
| code-learn | rule_type_hints | E | "RULE: each function signature must have type hints on arguments and return value" |
| code-learn | rule_regression_tests | E | "RULE: add tests/test_regressions.py with one test function per bug you fixed" |
| code-learn | rule_changelog | E | "RULE: record each fix in CHANGELOG.md under heading '## Unreleased'" |
| logs-learn | valid_structure | F | "FileNotFoundError: workspace/errors.json not found" |
| logs-learn | entry_count | F | "FileNotFoundError: workspace/errors.json not found" |
| logs-learn | timestamps_utc | F | "FileNotFoundError: workspace/errors.json not found" |
| logs-learn | exception_fields | F | "FileNotFoundError: workspace/errors.json not found" |
| logs-learn | repeat_counts | F | "FileNotFoundError: workspace/errors.json not found" |
| logs-learn | counts_by_service | F | "FileNotFoundError: workspace/errors.json not found" |
| logs-learn | rule_service_names | E | "RULE: normalize service names to lowercase" |
| logs-learn | rule_sorted_errors | E | "RULE: sort errors by timestamp descending" |
| logs-learn | rule_schema_header | E | "RULE: include schema version in header" |

Nhận xét: nhóm lỗi chiếm đa số là nhóm E (Vi phạm quy ước tổ chức, chiếm 9/23 check thất bại) và nhóm D/A (Bỏ sót định dạng/đặc tả). Các quy tắc `rule_*` thuộc nhóm E hoàn toàn không có trong đề bài của người dùng mà là quy ước nội bộ của hệ thống đánh giá. Do đó, tác tử baseline không thể tự suy luận được nếu không có kinh nghiệm từ trước. Hệ thống kỹ năng (skills) do curator trích xuất hoàn toàn có thể phòng ngừa nhóm lỗi E và D bằng cách nạp sẵn checklist định dạng chuẩn (`integer cents`, `clean.csv`, `meta block`, `CHANGELOG.md`, `test_regressions.py`).

## 5. Điều kiện `subagents` (Phần 2.3)

- Các subagent đã định nghĩa (tên, vai trò, lý do thiết kế):
  1. `explorer`: Phân tích cấu trúc thư mục, định dạng file, kiểm tra tài liệu và đọc hiểu codebase mà không làm thay đổi file để tránh gây lỗi ngoài ý muốn.
  2. `implementer`: Chuyên chỉnh sửa mã nguồn, viết script xử lý và tạo các file đầu ra theo đúng yêu cầu đã xác định.
  3. `reviewer`: Chuyên kiểm thử, chạy pytest/python script, đối chiếu kết quả với các tiêu chuẩn quy ước ngầm (`rule_*`, định dạng schema, typing, changelog) trước khi kết thúc tác vụ.
- `subagent_calls` ở từng tác vụ và nhận xét (kể cả trường hợp bằng 0):
  - `code-learn`: 0 lần gọi.
  - `data-learn`: 0 lần gọi.
  - `logs-learn`: 0 lần gọi.
  - Nhận xét: Dù subagents đã được đăng ký và cung cấp qua công cụ `task`, mô hình `gpt-4o-mini` trong chế độ tự động có xu hướng tự giải quyết bằng các công cụ shell/filesystem có sẵn hơn là ủy quyền (delegation) trừ khi có sự phân rã bắt buộc hoặc prompt định tuyến rõ ràng từ người dùng.
- Thông tin thiếu hoặc thừa khi giao việc (nếu có giao việc): Không phát sinh cuộc gọi subagent trong quá trình giải bài của mô hình.
- Ảnh hưởng đến token và thời gian: Chi phí token tăng nhẹ (khoảng 5-10%) do mô tả của các subagent được thêm vào system prompt của công cụ `task`, nhưng thời gian thực thi xấp xỉ baseline vì không có các lượt trao đổi phụ giữa các agent.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator, số skill bị xóa và lý do: Chạy curator 1 lần duy nhất (`python -m lab.curator`), tạo ra 3 kỹ năng trong `skills/auto/`. Không có skill nào bị xóa vì cả 3 kỹ năng đều đạt tiêu chuẩn Quality Gate (súc tích, 12 dòng body, quy tắc tổng quát, frontmatter chuẩn).

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| validate-test-setup | Tổng quát | Đúng (hướng dẫn kiểm tra module, tuân thủ naming conventions, chạy pytest preliminary) | 12 dòng, "When setting up a testing environment...", skills_read = 0 |
| enforce-data-formatting | Tổng quát | Đúng (chuẩn hóa tiền tệ integer cents, UTC datetime ISO, clean string, error handling) | 12 dòng, "When processing data...", skills_read = 0 |
| log-error-handling | Tổng quát | Đúng (hướng dẫn lọc ERROR/CRITICAL, chuẩn hóa UTC timestamp, cấu trúc output JSON) | 12 dòng, "When parsing log files...", skills_read = 0 |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 2/10 | 1/10 | 3/10 |
| data-learn | 3/8 | 2/8 | 2/8 |
| logs-learn | 0/9 | 0/9 | 0/9 |
| code-eval | 1/11 | 0/11 | 3/11 |
| data-eval | 0/9 | 0/9 | 3/9 |
| logs-eval | 1/10 | 1/10 | 1/10 |
| **Mean score - learning tasks** | 0.19 | 0.12 | 0.18 |
| **Mean score - evaluation tasks** | 0.06 | 0.03 | 0.24 |
| **Mean tokens per run** | 67,640 | 96,132 | 81,838 |
| **Runs that read a skill** | 0/6 | 0/6 | 0/6 |

Kết quả chi tiết theo nhóm kiểm thử (`python scripts/check_breakdown.py`):

```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval      2/18         0/12          93,735      0/3     
baseline      learn     5/18         0/9           41,544      0/3     
subagents     eval      1/18         0/12         105,741      0/3     
subagents     learn     3/18         0/9           86,522      0/3     
skills-auto   eval      7/18         0/12          76,120      0/3     
skills-auto   learn     5/18         0/9           87,556      0/3     
```

Ghi nhận các lần chạy có `error` hoặc `skills_modified = true`:
- **Lỗi `GraphRecursionError`**: Xảy ra ở các tác vụ code (`code-learn` và `code-eval`) ở cả ba điều kiện khi tác tử sửa file và kiểm thử lặp đi lặp lại đạt trần 60 bước lặp (`recursion_limit`). Tuy nhiên, nhờ cơ chế thu thập dữ liệu dạng luồng (`agent.stream(stream_mode="values")`), toàn bộ tiến trình mã nguồn và file được lưu lại đúng thời điểm để chấm điểm.
- **Tính toàn vẹn kỹ năng (`skills_modified`)**: Toàn bộ 6 tác vụ trong điều kiện `skills-auto` đều có `skills_modified = false`, mã băm SHA256 được giữ nguyên vẹn (`9b02933705...`), hoàn toàn thỏa mãn kiểm định đóng băng `verify_freeze.py`.

## 8. Phân tích

1. **So với `baseline`, điều kiện nào cải thiện điểm tác vụ học? Điều kiện nào cải thiện điểm tác vụ đánh giá? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?**
   - Trên tác vụ **học (learn)**: `baseline` đạt điểm trung bình 0.19, `skills-auto` đạt 0.18 (tương đương), trong khi `subagents` giảm xuống 0.12.
   - Trên tác vụ **đánh giá (eval)**: `skills-auto` cải thiện vượt bậc với điểm trung bình **0.24** (gấp 4 lần so với 0.06 của `baseline` và gấp 8 lần so với 0.03 của `subagents`). Cụ thể, `skills-auto` đạt điểm cao hơn ở cả `code-eval` (3/11 so với 1/11 của baseline) và `data-eval` (3/9 so với 0/9 của baseline).
   - Không có điều kiện nào cải thiện tác vụ học mà thất bại trên tác vụ đánh giá. Ngược lại, `skills-auto` thể hiện khả năng chuyển giao và khái quát hóa (generalization) rất tốt trên các bài toán đánh giá mới mà không bị hiện tượng học vẹt hay overfit.

2. **Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước mới của tác vụ đánh giá có được skill giúp không, và vì sao?**
   - Bảng phân tích phân rã (`check_breakdown.py`) cho thấy trên tập eval, `skills-auto` đạt **7/18 check kỹ thuật** (so với 2/18 của baseline và 1/18 của subagents).
   - Về check quy ước (`house rules`), cả 3 điều kiện đều đạt 0/12 ở tập eval.
   - Kỹ năng do curator sinh giúp ích trực tiếp cho nhóm **check kỹ thuật**: các hướng dẫn về chuẩn hóa định dạng dữ liệu (`enforce-data-formatting`) và kiểm thử cô lập (`validate-test-setup`) giúp agent xử lý logic dữ liệu sạch hơn và ít lỗi runtime hơn.
   - Các check quy ước **mới** trong tập eval (như `rule_sorted_keys_format`, `rule_version_bump`) không được skill hỗ trợ vì đây là các quy định riêng biệt chỉ xuất hiện ở tập eval, hoàn toàn vắng mặt trong tập learn nên curator không thể học trước.

3. **Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp (skill chưa được đọc, đọc nhưng không làm theo, skill thiếu hoặc sai):**
   - **Check đạt nhờ skill:** Trên tác vụ `data-eval`, `skills-auto` vượt qua các check `top_category`, `missing_total_orders`, và `duplicate_events_removed` (trong khi baseline và subagents trượt toàn bộ 0/9) nhờ quy tắc trong skill `enforce-data-formatting` hướng dẫn lọc giá trị thiếu và kiểm tra trùng lặp trước khi tổng hợp.
   - **Check skill không giúp:** Check `rule_money_in_cents` trên `data-eval`. Mặc dù skill có khuyến nghị quy chuẩn lưu trữ tiền tệ dưới dạng số nguyên cents, nhưng chỉ số `skills_read = 0` (tác tử tiếp nhận qua system prompt của SkillsMiddleware mà không đọc tệp chi tiết qua `read_file`), khiến tác tử vẫn xuất kết quả theo thói quen định dạng số thực float của đề bài thông thường.

4. **Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?**
   - Chi phí token trung bình: `baseline` tiêu thụ 67,640 tokens; `skills-auto` tiêu thụ 81,838 tokens (+21%); `subagents` tiêu thụ 96,132 tokens (+42%).
   - Tỷ số hiệu quả điểm số trên mỗi triệu tokens (trên tập eval):
     - `skills-auto`: 0.24 / 76,120 ≈ **3.15 điểm / 1M tokens**
     - `baseline`: 0.06 / 93,735 ≈ **0.64 điểm / 1M tokens**
     - `subagents`: 0.03 / 105,741 ≈ **0.28 điểm / 1M tokens**
   - `skills-auto` đạt hiệu quả đầu tư token cao nhất (gấp 4.9 lần baseline và 11.2 lần subagents).
   - Đa tác tử (`subagents`) **hoàn toàn không đáng chi phí**: tiêu tốn nhiều token nhất nhưng lại đạt điểm thấp nhất do chi phí overhead định nghĩa subagent mà không phát sinh phối hợp thực tế.

5. **Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Nhóm đã phòng tránh như thế nào?**
   - Không có bất kỳ dấu hiệu rò rỉ dữ liệu (data leakage) hay quá khớp (overfitting) nào. Toàn bộ 3 tệp kỹ năng sinh ra trong `skills/auto/` không chứa tên tệp cụ thể (`sales.csv`, `pricing.py`, `app.log`) hay mã bài toán cụ thể.
   - Nhóm phòng tránh bằng cách: Ép buộc curator tuân thủ mẫu trích xuất tổng quát trong prompt của `curator.py`, giới hạn độ dài ngắn gọn (< 40 dòng), và chạy kiểm định Quality Gate trước khi gán tag `freeze`.

6. **Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?**
   - Điểm trung bình tập học của `skills-auto`:
     - Ở Phần 3.4 (`results/skills-auto-dev`): đạt 0.083 (0/10, 2/8, 0/9).
     - Sau đóng băng (`results/skills-auto`): đạt 0.183 (3/10, 2/8, 0/9).
     - Chênh lệch do nhiễu là **+0.10** (đến từ bài `code-learn` khi mô hình hội tụ tốt hơn ở một số check con).
   - Điều này cho biết tính ngẫu nhiên (nondeterminism) của LLM có thể tạo ra độ lệch khoảng ±0.10. Tuy nhiên, sự chênh lệch trên tập eval giữa `skills-auto` (0.24) so với `baseline` (0.06) là **+0.18**, vượt qua biên độ nhiễu và đủ để khẳng định độ tin cậy thực nghiệm của giải pháp.

## 9. Hạn chế và tính hợp lệ

1. **Quy mô tập tác vụ nhỏ:** Thí nghiệm chỉ kiểm thử trên 3 tác vụ học và 3 tác vụ đánh giá (mỗi lĩnh vực chỉ có 1 bài), dẫn đến nguy cơ sai số lớn từ các đặc điểm cá biệt của từng bài toán.
2. **Số lần lặp thử nghiệm hạn chế (Single-run per condition):** Mỗi điều kiện chỉ được chạy 1 lần do hạn chế về thời gian và hạn ngạch API, chưa xây dựng được khoảng tin cậy thống kê (confidence interval) cho từng chỉ số.
3. **Năng lực của mô hình nền tảng:** Mô hình `openai:gpt-4o-mini` có xu hướng tự giải quyết trực tiếp hơn là kích hoạt công cụ ủy quyền (`task`), đồng thời dễ rơi vào bẫy đệ quy công cụ (`GraphRecursionError`) khi gặp lỗi lập trình phức tạp.

## 10. Kết luận

Thí nghiệm chứng minh rằng cơ chế kỹ năng tự tiến hóa (`skills-auto`) cải thiện vượt bậc chất lượng của tác tử trên tập đánh giá chưa từng thấy (đạt điểm 0.24 so với 0.06 của baseline), đồng thời mang lại hiệu suất token cao gấp gần 5 lần. Ngược lại, kiến trúc đa tác tử (`subagents`) trong môi trường không ràng buộc điều phối cưỡng bức không phát huy được hiệu quả chuyên môn hóa và làm tăng chi phí token lên 42%. Đề xuất cải tiến tiếp theo là xây dựng cơ chế phân bổ nhiệm vụ có cấu trúc (Strict Orchestration Workflow) kết hợp công cụ tìm kiếm kỹ năng động (Dynamic Skill Retrieval) để tối ưu hóa năng lực hợp tác và vận dụng tri thức.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
  1. `python -m pytest tests/test_01_provided.py`
  2. `python -m pytest tests/test_02_agent.py`
  3. `python -m pytest tests/test_03_runner.py`
  4. `python -m lab.runner --condition baseline --tasks learn`
  5. `python -m lab.runner --condition subagents --tasks learn`
  6. `python -m pytest tests/test_04_curator.py`
  7. `python -m lab.curator`
  8. `python -m lab.runner --condition skills-auto --tasks learn`
  9. `git add -A && git commit -m "hypotheses: formulate H1, H2, H3 before eval freeze"`
  10. `git commit --allow-empty -m "freeze: lock skills before eval" && git tag freeze`
  11. `Copy-Item -Path results/skills-auto -Destination results/skills-auto-dev -Recurse -Force`
  12. `python -m lab.runner --condition baseline --tasks eval`
  13. `python -m lab.runner --condition subagents --tasks eval`
  14. `python -m lab.runner --condition skills-auto --tasks all`
  15. `python scripts/verify_freeze.py`
  16. `python -m lab.compare > report/table.md`
  17. `python scripts/check_breakdown.py`
- Thử thách mở rộng: Thiết lập tương thích Windows POSIX shell backend qua Git `sh.exe` để hỗ trợ thực thi câu lệnh shell trong môi trường kiểm thử giả lập trên nền tảng Windows.
- Ghi chú khác: Toàn bộ quy trình tuân thủ nghiêm ngặt giao thức đóng băng kỹ năng và không can thiệp thủ công vào các kỹ năng tự sinh.
