import os, sys, subprocess
import ip_analysis

VERSION = 1.0
RECENT_SRC_PATH_FILE = 'recent_source_path.txt'
HTML_FILE_NAME = 'index.html'
FEEDBACK_FILE_NAME = 'GRADING_FEEDBACK.txt'

# Check for dependencies
# Python deps
try:
    from PyInquirer import prompt
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    print("Error: Depenedent packages not found.")
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
    print("Error: Dependencies not found (prettier).")
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
    
    # If recently used filepath no longer exists
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
                    default_path = os.path.join(f.path, 'docs')

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
    grading_results = [] # Return value
    
    # Find index.html in given directory 'dirpath'
    html_file_paths = []
    for f in os.scandir(dirpath):
        if '.html' in f.name:
            html_file_paths.append(f)

    first_file_in_directory = True

    for html_file in html_file_paths:
        # Grade result
        grading_result = {
            'filename': html_file.name,
            'error': False,
            'message': '',
            'check_syntax_passed': False,
            'check_footnotes_passed': False,
        }

        html_file_path = html_file.path
        # index.html not found
        if not html_file_path:
            grading_result['error'] = True
            grading_result['message'] = f"HTML_FILE_NAME not found in directory '{dirpath}'."
            return grading_result
        
        # Check syntax
        check_syntax_result = check_syntax(html_file_path)
        grading_result['check_syntax_passed'] = check_syntax_result['passed']
        if first_file_in_directory:
            file_open_mode = 'w'
            first_file_in_directory = False
        else:
            file_open_mode = 'a'

        with open(os.path.join(dirpath, FEEDBACK_FILE_NAME), file_open_mode) as f:
            f.write(f'<{html_file.name}>\n\n')
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
        grading_result['check_footnotes_passed'] = analysis_result['passed']
        # If no footnote was found in HTML, issue a warning
        if not analysis_result['correct_count'] and not analysis_result['problematic_count']:
            grading_result['message'] = "Warning: No footnotes found. Are you sure this is an Interactive Paper file?"
        if not analysis_result['passed'] and analysis_string:
            with open(os.path.join(dirpath, FEEDBACK_FILE_NAME), "a") as f:
                f.write("2. Footnote Analysis Results\n\n")
                f.write(analysis_string)
        
        grading_results.append(grading_result)

    return grading_results

def check_result(result:bool)->str:
    if result:
        return '\u2705 Passed'
    return '\u274c Failed'

def main():
    print(f"Interactive Paper Grader Version {VERSION}", end="\n\n", flush=True)
    try:
        source_path = prompt_source_path()
        
        # If one or more html file(s) exist in chosen path, start grading
        filenames_in_src_path = [f.name for f in os.scandir(source_path)]
        chosen_dirs = []
        for filename in filenames_in_src_path:
            if '.html' in filename:
                chosen_dirs = [source_path]
                break
        # If not, make user choose from subfolders
        if not chosen_dirs:
            chosen_dirs = prompt_choose_dirs(source_path)

        print("Starting automated grading...", flush=True)
        for idx, dirpath in enumerate(chosen_dirs):
            grading_results = grade_directory(dirpath)
            print(f"[{idx + 1}/{len(chosen_dirs)}]  <{os.path.basename(dirpath)}>")
            for grading_result in grading_results:
                print(f"'{grading_result['filename']}'")
                if grading_result['error']:
                    print(f"\tError: {grading_result['message']}")
                else:
                    print(f'\tSyntax check   : {check_result(grading_result["check_syntax_passed"])}')
                    print(f'\tFootnotes check: {check_result(grading_result["check_footnotes_passed"])}')
                    if grading_result['message']:
                        print(grading_result['message'])
                print()
        print("Grading complete!")
        print(f"Check '{FEEDBACK_FILE_NAME}' files in each target folders for detailed grading reports.")
    except KeyboardInterrupt:
        sys.exit(1)

if __name__ == "__main__":
    main()