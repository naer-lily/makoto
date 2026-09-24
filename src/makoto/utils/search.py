"""食物搜索工具。

基于名称 + 关键词的 Levenshtein 距离模糊搜索。
"""

ScoreItem = tuple[int, str]
"""（编辑距离, 名称）元组，距离越小越相似。"""


_EXACT_RANK = 0
"""查询词与候选词完全相等。"""

_SUBSTRING_RANK = 1
"""查询词是候选词的子串。"""

_FUZZY_RANK = 2
"""仅靠编辑距离相近，没有字面包含关系。"""


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


def _match_rank(query: str, tokens: set[str]) -> int:
    """判断查询词相对某个食物全部候选词的最佳匹配档位。

    档位越小越优先：完全相等优于「查询词是候选词的子串」，两者都优于
    仅靠编辑距离相近。子串判定忽略大小写，便于英文关键词（如 beef / Beef）。

    Args:
        query: 搜索查询词。
        tokens: 该食物的名称与全部关键词。

    Returns:
        匹配档位（0 = 完全相等，1 = 子串命中，2 = 仅距离相近）。
    """
    folded = query.casefold()
    folded_tokens = [token.casefold() for token in tokens]
    if folded in folded_tokens:
        return _EXACT_RANK
    if any(folded in token for token in folded_tokens):
        return _SUBSTRING_RANK
    return _FUZZY_RANK


def search_foods(
    query: str,
    foods: dict[str, list[str]],
    max_results: int = 20,
) -> list[ScoreItem]:
    """在食物库中按 Levenshtein 距离模糊搜索。

    对查询词与每个食物的名称及关键词分别计算编辑距离，取最小距离作为该食物的得分。
    排序依次比较匹配档位与编辑距离：只按距离排序时，大量条目会并列同分，排序退化为
    调用方给出的顺序，真正命中的食物可能被挤出 max_results 之外，造成「搜不到 =
    不存在」的误判，因此档位优先于距离。

    并列（同档位同距离）时不额外比较名称，保持调用方传入的顺序 —— 食物库的顺序由
    建库者维护，比按名称排序更贴合实际取用习惯。

    Args:
        query: 搜索查询词。
        foods: 食物名到关键词列表的映射。
        max_results: 最大返回数量。

    Returns:
        (编辑距离, 食物名) 列表，越靠前越相似。
    """
    scored: list[tuple[int, int, str]] = []

    for name, keywords in foods.items():
        tokens: set[str] = {name} | set(keywords)
        best = min(levenshtein_distance(query, token) for token in tokens)
        scored.append((_match_rank(query, tokens), best, name))

    scored.sort(key=lambda item: (item[0], item[1]))
    return [(distance, name) for _, distance, name in scored[:max_results]]
