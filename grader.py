import os, sys, subprocess
import ip_analysis

RECENT_SRC_PATH_FILE = 'recent_source_path.txt'
HTML_FILE_NAME = 'index.html'

# Check for dependencies
# Python deps
try:
    from PyInquirer import prompt
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    print("Depenedencies not installed.")
    sys.exit(1)
# CLI deps
try:
    subprocess.run(['prettier', '-v'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
except subprocess.CalledProcessError as e:
    if e.returncode == '127':
        print("Dependencies not installed.")
    else:
        print(f"Prettier unexpected exitted with code {e.returncode}.")
    sys.exit(1)
except FileNotFoundError:
    print("Dependencies not installed.")
    sys.exit(1)

def validte_source_path(path_str):
    """
    Check whether the path specified by the user actually exists

    path_str
        String containing directory path
    """
    if os.path.isdir(path_str):
        return True
    return "Not a valid directory path. Please specify an exisiting FOLDER, not a file."

def get_default_source_path():
    default_path = ''
    # Look for a 'recent_source_path' file
    if os.path.isfile(RECENT_SRC_PATH_FILE):
        with open(RECENT_SRC_PATH_FILE, "r") as rf:
            default_path = rf.read().strip()
    
    if default_path and not os.path.isdir(default_path):
        default_path = ''
        os.remove(RECENT_SRC_PATH_FILE)

    # Scan current directory for a folder containing
    # Interactive Paper folder structure, and select as the default path
    # if exists
    if not default_path:
        for f in os.scandir("."):
            if f.is_dir() and f.name[0] not in '._' and 'env' not in f.name:
                ip_dirs = ['docs', 'scripts', 'styles']
                ip_files = [HTML_FILE_NAME, '.gitignore']
                for sub_f in os.scandir(f.path):
                    if sub_f.is_dir():
                        try:
                            ip_dirs.remove(sub_f.name)
                        except ValueError:
                            continue
                    elif sub_f.is_file():
                        try:
                            ip_files.remove(sub_f.name)
                        except ValueError:
                            continue
                if not ip_dirs and not ip_files:
                    # Interactive Paper folder found
                    docs_dirpath = os.path.join(f.path, 'docs')
                    default_path = docs_dirpath

    return default_path

def prompt_source_path():
    """
    Ask user for a root path where all the submissions are.
    """
    
    question = [
        {
            'type':'input',
            'name':'source_path',
            'message': 'Enter source path',
            'filter': lambda x: x.strip(),
            'validate': validte_source_path,
            'default': get_default_source_path()
        }
    ]
    answer = prompt(question).get('source_path', '')
    if not answer:
        if os.path.isfile(RECENT_SRC_PATH_FILE):
            try:
                os.remove(RECENT_SRC_PATH_FILE)
            except FileNotFoundError:
                pass
        raise KeyboardInterrupt
    with open(RECENT_SRC_PATH_FILE, "w") as f:
        f.write(answer)
    
    return answer

def prompt_choose_dirs(path_str):
    """
    Ask user to choose folders to grade. Chosen folders must contain HTML_FILE_NAME file to grade
    """
    # List all subdirectories
    dirs = []
    files = os.scandir(path_str)
    for f in files:
        if f.is_dir():
            dirs.append({
                'name': f.name,
                'value': f.path,
                'checked': 'True'
            })
    # Ask user to choose multiple
    question = [
        {
            'type': 'checkbox',
            'name': 'chosen_dirs',
            'message': 'Select folders to grade',
            'choices': dirs
        }
    ]
    chosen_dirs = prompt(question).get('chosen_dirs', [])
    if not chosen_dirs:
        raise KeyboardInterrupt
    return chosen_dirs

def check_syntax(filename:str):
    """
    Check that the given file is formatted correctly and whether it contains any syntax errors.

    filepath
        Path to a code file supported by prettier.
    """
    # Requires prettier to be installed in system
    # Prettier exit codes:
    #   0: Everything formatted properly
    #   1: Something wasn't formatted properly
    #   2: Something's wrong with Prettier

    check_syntax_result = {
        'passed': True,
        'output': ''
    }

    try:
        prc = subprocess.run(["prettier", "-c", filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True, encoding='utf-8')
    except subprocess.CalledProcessError as err:
        if err.returncode == 2:
            check_syntax_result['passed'] = False
            prettier_output = err.output
            prettier_output = prettier_output.split("\n")
            prettier_output = [output for output in prettier_output \
                if ('Checking formatting...' not in output and 'All matched files use Prettier code style!' not in output)]
            prettier_output = "\n".join(prettier_output)
            check_syntax_result['output'] = prettier_output
    
    return check_syntax_result

def grade_directory(dirpath):
    # Grade result
    grading_result = {
        'error': False,
        'message': '',
        'check_syntax_passed': False,
        'check_footnotes_passed': False
    }

    # Find index.html in given directory 'dirpath'
    html_file_path = ''
    for f in os.scandir(dirpath):
        if f.name == HTML_FILE_NAME:
            html_file_path = f.path

    # index.html not found
    if not html_file_path:
        grading_result['error'] = True
        grading_result['message'] = f"HTML_FILE_NAME not found in directory '{dirpath}'."
        return grading_result
    
    # Check syntax
    check_syntax_result = check_syntax(html_file_path)
    grading_result['check_syntax_passed'] = check_syntax_result['passed']
    with open(os.path.join(dirpath, "GRADING_FEEDBACK.txt"), "w") as f:
        f.write("1. Syntax Check Results\n\n")
        if not check_syntax_result['passed']: 
            if check_syntax_result['output']:            
                f.write("Syntax error(s) found. The details of the first(if many) syntax error found is shown below.\n\n")
                f.write(check_syntax_result['output'])
                f.write("\n\n")
        else:
            f.write("No syntax error found. Well done!\n\n\n")
    
    # Check footnotes
    analysis_result, analysis_string = ip_analysis.run_analysis(html_file_path)
    grading_result['check_footnotes_passed'] = analysis_result
    if not analysis_result and analysis_string:
        with open(os.path.join(dirpath, "GRADING_FEEDBACK.txt"), "a") as f:
            f.write("2. Footnote Analysis Results\n\n")
            f.write(analysis_string)

    return grading_result

def check_result(result:bool)->str:
    if result:
        return '\u2705 Passed'
    return '\u274c Failed'

def main():
    try:
        source_path = prompt_source_path()
        
        # If index.html in chosen path, start grading the entered folder
        # If not, make user choose from subfolders
        files_in_src_path = [f.name for f in os.scandir(source_path)]
        if HTML_FILE_NAME in files_in_src_path:
            chosen_dirs = [source_path]
        else:
            chosen_dirs = prompt_choose_dirs(source_path)

        print("Starting automated grading...", flush=True)
        for idx, dirpath in enumerate(chosen_dirs):
            grading_result = grade_directory(dirpath)
            print(f"[{idx + 1}/{len(chosen_dirs)}]  <{os.path.basename(dirpath)}>")
            if grading_result['error']:
                print(f"\tError: {grading_result['message']}")
            else:
                print(f'\tSyntax check   : {check_result(grading_result["check_syntax_passed"])}')
                print(f'\tFootnotes check: {check_result(grading_result["check_footnotes_passed"])}')
            print()
        print("Grading complete!")
        print("Check 'GRADING_FEEDBACK.txt' files in each target folders for detailed grading results.")
    except KeyboardInterrupt:
        sys.exit(1)

if __name__ == "__main__":
    main()