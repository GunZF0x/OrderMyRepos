#/usr/bin/python3

from tabulate import tabulate
import argparse
import sys
import shutil
import textwrap
from pathlib import Path

# ANSI escape codes dictionary
colors = {
        "BLACK": '\033[30m',
        "RED": '\033[31m',
        "GREEN": '\033[32m',
        "BROWN": '\033[33m',
        "BLUE": '\033[34m',
        "PURPLE": '\033[35m',
        "CYAN": '\033[36m',
        "WHITE": '\033[37m',
        "GRAY": '\033[1;30m',
        "L_RED": '\033[1;31m',
        "L_GREEN": '\033[1;32m',
        "YELLOW": '\033[1;33m',
        "L_BLUE": '\033[1;34m',
        "PINK": '\033[1;35m',
        "L_CYAN": '\033[1;36m',
        "NC": '\033[m'
        }

# Define a simple character to print steps
sb: str = f'{colors["L_CYAN"]}[*]{colors["NC"]}'
whitespaces: str = " "*(len('[*]')+1)

def parse_args() -> argparse.Namespace:
    """
    Simple function to get flags given by the user
    """
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser()

    # Add an argument called "--flag" with action "store_true"
    parser.add_argument("-f", "--filename", type=str, default = "reposotiroes.txt",
                    help="Filename containing repositories to display (usually the file generated by addRepo.py)")
    parser.add_argument("--no-color", action="store_true",
                        help="Do not display the table with colors")

    # Parse the command-line arguments
    args = parser.parse_args(sys.argv[1:])

    check_arguments_length(parser)

    return args


def check_arguments_length(parser_variable) -> None:
    """
    Check if the user has provided at least 1 argument
    """
    if len(sys.argv) > 1:
        return
    if len(sys.argv) <= 1:
        print(f"Invalid argument length: {len(sys.argv)}")
        parser_variable.error(f"Arguments provided must be more than {len(sys.argv)}")
        sys.exit(1)
    return None

def create_table_elements(flags_var):
    """
    Creates items that will be stored inside 'tabulate' object
    """
    if flags_var.no_color:
        headers_defined = ["Repository Name", "OS", "Description"]

    else:
        headers_defined = [f"{colors['L_CYAN']}Repo Name{colors['NC']}",
                           f"{colors['RED']}OS{colors['NC']}",
                           f"{colors['L_GREEN']}Description{colors['NC']}"]
    print(headers_defined)
    return headers_defined
    

def check_file_to_read(flags_var) -> None:
    """
    Check if the file that stores all the repositories exists
    """

    # Get the path where the script is being executed (current path, not where the script is stored)
    file_to_read = Path.cwd().joinpath(flags_var.filename)

    # Get file path
    file_path = Path(file_to_read)

    # Check if the file containing the repositories exists
    if not file_path.exists():
        if not flags_var.no_color:
            print(f"{sb} {colors['RED']}Warning{colors['NC']}: '{file_to_read}' does not exist. Try using 'addRepo.py' to create a file and retry")
        else:
            print(f"[+] Warning: '{file_to_read}' does not exist. Try using 'addRepo.py' to create a file and retry")
        sys.exit(1)

    return None


def main():
    """MAIN"""
    # Get the flags from the user input
    flags = parse_args()
    # Check if the file that contains the repositories data exists (if not, exits)
    check_file_to_read(flags)
    headers_defined = ["Repo Name", "OS", "Description"]
    #description_repo = textwrap.wrap("Example of a looooooooooooooooooooooooooo\noooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo\noooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooong description")
    table = headers_defined, ["Repo example", "Windows", "Test"]
    print(tabulate(table, headers=headers_defined, tablefmt="grid"))
    width = shutil.get_terminal_size()[0]
    print(f"Current terminal size -> width: {width}")
    c = create_table_elements(flags)
    print(c[0], c[1], c[2])



if __name__ == "__main__":
        main()
