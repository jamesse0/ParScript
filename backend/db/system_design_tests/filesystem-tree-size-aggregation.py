import pytest
from solution import File, Folder


def test_file_total_size():
    f = File("a.txt", 10)
    assert f.total_size() == 10


def test_empty_folder_total_size():
    root = Folder("root")
    assert root.total_size() == 0


def test_folder_with_files_sums_sizes():
    root = Folder("root")
    root.add_child(File("a.txt", 10))
    root.add_child(File("b.txt", 5))
    assert root.total_size() == 15


def test_nested_folders_recursive_sum():
    root = Folder("root")
    root.add_child(File("a.txt", 10))

    docs = Folder("docs")
    docs.add_child(File("b.txt", 5))
    docs.add_child(File("c.txt", 7))

    root.add_child(docs)

    assert root.total_size() == 22


def test_deeply_nested_folders():
    root = Folder("root")
    level1 = Folder("level1")
    level2 = Folder("level2")

    level2.add_child(File("deep.txt", 3))
    level1.add_child(level2)
    level1.add_child(File("mid.txt", 4))
    root.add_child(level1)
    root.add_child(File("top.txt", 1))

    assert root.total_size() == 8


def test_remove_child_updates_size():
    root = Folder("root")
    root.add_child(File("a.txt", 10))
    root.add_child(File("b.txt", 5))
    assert root.total_size() == 15

    root.remove_child("a.txt")
    assert root.total_size() == 5


def test_remove_nonexistent_child_raises_keyerror():
    root = Folder("root")
    root.add_child(File("a.txt", 10))
    with pytest.raises(KeyError):
        root.remove_child("nope.txt")


def test_add_duplicate_name_raises_valueerror():
    root = Folder("root")
    root.add_child(File("a.txt", 10))
    with pytest.raises(ValueError):
        root.add_child(File("a.txt", 999))


def test_size_reflects_mutation_no_stale_caching():
    root = Folder("root")
    root.add_child(File("a.txt", 10))
    first = root.total_size()
    assert first == 10

    root.add_child(File("b.txt", 5))
    second = root.total_size()
    assert second == 15  # must NOT still be 10 from a cached earlier call


def test_removing_subfolder_removes_entire_subtree_contribution():
    root = Folder("root")
    root.add_child(File("top.txt", 1))

    docs = Folder("docs")
    docs.add_child(File("b.txt", 5))
    nested = Folder("nested")
    nested.add_child(File("deep.txt", 20))
    docs.add_child(nested)

    root.add_child(docs)
    assert root.total_size() == 26  # 1 + 5 + 20

    root.remove_child("docs")
    assert root.total_size() == 1  # entire docs subtree (5+20) is gone


def test_polymorphic_total_size_via_public_interface_only():
    # A folder containing a mix of Files and Folders must sum correctly
    # purely by calling total_size() on each child, without special-casing
    # types anywhere the test can observe.
    root = Folder("mixed")
    root.add_child(File("x.txt", 2))
    sub = Folder("sub")
    sub.add_child(File("y.txt", 3))
    root.add_child(sub)
    root.add_child(File("z.txt", 4))

    assert root.total_size() == 9


def test_mutating_child_after_add_is_reflected():
    # Since File.size is a public attribute, mutating it directly after
    # the file has been added to a folder should be reflected on the next
    # total_size() call -- this fails if the folder snapshotted sizes at
    # add_child() time instead of querying children live.
    root = Folder("root")
    f = File("a.txt", 10)
    root.add_child(f)
    assert root.total_size() == 10

    f.size = 50
    assert root.total_size() == 50