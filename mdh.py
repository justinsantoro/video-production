#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Markdown Helper

this script aids in the creation and
editing of storyboards as markdown files.

Usage:
    pass command line arguments from root directory of repo:

        ./mdh {command} {args ...}

Commands:
    dir {workdir}
        - sets the directory you want to work in.

    dir?
        - returns the name of the current working directory.

    build
        - builds a _storyboard.md template from the _vo.md in the working directory

    split {rowid} {text ...} {--img}(optional)
        - splits a row in the _storyboard.md in working directory
        after the sequence of given VO {text ...}. If --img flag is set then
        the names of the storyboard .svg files will be refactored.

    remove {rowid} {--img}(optional)
        - removes a row from the _storyboard.md in working directory. If --img flag is set then
        the names of the storyboard .svg files will be refactored.

Examples:
    ./mdh dir decredPoliteia
        - sets ./decredpoliteia as working directory

    ./mdh dir?
        - prints "./decredPoliteia"

    ./mdh build
        - creates decredPoliteia_storyboard.svg using decredPoliteia_vo.md as input.
        Also creates ./decredPoliteia/img/ if it doesnt already exist.

    ./mdh split 3 proposal system --img
        - splits row 3 of decredPoliteia_storyboard.md moving the voice over text after
        "proposal system" to a new row 4 and increments the original
        row 4 to row 5 etc... and refactors .svg file names.
