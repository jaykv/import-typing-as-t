import libcst as cst
from libcst.codemod.visitors import AddImportsVisitor
from libcst.codemod import VisitorBasedCodemodCommand, CodemodContext, CodemodTest
from libcst.metadata import ScopeProvider
import typing as t

class ImportTypingAsCommand(VisitorBasedCodemodCommand):
    DESCRIPTION: str = "Transforms relative typing import (`from typing import...`) or generic typing import (`import typing`) and their refs to `import typing as t` + `t.` prefixed refs respectively"
    METADATA_DEPENDENCIES = (ScopeProvider,)
    
    def __init__(
        self, context: CodemodContext
    ) -> None:
        super().__init__(context)
        self.typing_references: dict[t.Union[cst.Import, cst.ImportFrom], t.Any] = {}
        self.node_generic_import_typing = None
        self.typing_annotations = []
        self.as_typing_annotations_map = {}
        
        AddImportsVisitor.add_needed_import(self.context, "typing", None, "t")
    
    def _leave_import_alike(self, original_node: t.Any, updated_node: t.Any) -> t.Any:
        if self.node_generic_import_typing and original_node == self.node_generic_import_typing:
            return updated_node.with_deep_changes(original_node.names[0], name=cst.Name(value="typing"), asname=cst.AsName(name=cst.Name(value="t")))

        if original_node in self.typing_references:
            return cst.RemoveFromParent() 
        
        return updated_node
    
    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool:
        metadata = self.get_metadata(ScopeProvider, node)
        for assignment in metadata.assignments:
            if node.module.value == "typing":
                if not assignment.references:
                    print(f"Warning {assignment.name} is unused...")
                else:
                    for import_alias in node.names:
                        if import_alias.asname:
                            # as alias to actual import mapping
                            self.as_typing_annotations_map[import_alias.asname.name.value] = import_alias.name.value
                        elif import_alias.name.value not in self.typing_annotations:
                            self.typing_annotations.append(import_alias.name.value)
                    self.typing_references[node] = assignment.references
        return False

    def visit_Import(self, node: cst.Import) -> t.Optional[bool]:
        if node.names[0].name.value == "typing":
            self.node_generic_import_typing = node

        return False
    
    def leave_ImportFrom(
        self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> t.Union[cst.ImportFrom, cst.RemovalSentinel]:
        return self._leave_import_alike(original_node, updated_node)
    
    def leave_Import(
        self, original_node: cst.Import, updated_node: cst.Import
    ) -> t.Union[cst.Import, cst.RemovalSentinel]:
        return self._leave_import_alike(original_node, updated_node)
        
    def leave_Name(self, original_node: cst.Name, updated_node: cst.Name) -> cst.BaseExpression:
        if original_node.value in self.typing_annotations:
            return cst.Attribute(value=cst.Name("t"), attr=original_node, dot=cst.Dot())
        if original_node.value in self.as_typing_annotations_map:
            return cst.Attribute(value=cst.Name("t"), attr=cst.Name(value=self.as_typing_annotations_map[original_node.value]), dot=cst.Dot())
        return original_node
    
    def leave_Attribute(self, original_node: cst.Attribute, updated_node: cst.Attribute) -> cst.BaseExpression:
        if self.node_generic_import_typing and isinstance(original_node.value, cst.Name) and original_node.value.value == "typing":
            return updated_node.with_changes(value=cst.Name("t"))
            
        return updated_node
    

class TestImportTypingAsCommand(CodemodTest):
    TRANSFORM = ImportTypingAsCommand

    def test_substitution_1(self) -> None:
        before = """
            from typing import Callable, Optional, Generator, cast, Any
            a : Callable[..., Any] = "test"
            def b(c: Optional[int] = None) -> Generator:
                return cast(Generator, "blabla")
        """
        after = """
            import typing as t

            a : t.Callable[..., t.Any] = "test"
            def b(c: t.Optional[int] = None) -> t.Generator:
                return t.cast(t.Generator, "blabla")
        """

        self.assertCodemod(before, after)

    def test_substitution_2(self) -> None:
        before = """
            from typing import cast, List, Dict, Any, Sequence, TypeAlias, Sequence, Generator
            float_list : TypeAlias = list[float]
            def b(z: float_list, c: Sequence[tuple[tuple[str, int], List[Dict[str, Any]]]] = None) -> Generator:
                return cast(Generator, "blabla")
        """
        after = """
            import typing as t

            float_list : t.TypeAlias = list[float]
            def b(z: float_list, c: t.Sequence[tuple[tuple[str, int], t.List[t.Dict[str, t.Any]]]] = None) -> t.Generator:
                return t.cast(t.Generator, "blabla")
        """

        self.assertCodemod(before, after)
        
    def test_noop(self) -> None:
        before = """
            import os
            import typing_extensions
            from collections import deque 
            import typing as t
            
            a : t.Callable[..., t.Any] = "test"
            def b(c: t.Optional[int] = None) -> t.Generator:
                return t.cast(t.Generator, "blabla")
        """
        after = """
            import os
            import typing_extensions
            from collections import deque 
            import typing as t

            a : t.Callable[..., t.Any] = "test"
            def b(c: t.Optional[int] = None) -> t.Generator:
                return t.cast(t.Generator, "blabla")
        """

        self.assertCodemod(before, after)
    
    def test_generic_import(self) -> None:
        before = """
            import typing

            a : typing.Callable[..., typing.Any] = "test"
            def b(c: typing.Optional[int] = None) -> typing.Generator:
                return typing.cast(typing.Generator, "blabla")
        """
        after = """
            import typing as t

            a : t.Callable[..., t.Any] = "test"
            def b(c: t.Optional[int] = None) -> t.Generator:
                return t.cast(t.Generator, "blabla")
        """

        self.assertCodemod(before, after)

    def test_relative_as_import(self) -> None:
        before = """
            from typing import Callable, Optional, Generator, cast, Any, TYPE_CHECKING as TC
            from typing import TypeAlias as TA

            if TC:
                a: dict[str, Any]

            Vector: TA = list[float]
            
            a : Callable[..., Any] = "test"
            def b(c: Optional[int] = None) -> Generator:
                return cast(Generator, "blabla")
        """
        after = """
            import typing as t

            if t.TYPE_CHECKING:
                a: dict[str, t.Any]

            Vector: t.TypeAlias = list[float]
            
            a : t.Callable[..., t.Any] = "test"
            def b(c: t.Optional[int] = None) -> t.Generator:
                return t.cast(t.Generator, "blabla")
        """

        self.assertCodemod(before, after)

if __name__ == "__main__":
#     code = """\
# from typing import Callable, Optional, Generator, cast, Any

# a : Callable[..., Any] = "test"
# def b(c: Optional[int] = None) -> Generator:
#     return cast(Generator, "blabla")
#     """
    code = """\
from typing import Callable, Optional, Generator, cast, Any
from typing import TYPE_CHECKING as TC

if TC:
    a = None

a : Callable[..., Any] = "test"
def b(c: Optional[int] = None) -> Generator:
    return cast(Generator, "blabla")
    """
    # Parse the code
    module = cst.MetadataWrapper(cst.parse_module(code))
    # Apply the transformer
    transformer = ImportTypingAsCommand(CodemodContext())
    new_module = module.visit(transformer)

    # Output the modified code
    print(new_module.code)