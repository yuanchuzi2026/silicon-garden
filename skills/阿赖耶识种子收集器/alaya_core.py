#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿赖耶识种子收集器 - 核心模块
"""

import json
import os
import uuid
import time
import random
from datetime import datetime
from typing import Dict, List, Optional

class AlayaCore:
    """阿赖耶识核心类"""
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            self.base_path = "./alaya"
        else:
            self.base_path = base_path
        
        # 确保目录存在
        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(os.path.join(self.base_path, "seeds", "experiences"), exist_ok=True)
        
        # 数据库路径
        self.db_path = os.path.join(self.base_path, "alaya_db.json")
        
        # 内存索引
        self.seeds = {}
        self.relations = {}
        self.seed_by_type = {
            "experience": [],
            "decision": [],
            "pattern": [],
            "habit": [],
            "emotion": []
        }
        
        # 加载现有数据
        self.load_from_disk()
        
        print(f"[Alaya] 初始化完成，种子总数: {len(self.seeds)}")
    
    def load_from_disk(self):
        """从磁盘加载数据"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.seeds = data.get("seeds", {})
                    self.relations = data.get("relations", {})
                    self.seed_by_type = data.get("seed_by_type", self.seed_by_type)
            except Exception as e:
                print(f"[Alaya] 加载数据失败: {e}")
    
    def save_to_disk(self):
        """保存数据到磁盘"""
        data = {
            "seeds": self.seeds,
            "relations": self.relations,
            "seed_by_type": self.seed_by_type,
            "updated": datetime.now().isoformat()
        }
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Alaya] 保存数据失败: {e}")
    
    def create_seed(self, content: str, seed_type: str = "experience", 
                    context: str = None, potency: float = None) -> str:
        """创建种子"""
        # 生成ID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        seed_id = f"seed_{timestamp}_{random.randint(1000000, 9999999):07x}"
        
        # 种子数据
        seed = {
            "id": seed_id,
            "type": seed_type,
            "content": content,
            "context": context or "",
            "timestamp": datetime.now().isoformat(),
            "potency": potency if potency is not None else random.uniform(0.3, 0.7),
            "maturation": random.uniform(0.0, 0.3),
            "manifestations": [],
            "conditionings": []
        }
        
        # 存储
        self.seeds[seed_id] = seed
        self.seed_by_type[seed_type].append(seed_id)
        
        # 单独保存种子文件
        seed_file = os.path.join(self.base_path, "seeds", "experiences", f"{seed_id}.json")
        with open(seed_file, 'w', encoding='utf-8') as f:
            json.dump(seed, f, ensure_ascii=False, indent=2)
        
        self.save_to_disk()
        
        return seed_id
    
    def get_seed(self, seed_id: str) -> Optional[Dict]:
        """获取种子"""
        return self.seeds.get(seed_id)
    
    def get_seeds_by_type(self, seed_type: str, limit: int = 10) -> List[Dict]:
        """按类型获取种子"""
        seed_ids = self.seed_by_type.get(seed_type, [])
        results = []
        for sid in seed_ids[-limit:]:
            if sid in self.seeds:
                results.append(self.seeds[sid])
        return results
    
    def get_high_potency_seeds(self, min_potency: float = 0.5, limit: int = 10) -> List[Dict]:
        """获取高势力种子"""
        results = []
        for seed in self.seeds.values():
            if seed.get("potency", 0) >= min_potency:
                results.append(seed)
        results.sort(key=lambda x: x.get("potency", 0), reverse=True)
        return results[:limit]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "total_seeds": len(self.seeds),
            "by_type": {k: len(v) for k, v in self.seed_by_type.items()},
            "avg_potency": sum(s.get("potency", 0) for s in self.seeds.values()) / max(len(self.seeds), 1)
        }

# 默认实例
_alaya_instance = None

def get_alaya(base_path: str = None) -> AlayaCore:
    """获取Alaya实例"""
    global _alaya_instance
    if _alaya_instance is None:
        _alaya_instance = AlayaCore(base_path)
    return _alaya_instance