from tinygrad.ops import PatternMatcher, UPat, UOp, Ops, graph_rewrite
from tinygrad import Tensor
from typing import Dict
from .types import ActualTensors


#####
# Logic For Replacing Placeholders In Graph
#####


def buffer_uop_contains_placeholder(x: UOp) -> bool:
    """Determine if a BUFFER UOp contains a placeholder marker."""
    if x.op != Ops.BUFFER:
        return False
    # Check if arg is a tuple with at least 3 elements
    if not (isinstance(x.arg, tuple) and len(x.arg) >= 3):
        return False
    # Check if the third element is a string starting with 'placeholder:'
    return isinstance(x.arg[2], str) and x.arg[2].startswith("placeholder:")


def get_placeholder_name(buffer_arg: tuple) -> str | None:
    """Extract placeholder name from a placeholder buffer arg."""
    if isinstance(buffer_arg, tuple) and len(buffer_arg) >= 3:
        if isinstance(buffer_arg[2], str) and buffer_arg[2].startswith("placeholder:"):
            parts = buffer_arg[2].split(":")
            if len(parts) >= 2:
                return parts[1]
    return None


def replace_placeholder(ctx: ActualTensors, v: UOp, b: UOp) -> UOp | None:
    """Replace a VIEW(BUFFER) structure where BUFFER is a placeholder."""
    if not buffer_uop_contains_placeholder(b):
        return None

    # Extract placeholder name
    placeholder_name = get_placeholder_name(b.arg)
    print(placeholder_name)
    if not placeholder_name or placeholder_name not in ctx:
        return None

    # Return the replacement tensor's UOp
    return ctx[placeholder_name].lazydata


find_and_substitute_placeholders = PatternMatcher(
    [
        # Match VIEW(BUFFER) where BUFFER is a placeholder
        (
            UPat(Ops.VIEW, src=(UPat(Ops.BUFFER, name="b"),), name="v"),
            replace_placeholder,
        )
    ]
)


def substitute_placeholder_uop(uop: UOp, input_tensors: Dict[str, Tensor]):
    """Replace VIEW(BUFFER) structures with placeholders."""
    return graph_rewrite(
        uop, find_and_substitute_placeholders, ctx=input_tensors, bottom_up=True
    )


#####
# Logic For Reading Placeholder Names From Graph
#####


def collect_placeholder_names(ctx: Dict[str, set[str]], v: UOp, b: UOp) -> None:
    """Collect placeholder names without replacing anything."""
    if not buffer_uop_contains_placeholder(b):
        return None

    # Extract placeholder name
    placeholder_name = get_placeholder_name(b.arg)
    if placeholder_name:
        # Add to our collection in ctx
        if "found_placeholders" in ctx:
            ctx["found_placeholders"].add(placeholder_name)

    # Return None to avoid making replacements
    return None


def find_all_placeholders(uop: UOp) -> set[str]:
    """Find all placeholder names in a UOp graph."""
    # Create a context with a set to collect names
    ctx: Dict[str, set[str]] = {"found_placeholders": set()}

    # Create a matcher that collects names but doesn't replace
    collector = PatternMatcher(
        [
            (
                UPat(Ops.VIEW, src=(UPat(Ops.BUFFER, name="b"),), name="v"),
                collect_placeholder_names,
            )
        ]
    )

    # Run graph_rewrite with our collector (won't modify the graph)
    graph_rewrite(uop, collector, ctx=ctx, bottom_up=True)

    # Return the collected names
    return ctx["found_placeholders"]
