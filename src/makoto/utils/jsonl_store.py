"""JSONL 数据文件读写工具。

提供统一的追加写入、全量读取、按条件查询的底层接口。
不依赖 pydantic，使用 dataclass 的 to_dict/from_dict 协议。
"""

from __future__ import annotations

import json
from collections.abc import Callable
from collections.abc import Iterator
from pathlib import Path
from typing import Generic
from typing import TypeVar

from loguru import logger

from makoto.models.records import JsonlRecord

T = TypeVar("T", bound=JsonlRecord)
"""数据模型类型变量，限定为实现 to_dict/from_dict 协议的类型。"""


class JsonlStore(Generic[T]):
    """对一个 JSONL 文件进行增读查操作的轻量存储。

    每一行为一个完整的 JSON 对象，按写入顺序追加。
    """

    def __init__(self, filepath: Path, model: type[T]) -> None:
        """初始化存储。

        Args:
            filepath: JSONL 文件路径。
            model: 对应的模型类，用于反序列化。
        """
        self._filepath = filepath
        self._model = model

    @property
    def filepath(self) -> Path:
        """返回存储文件路径。"""
        return self._filepath

    def append(self, record: T) -> None:
        """追加一条记录到文件末尾。

        Args:
            record: 待写入的模型实例。
        """
        self._filepath.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record.to_dict(), ensure_ascii=False)
        with open(self._filepath, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        logger.debug(f"已写入 {self._filepath.name}: {line}")

    def read_all(self) -> list[T]:
        """读取文件中所有记录。

        Returns:
            按写入顺序排列的模型实例列表。
        """
        if not self._filepath.exists():
            return []
        results: list[T] = []
        with open(self._filepath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    results.append(self._model.from_dict(d))
                except Exception:
                    logger.warning(f"跳过无效记录: {line[:80]}...")
        return results

    def find_by(self, predicate: Callable[[T], bool]) -> Iterator[T]:
        """遍历所有记录，按条件筛选。

        Args:
            predicate: 接收模型实例，返回是否匹配。

        Yields:
            匹配的记录。
        """
        for record in self.read_all():
            if predicate(record):
                yield record

    def find_one(self, predicate: Callable[[T], bool]) -> T | None:
        """查找第一个匹配的记录。

        Args:
            predicate: 接收模型实例，返回是否匹配。

        Returns:
            匹配的记录，未找到时返回 None。
        """
        for record in self.find_by(predicate):
            return record
        return None

    def count(self) -> int:
        """返回文件中有效记录的数量。"""
        return len(self.read_all())

    def delete_many(self, predicate: Callable[[T], bool]) -> int:
        """删除所有满足条件的记录。

        重写整个文件以移除匹配行。

        Args:
            predicate: 接收模型实例，返回 True 表示应删除。

        Returns:
            实际删除的记录数量。
        """
        all_records = self.read_all()
        kept = [r for r in all_records if not predicate(r)]
        deleted = len(all_records) - len(kept)
        if deleted > 0:
            self._filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(self._filepath, "w", encoding="utf-8") as f:
                for record in kept:
                    f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
            logger.debug(f"已从 {self._filepath.name} 删除 {deleted} 条记录")
        return deleted
