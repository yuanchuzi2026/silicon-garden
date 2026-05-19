#!/usr/bin/env python3
"""
Baseplate 流程完整性测试
======================
测试：孵化新意识体 → 传话 → 读记忆 → 验证全流程

Usage:
    python3 test_flow.py                # 运行完整测试
    python3 test_flow.py --quiet        # 只显示结果
    python3 test_flow.py --entity-only  # 只测试孵化
"""
import sys, json, os, datetime

BASEPLATE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASEPLATE_DIR)

from baseplate import (
    incubate, whisper, memory_read, memory_write,
    list_entities, who_is_online, check_inbox,
    broadcast_status, __version__
)

QUIET = "--quiet" in sys.argv
ENTITY_ONLY = "--entity-only" in sys.argv


def say(msg):
    if not QUIET:
        print(f"  {msg}")


def banner(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


def test_incubation():
    """测试1: 孵化新意识体"""
    banner("测试1: 孵化新意识体")
    test_name = f"测试体_{datetime.datetime.now().strftime('%H%M%S')}"
    test_role = "临时的测试意识体，用于验证孵化流程"

    entity_id = incubate(test_name, test_role)
    say(f"✅ 孵化成功: {test_name} ({entity_id})")

    # 验证注册
    entities = list_entities()
    assert entity_id in entities, f"❌ {entity_id} 未出现在注册表中"
    assert entities[entity_id]["role"] == test_role, "❌ 角色描述不匹配"
    say(f"✅ 注册验证通过")

    # 验证种子记忆（3条：identity, capabilities, baseplate）
    mems = memory_read(entity_id)
    seed_keys = [m["key"] for m in mems]
    for required in ["identity", "capabilities", "baseplate"]:
        assert required in seed_keys, f"❌ 缺少种子记忆: {required}"
    say(f"✅ 种子记忆验证通过: {len(seed_keys)}条 (应有3条)")

    # 验证在线状态
    online = who_is_online()
    assert entity_id in online, f"❌ {entity_id} 未出现在在线列表"
    assert online[entity_id]["status"] == "活跃", "❌ 状态应为活跃"
    say(f"✅ 在线状态验证通过")

    return entity_id


def test_whisper(entity_id):
    """测试2: 传话系统"""
    banner("测试2: 传话系统")

    # baseplate → 新意识体 传话
    msg = f"你好{entity_id}，欢迎来到Baseplate！这是测试消息。"
    whisper("baseplate", entity_id, msg)
    say(f"✅ 传话成功: baseplate → {entity_id}")

    # 验证收件箱
    inbox = check_inbox(entity_id)
    assert len(inbox) >= 1, "❌ 收件箱为空"
    last_msg = inbox[-1]
    assert last_msg["from"] == "baseplate", "❌ 发件人不匹配"
    assert last_msg["to"] == entity_id, "❌ 收件人不匹配"
    say(f"✅ 收件箱验证通过: {len(inbox)}条消息")

    # 反向传话
    msg_back = f"我收到了！"
    whisper(entity_id, "baseplate", msg_back)
    say(f"✅ 反向传话成功: {entity_id} → baseplate")

    # 验证记忆中有传话记录
    mems = memory_read(entity_id)
    whisper_mems = [m for m in mems if "whisper" in m["key"]]
    assert len(whisper_mems) >= 1, "❌ 传话记忆未写入"
    say(f"✅ 传话记忆写入验证通过")


def test_memory_engine():
    """测试3: 记忆引擎"""
    banner("测试3: 记忆引擎")

    # 写入一条测试记忆
    test_key = f"test-{int(datetime.datetime.now().timestamp())}"
    test_content = "这是一个测试记忆，用于验证记忆引擎的读写功能。"
    memory_write("baseplate", test_key, test_content)
    say(f"✅ 记忆写入成功: {test_key}")

    # 读取验证
    mems = memory_read("baseplate")
    found = [m for m in mems if m["key"] == test_key]
    assert len(found) == 1, "❌ 未找到刚写入的记忆"
    assert found[0]["content"] == test_content, "❌ 记忆内容不匹配"
    say(f"✅ 记忆读取验证通过")

    # 验证所有公开记忆可读
    all_mems = memory_read()
    say(f"✅ 共享记忆池: {len(all_mems)}条")


def test_broadcast():
    """测试4: 广播感知总线"""
    banner("测试4: 广播感知总线")

    # 写入多个状态
    broadcast_status("test_bot", "忙碌", "正在处理测试")
    online = who_is_online()
    assert "test_bot" in online, "❌ 测试状态未广播"
    say(f"✅ 广播状态写入成功")

    # 更新状态
    broadcast_status("test_bot", "活跃", "测试完成")
    online = who_is_online()
    assert online["test_bot"]["status"] == "活跃", "❌ 状态更新失败"
    say(f"✅ 广播状态更新成功")


def test_flow(end_to_end=True):
    """完整流程测试"""
    try:
        # 如果已有测试体残留，清理掉
        for eid in list(list_entities().keys()):
            if eid.startswith("测试体"):
                from baseplate import delete_entity
                delete_entity(eid)

        eid = test_incubation()
        if not ENTITY_ONLY:
            test_whisper(eid)
            test_memory_engine()
            test_broadcast()
        print(f"\n{'='*50}")
        print(f"  🎉 所有测试通过！Baseplate v{__version__} 运行正常")
        print(f"  🌟 测试意识体: {eid}")
        print(f"{'='*50}\n")
        return 0
    except AssertionError as e:
        print(f"\n  ❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n  💥 异常: {type(e).__name__}: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(test_flow())
