# Kế hoạch audit logic theo nguồn tài liệu đáng tin cậy

Ngày: 2026-11-22. Trạng thái: kế hoạch, chưa bắt đầu.

## Mục tiêu

Mỗi quy tắc tính toán và mỗi đoạn diễn giải trong repo phải truy được về ít nhất hai nguồn có thẩm quyền (sách gốc, chú giải học thuật, tiêu chuẩn lịch), có ghi ấn bản và vị trí trang. Blog chỉ được dùng làm đầu mối để tìm nguồn, không bao giờ là bằng chứng.

Kết quả cuối cùng là một sổ đăng ký quy tắc máy đọc được. CI kiểm sổ này, và mỗi quy tắc nối tới test dùng ví dụ in trong sách.

## 1. Hiện trạng: phần nào đang thiếu nguồn

| Phần | Nguồn hiện tại | Mức rủi ro |
|---|---|---|
| Thần số học: cách rút gọn, mũi tên, ý nghĩa số (`numerology/`) | Blog Việt Nam và trang tổng hợp tiếng Anh | Cao: toàn bộ chưa đối chiếu sách |
| Lục Hào: bảng 64 quẻ, bát cung, nạp giáp, lục thân, lục thần, phục thần, `yongshen.md` | Kiến thức của mô hình, được một mô hình khác soát lại | Cao: hai mô hình đồng ý không phải là nguồn |
| Bảng thuật ngữ Hán Việt (`thuat-ngu-*.md`), tên 64 quẻ tiếng Việt | Kiến thức của mô hình | Trung bình |
| Bát Tự: tàng can, thập thần, khởi vận (`tiangan-dizhi.md`, `bazi_cli.py`) | Bảng tham chiếu có sẵn trong repo (chưa ghi nguồn), `lunar_python` | Trung bình |
| Tử Vi: an sao, tứ hóa, miếu hãm | `calculation.md`, iztro, 《紫微斗數全書》 cho bảng miếu hãm | Trung bình; phần miếu hãm đã có nguồn |
| Kỳ Môn: định cục, trực phù/trực sử, cách cục | Quy tắc do người viết upstream đặt (`ruleset-mainline.md`) | Cao: phái khác nhau nhiều, chưa ghi nguồn |
| Âm lịch Việt Nam, tiết khí, giờ mặt trời thực | Ephemeris của `lunar_python` + Meeus + mốc Tết lịch sử | Thấp; vẫn cần nguồn chuẩn để trích |
| Phần diễn giải trong `SKILL.md` và `references/` | Tác giả upstream và mô hình | Trung bình–cao |

## 2. Phân tầng nguồn

| Tầng | Loại | Ví dụ | Dùng để |
|---|---|---|---|
| T1 | Kinh điển, sách gốc, tiêu chuẩn chính thức | 《京氏易传》, 《渊海子平》, 《紫微斗数全书》, GB/T 33661-2017 | Xác lập quy tắc |
| T2 | Chú giải học thuật, sách của tác giả uy tín có ấn bản rõ ràng, công trình toán/thiên văn | 徐乐吾《子平真诠评注》, Reingold & Dershowitz *Calendrical Calculations*, Aslaksen *The Mathematics of the Chinese Calendar* | Giải thích và chọn giữa các dị bản |
| T3 | Sách thực hành phổ thông có ISBN | Sách dịch tiếng Việt, sách Nhật, sách Anh | Ghi nhận quy ước đang phổ biến ở từng thị trường |
| T4 | Phần mềm độc lập | iztro, chương trình âm lịch của Hồ Ngọc Đức | Ca kiểm chéo; phải ghi rõ dòng dõi mã nguồn |
| — | Blog, diễn đàn, video, nội dung AI | | Chỉ làm đầu mối tìm nguồn |

Quy tắc chấp nhận:

- Một quy tắc được "xác nhận" khi có ít nhất 1 nguồn T1 hoặc T2, cộng thêm 1 nguồn độc lập khác thuộc tầng T1–T3.
- Hai phần mềm cùng dòng dõi không được tính là hai nguồn. Ví dụ: `lunar_python`, `lunar-javascript`, `lunar-typescript` và iztro (dùng `lunar-typescript`) là cùng một dòng.
- Nguồn mâu thuẫn nhau thì không chọn ngầm. Quy tắc đó thành tham số có mặc định (như `late_zi_rule`), và ghi lý do chọn mặc định kèm nguồn của từng phía.

## 3. Danh mục nguồn cần tìm, theo hệ và ngôn ngữ

