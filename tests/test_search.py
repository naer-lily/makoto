"""测试 utils/search.py 的食物模糊搜索排序。"""

from makoto.utils.search import search_foods


def test_search_foods_exact_match_first() -> None:
    """完全相等的候选词优先于子串命中。"""
    foods = {"高蛋白": [], "高蛋白吐司": []}

    results = search_foods("高蛋白", foods)

    assert [name for _, name in results] == ["高蛋白", "高蛋白吐司"]


def test_search_foods_keyword_exact_match_first() -> None:
    """关键词完全命中同样算最高档位。"""
    foods = {"全麦面包": ["健身面包"], "法棍": ["面包"]}

    results = search_foods("健身面包", foods)

    assert results[0] == (0, "全麦面包")


def test_search_foods_substring_beats_closer_distance() -> None:
    """子串命中优先于编辑距离更小的无关条目。

    这是查重场景的关键保证：仅按距离排序时同分条目退回字典顺序，
    含有查询词的食物会被大批并列项挤出默认的 20 条上限。
    """
    foods = {
        "鸡蛋": ["蛋白"],
        "牛奶": ["乳制品"],
        "高蛋白吐司": ["健身面包"],
    }

    results = search_foods("高蛋白", foods)

    assert results[0] == (2, "高蛋白吐司")


def test_search_foods_exact_match_ignores_case() -> None:
    """档位判定忽略大小写，英文查询词不会因大小写落到低档位。"""
    foods = {"BEEF": [], "beef stew": [], "pork": []}

    results = search_foods("beef", foods)

    assert [name for _, name in results][:2] == ["BEEF", "beef stew"]


def test_search_foods_ties_keep_library_order() -> None:
    """同档同距离时保持食物库顺序，不打乱建库者维护的次序。"""
    foods = {"xyz": [], "abc": [], "def": []}

    results = search_foods("ghi", foods)

    assert [name for _, name in results] == ["xyz", "abc", "def"]


def test_search_foods_respects_max_results() -> None:
    """截断发生在排序之后，保留的是最相似的前若干条。"""
    foods = {f"食物{n}": [] for n in range(5)}

    results = search_foods("食物", foods, max_results=3)

    assert [name for _, name in results] == ["食物0", "食物1", "食物2"]
