# import-typing-as-t
LibCST Codemod to transform relative typing import (`from typing import...`) or generic typing import (`import typing`) and their refs to `import typing as t` + `t.` prefixed refs respectively.


## Examples

Before:
```python
    from typing import Callable, Optional, Generator, cast, Any
    a : Callable[..., Any] = "test"
    def b(c: Optional[int] = None) -> Generator:
        return cast(Generator, "blabla")
```

After:
```python
    import typing as t

    a : t.Callable[..., t.Any] = "test"
    def b(c: t.Optional[int] = None) -> t.Generator:
        return t.cast(t.Generator, "blabla")
```

---

Before:
```python
    from typing import cast, List, Dict, Any, Sequence, TypeAlias, Sequence, Generator
    float_list : TypeAlias = list[float]
    def b(z: float_list, c: Sequence[tuple[tuple[str, int], List[Dict[str, Any]]]] = None) -> Generator:
        return cast(Generator, "blabla")
```

After:
```python
    import typing as t

    float_list : t.TypeAlias = list[float]
    def b(z: float_list, c: t.Sequence[tuple[tuple[str, int], t.List[t.Dict[str, t.Any]]]] = None) -> t.Generator:
        return t.cast(t.Generator, "blabla")
```

---

Before:
```python
    import typing

    a : typing.Callable[..., typing.Any] = "test"
    def b(c: typing.Optional[int] = None) -> typing.Generator:
        return typing.cast(typing.Generator, "blabla")
```

After:
```python
    import typing as t

    a : t.Callable[..., t.Any] = "test"
    def b(c: t.Optional[int] = None) -> t.Generator:
        return t.cast(t.Generator, "blabla")
```