Ký hiệu: ✓ là tác phẩm chắc chắn tồn tại; ấn bản, ISBN và trang cụ thể vẫn phải xác minh khi có sách trong tay. (?) là tên chưa chắc, phải kiểm trước khi đưa vào sổ.

### Lịch pháp (dùng chung)

- ✓ GB/T 33661-2017《农历的编算和颁行》: quy tắc lập âm lịch Trung Quốc, gồm định sóc, định khí, đặt tháng nhuận.
- ✓ Helmer Aslaksen, *The Mathematics of the Chinese Calendar*: có phần lịch Việt Nam và "vấn đề năm 2033".
- ✓ Edward Reingold, Nachum Dershowitz, *Calendrical Calculations*: chương âm lịch Trung Quốc, kèm thuật toán độc lập.
- ✓ Hồ Ngọc Đức, bài và chương trình về âm lịch Việt Nam (UTC+7, mốc đổi lịch 1967–1968).
- ✓ Hồng Kông Thiên văn đài (香港天文台), bảng đối chiếu dương lịch – nông lịch. ✓ Phòng tính lịch của Đài thiên văn quốc gia Nhật (国立天文台 暦計算室): thời điểm 24 tiết khí. Cả hai dùng để làm ca kiểm cho tiết khí.

### Bát Tự

- T1: ✓《渊海子平》, ✓《三命通会》 (万民英), ✓《子平真诠》 (沈孝瞻), ✓《滴天髓》, ✓《穷通宝鉴》.
- T2: ✓ 徐乐吾《子平真诠评注》và《滴天髓补注》. ✓ 任铁樵 chú《滴天髓阐微》.
- Tiếng Việt: sách dịch của Thiệu Vĩ Hoa (邵伟华), như《四柱预测学》, bản tiếng Việt "Dự đoán theo tứ trụ" (?).
- Tiếng Nhật: ✓ 阿部泰山 (hệ 四柱推命 ở Nhật).
- Tiếng Anh: ✓ Joey Yap, các sách BaZi (T3, thương mại).
- Kiểm: bảng tàng can, thập thần, trường sinh, khởi vận "3 ngày 1 năm", đại vận trước giao vận, quy tắc giờ Tý (早子/夜子).

### Tử Vi

- T1: ✓《紫微斗数全书》, ✓《紫微斗数全集》.
- T2: ✓ 王亭之 (Trung Châu phái 中州派).
- Tiếng Việt: ✓ Vân Đằng Thái Thứ Lang, *Tử Vi Đẩu Số Tân Biên*. ✓ Thiên Lương, *Tử Vi Nghiệm Lý*. Hai sách này là nền cho "phái Việt Nam" (Tuần, Triệt…).
- Tiếng Nhật: ✓ 鮑黎明 (sách 紫微斗数 viết bằng tiếng Nhật).
- Kiểm: an 14 chính tinh, phụ tinh, tứ hóa theo can năm, cách tính tháng nhuận, ngũ hành cục, mệnh chủ/thân chủ.

### Kỳ Môn

- T1: ✓《烟波钓叟歌》, ✓《奇门遁甲统宗》, ✓《御定奇门宝鉴》.
- T2: ✓ 张志春《神奇之门》.
- Tiếng Nhật: ✓ 黒門 (sách 奇門遁甲).
- Kiểm: định cục (置闰 so với 拆补), đặt trực phù và trực sử, xử lý trung cung (寄坤 và các phép khác), định nghĩa các cách cục mà script phát hiện (phục ngâm, phản ngâm, môn bách…).

### Lục Hào

- T1: ✓《京氏易传》 (gốc của bát cung, thế ứng, nạp giáp). ✓《火珠林》.
- T2: ✓《增删卜易》 (野鹤老人). ✓《卜筮正宗》 (王洪绪). ✓《易冒》.
- Tiếng Việt: bản dịch "Tăng San Bốc Dịch" và "Bốc Phệ Chính Tông" (?). Phải xác minh người dịch và nhà xuất bản.
- Kiểm: toàn bộ `HEXAGRAMS`, `NAJIA`, `GENERATIONS`, lục thần theo can ngày, quy tắc phục thần, bảng dụng thần.

### Thần số học

