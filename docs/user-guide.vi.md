# Hướng dẫn sử dụng

[English](user-guide.md) | Tiếng Việt

Bộ skill gồm 5 hệ: Bát Tự (`bazi`), Tử Vi (`ziwei-doushu`), Kỳ Môn (`qimen-dunjia`), Lục Hào (`liuyao`), Thần số học (`numerology`). Mỗi hệ có một script Python tính toán; mô hình chỉ hỏi thông tin và diễn giải.

Kết quả để tham khảo, không thay cho lời khuyên y tế, pháp lý, tài chính.

## 1. Cài đặt

Cần Python 3.11 trở lên (`python3 --version`). Thần số học chỉ cần Python; 4 hệ còn lại cần thêm `lunar_python` và `tzdata`.

### Cách A: plugin Claude Code (khuyên dùng)

Trong Claude Code:

```bash
/plugin install numerologist-skills --marketplace <owner>/Numerologist_skills
```

`<owner>` là tài khoản GitHub chứa repo (bản fork của bạn). Claude Code cũ hơn 2.1.275 thì cài hai bước:

```bash
/plugin marketplace add <owner>/Numerologist_skills
```

```bash
/plugin install numerologist-skills@numerologist-skills
```

Cài thư viện Python một lần (đường dẫn là thư mục plugin đã cài, hoặc repo nếu dùng bản local):

```bash
python3 -m pip install -r bazi/scripts/requirements.txt
```

Lần đầu skill chạy script, Claude Code sẽ hỏi quyền chạy lệnh `python3 ...`. Chọn cho phép. Nếu từ chối, skill dừng lại và báo, không tự tính thay.

### Cách B: dùng thử từ repo, không cài

```bash
claude --plugin-dir /đường/dẫn/tới/Numerologist_skills
```

Chỉ có hiệu lực trong phiên đó, không đổi cấu hình chung.

### Cách C: MCP server (Claude Desktop và client MCP khác)

```bash
python3 -m pip install -r mcp-server/requirements.txt
```

```bash
claude mcp add numerologist -- python3 /đường/dẫn/tới/Numerologist_skills/mcp-server/server.py
```

Claude Desktop: thêm vào `mcpServers` trong `claude_desktop_config.json`:

```json
"numerologist": {"command": "python3", "args": ["/đường/dẫn/tới/Numerologist_skills/mcp-server/server.py"]}
```

Server có 5 tool: `bazi_chart`, `ziwei_chart`, `qimen_chart`, `liuyao_chart`, `numerology_chart`.

## 2. Hỏi thế nào

Cứ hỏi bằng lời thường, tiếng Việt hoặc tiếng Trung. Skill tự hỏi lại phần còn thiếu (giới tính, giờ sinh, việc cần xem…). Đưa đủ ngay từ đầu thì nhanh hơn.

| Hệ | Cần cung cấp | Câu hỏi mẫu |
|---|---|---|
| Bát Tự | ngày giờ sinh, giới tính, nơi sinh | "Lập lá số Bát Tự cho nữ, sinh 10:00 ngày 15/05/1990 dương lịch ở Hà Nội. Đại vận hiện tại thế nào?" |
| Tử Vi | ngày giờ sinh, giới tính; ngày âm thì nói rõ có nhuận không | "Lá số tử vi nam, sinh 14:30 ngày 16/08/2000 dương lịch. Xem cung Quan Lộc và năm 2027." |
| Kỳ Môn | việc cụ thể, thời điểm hỏi, nơi đang ở | "Dùng Kỳ Môn xem: chiều nay 15:00 đi ký hợp đồng ở hướng Đông có thuận không?" |
| Lục Hào | một việc cụ thể; kết quả 6 lần gieo xu từ dưới lên, hoặc nhờ gieo hộ | "Mình gieo được 7, 8, 9, 7, 6, 8 (từ dưới lên) lúc 10:00 hôm nay, hỏi phỏng vấn có đậu không." |
| Thần số học | ngày sinh dương lịch, họ tên khai sinh | "Thần số học cho Nguyễn Văn An, sinh 15/05/1990: số chủ đạo, biểu đồ ngày sinh, năm cá nhân 2026." |

Gieo xu Lục Hào: tung 3 đồng xu, mặt chữ (ngửa) tính 3, mặt lưng (sấp) tính 2, cộng lại (quy ước này chưa đối chiếu sách; có sách tính ngược lại). 6 và 9 là hào động. Ghi 6 lần từ dưới lên. Không có xu thì nói "gieo hộ mình", script gieo bằng số ngẫu nhiên an toàn và trả về từng lần gieo.

## 3. Các lựa chọn cách tính

Các trường phái tính khác nhau ở một số điểm. Script có mặc định và ghi rõ cách đã dùng trong `ruleset` của kết quả. Muốn đổi thì nói với Claude, ví dụ "tính theo giờ mặt trời thực".

