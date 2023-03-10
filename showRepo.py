#!/usr/bin/python3

from tabulate import tabulate
import argparse
import sys
import shutil
from pathlib import Path
from collections import Counter
import re
import pyperclip


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
        "NC": '\033[0m'
        }


# Define a simple character to print steps
sb: str = f'{colors["L_CYAN"]}[*]{colors["NC"]}'
sb_v2: str = f'{colors["RED"]}[{colors["YELLOW"]}+{colors["RED"]}]{colors["NC"]}'
whitespaces: str = " "*(len('[*]')+1)
warning: str = f'{colors["YELLOW"]}[{colors["RED"]}!{colors["YELLOW"]}]{colors["NC"]}'


def check_arguments() -> None:
    """
    Simple function to check if the user has provided arguments
    """
    if len(sys.argv) > 1:
        return
    else:
        print(f"No arguments provided. Run '{sys.argv[0]} --help' and retry")
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    """
    Simple function to get flags given by the user
    """
    # Create an ArgumentParser object that will store flags provided
    parser = argparse.ArgumentParser()

    # Add flags/switches
    parser.add_argument("-f", "--filename", type=str, default = "repositories.txt", metavar = 'filename',
                        help="Filename containing repositories to display; usually the file generated by addRepo.py. Default: ./repositories.txt")
    parser.add_argument("-s", "--search", type=str, help="Search for a word/string into Repository Name or its Description", metavar='string')
    parser.add_argument("-l", "--only-language", help="Search for a specific language. Case insensitive.", metavar='language')
    parser.add_argument("-x", "--only-os", type=str, help="Search for a specific repository whose scope is the one in this flag. Valid values: (A)ny, (L)inux, (W)indows",
                        metavar='OS')
    parser.add_argument("-c", "--copy", action="store_true", help="Copy the resulting repositories, after filtering, into clipboard")
    parser.add_argument("-o", "--output", type=str, help="Output filename to save the table", metavar='filename')
    parser.add_argument("--first", type=int, help="Select the first N results/rows", metavar='N')
    parser.add_argument("--last", type=int, help="Select the last N results/rows", metavar='N')
    parser.add_argument("-tf", "--table-format", type=str, default="grid", metavar = 'table_format',
                        help="Table format output. Check 'Table format' section at https://pypi.org/project/tabulate/ to see all options available. Some of them might be bugged. For some formats it is necessary to additionally use '--no-color' flag")
    parser.add_argument("--no-author", action="store_true", help="Do not show author name in repository name/only show repository name")
    parser.add_argument("--sort-by-author", action="store_true", help="Sort repositories alphabetically based on repos' authors")
    parser.add_argument("--sort-by-repo", action="store_true", 
                        help="Sort repositories alphabetically by their name (not considering authors)")
    parser.add_argument("--sort-by-language", action="store_true", 
                        help="Sort repositories alphabetically by their main programming language")
    parser.add_argument("--show-stats", action="store_true",
                        help="Display some statistics about the repositories (such as number of languages, distribution by OS, etc)")
    parser.add_argument("--no-color", action="store_true", help="Do not display the table with colors")
    # Parse command-line arguments
    args = parser.parse_args(sys.argv[1:])

    return args


def print_colors(no_color_boolean: bool, 
                 message: str, mode='output') -> None:
    """
    Simple message handler for '--no-color' flag
    """
    if mode == "output":
        if no_color_boolean:
            print(f"[*] {message}")
        else:
            print(f"{sb} {message}")
        return
    if mode == "warning":
        if no_color_boolean:
            print(f"[!] Warning! {message}")
        else:
            print(f"{warning} {colors['RED']}Warning!{colors['NC']} {message}")
        return
    if mode == "error":
        if no_color_boolean:
            print(f"[!] Error: {message}")
        else:
            print(f"{warning} {colors['RED']}Error: {message}{colors['NC']}")
        return
    print("No valid mode selected")
    sys.exit(1)


def get_percentage(number: int, total: int) -> float:
    """
    Returns the percentage a number represents within a total
    """
    return round(number/(1.0*total) * 100, 1)


