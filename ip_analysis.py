# ip_analysis = Interactive Paper Analysis Module

import sys
from bs4 import BeautifulSoup

ORPHANED_FOOTNOTE_DESCRIPTION = """   Orphaned footnotes are footnotes without a matching footnote link(a tags).
   In other words, there is no way to view an orphaned footnote at the webpage."""
BROKEN_FOOTNOTE_DESCRIPTION = """   Broken footnotes are footnote links without matching content.
   In other words, nothing will be displayed when a broken footnote link is clicked."""
DUPLICATE_FOOTNOTE_DESCRIPTION = """   Footnotes with duplicates mean that there are multiple footnote contents with the same ID.
   Footnote IDs must be unique across an entire Interactive Paper document."""
EMPTY_ID_FOOTNOTE_DESCRIPTION = """   All footnote links must either have a non-empty inner text or a non-empty 'data-ip-footnote-id' attribute.
   All footnote content divs must have a non-empty id attribute."""

MAX_COLUMN = 56

class Footnote:
    def __init__(self, footnote_id:str):
        self._footnote_id = footnote_id
        self._links = []
        self._contents = []
    
    @property
    def links(self):
        return self._links
    
    @links.setter
    def links(self, value):
        # In case there are multiple links to a single footnote
        self._links.append(value)
    
    @links.deleter
    def links(self):
        while self._links:
            del self._links[0]
        del self._links

    @property
    def contents(self):
        return self._contents
    
    @contents.setter
    def contents(self, value):
        # In case of duplicates
        self._contents.append(value)
    
    @contents.deleter
    def contents(self):
        while self._contents:
            del self._contents[0]
        del self._contents
    
    @property
    def footnote_id(self):
        f_id = ''
        # Handle special case of empty id
        if self._footnote_id == '__EMPTY_ID__':
            return f_id
        
        f_id = self._footnote_id
        # Remove line breaks, consecutive whitespaces
        f_id.replace("\n", " ")
        f_id = " ".join(f_id.split())
        
        # Truncate footnote id if it is too long
        if len(f_id) > MAX_COLUMN + 15:
            f_id = f_id[:MAX_COLUMN + 15 - 3] + '...'
        
        return f_id
    
    def get_link_text(self, link_elem=None)->str:
        # Get the tag as string
        link_text = str(link_elem)

        # Split it into lines
        link_text_lines = link_text.split("\n")
        
        # If one line is too long, truncate
        link_text_trunc = []
        for line in link_text_lines:
            if len(line) > MAX_COLUMN:
                line = line[:MAX_COLUMN - 3] + '...'
            link_text_trunc.append(line)
        
        # If the tag is more than 3 lines long, truncate
        if len(link_text_trunc) > 3:
            link_text_trunc = link_text_trunc[:3]
            link_text_trunc.append("...")

        # Join linebreaks with a replace string for proper formatting
        linebreak_replace = '\n' + '\t' + (' ' * 12) + '|  '
        return linebreak_replace.join(link_text_trunc)
    
    def get_content_text(self, content_elem=None)->str:
        # Get the tag as string
        content_text = str(content_elem)

        # Split it into lines
        content_text_lines = content_text.split("\n")
        
        # If one line is too long, truncate
        content_text_trunc = []
        for line in content_text_lines:
            if len(line) > MAX_COLUMN:
                line = line[:MAX_COLUMN - 3] + '...'
            content_text_trunc.append(line)
        
        # If the tag is more than 3 lines long, truncate
        if len(content_text_trunc) > 3:
            content_text_trunc = content_text_trunc[:3]
            content_text_trunc.append("...")

        # Join linebreaks with a replace string for proper formatting
        linebreak_replace = '\n' + '\t' + (' ' * 12) + '|  '
        return linebreak_replace.join(content_text_trunc)
    
    def is_problematic(self):
        """
        Check if a footnote is problematic
        """
        # Only content, no link
        orphaned = not bool(self._links)
        # No content for link (nothing to display when clicked upon)
        broken = not bool(self._contents)
        # Multiple contents with same ID
        duplicates = len(self._contents) > 1
        # If ID is empty
        empty_id = self._footnote_id == '__EMPTY_ID__'

        problematic = orphaned or broken or duplicates or empty_id

        return dict(problematic=problematic, 
                        orphaned=orphaned,
                        broken=broken,
                        duplicates=duplicates,
                        empty_id=empty_id)
    
    def __str__(self):
        """
        Returns footnote as a string
        """
        footnote_str = '' # Return value
        problems = self.is_problematic()
        
        problems_str = ''
        if problems['problematic']:
            if problems['empty_id']:
                problems_str += 'EMPTY ID'
            else:
                if problems['orphaned']:
                    problems_str += 'ORPHANED'
                if problems['broken']:
                    if problems_str:
                        problems_str += ', '
                    problems_str += 'BROKEN'
                if problems['duplicates']:
                    if problems_str:
                        problems_str += ', '
                    problems_str += 'DUPLICATES'
            problems_str = ' (' + problems_str + ')'

        # Separator
        header = f"  FOOTNOTE{problems_str}  "
        footnote_str += '{:-^79}'.format(header) + '\n'

        # ID
        footnote_str += "  * FOOTNOTE ID\n"
        if problems['empty_id']:
            footnote_str += '\t' + '(empty)' + '\n'
        else:
            footnote_str += '\t' + self.footnote_id + '\n'
        footnote_str += '\n'

        # Link(s)
        footnote_str += f"  * LINK{'S' if len(self._links) > 1 else ''} ({len(self._links)})\n"
        if problems['orphaned'] and not problems['empty_id']:
            footnote_str += "\tNo link found (orphaned).\n"
        else:
            for link_elem in self._links:
                link_text = self.get_link_text(link_elem)
                footnote_str += f"\tLine {'{:5d}'.format(link_elem.sourceline)}  |  {link_text}\n"
        footnote_str += '\n'
        
        # Content(s)
        footnote_str += f'  * CONTENT{"S" if problems["duplicates"] else ""} '
        footnote_str += f'({len(self._contents)}{" duplicates" if problems["duplicates"] else ""})\n'
        if problems['broken'] and not problems['empty_id']:
            footnote_str += "\tNo content found (broken).\n"
        else:
            for content_elem in self._contents:
                content_text = self.get_content_text(content_elem)
                footnote_str += f"\tLine {'{:5d}'.format(content_elem.sourceline)}  |  {content_text}\n"
        
        # Seperator
        footnote_str += "-"*79
        return footnote_str

