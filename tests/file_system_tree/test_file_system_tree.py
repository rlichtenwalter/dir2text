"""Unit tests for the FileSystemTree class."""

import os
from pathlib import Path

import pytest

from dir2text.exclusion_rules.git_rules import GitIgnoreExclusionRules
from dir2text.file_system_tree.file_system_tree import FileSystemTree


@pytest.fixture
def temp_directory(tmp_path):
    # Create a temporary directory structure
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1" / "file1.txt").touch()
    (tmp_path / "dir2").mkdir()
    (tmp_path / "dir2" / "file2.py").touch()
    (tmp_path / "dir2" / "file2.pyc").touch()
    return tmp_path


@pytest.fixture
def temp_directory_with_symlinks(tmp_path):
    """Create a temporary directory structure with symlinks."""
    # Create directories and files
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def main(): pass")
    (tmp_path / "src" / "utils").mkdir()
    (tmp_path / "src" / "utils" / "helpers.py").write_text("def helper(): pass")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "readme.md").write_text("# Documentation")

    # Create symlinks
    try:
        # Create a symlink from "build" to "src"
        os.symlink(tmp_path / "src", tmp_path / "build")

        # Create a symlink loop
        os.symlink(tmp_path / "src", tmp_path / "src" / "utils" / "loop")

        has_symlinks = True
    except (OSError, NotImplementedError):
        # On some platforms (like Windows) creating symlinks might require special permissions
        has_symlinks = False

    return tmp_path, has_symlinks


@pytest.fixture
def temp_gitignore(temp_directory):
    gitignore_content = "*.pyc"
    gitignore_file = temp_directory / ".gitignore"
    gitignore_file.write_text(gitignore_content)
    return str(gitignore_file)


def test_file_system_tree_initialization(temp_directory):
    fs_tree = FileSystemTree(str(temp_directory))
    assert fs_tree.root_path == Path(temp_directory)
    assert fs_tree._tree is None


def test_file_system_tree_build(temp_directory):
    fs_tree = FileSystemTree(str(temp_directory))
    tree = fs_tree.get_tree()
    assert tree is not None
    assert tree.name == temp_directory.name
    assert tree.children is not None
    assert len(tree.children) == 2  # dir1 and dir2


def test_file_system_tree_with_exclusions(temp_directory, temp_gitignore):
    exclusion_rules = GitIgnoreExclusionRules(temp_gitignore)
    fs_tree = FileSystemTree(str(temp_directory), exclusion_rules)
    tree = fs_tree.get_tree()
    assert tree is not None
    assert tree.children is not None
    dir2 = next((node for node in tree.children if node.name == "dir2"), None)
    assert dir2 is not None
    assert dir2.children is not None
    assert len(dir2.children) == 1  # Only file2.py, file2.pyc is excluded


def test_file_system_tree_refresh(temp_directory):
    fs_tree = FileSystemTree(str(temp_directory))
    fs_tree.get_tree()
    (temp_directory / "new_file.txt").touch()
    fs_tree.refresh()
    tree = fs_tree.get_tree()
    assert tree is not None
    assert tree.children is not None
    assert any(node.name == "new_file.txt" for node in tree.children)


def test_file_system_tree_non_existent_directory():
    with pytest.raises(FileNotFoundError):
        FileSystemTree("/non/existent/directory").get_tree()


def test_file_system_tree_file_as_root():
    with pytest.raises(NotADirectoryError):
        FileSystemTree(__file__).get_tree()


def test_file_system_tree_empty_directory(temp_directory):
    # Test handling of empty directories
    empty_dir = temp_directory / "empty_dir"
    empty_dir.mkdir()
    fs_tree = FileSystemTree(str(temp_directory))
    tree = fs_tree.get_tree()
    assert tree is not None
    empty_node = next((node for node in tree.children if node.name == "empty_dir"), None)
    assert empty_node is not None
    assert empty_node.children == ()


