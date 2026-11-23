---
name: numerology
description: >
  Thần số học Pythagoras (numerology): số chủ đạo / đường đời (life path), số sứ mệnh, số linh hồn,
  số nhân cách, số trưởng thành, số ngày sinh, năm cá nhân, biểu đồ ngày sinh và các mũi tên,
  4 đỉnh cao và 4 thử thách. Dùng khi người dùng nhắc đến thần số học, số chủ đạo, con số đường đời,
  biểu đồ ngày sinh, mũi tên trống, năm cá nhân, life path number, numerology. Luôn dùng skill này
  và chạy script của nó cho mọi con số, kể cả câu hỏi ngắn; không tự cộng nhẩm (các cách tính khác nhau
  cho ra số khác nhau, script ghi rõ cách đã dùng). Mô hình chỉ hỏi thông tin và diễn giải.
compatibility: Requires Python 3.11+ only (no third-party packages); run scripts/numerology_cli.py for all calculations.
---

# Thần số học

Read:

- `references/y-nghia-so.md`

## Nguyên tắc

- Con số mô tả khuynh hướng, điểm mạnh và điều cần rèn; không phải định mệnh. Không nói "số xấu", "số khổ".
- Mọi con số lấy từ script. Không tự cộng nhẩm, không sửa kết quả.
- Thần số học không có cơ sở khoa học. Với sức khỏe, pháp lý, tài chính, chọn nghề hay hôn nhân, chỉ đưa góc nhìn tham khảo và khuyên dựa vào thông tin thực tế.
- Trả lời bằng ngôn ngữ người dùng dùng (mặc định tiếng Việt).
- Mục nào trong `references/y-nghia-so.md` ghi "chưa đối chiếu sách" là cách hiểu hiện đại; khi dùng phải nói rõ đó không phải nội dung sách.

## Bước 1: hỏi thông tin

Cần:

1. Ngày sinh dương lịch (ngày, tháng, năm). Người dùng đưa ngày âm thì đổi sang dương lịch trước; nếu cần, dùng skill `bazi` hoặc `ziwei-doushu` với `calendar_locale: "vn"` để đổi.
2. Họ tên đầy đủ khai sinh (để tính số sứ mệnh, linh hồn, nhân cách). Không có tên thì vẫn tính được các số theo ngày sinh.
3. Năm cần xem năm cá nhân. Người dùng không nói thì dùng năm hiện tại; luôn truyền `query_year` vì script không tự lấy năm hiện tại.

Hỏi thêm khi người dùng đã quen một cách tính:

- Số chủ đạo theo cách Việt Nam phổ biến (2–11, 22/4, 33/6; không có 1, thay bằng 10), cách phương Tây (1–9, 11, 22, 33) hay đúng sách Phillips (2–11, 22/4; 33 tính là 6): `life_path_rule` = `vn` (mặc định) / `classic` / `phillips`.
- Cộng tất cả chữ số (mặc định) hay rút gọn riêng ngày, tháng, năm rồi cộng: `life_path_method` = `digits` / `components`. Hai cách có thể ra số khác nhau (ví dụ 6/7/1989: `digits` ra 4, `components` ra 22/4). Kết quả lệch với app người dùng đang xem thì thử cách còn lại và nói rõ.
- Chữ Y tính là nguyên âm (mặc định, hợp với tên tiếng Việt như Huy, Thủy) hay phụ âm: `y_as_vowel`.

## Bước 2: gọi script

Script nằm trong thư mục skill này, ký hiệu `<skill_dir>` (thư mục chứa SKILL.md; khi cài làm plugin Claude Code là base directory của skill).

Script chỉ dùng thư viện chuẩn của Python 3.11+, không cần cài thêm.

```bash
python3 "<skill_dir>/scripts/numerology_cli.py" \
  --input "tmp/numerology_input.json" \
  --output "tmp/numerology_output.json"
```

