"""Tests for envdiff.patch module."""

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.patch import EnvPatch, build_patch, render_patch_dotenv


def _entry(key, status, left=None, right=None):
    return DiffEntry(key=key, status=status, left_value=left, right_value=right)


def _result(*entries):
    return DiffResult(entries=list(entries))


class TestBuildPatch:
    def test_added_key_goes_to_additions(self):
        diff = _result(_entry("NEW", DiffStatus.ADDED, right="val"))
        patch = build_patch(diff)
        assert "NEW" in patch.additions
        assert patch.additions["NEW"] == "val"

    def test_removed_key_goes_to_deletions(self):
        diff = _result(_entry("OLD", DiffStatus.REMOVED, left="val"))
        patch = build_patch(diff)
        assert "OLD" in patch.deletions

    def test_changed_key_goes_to_updates(self):
        diff = _result(_entry("K", DiffStatus.CHANGED, left="v1", right="v2"))
        patch = build_patch(diff)
        assert "K" in patch.updates
        assert patch.updates["K"] == "v2"

    def test_unchanged_key_ignored(self):
        diff = _result(_entry("K", DiffStatus.UNCHANGED, left="v", right="v"))
        patch = build_patch(diff)
        assert patch.is_empty

    def test_deletions_are_sorted(self):
        diff = _result(
            _entry("Z", DiffStatus.REMOVED, left="z"),
            _entry("A", DiffStatus.REMOVED, left="a"),
        )
        patch = build_patch(diff)
        assert patch.deletions == ["A", "Z"]

    def test_is_empty_true_for_no_changes(self):
        patch = EnvPatch()
        assert patch.is_empty

    def test_is_empty_false_when_additions(self):
        patch = EnvPatch(additions={"K": "v"})
        assert not patch.is_empty


class TestRenderPatchDotenv:
    def test_additions_section_present(self):
        patch = EnvPatch(additions={"FOO": "bar"})
        output = render_patch_dotenv(patch)
        assert "# --- Additions ---" in output
        assert "FOO=bar" in output

    def test_updates_section_present(self):
        patch = EnvPatch(updates={"X": "new"})
        output = render_patch_dotenv(patch)
        assert "# --- Updates ---" in output
        assert "X=new" in output

    def test_deletions_section_present(self):
        patch = EnvPatch(deletions=["GONE"])
        output = render_patch_dotenv(patch)
        assert "# --- Deletions ---" in output
        assert "# UNSET GONE" in output

    def test_empty_patch_renders_empty_string(self):
        patch = EnvPatch()
        assert render_patch_dotenv(patch) == ""

    def test_additions_are_sorted(self):
        patch = EnvPatch(additions={"Z": "1", "A": "2"})
        output = render_patch_dotenv(patch)
        a_pos = output.index("A=")
        z_pos = output.index("Z=")
        assert a_pos < z_pos

    def test_full_patch_section_order(self):
        patch = EnvPatch(
            additions={"NEW": "1"},
            updates={"UPD": "2"},
            deletions=["DEL"],
        )
        output = render_patch_dotenv(patch)
        add_pos = output.index("Additions")
        upd_pos = output.index("Updates")
        del_pos = output.index("Deletions")
        assert add_pos < upd_pos < del_pos