| Lựa chọn | Áp dụng | Mặc định | Khi nào đổi |
|---|---|---|---|
| Âm lịch Việt Nam / Trung Quốc (`calendar_locale`) | Bát Tự, Tử Vi, Kỳ Môn | `cn` | Ngày âm theo lịch Việt Nam: nói "âm lịch Việt Nam". Lệch nhau vài tháng mỗi thập kỷ, có năm lệch cả tháng (Tết 1985: VN 21/1, TQ 20/2). Khi hai lịch khác nhau ở ngày đó, kết quả có cảnh báo nêu cả hai. |
| Giờ Tý (`late_zi_rule`) | Bát Tự, Tử Vi, Lục Hào | 23:00 tính sang ngày mới | Thầy/phần mềm của bạn dùng "dạ Tý" (23:00–24:00 vẫn là ngày cũ). |
| Giờ mặt trời thực (`true_solar_time`) | Bát Tự, Tử Vi, Kỳ Môn | tắt | Sinh xa kinh tuyến múi giờ (Tây Bắc VN, Tân Cương…) hoặc thầy yêu cầu; cần kinh độ nơi sinh. |
| Tháng nhuận (`leap_month_rule`) | Tử Vi | ngày 1–15 tính tháng này, 16 trở đi tính tháng sau | Theo cách của phần mềm bạn đang đối chiếu. 《紫微斗數全書》 tính cả tháng nhuận theo tháng sau (`next`). |
| Tứ hóa can Nhâm (`sihua_rule`) | Tử Vi | `zuofu`: Tả phụ hóa khoa | `quanshu` nếu theo 《紫微斗數全書》 (Thiên phủ hóa khoa). |
| Rút gọn số chủ đạo (`life_path_rule`) | Thần số học | `vn`: 2–11, 22/4, 33/6 | `classic` nếu theo sách phương Tây (1–9, 11, 22, 33); `phillips` nếu theo đúng sách Phillips (33 tính là 6, tuổi đỉnh cao đầu = 36 − 10 hoặc 11). |
| Cách cộng (`life_path_method`) | Thần số học | cộng mọi chữ số | Kết quả lệch với app khác thì thử cách rút gọn riêng ngày/tháng/năm. |

Cảnh báo thường gặp trong kết quả (Claude sẽ nói lại):

- Giờ sinh sát ranh giới canh giờ (±15 phút): nên xem cả hai canh giờ.
- Sinh sát tiết khí (±24 giờ): trụ tháng, có khi cả trụ năm, có thể đổi nếu giờ sinh lệch.
- Sinh trong giờ mùa hè (Trung Quốc 1986–1991): giờ đồng hồ khi đó nhanh 1 tiếng.
- Sinh từ 1968 đến 13/6/1975 ở miền Nam Việt Nam: giờ đồng hồ miền Nam khi đó theo UTC+8, âm lịch theo lịch truyền thống (Tết 1968 miền Nam 30/1, miền Bắc 29/1).

## 4. Chạy script trực tiếp (không qua Claude)

Mỗi script đọc một file JSON và ghi một file JSON:

```bash
python3 bazi/scripts/bazi_cli.py --input input.json --output output.json
```

Ví dụ `input.json` cho Bát Tự:

```json
{"birth_time": "1990-05-15 10:00", "gender": "女", "calendar_locale": "vn", "query_year": 2026}
```

Trường nhập của từng hệ có trong `SKILL.md` tương ứng (mục gọi script). Lỗi nhập liệu nằm ở trường `error` của output.

## 5. Sự cố thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `command not found: python` | Dùng `python3`; skill đã gọi `python3`, chỉ lệnh bạn tự gõ mới cần đổi. |
| `ModuleNotFoundError: lunar_python` hoặc error "缺少依赖 lunar_python" | `python3 -m pip install -r <skill>/scripts/requirements.txt`. Python cài qua Homebrew có thể đòi thêm `--break-system-packages`, hoặc dùng venv. |
| Claude tự tính mà không chạy script | Nhắc "dùng skill … và chạy script". Kiểm tra bạn đã cho phép lệnh `python3`. |
| Kết quả khác phần mềm/thầy khác | Hỏi cách tính bên kia (âm lịch VN hay TQ, giờ Tý, giờ mặt trời thực, tháng nhuận) rồi yêu cầu tính lại theo đúng cách đó. |
| Lá số Tử Vi thiếu Tuần, Triệt | Script theo Tam Hợp phái Trung Quốc, chưa an các sao riêng của Tử Vi Việt Nam. |

## 6. Cho người phát triển

```bash
python3 -m pip install -r requirements-dev.txt
```

```bash
pytest -q
```

- Sửa phần dùng chung chỉ ở `core/`, rồi chạy `python3 tools/sync_core.py`. CI kiểm bằng `python3 tools/sync_core.py --check`.
- Đo chất lượng luận giải (tốn phí, khoảng $0.45 mỗi lần với Haiku, 3 lượt mỗi ca):

```bash
claude plugin eval . --model haiku --runs 3 --allow-tools 'Bash(python:*)' 'Bash(python3:*)' Write --no-publish
```

  `python3` của máy phải import được `lunar_python`, nếu không các ca Bát Tự, Tử Vi, Lục Hào sẽ trượt.