def test_symlink_detection(temp_directory_with_symlinks):
    """Test that symlinks are properly detected and represented."""
    tmp_path, has_symlinks = temp_directory_with_symlinks

    if not has_symlinks:
        pytest.skip("Symlink creation not supported on this platform/environment")

    # Test with default behavior (don't follow symlinks)
    fs_tree = FileSystemTree(str(tmp_path))
    tree = fs_tree.get_tree()
    assert tree is not None

    # Get the build symlink node
    build_node = next((node for node in tree.children if node.name == "build"), None)
    assert build_node is not None
    assert build_node.is_symlink
    assert build_node.symlink_target is not None

    # Check symlink count
    assert fs_tree.get_symlink_count() == 2

    # Check tree representation
    tree_repr = fs_tree.get_tree_representation()
    assert "build → " in tree_repr
    assert "[symlink]" in tree_repr

    # Check symlink iteration
    symlinks = list(fs_tree.iterate_symlinks())
    assert len(symlinks) == 2
    symlink_paths = [s[1] for s in symlinks]  # Get relative paths
    assert "build" in symlink_paths


def test_follow_symlinks(temp_directory_with_symlinks):
    """Test following symlinks during traversal."""
    tmp_path, has_symlinks = temp_directory_with_symlinks

    if not has_symlinks:
        pytest.skip("Symlink creation not supported on this platform/environment")

    # Test with follow_symlinks=True
    fs_tree = FileSystemTree(str(tmp_path), follow_symlinks=True)
    tree = fs_tree.get_tree()
    assert tree is not None

    # Now build should be treated as a directory, not a symlink
    build_node = next((node for node in tree.children if node.name == "build"), None)
    assert build_node is not None
    assert build_node.is_dir
    assert not build_node.is_symlink

    # Check that the contents of the src directory are also under build
    assert any(node.name == "main.py" for node in build_node.children)

    # Check symlink count - should be 0 since we're following symlinks
    assert fs_tree.get_symlink_count() == 0

    # Check tree representation
    tree_repr = fs_tree.get_tree_representation()
    assert "build/" in tree_repr  # Should be shown as directory
    assert "loop/" not in tree_repr  # Loop should be detected and not followed

    # Check file iteration to verify we can access the files through symlinks
    files = list(fs_tree.iterate_files())
    file_paths = [f[1] for f in files]  # Get relative paths

    # We should have these files:
    # - src/main.py
    # - src/utils/helpers.py
    # - docs/readme.md
    # - build/main.py (same file as src/main.py)
    # - build/utils/helpers.py (same file as src/utils/helpers.py)
    assert len(files) == 5
    assert "src/main.py" in file_paths
    assert "build/main.py" in file_paths


def test_symlink_loop_detection(temp_directory_with_symlinks):
    """Test that symlink loops are properly detected and handled."""
    tmp_path, has_symlinks = temp_directory_with_symlinks

    if not has_symlinks:
        pytest.skip("Symlink creation not supported on this platform/environment")

    # Create a tree with follow_symlinks=True
    fs_tree = FileSystemTree(str(tmp_path), follow_symlinks=True)

    # Get the tree (this should not hang due to loop detection)
    tree = fs_tree.get_tree()

    # Verify the loop is detected by checking tree structure
    assert tree is not None
    # Find the loop node (utils/loop)
    loop_node = None
    for node in tree.descendants:
        if node.name == "loop" and hasattr(node, "symlink_target"):
            loop_node = node
            break

    # Assert that we found the loop node and it's properly marked
    assert loop_node is not None
    assert loop_node.is_symlink
    assert hasattr(loop_node, "symlink_target")
    assert "loop" in loop_node.symlink_target or loop_node.symlink_target == "[loop detected]"


def test_iterate_symlinks(temp_directory_with_symlinks):
    """Test iterate_symlinks method."""
    tmp_path, has_symlinks = temp_directory_with_symlinks

    if not has_symlinks:
        pytest.skip("Symlink creation not supported on this platform/environment")

    # Create tree with default settings (don't follow symlinks)
    fs_tree = FileSystemTree(str(tmp_path))

    # Iterate symlinks
    symlinks = list(fs_tree.iterate_symlinks())
    assert len(symlinks) == 2

    # Check format of symlink tuples: (abs_path, rel_path, target)
    for symlink in symlinks:
        assert len(symlink) == 3
        abs_path, rel_path, target = symlink
        assert os.path.isabs(abs_path)
        assert not os.path.isabs(rel_path)
        assert target  # Should have a target string

    # With follow_symlinks=True, iterate_symlinks should return empty
    fs_tree_follow = FileSystemTree(str(tmp_path), follow_symlinks=True)
    symlinks_follow = list(fs_tree_follow.iterate_symlinks())
    assert len(symlinks_follow) == 0


