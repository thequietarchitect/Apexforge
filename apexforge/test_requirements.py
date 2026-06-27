from language.compiler import compile_source
from authority.registry import AuthorityRegistry
from workflow.directive_engine import validate_authorities

source = """
directive Investigate {
    authority Sentinel
    requires Observe
}
"""

program = compile_source(source)

authority_registry = AuthorityRegistry()

try:
    validate_authorities(program, authority_registry)
    raise AssertionError("Expected missing authority failure")
except Exception:
    print("PASS: missing authority blocked")