**Ghi và chạy (bắt buộc)**: dùng tool Write tạo `tmp/numerology_input.json` trong thư mục làm việc hiện tại (Write cần đường dẫn tuyệt đối, tức `<thư mục hiện tại>/tmp/numerology_input.json`; đường dẫn tương đối `tmp/...` trong lệnh bên dưới trỏ tới cùng file); không dùng heredoc, `echo >` hay lệnh ghép `mkdir && ...`. Sau đó chạy riêng đúng một lệnh `python3` ở trên (không thêm `cd`, `&&`, pipe), rồi dùng Read đọc file output. Lệnh bị từ chối thì báo người dùng cần cho phép chạy script python này, không chuyển sang tự tính. Lệnh dùng `python3`; chỉ khi máy không có `python3` (một số máy Windows) mới đổi sang `python`. `python3` chạy được script nghĩa là thư viện đã đủ, đừng cài thêm.

Input:

```json
{
  "birth_date": "1990-05-15",
  "full_name": "Nguyễn Văn An",
  "query_year": 2026,
  "life_path_rule": "vn|classic",
  "life_path_method": "digits|components",
  "y_as_vowel": true
}
```

- Chỉ `birth_date` bắt buộc. Tên có dấu tiếng Việt được tự bỏ dấu (Đ thành D).
- Output có `error` thì hỏi lại người dùng theo nội dung lỗi; không tự tính thay.

## Bước 3: đọc output

| Trường | Ý nghĩa |
|---|---|
| `normalized_input` | Ngày sinh, họ tên đã bỏ dấu (`normalized_name`) và các lựa chọn cách tính; kiểm tra đúng thông tin người dùng đưa |
| `ruleset` | Cách tính đã dùng cho từng con số; nói lại với người dùng khi có khác biệt cách tính |
| `life_path` | Số chủ đạo: `value`, `display` (như 22/4, 10/1), `digit_sum` (tổng mọi chữ số); cách `components` có thêm `components_sum` |
| `birthday` | Số ngày sinh |
| `name.expression` / `soul_urge` / `personality` | Số sứ mệnh / linh hồn / nhân cách; `letters` là bảng chữ cái đã tính |
| `maturity` | Số trưởng thành |
| `personal_year` | Năm cá nhân của `query_year` |
| `birth_chart` | `counts` số lần xuất hiện 1–9, `missing` số thiếu, `arrows` mũi tên (`full` / `empty` / `partial`) |
| `pinnacles` | 4 đỉnh cao: giá trị và khoảng tuổi |
| `challenges` | 4 thử thách |
| `warnings` | Lưu ý (thiếu họ tên, tên không có nguyên âm…); đưa vào phần giải thích cho người dùng |

## Bước 4: diễn giải

Thứ tự:

1. Số chủ đạo: tính cách cốt lõi, điểm mạnh, điều cần rèn.
2. Số sứ mệnh, linh hồn, nhân cách: so với số chủ đạo, chỗ nào cùng hướng, chỗ nào giằng co.
3. Biểu đồ ngày sinh: số lặp nhiều, số thiếu, mũi tên đủ và mũi tên trống. Tên mũi tên lấy từ `references/y-nghia-so.md` và nói rõ đó là cách gọi phổ biến.
4. Đỉnh cao và thử thách theo giai đoạn tuổi; nhấn mạnh giai đoạn hiện tại.
5. Năm cá nhân: chủ đề của năm và gợi ý hành động cụ thể.

Phong cách:

- Nói rõ, cụ thể, có ví dụ đời thường; không dùng câu chung chung áp dụng cho ai cũng đúng.
- Mỗi điểm mạnh đi kèm một điều cần rèn.
- Kết bằng 2–3 gợi ý hành động thực tế.

Cuối mỗi lần luận giải đầy đủ:

> Thần số học là một hệ thống biểu tượng, không phải khoa học. Kết quả để tham khảo và tự suy ngẫm, không thay cho lời khuyên chuyên môn về sức khỏe, pháp lý, tài chính.
