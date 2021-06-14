from itertools import takewhile
from pathlib import Path
from typing import (
    Iterator,
    Optional,
)

import attr
import pytest

from syrupy.constants import PYTEST_NODE_SEP
from syrupy.utils import import_module_member


@attr.s
class PyTestLocation:
    _node: "pytest.Item" = attr.ib()
    nodename: str = attr.ib(init=False)
    testname: str = attr.ib(init=False)
    methodname: str = attr.ib(init=False)
    modulename: str = attr.ib(init=False)
    filepath: str = attr.ib(init=False)

    def __attrs_post_init__(self) -> None:
        if self.__is_doctest(self._node):
            return self.__attrs_post_init_doc__()
        self.__attrs_post_init_def__()

    def __attrs_post_init_def__(self) -> None:
        self.filepath = getattr(self._node, "fspath", None)
        obj = getattr(self._node, "obj", None)
        self.modulename = obj.__module__
        self.methodname = obj.__name__
        self.nodename = getattr(self._node, "name", None)
        self.testname = self.nodename or self.methodname

    def __attrs_post_init_doc__(self) -> None:
        doctest = getattr(self._node, "dtest", None)
        self.filepath = doctest.filename
        try:
            module_member = import_module_member(doctest.name)
            self.modulename = module_member.__module__
            self.methodname = module_member.__name__
            self.nodename = module_member.__name__
        except Exception:
            self.modulename = ".".join(doctest.name.split(".")[:-1])
            self.methodname = ""
            self.nodename = self.__sanitise_docstr(doctest.docstring)
        self.testname = self.nodename or self.methodname

    @property
    def classname(self) -> Optional[str]:
        """
        Pytest node names contain file path and module members delimited by `::`
        Example tests/grouping/test_file.py::TestClass::TestSubClass::test_method
        """
        nodeid: str = getattr(self._node, "nodeid", None)
        return ".".join(nodeid.split(PYTEST_NODE_SEP)[1:-1]) or None

    @property
    def filename(self) -> str:
        return Path(self.filepath).stem

    @property
    def snapshot_name(self) -> str:
        if self.classname is not None:
            return f"{self.classname}.{self.testname}"
        return str(self.testname)

    def __is_doctest(self, node: "pytest.Item") -> bool:
        return hasattr(node, "dtest")

    def __sanitise_docstr(self, docstr: str) -> str:
        return PYTEST_NODE_SEP.join(
            s
            for s in takewhile(
                lambda s: not s.startswith(">>>"),
                (s.strip() for s in docstr.splitlines()),
            )
            if s
        )

    def __valid_id(self, name: str) -> str:
        """
        Take characters from the name while the result would be a valid python
        identified. Example: "test_2[A]" returns "test_2" while "1_a" would return ""
        """
        valid_id = ""
        for char in name:
            new_valid_id = f"{valid_id}{char}"
            if not new_valid_id.isidentifier():
                break
            valid_id = new_valid_id
        return valid_id

    def __valid_ids(self, name: str) -> Iterator[str]:
        """
        Break a name path into valid name parts stopping at the first non valid name.
        Example "TestClass.test_method_[1]" would yield ("TestClass", "test_method_")
        """
        for n in name.split("."):
            valid_id = self.__valid_id(n)
            if valid_id:
                yield valid_id
            if valid_id != n:
                break

    def __parse(self, name: str) -> str:
        return ".".join(self.__valid_ids(name))

    def matches_snapshot_name(self, snapshot_name: str) -> bool:
        return self.__parse(self.snapshot_name) == self.__parse(snapshot_name)

    def matches_snapshot_location(self, snapshot_location: str) -> bool:
        return self.filename in snapshot_location
