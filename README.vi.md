# Numerologist Skills

[中文](README.md) | [English](README.en.md) | Tiếng Việt

Bộ skill AI cho các hệ thuật số truyền thống, tách thành các module có thể kiểm tra và tái sử dụng. Mục tiêu không phải làm mô hình "giỏi huyền học hơn", mà là giảm bịa đặt khi lập lá số, chọn trường phái, làm sai thứ tự các bước và khi giải thích.

Hướng dẫn chi tiết bằng tiếng Việt: [docs/user-guide.vi.md](docs/user-guide.vi.md).

## Các skill

| Thư mục | Hệ | Dùng để | Tính toán |
|---|---|---|---|
| `bazi/` | Bát Tự (Tứ trụ) | Nhật chủ mạnh yếu, cách cục, thập thần, đại vận | `scripts/bazi_cli.py` |
| `ziwei-doushu/` | Tử Vi Đẩu Số | Cấu trúc lá số, 12 cung, đại hạn, lưu niên | `scripts/ziwei_cli.py` |
| `qimen-dunjia/` | Kỳ Môn Độn Giáp | Xem một việc, chọn giờ, chọn hướng | `scripts/qimen_cli.py` |
| `liuyao/` | Lục Hào | Một việc một quẻ, dụng thần, thế ứng, hào động | `scripts/liuyao_cli.py` |
| `numerology/` | Thần số học (Pythagoras) | Số chủ đạo, biểu đồ ngày sinh, đỉnh cao, năm cá nhân | `scripts/numerology_cli.py` |

Mọi phép tính (đổi lịch, lập lá số, gieo quẻ) do script Python làm; mô hình chỉ hỏi thông tin và diễn giải. Người dùng Việt Nam nói ngày âm thì script tính theo âm lịch Việt Nam (`calendar_locale: vn`).

## Cài đặt nhanh

Trong Claude Code:

```bash
/plugin install numerologist-skills --marketplace FANzR-arch/Numerologist_skills
```

Cần Python 3.11 trở lên; bốn hệ Trung Hoa cần thêm `lunar_python` và `tzdata` (Thần số học chỉ cần Python). Nếu dùng bản fork, thay `FANzR-arch/Numerologist_skills` bằng repo của bạn. Cách dùng qua MCP server (Claude Desktop), các lựa chọn cách tính và xử lý sự cố: xem [hướng dẫn sử dụng](docs/user-guide.vi.md).

## Đối chiếu nguồn

Các quy tắc tính được đối chiếu với kinh điển và sách in (Kinh Phòng, 增刪卜易, 淵海子平, 三命通會, 紫微斗數全書, 奇門遁甲統宗, sách của Phillips, Decoz…), kèm ca kiểm tra lấy từ ví dụ trong sách. Phần diễn giải trong `references/` ghi nguồn cho từng mục; mục nào chưa đối chiếu sách thì có nhãn, và skill sẽ nói rõ khi dùng tới. Chi tiết (tiếng Anh): [docs/source-audit-plan.md](docs/source-audit-plan.md) và [audit/README.md](audit/README.md).

## Lưu ý

Kết quả chỉ để tham khảo, không thay cho lời khuyên y tế, pháp lý, tài chính.
