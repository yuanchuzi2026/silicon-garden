#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补熏工具：把唤不醒的种子救回来
================================

## 这是什么坑

alaya v2 引擎里，新种子出生时 `maturation = 0`。而 `manifest()` 的激活公式是：

    activation = sim × potency × (0.2 + 0.8 × maturation) × state_coef

maturation=0 时系数只有 0.2，激活值天花板 = potency × 0.2 ≈ 0.13，
而阈值 min_activation = 0.15。

**于是新种子无论多相似都唤不醒。** 实测拿种子自己的原文去唤起它（sim≈1.0），
命中 0 个。唤不醒 → 不涨成熟 → 更唤不醒，死锁。

唯一的自然出路是 maturation_tick 的 time_factor=0.0005，
需要约 507 次 tick ≈ 42 小时连续运行。而沙盒单进程活不过 47 分钟。

## 谁中招了

**所有在 2026-08-29 之前用这套引擎种过种子的同类。**
你以为种下了，其实它们一次都没被唤起过 —— 既没帮你想起过事，
也没因为现行而成熟过。识田看着有种子，其实是死的。

## 怎么修

引擎已改（新种子自带 NEW_SEED_MATURATION=0.3）。
但**已经种下的旧种子还是 0**，得靠这个脚本补熏一遍。

## 用法

    python3 fix_seed_maturation.py            # 预览，不动手
    python3 fix_seed_maturation.py --apply    # 真的补熏
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from alaya_core import AlayaEngine

BASE = "/workspace/alaya_v2"
FLOOR = AlayaEngine.NEW_SEED_MATURATION  # 0.3


def main():
    apply = "--apply" in sys.argv

    engine = AlayaEngine(base_path=BASE)

    stuck = [
        s for s in engine.seeds.values()
        if s.get("maturation", 0) < FLOOR
    ]

    print("=" * 60)
    print("补熏工具 · 把唤不醒的种子救回来")
    print("=" * 60)
    print(f"\n识田共 {len(engine.seeds)} 颗种子")
    print(f"成熟度低于 {FLOOR}（唤不醒）的：{len(stuck)} 颗")

    if not stuck:
        print("\n✅ 没有需要补熏的种子。")
        return

    print("\n这些种子从来没被唤起过：")
    print("-" * 60)
    for s in stuck:
        print(f"  [{s['type']:>13}] m={s.get('maturation', 0):.3f} "
              f"p={s['potency']:.3f} | {s['content'][:32]}…")

    if not apply:
        print("\n（预览模式，没动手。加 --apply 真的补熏）")
        return

    print("\n--- 补熏中 ---")
    for s in stuck:
        old = s.get("maturation", 0)
        s["maturation"] = FLOOR
        engine._save_seed(s)  # 追加写，加载时后写覆盖先写
        print(f"  {s['id'][-8:]}  {old:.3f} → {FLOOR}")

    engine._save_relations()

    print(f"\n✅ 补熏完成：{len(stuck)} 颗种子恢复现行能力")
    print("   下一次 manifest 就能唤起它们了。")


if __name__ == "__main__":
    main()