def test_symlinks_with_exclusions(temp_directory_with_symlinks):
    """Test combining symlink handling with exclusion rules."""
    tmp_path, has_symlinks = temp_directory_with_symlinks

    if not has_symlinks:
        pytest.skip("Symlink creation not supported on this platform/environment")

    # Create a temporary exclusion file
    exclusion_file = tmp_path / ".dir2textignore"
    exclusion_file.write_text("build/\n*.md\n")

    # Create exclusion rules
    rules = GitIgnoreExclusionRules(exclusion_file)

    # Create a tree with exclusions
    fs_tree = FileSystemTree(str(tmp_path), exclusion_rules=rules)

    # Check that excluded symlinks aren't in the tree
    tree = fs_tree.get_tree()
    assert tree is not None
    build_node = next((node for node in tree.children if node.name == "build"), None)
    assert build_node is None  # Should be excluded

    # Check that excluded files aren't in the iteration
    files = list(fs_tree.iterate_files())
    file_paths = [f[1] for f in files]

    assert "docs/readme.md" not in file_paths  # Should be excluded
    assert "src/main.py" in file_paths  # Should be included
    assert "src/utils/helpers.py" in file_paths  # Should be included

    # Check symlinks - build should be excluded
    symlinks = list(fs_tree.iterate_symlinks())
    symlink_paths = [s[1] for s in symlinks]
    assert "build" not in symlink_paths
    assert "src/utils/loop" in symlink_paths  # Still included


def test_iterate_and_render_order_match(tmp_path):
    """Regression (B3): file iteration order must match tree-render order.

    Before the canonical-sort pass was introduced in `_build_tree`, the tree renderer
    sorted children as (dirs-first, case-insensitive by name) while `iterate_files`
    walked children in the case-SENSITIVE byte order produced by `sorted(os.listdir(...))`.
    The two output surfaces of the same tool disagreed on order.

    This test pins the invariant: for any directory with mixed-case names, the
    filenames appearing in `get_tree_representation` must appear in the same order
    as the relative paths yielded by `iterate_files`.
    """
    (tmp_path / "B.py").touch()
    (tmp_path / "a.py").touch()
    (tmp_path / "A.py").touch()
    (tmp_path / "b.py").touch()
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "Y.py").touch()
    (sub / "x.py").touch()

    tree = FileSystemTree(str(tmp_path))

    # Extract filenames from the rendered tree in the order they appear.
    rendered_lines = tree.get_tree_representation().splitlines()
    rendered_files = []
    for line in rendered_lines[1:]:  # skip the root line
        if "── " not in line:
            continue
        name = line.split("── ", 1)[1]
        if name.endswith("/"):
            continue  # directory line
        rendered_files.append(name)

    iterated = [rel.split("/")[-1] for _abs, rel in tree.iterate_files()]

    assert iterated == rendered_files, (
        f"iterate_files order ({iterated}) disagrees with tree-render order ({rendered_files})"
    )


def test_canonical_child_order_mixed_case(tmp_path):
    """Regression (B3): canonical order is dirs-first, case-insensitive by name.

    Pins the exact ordering so a future refactor doesn't silently regress the
    key. Directories (uppercase or lowercase) come before any file, and within
    each group names are alphabetized case-insensitively.
    """
    (tmp_path / "Zeta").mkdir()  # directory, uppercase
    (tmp_path / "alpha").mkdir()  # directory, lowercase
    (tmp_path / "Beta.py").touch()  # file, uppercase
    (tmp_path / "apple.py").touch()  # file, lowercase
    (tmp_path / "Cherry.py").touch()

    tree = FileSystemTree(str(tmp_path))
    root = tree.get_tree()
    assert root is not None
    child_names = [c.name for c in root.children]
    # Directories first (alpha, Zeta — case-insensitive), then files (apple, Beta, Cherry)
    assert child_names == ["alpha", "Zeta", "apple.py", "Beta.py", "Cherry.py"]


