from language.parser import parse

source = """
principal Lyra {
    authority Sentinel
}
"""

principal = parse(source)

print(principal)
print(principal.name)
print(principal.authorities[0].name)