"""


import copy
import os
import sys


class Row(object):
    """Object representing one row in a _storyboard.md file.

    Constructed based on a list of strings representing
    cells of a row.
    """

    def __init__(self, row=list()):
        self.i = int(row[0])
        self.visual = row[1]
        # if visual contains img link
        if self.visual[1] == '!':
            # get local img path
            self.img_path = self.visual.split('(')[1].split(')')[0][1:]
        else:
            self.img_path = False
        self.vo = row[2]
        self.time = row[3]

    def build(self):
        """Returns self as formatted md table row string.

        :return: str() - formatted md storyboard table row
        """

        return '| {} |{}|{}|{}|\n'.format(str(self.i),
                                     self.visual,
                                     self.vo,
                                     self.time)

    def split(self, id):
        """Splits self.vo after given text id.
        Returns second half for inclusion in new row.

        :param id: str() - id of where to split vo text
        :return: str() - second half of split vo text
        """
        vo = self.vo.split(' ')[1:-1]
        x = 0
        for i, word in enumerate(vo):
            if word in id:
                x += 1
                if x == len(id):
                    self.vo = build_sentence(vo[:i+1])
                    return build_sentence(vo[i+1:])

    def increment(self):
        """Increments index column and img path.

        ":return: None
        """
        self.i = self.i+1
        if self.img_path:
            self.visual = self.visual.replace(str(self.i-1), str(self.i))
            self.img_path = self.img_path.replace(str(self.i-1), str(self.i))

    def decrement(self):
        """Increments index column and img path.

                ":return: None
                """
        self.i = self.i - 1
        if self.img_path:
            self.visual = self.visual.replace(str(self.i + 1), str(self.i))
            self.img_path = self.img_path.replace(str(self.i + 1), str(self.i))

    def rename_img_up(self):
        """increments img filename in ./{workdir}/img/

        :return: None
        """
        if self.img_path:
            os.rename(os.path.abspath(self.img_path.replace(str(self.i), str(self.i-1))),
                    os.path.abspath(self.img_path))

    def rename_img_down(self):
        """decrements img filename in ./{workdir}/img/

        :return: None
        """
        if self.img_path:
            os.rename(os.path.abspath(self.img_path.replace(str(self.i), str(self.i+1))),
                    os.path.abspath(self.img_path))

# MAIN FUNCTIONS


def check_dir():
    """Checks the current set working directory by
    reading ./mdh.conf.

    :return: str() - Name of current working directory.
    """
    dir = read_f('./mdh.conf')[0].replace('\n', '')
    if dir == '':
        print('working directory not set! Set with [dir].')
        exit()
    else:
        return dir


def set_dir(dir):
    """sets the current working directory by
    writing to ./mdh.conf.

    :param dir: str() - name of working directory
    :return: None
    """
    if os.path.isdir('./{}'.format(dir)):
        write_f('./mdh.conf', [dir])
    else:
        print('Subdirectory ./{} does not exist!'.format(dir))


def split_row(path, row_id, text, img):
    """Splits specified storyboard row into two,
    writes updated storyboard file, and renames
    svg files in ./{workingDir}/img/ if flag set.

    :param path: str() - file path to be edited
    :param row_id: int() - row # to be split
    :param text: list( str(), ... ) - text to determine where to split VO string
    :param img: bool() - whether or not to refactor storyboard img directory.
    :return: None
    """

    def increment_img():
        """increment storyboard svg file names

        :return: None
        """
        for r in reversed(table[row_id+1:]):
            r.rename_img_up()
        return None

    header, table = parse_story(path)
    new_vo = table[row_id-1].split(text)
    new_row = copy.copy(table[row_id-1])
    new_row.vo = new_vo
    table.insert(row_id, new_row)

    # loop through list of Rows and increment them.
    i = row_id
    while row_id <= i < len(table):
        table[i].increment()
        i += 1

    # build updated storyboard lines of entire file
    lines = header
    for row in table:
        lines.append(row.build())

    #print(lines)

    # write file
    write_f(path, lines)
    if img:
        increment_img()


def delete_row(path, row_id, img):
    """Removes a row from a storyboard,
    writes updated storyboard file, and renames
    svg files in ./{workingDir}/img/ if flag set

    :param path: str() - file path to be edited
    :param row_id: int() - row # to be deleted
    :param img: bool() - whether or not to refactor storyboard img directory.
    :return: None
    """

    def decrement_img():
        """decrement storyboard svg file names

        :return: None
        """
        # delete the image corresponding to the deleted row.
        try:
            if del_image:
                os.remove(del_image)
        except FileNotFoundError:
            print(table[row_id].img_path + 'not found!')

        #decrement the following images
        for r in table[row_id - 1:]:
            r.rename_img_down()
        return None

    header, table = parse_story(path)
    del_image = table[row_id-1].img_path
    del table[row_id -1]

    # loop through list of Rows and decrement them.
    for row in table[row_id-1:]:
        row.decrement()

    # build updated storyboard lines of entire file
    lines = header
    for row in table:
        lines.append(row.build())

    # write file
    write_f(path, lines)
    if img:
        decrement_img()


def gen_story(i, o, dir):
    """Generates a markdown storyboard template file based on the input
    VO script

    :param i: str() - path to input VO script
    :param o: - str() - path of output storyboard file
    :param dir: - str() - working directory for building img links
    """
    # build storyboard and write
    write_f(o, build_story(read_f(i), dir))

    # check and create storyboard /img dir
    if not os.path.isdir('./{}/img'.format(dir)):
        os.mkdir('./{}/img'.format(dir))


# HELPER FUNCTIONS


def build_sentence(words):
    """Build a sentence from list of words

    :param words: list( str(), ... ) - list of word strings
    :return: None
    """
    sentence = ' '
    for i, word in enumerate(words):
        sentence += word + ' '
    return sentence

def read_f(path):
    """Read file from path

    :param path: str() - file path to read.
    :return: list( str(), ...) - list of strings representing each line of file
    """
    with open(path, "r") as f:
        return f.readlines()


def write_f(path, lines):
    """Write file to path from list of lines.

    :param path: str() - file path to write.
    :param lines: list( str(), ... ) - list of lines to write.
    :return: None
    """
    with open(path, "w") as f:
        for line in lines:
            f.write(line)


def build_story(lines, dir):
    """Generates a _storyboard.md based on
    an input _vo.md

    :param lines: list( str(), ... ) - _vo.md lines
    :param dir: str() - working directory
    :return: list( str(), ... ) - _story.md lines
    """
    skip = ['#', '`', '*', '\n', ' ']
    story_lines = [ lines[0],
                    '\n',
                   '### Storyboard\n',
                   '**Estimated Runtime:**\n',
                   '\n',
                   '| No. | VISUAL | AUDIO | TIME\n',
                   '| :-: | :----: | :--- | :--:\n'
                ]
    i = 1
    for line in lines:
        if line[0] in skip:
            pass
        else:
            story_lines.append(
                '| {} | ![shot {}](../{}/img/shot_{}.svg) | {} |  |\n'.format
                (i, i, dir, i, line[:-1])
            )
            i += 1
    return story_lines


def parse_story(path):
    """Parses _storyboard.md file into a list of header lines and
    another list of table rows as Row objects

    :param path: str()
    :return: list( str(), ... ), list( Row(), ... )
    """
    lines = read_f(path)
    # TODO: allow for variable header formats
    header = lines[:7]
    table_lines = lines[7:]
    #print(header)
    table = []
    for line in table_lines:
        table.append(Row(line.split('|')[1:]))
    return header, table


# ARG PARSING


def confirm(x):
    """determine if user confimed change or not

    :param x: str()
    :return: bool()
    """
    if x.lower() == 'y':
        return True
    else:
        print('cancelled')
        exit()


def parse_args():
    """Parse input user args
    
    :return: None
    """
    x_args = ['build', 'split', 'dir', 'dir?', 'remove']
    i_args = sys.argv[1:]

    if i_args[0] not in x_args:
        print('Unknown command. Use ' + str(x_args))
    else:
        if i_args[0] == 'dir':
            set_dir(i_args[1])
        elif i_args[0] == 'dir?':
            dir = check_dir()
            print('working dicrectory: ./{}'.format(dir))
        dir = check_dir()
        if i_args[0] == 'build':
            i = './{}/{}_script.md'.format(dir, dir)
            o = './{}/{}_storyboard.md'.format(dir, dir)
            if os.path.isfile(o):
                confirm(input('{} Already Exists! overwrite? Y/n: '.format(o, i)))
            gen_story(i, o, dir)
        elif i_args[0] == 'split':
            img = False
            row_id = int(i_args[1])
            if i_args[-1] == '--img':
                text = i_args[2:-1]
                img = True
            # print(img)
            else:
                text = i_args[2:]
            i = './{}/{}_storyboard.md'.format(dir, dir)
            if confirm(input('split row {} in storyboard {} at "{}"? Y/n: '.format(
                    row_id, i, text))):
                split_row(i, row_id, text, img)
        elif i_args[0] == 'remove':
            img = False
            row_id = int(i_args[1])
            if i_args[-1] == '--img':
                img = True
            # print(img)
            i = './{}/{}_storyboard.md'.format(dir, dir)
            if confirm(input('Remove row {} in storyboard {} ? Y/n: '.format(
                    row_id, i))):
                delete_row(i, row_id, img)


if __name__ == '__main__':
    parse_args()