def test_inode_not_leaked_on_permission_denied(tmp_path):
    """Regression (B1): a permission-denied directory must not leak its inode.

    Before the fix, `_create_node`'s early `return node` on a listdir PermissionError
    (IGNORE mode) skipped the `visited_inodes.remove(file_id)` cleanup. A later path
    reaching the same inode via a symlink would be falsely flagged as `[loop detected]`.

    The scenario: `forbidden/` is permission-denied; `other/link_to_forbidden` is a
    symlink pointing at it. With `follow_symlinks=True`, the symlink is a legitimate
    reference to the forbidden directory — NOT a loop. The fix must render it as a
    directory, not as a loop marker.
    """
    # Set up the forbidden directory and a symlink pointing to it from a sibling.
    forbidden = tmp_path / "forbidden"
    forbidden.mkdir()
    (forbidden / "secret.txt").write_text("nope")

    other = tmp_path / "other"
    other.mkdir()
    try:
        os.symlink(forbidden, other / "link_to_forbidden")
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation not supported on this platform")

    # Revoke read/execute permission on the forbidden directory AFTER creating
    # the symlink (permission on the symlink itself doesn't matter on Linux).
    forbidden.chmod(0)

    try:
        tree = FileSystemTree(str(tmp_path), follow_symlinks=True)
        root = tree.get_tree()
        assert root is not None

        # Locate the symlink node in the tree.
        link_node = next(
            (n for n in root.descendants if n.name == "link_to_forbidden"),
            None,
        )
        assert link_node is not None, "symlink node should appear in the tree"

        # Before the fix, the target's inode was leaked into visited_inodes by
        # forbidden/'s early return on PermissionError, so when we later reached
        # link_to_forbidden its target inode was already in the set and the
        # node was caught by the `loop_detected and is_symlink` branch — tagged
        # with symlink_target = "[loop detected]".
        #
        # With the fix, the finally clause discards the inode on every exit
        # path, so by the time we reach link_to_forbidden the set is clean:
        # no false loop. The node is created via the normal follow_symlinks
        # branch (is_symlink=False, is_dir=True) with no symlink_target tag.
        #
        # Note: the tree renderer hides [loop detected] nodes when
        # follow_symlinks=True, so we cannot assert on rendered text — we must
        # inspect the node object directly.
        symlink_target = getattr(link_node, "symlink_target", None)
        assert symlink_target != "[loop detected]", (
            f"Permission-denied inode was leaked; symlink falsely flagged as loop. "
            f"Got symlink_target={symlink_target!r}"
        )
        assert link_node.is_dir, "Followed symlink to a directory should have is_dir=True"
        assert not link_node.is_symlink, "Followed symlink should have is_symlink=False (replaced with target)"
    finally:
        # Restore permissions so pytest can clean up tmp_path.
        forbidden.chmod(0o755)


def test_directory_count_flat_directory(tmp_path):
    """Test directory_count is 0 (not -1) for a flat directory with only files."""
    (tmp_path / "a.txt").touch()
    (tmp_path / "b.txt").touch()
    tree = FileSystemTree(str(tmp_path))
    assert tree.get_directory_count() == 0
    assert tree.get_file_count() == 2


def test_directory_exclusion_with_trailing_slash(temp_directory):
    """Test that directory patterns with trailing slash properly exclude directories from tree.

    This is a regression test for a bug where directory-only patterns like 'mydir/' would
    exclude the contents but still show empty directories in the tree output.
    """
    # Create test structure: mydir/subdir/file.txt and mydir/file2.txt
    test_dir = temp_directory / "mydir"
    test_subdir = test_dir / "subdir"
    test_subdir.mkdir(parents=True)

    (test_dir / "file2.txt").write_text("content2")
    (test_subdir / "file.txt").write_text("content1")
    (temp_directory / "regular_file.txt").write_text("regular content")

    # Create exclusion rules with trailing slash (directory-only pattern)
    rules = GitIgnoreExclusionRules()
    rules.add_rule("mydir/")

    # Create tree with exclusion rules
    fs_tree = FileSystemTree(str(temp_directory), exclusion_rules=rules)
    tree = fs_tree.get_tree()
    assert tree is not None

    # The mydir directory should NOT appear in the tree at all
    mydir_in_tree = any(node.name == "mydir" for node in tree.children)
    assert not mydir_in_tree, "Directory 'mydir' should be completely excluded from tree"

    # Files inside mydir should not be iterable
    files = list(fs_tree.iterate_files())
    file_paths = [f[1] for f in files]

    assert "mydir/file2.txt" not in file_paths, "Files inside excluded directory should not be listed"
    assert "mydir/subdir/file.txt" not in file_paths, "Nested files inside excluded directory should not be listed"
    assert "regular_file.txt" in file_paths, "Regular files should still be listed"

    # Tree representation should not show the excluded directory
    tree_repr = fs_tree.get_tree_representation()
    assert "mydir" not in tree_repr, "Excluded directory should not appear in tree representation"
    assert "regular_file.txt" in tree_repr, "Regular files should appear in tree representation"


