"""

Main thread and thread handling functions for extracting of file metadata and
adding to a Queue

"""

import hashlib
import os
import threading
import time

import filestructure
from debug import print_debug


class Md5Thread(threading.Thread):
    def __init__(self, thread_id, name, file_queue, xname=''):
        """ Initialize the queue """

        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.name = name
        self.file_queue = file_queue
        self.xname = xname

    def run(self):
        """ Start the queue """
        print_debug("Starting " + self.name)
        self.process_data(self.name, self.file_queue)
        print_debug("Exiting " + self.name)

    def process_data(self, thread_name, file_queue, exitFlag=False):
        """
        Retrieve a file from the queue, while locking, and sent for
        processing
        """

        while not exitFlag:
            print_debug("processing MD5 thread")
            work_queue = filestructure.WorkQueue()
            queue_lock = work_queue.queue_lock
            my_dict = filestructure.Md5Structure()

            queue_lock.acquire()
            if not work_queue.empty():
                data = file_queue.get()
                queue_lock.release()
                print_debug("%s processing %s" % (thread_name, data))
                print_debug(data)

                for size, value in data.items():
                    for file_name, inode in value.items():
                        checksum = self.md5(file_name)
                        my_dict.put(file_name, size, inode, checksum)
            else:
                queue_lock.release()
                exitFlag = True
            print_debug("end of process data")
            time.sleep(1)

    @classmethod
    def md5(cls, filename):
        """
        Get md5 check sum of a givin file by breaking it up into chunks,
        getting the checksum of each chunk and putting it all together to
        return the result
        """

        hash_md5 = hashlib.md5()
        with open(filename, "rb") as file_handle:
            for chunk in iter(lambda: file_handle.read(16384), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()


class FileThread(threading.Thread):
    """
    Main thread for handeling file metadata extraction methods
    """

    def __init__(self, thread_id, name, file_queue):
        """ Initialize the queue """

        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.name = name
        self.file_queue = file_queue

    def run(self):
        """ Start the queue """
        print_debug("Starting " + self.name)
        self.process_data(self.name, self.file_queue)
        print_debug("Exiting " + self.name)

    def process_data(self, thread_name, file_queue):
        """
        Retrieve a file from the queue, while locking, and sent for
        processing
        """
        while not exitFlag:
            print_debug("Processing File Thread")
            work_queue = filestructure.WorkQueue()
            queue_lock = work_queue.queue_lock
            queue_lock.acquire()
            if not work_queue.empty():
                print_debug(work_queue.qsize())
                data = file_queue.get()
                queue_lock.release()
                print_debug("%s processing %s" % (thread_name, data))
                self.scan_files(data)
            else:
                queue_lock.release()
        print_debug("end of process data")
        time.sleep(1)

    @classmethod
    def scan_files(cls, filename):
        """
        Extract size, inode, md5 sum from given file and add to structure
        """

        my_dict = filestructure.FileStructure()
        path = filename
        if os.path.isfile(path):
            size = os.path.getsize(path)
            inode = os.stat(path).st_ino
            my_dict.put(str(path), str(size), str(inode))
            print_debug('updating for {}'.format(path))
        else:
            print_debug('{} is not a file'.format(path))

    @classmethod
    def md5(cls, filename):
        """
        Get md5 check sum of a givin file by breaking it up into chunks,
        getting the checksum of each chunk and putting it all together to
        return the result
        """

        hash_md5 = hashlib.md5()
        with open(filename, "rb") as file_handle:
            for chunk in iter(lambda: file_handle.read(16384), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
