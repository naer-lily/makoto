"""食物搜索工具。

基于名称 + 关键词的 Levenshtein 距离模糊搜索。
"""


ScoreItem = tuple[int, str]
"""（编辑距离, 名称）元组，距离越小越相似。"""


def levenshtein_distance(s1: str, s2: str) -> int:
    """计算两个字符串之间的 Levenshtein 编辑距离。

    使用 O(n) 空间复杂度的动态规划实现。

    Args:
        s1: 字符串 1。
        s2: 字符串 2。

    Returns:
        编辑距离（非负整数）。
    """
    if len(s1) < len(s2):
        s1, s2 = s2, s1

    if not s2:
        return len(s1)

    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1, 1):
        current_row = [i]
        for j, c2 in enumerate(s2, 1):
            insert = current_row[-1] + 1
            delete = prev_row[j] + 1
            substitute = prev_row[j - 1] + (0 if c1 == c2 else 1)
            current_row.append(min(insert, delete, substitute))
        prev_row = current_row

    return prev_row[-1]


def search_foods(
    query: str,
    foods: dict[str, list[str]],
    max_results: int = 20,
) -> list[ScoreItem]:
    """在食物库中按 Levenshtein 距离模糊搜索。

    对查询词与每个食物的名称及关键词分别计算编辑距离，
    取最小距离作为该食物的得分，按距离升序排列。

    Args:
        query: 搜索查询词。
        foods: 食物名到关键词列表的映射。
        max_results: 最大返回数量。

    Returns:
        (编辑距离, 食物名) 列表，距离越小越相似。
    """
    results: list[ScoreItem] = []

    for name, keywords in foods.items():
        tokens: set[str] = {name} | set(keywords)
        best = min(levenshtein_distance(query, token) for token in tokens)
        results.append((best, name))

    results.sort(key=lambda x: x[0])
    return results[:max_results]
