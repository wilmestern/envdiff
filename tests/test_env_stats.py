"""Tests for envdiff.env_stats."""
from envdiff.env_stats import EnvStats, compute_stats, format_stats_text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _env(**kwargs: str):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# TestComputeStats
# ---------------------------------------------------------------------------

class TestComputeStats:
    def test_empty_env_returns_zeros(self):
        stats = compute_stats({})
        assert stats.total == 0
        assert stats.sensitive_count == 0
        assert stats.plain_count == 0
        assert stats.empty_value_count == 0

    def test_counts_total_keys(self):
        stats = compute_stats({"A": "1", "B": "2", "C": "3"})
        assert stats.total == 3

    def test_detects_sensitive_keys(self):
        stats = compute_stats({"DB_PASSWORD": "secret", "APP_NAME": "myapp"})
        assert stats.sensitive_count == 1
        assert stats.plain_count == 1

    def test_counts_empty_values(self):
        stats = compute_stats({"KEY_A": "", "KEY_B": "", "KEY_C": "value"})
        assert stats.empty_value_count == 2

    def test_prefix_breakdown_single_underscore(self):
        stats = compute_stats({"APP_HOST": "x", "APP_PORT": "80", "DB_HOST": "y"})
        assert stats.prefixes["APP"] == 2
        assert stats.prefixes["DB"] == 1

    def test_prefix_for_key_without_underscore(self):
        stats = compute_stats({"HOME": "/root"})
        assert stats.prefixes["HOME"] == 1

    def test_longest_key(self):
        stats = compute_stats({"SHORT": "a", "MUCH_LONGER_KEY": "b"})
        assert stats.longest_key == "MUCH_LONGER_KEY"

    def test_longest_value_key(self):
        stats = compute_stats({"A": "short", "B": "a much longer value here"})
        assert stats.longest_value_key == "B"

    def test_longest_key_empty_env(self):
        stats = compute_stats({})
        assert stats.longest_key == ""
        assert stats.longest_value_key == ""

    def test_as_dict_contains_expected_keys(self):
        stats = compute_stats({"X_Y": "v"})
        d = stats.as_dict()
        assert "total" in d
        assert "sensitive_count" in d
        assert "plain_count" in d
        assert "empty_value_count" in d
        assert "prefixes" in d
        assert "longest_key" in d
        assert "longest_value_key" in d

    def test_as_dict_prefixes_sorted(self):
        stats = compute_stats({"Z_A": "1", "A_B": "2"})
        keys = list(stats.as_dict()["prefixes"].keys())
        assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# TestFormatStatsText
# ---------------------------------------------------------------------------

class TestFormatStatsText:
    def test_contains_total(self):
        stats = compute_stats({"A": "1"})
        text = format_stats_text(stats)
        assert "Total keys" in text
        assert "1" in text

    def test_contains_prefix_section(self):
        stats = compute_stats({"APP_HOST": "x"})
        text = format_stats_text(stats)
        assert "Prefix breakdown" in text
        assert "APP" in text

    def test_empty_env_shows_none_for_longest(self):
        stats = EnvStats()
        text = format_stats_text(stats)
        assert "(none)" in text