def parse_file(filepath:str):
    """
    Read from the given HTML file and parse the HTML code to look for footnotes

    filepath
        Path to a file containing HTML code of a Interactive Paper
    """
    try:
        with open(filepath, 'r') as codefile:
            soup = BeautifulSoup(codefile, "html.parser")
    except FileNotFoundError:
        print("File not found.")
        sys.exit(1)
    
    # Footnote links are anchor(<a>) tags without href attribute
    anchors = soup.select("a")
    footnote_links = []
    for a in anchors:
        if not a.get('href', ''):
            footnote_links.append(a)
    footnote_contents = soup.select("div.footnote")

    # Dictionary of Footnote class objects
    found_footnotes = dict()

    # Create footnote objects while iterating over links
    for link_elem in footnote_links:
        if link_elem.get('data-ip-footnote-id', ''):
            footnote_id = link_elem.get('data-ip-footnote-id')
        else:
            footnote_id = str(link_elem.string)
        if not footnote_id:
            footnote_id = '__EMPTY_ID__'
            # raise ValueError(f'Empty footnote id while parsing tag: {str(link_elem)}')
        
        if footnote_id in found_footnotes:
            found_footnotes[footnote_id].links = link_elem
        else:
            footnote_obj = Footnote(footnote_id)
            footnote_obj.links = link_elem
            found_footnotes[footnote_id] = footnote_obj
    
    # Check for content corresponding to that footnote ID
    for content_elem in footnote_contents:
        footnote_id = content_elem.get('id', '')
        if not footnote_id:
            footnote_id = '__EMPTY_ID__'
            # raise ValueError(f'Empty footnote id while parsing tag: {str(content_elem)}')

        footnote = found_footnotes.get(footnote_id, None)
        if footnote:
            footnote.contents = content_elem
        else:
            # Orphaned footnote
            new_footnote = Footnote(footnote_id)
            new_footnote.contents = content_elem
            found_footnotes[footnote_id] = new_footnote
    
    return found_footnotes

