
HEADER = '\033[95m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'

def warning(message):
    print(f"{WARNING}{message}{RESET}")

def success(message):
    print(f"{OKGREEN}{message}{RESET}")

def error(message):
    print(f"{BOLD}{FAIL}{message}{RESET}")

def header(message):
    print(f"{HEADER}{message}{RESET}")