def test_directory_exclusion_without_trailing_slash(temp_directory):
    """Test that directory patterns without trailing slash properly exclude directories from tree."""
    # Create test structure
    test_dir = temp_directory / "mydir"
    test_subdir = test_dir / "subdir"
    test_subdir.mkdir(parents=True)

    (test_dir / "file2.txt").write_text("content2")
    (test_subdir / "file.txt").write_text("content1")
    (temp_directory / "regular_file.txt").write_text("regular content")

    # Create exclusion rules without trailing slash
    rules = GitIgnoreExclusionRules()
    rules.add_rule("mydir")

    # Create tree with exclusion rules
    fs_tree = FileSystemTree(str(temp_directory), exclusion_rules=rules)
    tree = fs_tree.get_tree()
    assert tree is not None

    # The mydir directory should NOT appear in the tree
    mydir_in_tree = any(node.name == "mydir" for node in tree.children)
    assert not mydir_in_tree, "Directory 'mydir' should be completely excluded from tree"

    # Files inside mydir should not be iterable
    files = list(fs_tree.iterate_files())
    file_paths = [f[1] for f in files]

    assert "mydir/file2.txt" not in file_paths
    assert "mydir/subdir/file.txt" not in file_paths
    assert "regular_file.txt" in file_paths


def test_trailing_slash_vs_no_slash_tree_consistency(temp_directory):
    """Test that both trailing slash and no slash patterns result in identical tree output.

    This ensures that while the gitignore pattern matching behavior differs slightly,
    the final tree construction behavior is consistent.
    """
    # Create test structure
    test_dir = temp_directory / "testdir"
    test_subdir = test_dir / "subdir"
    test_subdir.mkdir(parents=True)

    (test_dir / "file1.txt").write_text("content1")
    (test_subdir / "file2.txt").write_text("content2")
    (temp_directory / "other_file.txt").write_text("other content")

    # Test with trailing slash pattern
    rules_with_slash = GitIgnoreExclusionRules()
    rules_with_slash.add_rule("testdir/")
    fs_tree_with_slash = FileSystemTree(str(temp_directory), exclusion_rules=rules_with_slash)

    # Test without trailing slash pattern
    rules_without_slash = GitIgnoreExclusionRules()
    rules_without_slash.add_rule("testdir")
    fs_tree_without_slash = FileSystemTree(str(temp_directory), exclusion_rules=rules_without_slash)

    # Both should have identical tree structure
    tree_with_slash = fs_tree_with_slash.get_tree_representation()
    tree_without_slash = fs_tree_without_slash.get_tree_representation()

    assert tree_with_slash == tree_without_slash, "Tree output should be identical regardless of trailing slash"

    # Both should have identical file iteration results
    files_with_slash = sorted([f[1] for f in fs_tree_with_slash.iterate_files()])
    files_without_slash = sorted([f[1] for f in fs_tree_without_slash.iterate_files()])

    assert files_with_slash == files_without_slash, "File iteration should be identical regardless of trailing slash"

    # Neither should show the excluded directory
    assert "testdir" not in tree_with_slash, "Excluded directory should not appear in tree (with slash)"
    assert "testdir" not in tree_without_slash, "Excluded directory should not appear in tree (without slash)"

    # Both should include other files
    assert "other_file.txt" in files_with_slash
    assert "other_file.txt" in files_without_slash
