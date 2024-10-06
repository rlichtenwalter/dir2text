import subprocess
import sys

def run_tests():
    subprocess.run(["pytest"], check=True)

def run_lint():
    subprocess.run(["flake8", "src", "tests"], check=True)

def run_typecheck():
    subprocess.run(["mypy", "src"], check=True)

def run_format():
    subprocess.run(["black", "src", "tests"], check=True)

def run_coverage():
    subprocess.run(["pytest", "--cov=dir2text", "tests/", "--cov-report=xml"], check=True)

if __name__ == "__main__":
    globals()[sys.argv[1]]()