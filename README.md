# Interactive Papers Grader

## Prerequisites
Make sure [Python3](https://www.python.org/downloads/) is installed in your system. For Windows users, make sure [to add Python to your PATH environment variable](https://docs.python.org/3/using/windows.html#excursus-setting-environment-variables).
Run the following command to check that everything is set.
```
python3 --version
```
You should see the following output, with the 'x's replaced with the actual version number of the Python installed in your system. As long as it starts with 3, you are good to go.
```
Python 3.x.x
```

## Getting Ready
You only have to follow the instructions in this section one time.
### 1. Downloading the source code
```
git clone https://github.com/seanK200/interactive-papers-grader.git
cd interactive-papers-grader/
```
### 2. Python Virtual Environment (optional, recommended)
The Interactive Paper grader depends on external packages to run properly, and you must install them before running the program.However, before you do so, you may want to setup and activate a [Python virtual environment](https://docs.python.org/3/tutorial/venv.html). This basically means all the downloads that will occur in the following steps will be downloaded to this directory, and will not be installed globally on your system. This will make it easier to delete unnecessary files when you are done with this project and prevent clogging up your system.

As an example, the below command initializes a virtual environment named `env` on the working directory using [venv](https://docs.python.org/3/library/venv.html).
```
python3 -m venv env
```

### 3. Activating the Python Virtual Environment
You only need to do this step if you have done step 2.
#### Windows
```
env\Scripts\activate.bat
```
#### Unix, macOS
```
source env/bin/activate
```

### 4. Installing dependencies
The Interactive Paper grader depends on external packages to run properly. Automatically install all of them by invoking the following commands.
```
python3 -m pip install -U pip setuptools wheel
python3 -m pip install -r requirements.txt
```

## Usage
### Download the student submissions
It is recommended to download the submissions in the same folder as the 'grader.py' script. If the download contains the entire source code of Interactive Papers (complete with `docs`, `scripts`, `styles` directories), **and** it is in the same directory as the grader script, the program will automatically detect its presence.

### Run the grader
```
python3 grader.py
```

### Enter directory to grade
Enter the path to the **FOLDER**(not to a source FILE) where the Interactive Paper HTML file is located when prompted.
```
? Enter source path: ./interactive-papers/docs/week1
```

The folder you entered above can be either of the following:

#### Case 1
The folder contains subfolders that contain one or more Interactive Paper html file(s).

Example: week0
```
interactive-papers/docs/week0
├── group1
│   ├── images
│   └── index.html
├── group2
│   ├── images
│   └── index.html
└── group3
    ├── images
    └── index.html
```

#### Case 2
The folder contains one or more Interactive Paper html file.

Example: group1
```
interactive-papers/docs/week0/group1
├── images
└── index.html
```

### Choose subdirectories (Case 1)
If needed (**Case 1**), you will be asked to choose the subfolders to grade. Use the up/down arrow keys and the space key to select folders.
> Tip: Hit the 'a' key to select (a)ll
```
? Select folders to grade (<up>, <down> to move, <space> to select, <a> to toggle, <i> to invert)
 ○ group1
 ○ group2
 ○ group3
```

### Viewing grading results
After some time the grading will be finished. Check the console output for a summary of the grading results. A more detailed report file will be generated in each target folder(s), which you can view by opening `GRADING_FEEDBACK.txt`.

## License
This project is licensed using the MIT license (see LICENSE).