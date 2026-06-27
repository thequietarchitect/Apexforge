from language.compiler import compile_source

source = """
directive Investigate {
    authority Sentinel
    requires Observe
}
"""

air = compile_source(source)

print(air)

assert air.directives[0].name == "Investigate"
assert air.authorities[0].name == "Sentinel"
assert air.requirements[0].capability == "Observe"

print("PASS")