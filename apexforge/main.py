from examples.gravitas import run_gravitas_demo

if __name__ == "__main__":
    result = run_gravitas_demo()
    print("ApexForge main ran.")
    print("Execution OK:", result.ok)
    print("Final Vigilance:", result.final_state.get_int("state:Vigilance"))