- T2/T3: ✓ David A. Phillips, *The Complete Book of Numerology*. Đây được cho là nguồn gốc của cách tính phổ biến ở Việt Nam (biểu đồ ngày sinh, mũi tên); cần xác nhận lại.
- T2/T3: ✓ Hans Decoz, *Numerology: Key to Your Inner Self*. ✓ Matthew Oliver Goodwin, *Numerology: The Complete Guide*. ✓ Juno Jordan, *The Romance in Your Name*. Các sách này là cách tính phương Tây "classic".
- Tiếng Việt: bản dịch sách của Phillips đang bán ở Việt Nam (?). Phải xác minh tên sách, người dịch, nhà xuất bản.
- Kiểm: cách rút gọn `vn` và `classic`, cách cộng `digits` và `components`, tên và định nghĩa các mũi tên, cách tính đỉnh cao/thử thách, quy tắc chữ Y, toàn bộ `y-nghia-so.md`.

## 4. Đơn vị audit: sổ đăng ký quy tắc

Thêm thư mục `audit/`:

```
audit/
  sources.yaml      # thư mục nguồn
  rules.yaml        # mỗi quy tắc một mục
  cases/            # ca vàng chép từ ví dụ trong sách (chỉ input, output kỳ vọng và trích dẫn)
```

`sources.yaml`, mỗi nguồn một mục:

```yaml
- id: jingshi-yizhuan
  title: 京氏易传
  author: 京房
  language: zh
  tier: T1
  edition: "<nhà xuất bản, năm, ISBN>"
  access: "ctext.org / bản giấy / ảnh chụp do người dùng cung cấp"
```

`rules.yaml`, mỗi quy tắc một mục:

```yaml
- id: liuyao.palace.generations
  engine: liuyao
  code: liuyao/scripts/liuyao_cli.py:GENERATIONS
  claim: "Bát cung: thế hào của quẻ thuần ở hào 6, nhất thế…ngũ thế ở hào 1–5, du hồn hào 4, quy hồn hào 3"
  sources:
    - {id: jingshi-yizhuan, locator: "quyển 上, tr. …", stance: agree}
    - {id: zengshan-buyi, locator: "…", stance: agree}
  verdict: confirmed        # confirmed | variant | conflict | unverified
  tests: [liuyao/scripts/tests/test_liuyao_cli.py::TestPalaces]
```

- `verdict: variant` dùng khi các nguồn có dị bản. Quy tắc đó phải là tham số trong script, và mục trong sổ ghi rõ nguồn của từng phía.
- Trích dẫn: chỉ ghi vị trí (quyển, trang) và một đoạn trích rất ngắn khi thật cần. Không chép nguyên văn dài, không đưa bản scan vào repo. Diễn giải viết bằng lời của mình.

## 5. Ca vàng từ sách

Ví dụ in sẵn trong sách là oracle mạnh nhất, vì nó độc lập với cả code lẫn mô hình. Ví dụ: lá số mẫu trong 《紫微斗数全书》, quẻ mẫu trong《增删卜易》, mệnh lệ trong《子平真诠评注》, bảng mẫu trong sách Phillips.

- Mỗi ca ghi vào `audit/cases/<engine>/<id>.json`: input, các trường output kỳ vọng, và `source` (id + vị trí trang).
- Một test tham số hoá đọc toàn bộ `audit/cases/` và chạy qua `build_output` của từng engine.
- Ca không khớp không được sửa tay cho khớp. Phải truy xem lỗi nằm ở code, ở dị bản, hay ở lỗi in của sách, rồi ghi kết luận vào `rules.yaml`.

## 6. Quy trình cho mỗi quy tắc

1. **Trích**: lấy danh sách quy tắc tự động từ code (các bảng hằng số, các trường `ruleset`) bằng một script `tools/audit_extract.py`. Không liệt kê bằng tay.
2. **Tìm nguồn**:
   - Sách cổ thuộc phạm vi công cộng: agent tìm trên ctext.org và zh.wikisource, ghi vị trí.
   - Sách còn bản quyền: người dùng cung cấp ảnh chụp các trang liên quan; agent đọc, đối chiếu và ghi vị trí.
3. **Đối chiếu**: so từng ô của bảng, không chỉ so ý chung chung.
4. **Ghi kết luận** vào `rules.yaml`. Nếu mâu thuẫn: biến quy tắc thành tham số, hoặc ghi mặc định kèm lý do.
5. **Thêm ca vàng** nếu sách có ví dụ.
6. **Review**: một agent khác kiểm lại vị trí trích dẫn trên đúng tài liệu đó, không kiểm bằng trí nhớ. Mỗi engine thêm một vòng người am hiểu đọc lại.

## 7. Công cụ và kiểm tự động

