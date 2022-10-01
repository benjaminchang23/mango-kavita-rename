import argparse
from distutils.log import debug
import json
import os
from typing import List

from re import match as reg_match
from re import search as reg_search

parser = argparse.ArgumentParser(description="modify directory structure of mango output.")
parser.add_argument("--inputfields", required=True, help="JSON file containing all the required fields.")
parser.add_argument("--debug", required=False, action="store_true", help="debug printout.")

args = parser.parse_args()

debug = False
if args.debug:
    print("allow debug")
    debug = True

def DebugPrint(output : str):
    if debug:
        print(output)

def ReadInputJson(jsonFile):
    fp = open(jsonFile, "r")
    inputs = json.load(fp)
    target_directory = inputs.get("target_directory")
    return target_directory

def GetChapterChapterNum(chapter_name : str) -> str:
    search_res = reg_search("^.*Ch\. ([0-9\.]+?)\.cbz$", chapter_name)
    if search_res is not None:
        return search_res.group(1)

    return None

def GetChapterTitle(chapter_name : str) -> str:
    if reg_match("^.*Vol\. [0-9]+ Ch\. [0-9\.]+\.cbz", chapter_name):
        DebugPrint("with Vol. : {}".format(chapter_name))
        search_res = reg_search("^(.+?) Vol. [0-9]+ Ch\. [0-9\.]+\.cbz$", chapter_name)
    elif reg_match("^.*Ch\. [0-9\.]+\.cbz$", chapter_name):
        DebugPrint("without Vol : {}".format(chapter_name))
        search_res = reg_search("^(.+?).*Ch\. [0-9\.]+\.cbz$", chapter_name)
    if search_res is not None:
        return search_res.group(1)

    return None

def GetChapterVolumeNum(chapter_name : str) -> str:
    search_res = reg_search("^.*Vol\. ([0-9]+?) Ch\. [0-9\.]+\.cbz$", chapter_name)
    if search_res is not None:
        return search_res.group(1)

    return None

def GetSeriesList(target_directory : str) -> List[str]:
    return [f.path for f in os.scandir(target_directory) if f.is_dir()]

def GetUnmodifiedChapterList(target_directory : str, series_name : str) -> List[str]:
    return [f.path for f in os.scandir(target_directory) if IsUnmodifiedChapter(f, series_name)]

def IsUnmodifiedChapter(dir_entry : str, series_name : str) -> bool:
    path_str = os.path.basename(dir_entry.path)
    # only get things that do not start with series name
    if reg_match("^.*Vol\. [0-9]+ Ch\. [0-9\.]+\.cbz$", path_str) and not reg_match("^{} Vol\. [0-9]+ Ch\. [0-9\.]+.*\.cbz$".format(series_name), path_str):
        DebugPrint("with Vol.: {}".format(path_str))
        return True
    if reg_match("^.*Ch\. [0-9\.]+\.cbz$", path_str) and not reg_match("^{}.*Ch\. [0-9\.]+.*\.cbz$".format(series_name), path_str):
        DebugPrint("without Vol.: {}".format(path_str))
        return True
    return False

if __name__ == "__main__":
    # read json
    (target_directory) = ReadInputJson(args.inputfields)

    # get all dir names as titles
    series_paths = GetSeriesList(target_directory)

    print("found {} series".format(len(series_paths)))

    for series_path in series_paths:
        series_name = os.path.basename(series_path)
        # print("series fullpath: {}".format(series_path))
        print("series name: {}".format(series_name))
        chapter_list = GetUnmodifiedChapterList(series_path, series_name)

        # modify each title chapter to -> title - vol/ch num - chapter title
        for chapter_path in chapter_list:
            # print("processing: {}".format(chapter_path))
            chapter_name = os.path.basename(chapter_path)

            # regex search for vol/ch name and title
            volume_number_str = GetChapterVolumeNum(chapter_name)
            chapter_number_str = GetChapterChapterNum(chapter_name)
            chapter_title_str = GetChapterTitle(chapter_name)

            # chapter number must not be none
            if chapter_number_str is None:
                print("warn: series: {} chapter: {} fail regex search for chapter number str".format(series_name, chapter_name))
                continue
            
            new_name = series_name
            if volume_number_str is not None:
                new_name = new_name + " Vol. " + volume_number_str
            new_name = new_name + " Ch. " + chapter_number_str
            if chapter_title_str is not None and chapter_title_str != series_name:
                new_name = new_name + " " + chapter_title_str
            new_name = new_name + ".cbz"
            print("new_name: {}".format(new_name))
            abs_new = os.path.join(os.path.dirname(chapter_path), new_name)
            os.rename(chapter_path, abs_new)
            print("{} renamed to {}".format(chapter_path, abs_new))
            