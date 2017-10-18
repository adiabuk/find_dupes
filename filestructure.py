"""

Filestrcutre class and suporting functions for storing, sorting, extracting,
and manipulating file file attributes and other metadata

"""

import Queue
import json
import threading


from collections import defaultdict
from debug import print_debug


class Singleton(type):
    """
    base singleton class to subclass from other classes
    """

    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class WorkQueue(Queue.Queue, object):
    """
    Queue object as a singleton, used to hold files which will be checked
    for possible duplicates
    """

    __metaclass__ = Singleton

    def __init__(self, *args, **kwargs):
        self.queue_lock = threading.Lock()
        super(WorkQueue, self).__init__(*args, **kwargs)

class BaseStructure(dict):
    #__metaclass__ = Singleton
    #__metaclass__ = ABCMeta
    def __init__(self):
        self.my_dict = defaultdict(dict)
        super(BaseStructure, self).__init__()

    def get(self):
        #### no overwrite
        """ get entire object """
        return self.my_dict


class Md5Structure(BaseStructure):

    __metaclass__ = Singleton

    def put(self, path, size, inode, checksum):
        """
        Insert item into structure, given the path, md5 hash, size, and
        inode.  Checks will be made to ensure that if the md5 hash and/or inode
        provided already exists, we will not overwrite, but add this as a value
        in a nested dictionary to sort later
        """
        print_debug("putting size:{}, path:{},inode:{}".format(size, path,
                                                               inode))

        # {'dasdsadsa': {'entries': {'file3': 332, 'file2': 234, 'file1': 123}, 'size': 1}}
        if not checksum in self.my_dict:
            print_debug('path not present')
            self.my_dict.update({checksum:dict()})
        else:
            #self.my_dict[checksum].update({'size': size})
            print_debug('path1 already present')
        if not 'entries' in self.my_dict[checksum]:
            print_debug('path not present')
            self.my_dict[checksum].update({'entries':{}})
        else:
            print_debug('path2 already present')
        try:
            self.my_dict[checksum]['entries'].update({path: inode})
            self.my_dict[checksum]['size'] = size
        except ValueError as ex:   #remove?!?
            print 'yyy', self.my_dict[checksum]
            print "xxx ", type(path), type(inode), ex

class FileStructure(dict):
    """
    main structure for storing details of all files in the filesystem
    """

    __metaclass__ = Singleton

    def __init__(self):

        self.my_dict = defaultdict(dict)
        super(FileStructure, self).__init__()

    def __getitem__(self, item):
        """ Fetch single attribute from object """
        # FIXME
        print "getting item {}".format(item)

        try:
            return self.my_dict
        except KeyError:
            print "poo"

    def __str__(self):
        """ how to print structure """

        print_debug("returning")
        return json.dumps(self.my_dict)



    def __setitem__(self, *args, **kwargs):
        """ set single item in the structure """

        print_debug("setting item")

    def put(self, path, size, inode):
        """ Insert item into structure, given the path, md5 hash, size, and
        inode.  Checks will be made to ensure that if the md5 hash and/or inode
        provided already exists, we will not overwrite, but add this as a value
        in a nested dictionary to sort later
        """
        print_debug("putting size:{}, path:{},inode:{}".format(size, path,
                                                               inode))
        self.my_dict[size].update({path:inode})

    def get(self):
        """ get entire object """
        return self.my_dict