def stats_table_elements(flags_var, table_elements):
    """
    Analyze some elements extracted from the repositories file
    """
    # Check the number of programming languages
    languages = [item[3].lower() for item in table_elements]
    counter_object = Counter(languages)
    keys = counter_object.keys()
    num_values = len(keys)
    # Get OS details
    OS_list = [item[2] for item in table_elements]
    counts_OS = Counter(OS_list)
    any_percentage = get_percentage(counts_OS['Any'], len(OS_list))
    linux_percentage = get_percentage(counts_OS['Linux'], len(OS_list))
    windows_percentage = get_percentage(counts_OS['Windows'], len(OS_list))
    if flags_var.no_color:
        print(f"[*] Number of different languages: {num_values}")
        print("[*] Operating System scope:")
        print(f"{whitespaces}[+] Any: {counts_OS['Any']} ({any_percentage}%)")
        print(f"{whitespaces}[+] Linux: {counts_OS['Linux']} ({linux_percentage}%)")
        print(f"{whitespaces}[+] Windows: {counts_OS['Windows']} ({windows_percentage}%)")
    else:
        print(f"{sb} Number of different languages: {colors['PURPLE']}{num_values}{colors['NC']}")
        print(f"{sb} Operating System scope:")
        print(f"{whitespaces}{sb_v2} Any: {colors['PURPLE']}{counts_OS['Any']}{colors['NC']} ({colors['RED']}{any_percentage}%{colors['NC']})")
        print(f"{whitespaces}{sb_v2} Linux: {colors['PURPLE']}{counts_OS['Linux']}{colors['NC']} ({colors['RED']}{linux_percentage}%{colors['NC']})")
        print(f"{whitespaces}{sb_v2} Windows: {colors['PURPLE']}{counts_OS['Windows']}{colors['NC']} ({colors['RED']}{windows_percentage}%{colors['NC']})")
    return


def delete_git_extension(no_color_boolean: bool, url: str):
    """
    Delete ".git" extension from weblink repository column
    """
    # If the last 4 characters are ".git"
    if url[-4:] == '.git':
        # Return url without ".git" extension
        return url[:-4]
    else:
        print_colors(no_color_boolean, "Unable to cut '.git' string in '{url}'. Returning original url instead...",
                     mode='warning')
        return url


