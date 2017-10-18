#!/usr/bin/env python2

"""
find duplicate files based on size, and md5sum, inode
calculate potential diskspace saving based on converting same files to hard
links.  Sort similar files and prompt user to unify similar files into a single
inode.

TODO: add option to sort by similar filenames/regadless of filesize and md5sum,
in order to potentially clear old versions of the same file.

Author: Amro Diab
Date: 10/05/2016

"""

import __builtin__
import itertools
import json
import os
import sys
import threading
import time

from optparse import OptionParser

from debug import print_debug
from filestructure import FileStructure, Md5Structure, WorkQueue
from processthreads import FileThread, Md5Thread
from progress import ProgressBar

CURRENT_DIR = os.getcwd()
__builtin__.exitFlag = 0


def print_report(final_dict, pretty):
    """
    Print final report of found repeated files in filestructure
    """

    total_system = 0
    for md5 in final_dict.keys():
        if len(final_dict[md5]['entries']) > 2:

            filenames = []  # to collect file names from the various inodes
            count = len(final_dict[md5]['entries'])
            size = int(final_dict[md5]['size'])
            total_size = (int(size) * count) - int(size)
            for key, value in final_dict[md5]['entries'].items():
                filenames.append((key, value))
            sys.stdout.write("md5:{}\n".format(md5))
            print "entries:"
            for file_entry in filenames:
                sys.stdout.write("name: {0}, inode: {1}\n"
                                 .format(file_entry[0], file_entry[1]))
            print
            print "single size: ", size
            print "number of files: ", count
            print "saving for cluster ", total_size
            print "\n"
            total_system += total_size
            print "-"*20
        else:
            del final_dict[md5]
    if pretty:
        print json.dumps(final_dict, indent=4, sort_keys=True)
    else:
        #print json.dumps(final_dict)
        print

    print "\n\n\nTotal potential saving entire subtree: {}".format(human_bytes(total_system))



def print_status(title):
    """Print current stage title"""

    sys.stderr.write("\n* {}\n".format(title))


def parse_options():
    """ parse commandline options """

    parser = OptionParser()

    parser.add_option("-d", "--debug", action="store_true", default=False,
                      help="turn on debug output")
    parser.add_option("-p", "--pretty_print", action="store_true",
                      default=False, help="pretty print json")
    parser.add_option("-t", "--threads", type="int", default=30,
                      help="number of threads in pool")
    parser.add_option("-f", "--ignore_dot_files", action="store_true",
                      default=False, help="do not process dot files")
    parser.add_option("-r", "--ignore_dot_dirs", action="store_true",
                      default=False, help="do not process dot dirs")
    parser.add_option("-i", "--ignore_dirs", type="str", default="",
                      help="list of comma separated directory names to ignnore")
    parser.add_option("-x", "--ignore_files", type="str", default="",
                      help="list of comma sepatated filenames to ignore")
    parser.add_option("-s", "--minimum_file_size", type="int", default=None,
                      help="minimum file size to check (bytes)")
    parser.add_option("-o", "--only_file_extension", type="str", default="",
                      help="single file extension to compare")
    (options, _) = parser.parse_args()
    return options


def human_bytes(num, suffix='B'):
    """ convert from bytes to human-readable format with unit suffix """

    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def create_threads(max_count, work_queue, thread_class):
    """
    Create new threads
    """
    # Create new threads
    thread_id = 1
    threads = []
    thread_list = list("Thread {}".format(x) for x in range(max_count))
    thread_progress = ProgressBar(max_count, fmt=ProgressBar.FULL)
    for iteration, thread_name in enumerate(thread_list):
        thread = thread_class(thread_id, thread_name, work_queue)
        thread.start()
        threads.append(thread)
        thread_id += 1
        thread_progress.print_progress(iteration)
    thread_progress.print_progress(max_count)
    return threads

def wrapper(func, args, res):
    """ wrapper for running function with threading module """
    res.append(func(*args))

