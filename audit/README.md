# Sổ audit theo nguồn

> **English summary.** This directory checks every calculation rule and reference section against books and standards. `rules.json` holds one entry per audit unit (constant table, function, `ruleset` field, doc file), extracted automatically by `python3 tools/audit.py sync`, with a verdict (`unverified`, `confirmed`, `variant`, `conflict`, `not_applicable`), cited sources and locators. `confirmed` requires at least one T1/T2 source and two independent lineages; blogs never count. `sources.json` lists the sources with tier, lineage and edition. `cases/<engine>/*.json` are golden cases copied from worked examples in those books and run by `audit/tests/test_golden_cases.py`. CI runs `python3 tools/audit.py check`, which fails when the registry is out of sync with the code or malformed. The rest of this file is in Vietnamese.

Kế hoạch tổng: `docs/ke-hoach-audit-nguon.md`.

| File | Nội dung | Ai sửa |
|---|---|---|
| `rules.json` | Mỗi đơn vị audit một mục: bảng hằng số, hàm, mục `ruleset`, file tài liệu | `tools/audit.py sync` sinh khung; người thực hiện điền `claim`, `sources`, `verdict`, `notes`, `tests` |
| `sources.json` | Thư mục nguồn: tầng T1–T4, ngôn ngữ, dòng dõi (`lineage`), ấn bản | Người thực hiện |
| `cases/<engine>/<id>.json` | Ca vàng chép từ ví dụ in trong sách | Người thực hiện |

## Lệnh

```bash
python3 tools/audit.py sync
```

Chạy sau mỗi lần sửa code hoặc tài liệu trong skill. Lệnh này thêm đơn vị mới, xoá đơn vị không còn, cập nhật vị trí và fingerprint. Phần người điền được giữ nguyên.

```bash
python3 tools/audit.py check
```

CI chạy lệnh này. Fail khi sổ chưa đồng bộ với code hoặc sai cấu trúc. Lệnh in bảng độ phủ theo engine, và liệt kê các mục `stale`: đã audit, nhưng code đổi sau đó nên cần audit lại. Audit lại xong thì sửa `stale` thành `false` trong `rules.json`. Chỉ dịch dòng code thì không tính là thay đổi.

Đổi tên hàm hoặc hằng số sẽ tạo đơn vị mới; đơn vị cũ bị xoá và in ra ở mục `removed` khi `sync`. Nếu đơn vị cũ đã audit thì chép phần đã điền sang id mới.

## Điền một mục

```json
{
  "id": "liuyao.table.NAJIA",
  "claim": "Nạp giáp Kinh Phòng: Càn nội 甲子 甲寅 甲辰, ngoại 壬午 壬申 壬戌; …",
  "sources": [
    {"id": "jingshi-yizhuan", "locator": "<ấn bản>, quyển …, tr. …", "stance": "agree"},
    {"id": "zengshan-buyi", "locator": "<ấn bản>, chương …, tr. …", "stance": "agree"}
  ],
  "verdict": "confirmed",
  "notes": "",
  "tests": ["liuyao/scripts/tests/test_liuyao_cli.py::TestNajiaAndLiuqin"]
}
```

`verdict`:

- `unverified`: chưa đối chiếu. Đây là mặc định.
- `confirmed`: cần ít nhất 1 nguồn T1/T2 và 2 nguồn khác `lineage`.
- `variant`: các nguồn có dị bản. Quy tắc phải là tham số trong script; `sources` ghi nguồn của từng phía.
- `conflict`: code khác nguồn và chưa sửa. Ghi rõ trong `notes`.
- `not_applicable`: không phải quy tắc thuật số (parse input, I/O). Bắt buộc có `notes`.

Quy định:

- Chỉ ghi `locator` (ấn bản, quyển, trang) khi đã thực sự đọc trang đó.
- Không chép nguyên văn dài, không đưa bản scan vào repo.
- Blog không phải nguồn.
- Khi đã có ấn bản cụ thể thì điền `edition`, `access` trong `sources.json`, và đặt `verified: true`.

## Ca vàng

```json
{
  "source": {"id": "zengshan-buyi", "locator": "<ấn bản>, tr. …, quẻ lệ …"},
  "input": {"time": "…", "lines": [7, 8, 9, 7, 6, 8]},
  "expect": {"hexagram.name": "雷火丰", "lines.1.liuqin": "官鬼"}
}
```

`expect` dùng đường dẫn trường có dấu chấm, phần tử trong danh sách đánh số từ 0. `audit/tests/test_golden_cases.py` chạy mọi ca. Ca nào không khớp thì truy nguyên nhân: lỗi code, dị bản, hay lỗi in. Không sửa ca cho khớp với code.