- `tools/audit_extract.py`: sinh danh sách quy tắc từ code. CI báo khi code có quy tắc mới mà sổ chưa có.
- `tools/audit_check.py` (chạy trong CI):
  - Mỗi quy tắc phải có `verdict`.
  - Quy tắc `confirmed` phải có nguồn T1 hoặc T2, cộng một nguồn độc lập.
  - Mọi `id` nguồn phải tồn tại trong `sources.yaml`.
  - Mọi `tests` được trỏ tới phải tồn tại.
- Báo cáo độ phủ: tỷ lệ quy tắc `confirmed` / `variant` / `conflict` / `unverified` theo từng engine, in trong CI và ghi vào lộ trình.
- Tận dụng những gì đã có: các test oracle số học, đối chiếu iztro (ghi rõ là T4, cùng dòng dõi với `lunar_python`), bộ eval (thêm ca kiểm diễn giải theo đúng nguồn).

## 8. Thứ tự làm (theo rủi ro và mức phụ thuộc)

| Giai đoạn | Nội dung | Xong khi |
|---|---|---|
| A0. Khung | `audit/`, schema, `audit_extract.py`, `audit_check.py`, CI ở chế độ chỉ báo | Mọi quy tắc trong code đã có mục trong sổ (phần lớn `unverified`) |
| A1. Lịch pháp | Đối chiếu GB/T 33661, Aslaksen, Hồ Ngọc Đức; ca vàng tiết khí lấy từ bảng của Đài thiên văn quốc gia Nhật và Hồng Kông Thiên văn đài | 100% quy tắc lịch `confirmed`; ca vàng về Tết VN/TQ và tháng nhuận năm 2033 |
| A2. Thần số học | Sách Phillips và 2 sách phương Tây; viết lại `y-nghia-so.md` theo nguồn | Không còn nội dung nào chỉ có nguồn blog; tên mũi tên có nguồn |
| A3. Lục Hào | 京氏易传, 增删卜易, 卜筮正宗; ca vàng là quẻ mẫu trong sách | Bảng 64 quẻ, nạp giáp, bát cung, phục thần `confirmed`; ≥10 ca vàng |
| A4. Bát Tự | Các kinh điển và chú giải của 徐乐吾; mệnh lệ in trong sách | Bảng tàng can, thập thần, khởi vận `confirmed`; ≥10 mệnh lệ |
| A5. Tử Vi | 全书/全集, 王亭之, Thái Thứ Lang | Cách an sao `confirmed`; điểm khác giữa phái Việt Nam và Tam Hợp được liệt kê và có nguồn (mở đường cho tham số `school: vn`) |
| A6. Kỳ Môn | 烟波钓叟歌, 统宗, 宝鉴, 神奇之门 | Mỗi điểm khác nhau giữa các phái thành tham số hoặc được ghi rõ |
| A7. Diễn giải | `SKILL.md` và `references/` của cả 5 hệ: mỗi khẳng định về ý nghĩa có nguồn, hoặc bị gỡ | Không còn khẳng định diễn giải nào không có nguồn |

Lịch pháp đi trước vì mọi engine đều dựa vào nó. Thần số học và Lục Hào đi ngay sau vì hiện hoàn toàn không có nguồn sách.

## 9. Phân vai

- **Agent**:
  - Trích quy tắc từ code.
  - Tìm sách cổ trên ctext.org và Wikisource.
  - Đọc ảnh chụp trang sách người dùng cung cấp.
  - Điền sổ, viết test và ca vàng.
  - Đối chiếu từng ô bảng.
  - Agent không được ghi vị trí trích dẫn mà nó chưa thực sự đọc.
- **Người dùng / chuyên gia**:
  - Mua hoặc mượn sách còn bản quyền và chụp các trang cần thiết.
  - Chốt mặc định khi các phái khác nhau.
  - Đọc duyệt phần diễn giải tiếng Việt.

## 10. Cần bạn quyết định trước khi bắt đầu A0

1. Mặc định cho người dùng Việt Nam: giữ `calendar_locale: cn` hay đổi sang `vn` khi người dùng nói tiếng Việt? Có làm phái Tử Vi Việt Nam (`school: vn`) ở A5 không?
2. Sách giấy nào bạn có hoặc mua được, nhất là bản tiếng Việt của Thiệu Vĩ Hoa, Thái Thứ Lang, Phillips và các bản dịch Lục Hào?
3. Có người am hiểu từng hệ để duyệt phần kết luận không? Hay chỉ dựa trên nguồn sách và review chéo giữa các agent?