def filter_data_table(flags_var, printable_data_table):
    """
    Function that sorts and filters table body/data based on flags provided by the user
    """
    # Save the original table length for analytics purposes
    original_length_table = len(printable_data_table)

    # Sort repositories alphabetically by their author
    if flags_var.sort_by_author:
        temp_data_table = sorted(printable_data_table, key=lambda x: x[1])
        printable_data_table = temp_data_table
    # Sort repositories aplhabetically by its programming language 
    if flags_var.sort_by_language:
        if flags_var.only_language:
            print_colors(flags_var.no_color, "'--sort-by-language' and '--only-language' flags simultaneously enabled...",
                         mode='warning')
        temp_data_table = sorted(printable_data_table, key= lambda x: x[3])
        printable_data_table = temp_data_table
    # Sort repositories alphabetically by repository name
    if flags_var.sort_by_repo:
        if flags_var.sort_by_author or flags_var.sort_by_repo:
            print_colors(flags_var.no_color, "Multiple 'sort' flags simultaneously enabled. Output will be sortered by repository name...",
                         mode='warning')
        try:
            temp_data_table = sorted(printable_data_table, key=lambda x: x[1].split('/')[1])
            printable_data_table = temp_data_table
        except:
            print_colors(flag_var.no_color, "Unable to sort by author", mode='warning')
    # Filter by programming language             
    if flags_var.only_language:
        temp_data_table = []
        for rows in printable_data_table:
            if rows[3].lower() == flags_var.only_language.lower():
                temp_data_table.append(rows)
        if len(temp_data_table) == 0:
            print_colors(flags_var.no_color, f"No results found for language '{flags_var.only_language}'...",
                         mode='error')
            sys.exit(1)
        printable_data_table = temp_data_table
    # Filter by searching a word in the 'Description' column 
    if flags_var.search:
        temp_data_table = []
        for rows in printable_data_table:
            for n_col, cols in enumerate(rows):
                    # Check for a string, except in Github weblink, OS or Programming language
                if n_col in [0,2,3]:
                    continue
                if flags_var.search.lower() in cols.lower():
                    temp_data_table.append(rows)
                    break
        if len(temp_data_table) == 0:
            print_colors(flags_var.no_color, f"Word '{flags_var.search}' could not be found for any repository...",
                         mode='error')
            sys.exit(1)
        printable_data_table = temp_data_table
    # Filter by Operating System
    if flags_var.only_os:
        if re.match(r"^w(indows)?$", flags_var.only_os, re.IGNORECASE):
            only_os_var = "Windows"
        elif re.match(r"^l(inux)?$", flags_var.only_os, re.IGNORECASE):
            only_os_var = "Linux"
        elif re.match(r"^a(ny)?$", flags_var.only_os, re.IGNORECASE):
            only_os_var = "Any"
        else:
            print_colors(flags_var.no_color, f"'{flags_var.only_os}' is not a valid value for '--only-os' flag. Valid values: (A)ny, (L)inux, (W)indows. Please retry...",
                         mode='warning')
            sys.exit(1)
        temp_data_table = []
        for rows in printable_data_table:
            if rows[2] == only_os_var and only_os_var != '':
                temp_data_table.append(rows)
        if len(temp_data_table) == 0:
            print_colors(flags_var.no_color, f"No items found for {only_os_var} OS...",
                        mode = 'error')
            sys.exit(1)
        printable_data_table = temp_data_table
    # Select the first N rows if '--first' flag is provided
    if flags_var.first:
        if flags_var.first > len(printable_data_table):
            print_colors(flags_var.no_color, f"Unable to show first {flags_var.first} rows since max number of rows is {len(printable_data_table)}. Displaying full table...",
                         mode='warning')
        else:
            printable_data_table = printable_data_table[:flags_var.first]
    # Select the last N rows if '--last' flag is enabled
    if flags_var.last:
        if flags_var.first:
            print_colors(flags_var.no_color, f"'--first' and '--last' simultaneously enabled. Result will be cut only considering '--first' flag (first {flags_var.first} rows)...",
                         mode='warning')
        if not flags_var.first and flags_var.last > len(printable_data_table):
            print_colors(flags_var.no_color, f"Unable to show last {flags_var.last} rows since max number of rows is {len(printable_data_table)}. Displaying full table...",
                         mode='warning')
        else:
            printable_data_table = printable_data_table[(-1 * flags_var.last):]

    # Only show repository name, no author
    if flags_var.no_author:
        for index, row in enumerate(printable_data_table):
            try:
                printable_data_table[index][1] = row[1].split('/')[1]
            except:
                pass
    # Copy lists, after filtering, to output
    if flags_var.copy:
        if len(printable_data_table) == 0:
            print_colors(flags_var.no_color, "Repository list is empty", mode='error')
            sys.exit(1)
        if len(printable_data_table) == 1:
            print_colors(flags_var.no_color, "Repository copied to clipboard!",
                             mode='output')
            pyperclip.copy(delete_git_extension(flags_var.no_color, printable_data_table[0][0]))
        if len(printable_data_table) > 1:
            repos = []
            for row in printable_data_table:
                repos.append(delete_git_extension(flags_var.no_color, row[0]))
            repos_string = '\n'.join(map(str, repos))
            pyperclip.copy(repos_string)
            print_colors(flags_var.no_color, "Multiple repositories copied to clipboard!",
                         mode='output')
    # Shows statistics
    if flags_var.show_stats:
        if len(printable_data_table) < original_length_table:
            if flags_var.no_color:
                print(f"[*] Number of repositories after applying filters: {len(printable_data_table)}")
            else:
                print(f"{sb} Number of repositories after applying filters: {colors['PURPLE']}{len(printable_data_table)}{colors['NC']}")
        # Show some statistics for the data that will be returned and shown in the final table
        stats_table_elements(flags_var, printable_data_table)

    return printable_data_table
            

