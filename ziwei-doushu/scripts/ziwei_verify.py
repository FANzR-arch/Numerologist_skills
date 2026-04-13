#!/usr/bin/env python3
"""紫微斗数 安紫微星 查表生成器与验证工具

算法来源：标准安紫微星诀
1. q = ceil(生日 / 局数)
2. r = q × 局数 - 生日  (不足数)
3. 从寅宫起1，顺数到q → 得基准宫
4. r=0 留在基准宫；r为奇数逆行r步；r为偶数(>0)顺行r步
"""

import math

DIZHI = ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑']
WUXING = {2: '水二局', 3: '木三局', 4: '金四局', 5: '土五局', 6: '火六局'}


def calc_ziwei(n, d):
    q = math.ceil(d / n)
    r = q * n - d
    base = (q - 1) % 12
    if r == 0:
        return DIZHI[base]
    elif r % 2 == 1:
        return DIZHI[(base - r + 120) % 12]
    else:
        return DIZHI[(base + r) % 12]


def print_markdown_table(n):
    table = [calc_ziwei(n, d) for d in range(1, 31)]
    print(f"**{WUXING[n]}**\n")
    # Row 1-10
    print("| 日数 | " + " | ".join(str(i) for i in range(1, 11)) + " |")
    print("|------|" + "|".join("---" for _ in range(10)) + "|")
    print("| 紫微 | " + " | ".join(table[0:10]) + " |\n")
    # Row 11-20
    print("| 日数 | " + " | ".join(str(i) for i in range(11, 21)) + " |")
    print("|------|" + "|".join("----" for _ in range(10)) + "|")
    print("| 紫微 | " + " | ".join(table[10:20]) + " |\n")
    # Row 21-30
    print("| 日数 | " + " | ".join(str(i) for i in range(21, 31)) + " |")
    print("|------|" + "|".join("----" for _ in range(10)) + "|")
    print("| 紫微 | " + " | ".join(table[20:30]) + " |\n")


if __name__ == '__main__':
    # 验证基本性质: d = k*n 时, 紫微在 寅(k=1), 卯(k=2), ...
    print("=== 基本性质验证: d=k×局数 时紫微应在 寅卯辰巳... ===\n")
    all_ok = True
    for n in [2, 3, 4, 5, 6]:
        for k in range(1, 13):
            d = k * n
            if d > 30:
                break
            expected = DIZHI[k - 1]
            actual = calc_ziwei(n, d)
            if actual != expected:
                print(f"  FAIL: {WUXING[n]} d={d}: got {actual}, expected {expected}")
                all_ok = False
    print(f"{'全部通过 ✓' if all_ok else '有错误 ✗'}\n")

    # 验证已知正确值 (文墨天机)
    r = calc_ziwei(4, 18)
    print(f"金四局 d=18: {r} (文墨天机确认应为 申) {'✓' if r == '申' else '✗'}\n")

    # 生成所有 markdown 表
    print("=== 正确的紫微星安星表 ===\n")
    for n in [2, 3, 4, 5, 6]:
        print_markdown_table(n)