def check_footnotes(footnotes:list[Footnote])->tuple[int, int, dict]:
    """
    Check if parsed footnotes have problems, and categorize them into appropriate lists

    (Returns)
        correct_count:int
            The number of correctly written footnotes
        problematic_count:int
            The number of footnotes with one or more problems
        problematic_footnotes:dict
            (key) 'orphaned' (value) list[Footnotes]
            (key) 'broken' (value) list[Footnotes]
            (key) 'duplicates' (value) list[Footntoes]
    """
    # Init
    correct_count = 0
    problematic_count = 0
    problematic_footnotes = {
        'orphaned': [],
        'broken': [],
        'duplicates': [],
        'empty_id': []
    }
    
    # For every footnote
    for footnote_obj in footnotes.values():
        # Check if it is problematic
        problems = footnote_obj.is_problematic()
        problematic = problems['problematic']
        if not problematic:
            correct_count += 1
            continue
        
        # If it is problematic, add to appropriate lists
        problematic_count += 1
        is_orphaned = problems['orphaned']
        is_broken = problems['broken']
        duplicates_exist = problems['duplicates']
        empty_id = problems['empty_id']

        if empty_id:
            problematic_footnotes['empty_id'].append(footnote_obj)
        elif is_orphaned:
            problematic_footnotes['orphaned'].append(footnote_obj)
        elif is_broken:
            problematic_footnotes['broken'].append(footnote_obj)
        elif duplicates_exist:
            problematic_footnotes['duplicates'].append(footnote_obj)
    
    return correct_count, problematic_count, problematic_footnotes

def get_problems_string(problematic_footnotes):
    problems_str = '' # Return value

    orphaned = problematic_footnotes['orphaned']
    broken = problematic_footnotes['broken']
    duplicates = problematic_footnotes['duplicates']
    empty_id = problematic_footnotes['empty_id']

    # Orphaned footnotes
    if orphaned:
        problems_str += f">> Found {len(orphaned)} orphaned footnote{'s' if len(orphaned) > 1 else ''}.\n"
        problems_str += ORPHANED_FOOTNOTE_DESCRIPTION + "\n\n"
        for footnote_obj in orphaned:
            problems_str += str(footnote_obj) + "\n\n"
        problems_str += '\n'
    
    # Broken footnotes
    if broken:
        problems_str += f">> Found {len(broken)} broken footnote{'s' if len(broken) > 1 else ''}.\n"
        problems_str += BROKEN_FOOTNOTE_DESCRIPTION + "\n\n"
        for footnote_obj in broken:
            problems_str += str(footnote_obj) + "\n\n"
        problems_str += '\n'
    
    # Footnotes with duplicates
    if duplicates:
        problems_str += f">> Found {len(duplicates)} footnote{'s' if len(duplicates) > 1 else ''} with duplicates.\n"
        problems_str += DUPLICATE_FOOTNOTE_DESCRIPTION + "\n\n"
        for footnote_obj in duplicates:
            problems_str += str(footnote_obj) + "\n\n"
        problems_str += '\n'
    
    # Footnote links/contents with the id attribute empty
    if empty_id:
        problems_str += f">> Found {len(empty_id)} footnote{'s' if len(empty_id) > 1 else ''} with an empty id attribute.\n"
        problems_str += EMPTY_ID_FOOTNOTE_DESCRIPTION + '\n\n'
        for footnote_obj in empty_id:
            problems_str += str(footnote_obj) + '\n\n'
    
    return problems_str

def get_analysis_string(correct_count, problematic_count, problematic_footnotes)->str:
    analysis_string = '' # Return value
    analysis_string += f"Found {correct_count} correctly formatted footnote{'s' if correct_count else ''}.\n"
    analysis_string += f"Found {problematic_count} incorrectly formatted footnote{'s' if problematic_count else ''}"
    if problematic_count:
        analysis_string += ' (details listed below).\n'
    else:
        analysis_string += '.'
    analysis_string += '\n'

    # Get all the problems
    analysis_string += get_problems_string(problematic_footnotes)
    return analysis_string

def run_analysis(filepath:str)->tuple[dict, str]:
    """
    Run check on the given Interactive Paper HTML code.

    filepath
        Path to an HTML file containing Interactive Paper code.

    (Return)
        analysis_result:dict
            passed:bool
                True when all footnotes are used correctly, False otherwise.
            correct_count:int
                Number of correctly formatted footnotes
            problematic_count:int
                Number of incorrectly formatted footnotes
        analysis_string:str
            String containing explanation of check result
    """
    found_footnotes = parse_file(filepath)
    correct_count, problematic_count, problematic_footnotes = \
        check_footnotes(found_footnotes)
    analysis_string = \
        get_analysis_string(correct_count, problematic_count, problematic_footnotes)
    
    analysis_result = {
        'passed': problematic_count == 0 and correct_count > 0,
        'correct_count' : correct_count,
        'problematic_count': problematic_count
    }
    
    return analysis_result, analysis_string

def main():
    """
    Runner code when the module is run directly
    """
    filepath = input("Enter file path: ")
    found_footnotes = parse_file(filepath)
    correct_count, problematic_count, problematic_footnotes = \
        check_footnotes(found_footnotes)
    analysis_string = \
        get_analysis_string(correct_count, problematic_count, problematic_footnotes)

    print(analysis_string)

if __name__ == "__main__":
    main()