def create_table_elements(flags_var, width_terminal, printable_data_rows_table):
    """
    Add colors to the table and sets their parts ready to be printed
    """
    # Headers for the table
    headers_table = ["Repository Name", "OS", "Language", "Description"]
    # Get the max length (the sum of them) for columns that are not the "Description column"
    max_length = 0
    table_to_show = [[item for item in sublist[1:]] for sublist in printable_data_rows_table] 
    for col in table_to_show:
        new_length = len(col[0]) + len(col[1]) + len(col[2]) + 12 # '12' considering symbols and spaces
        if new_length > max_length:
            max_length = new_length
    # Max allowed length before 'wrapping' text
    max_allowed_length = width_terminal - max_length - 12

    if flags_var.no_color:
        return headers_table, table_to_show, max_allowed_length
    else:
        colors_headers_table = [f"{colors['L_CYAN']}Repo Name{colors['NC']}",
                                f"{colors['PINK']}OS{colors['NC']}",
                                f"{colors['L_RED']}Language{colors['NC']}",
                                f"{colors['L_GREEN']}Description{colors['NC']}"]
        # Create a table body containing ANSI escape codes so it will print in colors
        colors_row_table = []
        for row in table_to_show:
            color_column = []
            # 'Repo Name' column
            color_column.append(f"{colors['CYAN']}{row[0]}{colors['NC']}")
            # 'Operating System (OS)' column
            color_column.append(f"{colors['PURPLE']}{row[1]}{colors['NC']}")
            # 'Language' column
            color_column.append(f"{colors['RED']}{row[2]}{colors['NC']}")
            # 'Description' column
            color_column.append(f"{colors['GREEN']}{row[3]}{colors['NC']}")
            colors_row_table.append(color_column)
        return colors_headers_table, colors_row_table, max_allowed_length


def read_columns_in_repository_file(flag_var):
    """
    Read the repositories file where the separator is "--"
    """
    rows = []
    with open(flag_var.filename, "r") as file:
        for line in file:
            col = []
            row = line.strip().split("--")
            for column in row:
                col.append(column.strip())
            rows.append(col)
    if not flag_var.show_stats:
        return rows
    print()
    if flag_var.no_color:
        print(f"[*] Total number of repositories: {len(rows)}")
    else:
        print(f"{sb} Total number of repositories: {colors['PURPLE']}{len(rows)}{colors['NC']}")
    return rows


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
        print_colors(flags_var.no_color, f"{file_to_read}' does not exist. Try using 'addRepo.py' to create a file and retry",
                     mode='error')
        sys.exit(1)
    return None


def print_table(flags_var, body_table, headers_table, max_allowed_length):
    """
    Print the final table/result
    """
    print()
    print(tabulate(body_table, 
          headers=headers_table, tablefmt=flags_var.table_format, 
          maxcolwidths=[None, None, None, max_allowed_length]))


def save_file(flags_var, body_table, max_allowed_length):
    """
    Save the table displayed in a 'no color' format to avoid ANSII escape characters
    """
    if not flags_var.output:
        return
    headers_table = ["Repository Name", "OS", "Language", "Description"]

    table_to_save = tabulate(body_table, 
                             headers=headers_table, tablefmt=flags_var.table_format, 
                             maxcolwidths=[None, None, None, max_allowed_length])
    with open(flags_var.output, "w") as file:
        file.write(table_to_save)
    return


def main():
    """MAIN"""
    # Check if the user has provided arguments
    check_arguments()
    # Get flags from user input
    flags = parse_args()
    # Check if the file that contains the repositories data exists (if not, exits)
    check_file_to_read(flags)
    # Get terminal width
    width = shutil.get_terminal_size()[0]
    # Get data contained in the file
    printable_data_table = read_columns_in_repository_file(flags)
    # Sort/filter the list (or not) based on flags provided
    filtered_printable_data_table = filter_data_table(flags, printable_data_table)
    # Create table body that will be printed
    headers_table, body_table, max_allowed_length = create_table_elements(flags, width, filtered_printable_data_table)
    # Print the table
    print_table(flags, body_table, headers_table, max_allowed_length)
    # Save the file (if requested by the user)
    save_file(flags, filtered_printable_data_table, max_allowed_length)
    

if __name__ == "__main__":
        main()

