# Thuật ngữ chung Hán → Việt

Dùng khi trả lời người dùng nói tiếng Việt. Script luôn xuất tiếng Trung; khi viết cho người dùng, đổi sang âm Hán Việt dưới đây. Lần đầu nêu một thuật ngữ thì ghi chữ Hán trong ngoặc, ví dụ "Nhật chủ (日主)".

## Thiên can 天干

| Hán | Việt | Âm dương | Ngũ hành |
|---|---|---|---|
| 甲 | Giáp | Dương | Mộc |
| 乙 | Ất | Âm | Mộc |
| 丙 | Bính | Dương | Hỏa |
| 丁 | Đinh | Âm | Hỏa |
| 戊 | Mậu | Dương | Thổ |
| 己 | Kỷ | Âm | Thổ |
| 庚 | Canh | Dương | Kim |
| 辛 | Tân | Âm | Kim |
| 壬 | Nhâm | Dương | Thủy |
| 癸 | Quý | Âm | Thủy |

## Địa chi 地支

| Hán | Việt | Con giáp ở Việt Nam |
|---|---|---|
| 子 | Tý | Chuột |
| 丑 | Sửu | Trâu |
| 寅 | Dần | Hổ |
| 卯 | Mão (miền Nam: Mẹo) | Mèo (Trung Quốc là Thỏ) |
| 辰 | Thìn | Rồng |
| 巳 | Tỵ | Rắn |
| 午 | Ngọ | Ngựa |
| 未 | Mùi | Dê |
| 申 | Thân | Khỉ |
| 酉 | Dậu | Gà |
| 戌 | Tuất | Chó |
| 亥 | Hợi | Lợn |

Can chi ghép đọc liền: 甲子 Giáp Tý, 乙丑 Ất Sửu, 庚午 Canh Ngọ.

## Ngũ hành 五行

金 Kim · 木 Mộc · 水 Thủy · 火 Hỏa · 土 Thổ. Sinh 生: sinh. Khắc 克: khắc.

## Lịch pháp

| Hán | Việt |
|---|---|
| 农历 | âm lịch |
| 公历 | dương lịch |
| 闰月 | tháng nhuận |
| 正月 / 腊月 | tháng Giêng / tháng Chạp |
| 初一 / 十五 | mùng 1 / rằm |
| 节气 | tiết khí |
| 立春 | Lập Xuân |
| 冬至 | Đông Chí |
| 时辰 | canh giờ (giờ âm, mỗi giờ 2 tiếng) |
| 子时 | giờ Tý (23:00–00:59) |
| 真太阳时 | giờ mặt trời thực |
| 夏令时 | giờ mùa hè |
| 虚岁 | tuổi mụ |
| 旬空 / 空亡 | Tuần không / Không vong |

## Âm lịch Việt Nam

- Từ tháng 11 âm năm Đinh Mùi (12/1967), âm lịch Việt Nam tính theo múi giờ UTC+7, khác Trung Quốc (UTC+8). Vài tháng mỗi thập kỷ lệch một ngày, có năm lệch cả tháng (Tết Ất Sửu 1985: Việt Nam 21/1, Trung Quốc 20/2).
- Người dùng Việt Nam nói ngày âm thì truyền `"calendar_locale": "vn"` cho script. Người dùng nói theo lịch Trung Quốc, hoặc dùng phần mềm Trung Quốc, thì giữ mặc định `cn`.
- Miền Nam dùng giờ đồng hồ UTC+8 đến 13/6/1975. Âm lịch miền Nam vẫn theo lịch truyền thống (kinh tuyến Bắc Kinh), nên Tết 1968 miền Nam là 30/1, miền Bắc là 29/1. Các năm 1969–1975 chưa có nguồn xác nhận. Script cảnh báo cho giai đoạn này, cần hỏi người dùng sinh ở miền nào.
- Trước 1967, Việt Nam dùng lịch Trung Quốc theo kinh tuyến Bắc Kinh; script đang tính theo 120°Đ, có thể lệch một ngày ở vài tháng (chưa sửa, xem `audit/rules.json`).