def find_files(options, work_queue):
    """ Find list of files in current subtree with applied filters """
    only_file_extension = options.only_file_extension

    ignore_dot_files = options.ignore_dot_files
    ignore_dot_dirs = options.ignore_dot_dirs

    ignore_files = [x.strip() for x in options.ignore_files.split(',')]
    ignore_dirs = [x.strip() for x in options.ignore_dirs.split(',')]

    for (dirname, dirs, files) in os.walk(CURRENT_DIR):
        # strip out ignored dirs
        dirs[:] = [d for d in dirs if not d[0] == '.'] if ignore_dot_dirs else dirs
        dirs[:] = [x for x in dirs if x not in ignore_dirs]

        # strip out ignored files
        files = [f for f in files if not f[0] == '.'] if ignore_dot_files else files
        files = [x for x in files if x not in ignore_files]
        files = [x for x in files if x.endswith(only_file_extension)]

        for filename in files:
            fullpath = dirname + '/' + filename
            print_debug(fullpath)
            work_queue.put(fullpath)

def spinner_func(options, work_queue, queue_lock):
    """ Run spinner whilst file list is being created """
    res = []
    spin_thread = threading.Thread(target=wrapper,
                                   args=(find_files, (options, work_queue),
                                         res))
    spin_thread.daemon = True
    spin_thread.start()
    spinner = itertools.cycle(['-', '\\', '|', '/'])

    try:
        while spin_thread.is_alive():
            sys.stdout.write(spinner.next())  # write the next character
            sys.stdout.flush()                # flush stdout buffer (actual character display)
            sys.stdout.write('\b')            # erase the last written char
            time.sleep(0.1)
            spin_thread.join(0.2)
    except KeyboardInterrupt:
        __builtin__.exitFlag = 1
        queue_lock.release()
        sys.exit(1)

def threads_completion(threads):
    """ Wait for threads to complete """
    for thread in threads:
        thread.join()

def queue_completion(work_queue, progress):
    """
    Wait for queue to become empty and update progress bar
    """
    while not work_queue.empty():
        progress.print_progress(work_queue.qsize())
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            __builtin__.exitFlag = 1
            sys.exit(1)
    __builtin__.exitFlag = 1


def main():
    """ main function if not called as a module """

    options = parse_options()

    __builtin__.debug = options.debug
    pretty = options.pretty_print
    max_count = options.threads
    minimum_file_size = options.minimum_file_size
    work_queue = WorkQueue()
    queue_lock = work_queue.queue_lock

    print_status("Generating Threads")
    threads = create_threads(max_count, work_queue, FileThread)

    # Acquire file list
    print_status("Getting file list")
    queue_lock.acquire()
    spinner_func(options, work_queue, queue_lock)
    queue_lock.release()

    print_status("Getting file metadata")
    progress = ProgressBar(work_queue.qsize(), fmt=ProgressBar.FULL,
                           reverse=True)

    # Wait for queue to empty
    queue_completion(work_queue, progress)
    progress.print_progress(work_queue.qsize())

    # Wait for all threads to complete
    threads_completion(threads)

    print_status("Removing non-duplicate files from list")
    my_dict = dict(FileStructure().get())
    num_files = sum(len(v) for v in my_dict.itervalues())
    dupe_progress = ProgressBar(num_files, fmt=ProgressBar.FULL)

    keys_to_delete = []
    keys_to_delete.append('0')
    i = 0

    for key, value in my_dict.iteritems():
        i += len(value.keys())
        if len(value.keys()) != 1 and key != '0' and int(key) > minimum_file_size:
            print_debug("a-size:" + " " + str(minimum_file_size) + " " +  str(key))
            work_queue.put({key: value})
            dupe_progress.print_progress(i)
    dupe_progress.print_progress(num_files)


    initial = float(work_queue.qsize())


    __builtin__.exitFlag = 0

    print_status("Creating more threads")
    threads = create_threads(max_count, work_queue, Md5Thread)

    print_status("Collecting md5 checksums")
    md5_progress = ProgressBar(initial, fmt=ProgressBar.FULL, reverse=True)
    queue_completion(work_queue, progress)

    md5_progress.print_progress(work_queue.qsize())

    threads_completion(threads)
    print_status("calculating disk usage savings")
    my_new_hash = dict(Md5Structure().get())

    print_report(my_new_hash, pretty)

if __name__ == '__main__':
    main()
