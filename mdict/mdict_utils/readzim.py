# pyZIM is a ZIM reader written entirely in Python 3.
# PyZIM takes its inspiration from the Internet in a Box project,
#  which can be seen in some of the main structures used in this project,
#  yet it has been developed independently and is not considered a fork
#  of the project. For more information on the Internet in a Box project,
#  do have a look at https://github.com/braddockcg/internet-in-a-box .


# Copyright (c) 2016, Kim Bauters, Jim Lemmers
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are
# those of the authors and should not be interpreted as representing official
# policies, either expressed or implied, of the FreeBSD Project.

import io
import lzma
import zstandard

from collections import namedtuple
from functools import partial
from math import floor, pow, log
from struct import Struct, pack, unpack

verbose = False

#####
# Definition of a number of basic structures/functions to simplify the code
#####

ZERO = pack("B", 0)  # defined for zero terminated fields
Field = namedtuple("Field", ["format", "field_name"])  # a tuple
Article = namedtuple("Article", ["data", "namespace", "mimetype"])  # a triple

iso639_3to1 = {"ara": "ar", "dan": "da", "nld": "nl", "eng": "en",
               "fin": "fi", "fra": "fr", "deu": "de", "hun": "hu",
               "ita": "it", "nor": "no", "por": "pt", "ron": "ro",
               "rus": "ru", "spa": "es", "swe": "sv", "tur": "tr"}


def read_zero_terminated(file, encoding):
    """
    Retrieve a ZERO terminated string by reading byte by byte until the ending
    ZERO terminated field is encountered.
    :param file: the file to read from
    :param encoding: the encoding used for the file
    :return: the decoded string, up to but not including the ZERO termination
    """
    # read until we find the ZERO termination
    buffer = iter(partial(file.read, 1), ZERO)
    # join all the bytes together
    field = b"".join(buffer)
    # transform the bytes into a string and return the string
    return field.decode(encoding=encoding, errors="ignore")


def convert_size(size):
    """
    Convert a given size in bytes to a human-readable string of the file size.
    :param size: the size in bytes
    :return: a human-readable string of the size
    """
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    power = int(floor(log(size, 1024)))
    base = pow(1024, power)
    size = round(size / base, 2)
    return '%s %s' % (size, size_name[power])


#####
# Description of the structure of a ZIM file, as of late 2017
# For the full definition: http://www.openzim.org/wiki/ZIM_file_format .
#
# The field format used are the same format definitions as for a Struct:
# https://docs.python.org/3/library/struct.html#format-characters
# Notably, as used by ZIMply, we have:
#   I   unsigned integer (4 bytes)
#   Q   unsigned long long (8 bytes)
#   H   unsigned short (2 bytes)
#   B   unsigned char (1 byte)
#   c   char (1 byte)
#####

HEADER = [  # define the HEADER structure of a ZIM file
    Field("I", "magicNumber"),
    Field("I", "version"),
    Field("Q", "uuid_low"),
    Field("Q", "uuid_high"),
    Field("I", "articleCount"),
    Field("I", "clusterCount"),
    Field("Q", "urlPtrPos"),
    Field("Q", "titlePtrPos"),
    Field("Q", "clusterPtrPos"),
    Field("Q", "mimeListPos"),
    Field("I", "mainPage"),
    Field("I", "layoutPage"),
    Field("Q", "checksumPos")
]

ARTICLE_ENTRY = [  # define the ARTICLE ENTRY structure of a ZIM file
    Field("H", "mimetype"),
    Field("B", "parameterLen"),
    Field("c", "namespace"),
    Field("I", "revision"),
    Field("I", "clusterNumber"),
    Field("I", "blobNumber")
    # zero terminated url of variable length; not a Field
    # zero terminated title of variable length; not a Field
    # variable length parameter data as per parameterLen; not a Field
]

REDIRECT_ENTRY = [  # define the REDIRECT ENTRY structure of a ZIM file
    Field("H", "mimetype"),
    Field("B", "parameterLen"),
    Field("c", "namespace"),
    Field("I", "revision"),
    Field("I", "redirectIndex")
    # zero terminated url of variable length; not a Field
    # zero terminated title of variable length; not a Field
    # variable length parameter data as per parameterLen; not a Field
]

CLUSTER = [  # define the CLUSTER structure of a ZIM file
    Field("B", "compressionType")
]


#####
# The internal classes used to easily access
# the different structures in a ZIM file.
#####

class Block:
    def __init__(self, structure, encoding):
        self._structure = structure
        self._encoding = encoding
        # Create a new Struct object to correctly read the binary data in this
        # block in particular, pass it along that it is a little endian (<),
        # along with all expected fields.
        self._compiled = Struct("<" + "".join(
            [field.format for field in self._structure]))
        self.size = self._compiled.size

    def unpack(self, buffer, offset=0):
        # Use the Struct to read the binary data in the buffer
        # where this block appears at the given offset.
        values = self._compiled.unpack_from(buffer, offset)
        # Match up each value with the corresponding field in the block
        # and put it in a dictionary for easy reference.
        return {field.field_name: value for value, field in
                zip(values, self._structure)}

    def _unpack_from_file(self, file, offset=None):
        if offset is not None:
            # move the pointer in the file to the specified offset;
            # this is not index 0
            file.seek(offset)
        # read in the amount of data corresponding to the block size
        buffer = file.read(self.size)
        # return the values of the fields after unpacking them
        return self.unpack(buffer)

    def unpack_from_file(self, file, seek=None):
        # When more advanced behaviour is needed,
        # this method can be overridden by subclassing.
        return self._unpack_from_file(file, seek)


class HeaderBlock(Block):
    def __init__(self, encoding):
        super().__init__(HEADER, encoding)


class MimeTypeListBlock(Block):
    def __init__(self, encoding):
        super().__init__("", encoding)

    def unpack_from_file(self, file, offset=None):
        # move the pointer in the file to the specified offset as
        # this is not index 0 when an offset is specified
        if offset is not None:
            file.seek(offset)
        mimetypes = []  # prepare an empty list to store the mimetypes
        while True:
            # get the next zero terminated field
            s = read_zero_terminated(file, self._encoding)
            mimetypes.append(s)  # add the newly found mimetype to the list
            if s == "":  # the last entry must be an empty string
                mimetypes.pop()  # pop the last entry
                return mimetypes  # return the list of mimetypes we found


class ClusterBlock(Block):
    def __init__(self, encoding):
        super().__init__(CLUSTER, encoding)


class ClusterData(object):
    def __init__(self, file, offset, encoding):
        self.file = file  # store the file
        self.offset = offset  # store the offset
        cluster_info = ClusterBlock(encoding).unpack_from_file(
            self.file, self.offset)  # Get the cluster fields.
        # Verify whether the cluster has compression
        self.compression = {4: "lzma", 5: "zstd"}.get(cluster_info['compressionType'], False)
        # at the moment, we don't have any uncompressed data
        self.uncompressed = None
        self._decompress()  # decompress the contents as needed
        # Prepare storage to keep track of the offsets
        # of the blobs in the cluster.
        self._offsets = []
        # proceed to actually read the offsets of the blobs in this cluster
        self._read_offsets()

    def _decompress(self, chunk_size=32768):
        if self.compression == "lzma":
            # create a bytes stream to store the uncompressed cluster data
            self.buffer = io.BytesIO()
            decompressor = lzma.LZMADecompressor()  # prepare the decompressor
            # move the file pointer to the start of the blobs as long as we
            # don't reach the end of the stream.
            self.file.seek(self.offset + 1)

            while not decompressor.eof:
                chunk = self.file.read(chunk_size)  # read in a chunk
                data = decompressor.decompress(chunk)  # decompress the chunk
                self.buffer.write(data)  # and store it in the buffer area

        elif self.compression == "zstd":
            # create a bytes stream to store the uncompressed cluster data
            self.buffer = io.BytesIO()
            decompressor = zstandard.ZstdDecompressor().decompressobj()  # prepare the decompressor
            # move the file pointer to the start of the blobs as long as we
            # don't reach the end of the stream.
            self.file.seek(self.offset + 1)
            while True:
                chunk = self.file.read(chunk_size)  # read in a chunk
                try:
                    data = decompressor.decompress(chunk)  # decompress the chunk
                    self.buffer.write(data)  # and store it in the buffer area
                except zstandard.ZstdError as e:
                    break

    def _source_buffer(self):
        # get the file buffer or the decompressed buffer
        buffer = self.buffer if self.compression else self.file
        # move the buffer to the starting position
        buffer.seek(0 if self.compression else self.offset + 1)
        return buffer

    def _read_offsets(self):
        # get the buffer for this cluster
        buffer = self._source_buffer()
        # read the offset for the first blob
        offset0 = unpack("<I", buffer.read(4))[0]
        # store this one in the list of offsets
        self._offsets.append(offset0)
        # calculate the number of blobs by dividing the first blob by 4
        number_of_blobs = int(offset0 / 4)
        for idx in range(number_of_blobs - 1):
            # store the offsets to all other blobs
            self._offsets.append(unpack("<I", buffer.read(4))[0])

    def read_blob(self, blob_index):
        # check if the blob falls within the range
        if blob_index >= len(self._offsets) - 1:
            raise IOError("Blob index exceeds number of blobs available: %s" %
                          blob_index)
        buffer = self._source_buffer()  # get the buffer for this cluster
        # calculate the size of the blob
        blob_size = self._offsets[blob_index + 1] - self._offsets[blob_index]
        # move to the position of the blob relative to current position
        buffer.seek(self._offsets[blob_index], 1)
        return buffer.read(blob_size)


class DirectoryBlock(Block):
    def __init__(self, structure, encoding):
        super().__init__(structure, encoding)

    def unpack_from_file(self, file, seek=None):
        # read the first fields as defined in the ARTICLE_ENTRY structure
        field_values = super()._unpack_from_file(file, seek)
        # then read in the url, which is a zero terminated field
        field_values["url"] = read_zero_terminated(file, self._encoding)
        # followed by the title, which is again a zero terminated field
        field_values["title"] = read_zero_terminated(file, self._encoding)
        field_values["namespace"] = field_values["namespace"].decode(
            encoding=self._encoding, errors="ignore")
        return field_values


class ArticleEntryBlock(DirectoryBlock):
    def __init__(self, encoding):
        super().__init__(ARTICLE_ENTRY, encoding)


class RedirectEntryBlock(DirectoryBlock):
    def __init__(self, encoding):
        super().__init__(REDIRECT_ENTRY, encoding)


#####
# Support functions to simplify (1) the uniform creation of a URL
# given a namespace, and (2) searching in the index.
#####

def full_url(namespace, url):
    return str(namespace) + '/' + str(url)


def binary_search(func, item, front, end):
    found = False
    middle = 0

    # continue as long as the boundaries don't cross and we haven't found it
    while front < end and not found:
        middle = floor((front + end) / 2)  # determine the middle index
        # use the provided function to find the item at the middle index
        found_item = func(middle)
        if found_item == item:
            found = True  # flag it if the item is found
        else:
            if found_item < item:  # if the middle is too early ...
                # move the front index to the middle
                # (+ 1 to make sure boundaries can be crossed)
                front = middle + 1
            else:  # if the middle falls too late ...
                # move the end index to the middle
                # (- 1 to make sure boundaries can be crossed)
                end = middle - 1

    return middle if found else None


class ZIMFile:
    """
    The main class to access a ZIM file.
    Two important public methods are:
        get_article_by_url(...)
      is used to retrieve an article given its namespace and url.

        get_main_page()
      is used to retrieve the main page article for the given ZIM file.
    """

    def __init__(self, filename, encoding):
        self._enc = encoding
        self.filename = filename
        # open the file as a binary file
        file = open(filename, "rb")
        # retrieve the header fields
        self.header_fields = HeaderBlock(self._enc).unpack_from_file(file)
        self.mimetype_list = MimeTypeListBlock(self._enc).unpack_from_file(
            file, self.header_fields["mimeListPos"])
        self.header = self.metadata(file)
        # create the object once for easy access
        # self.redirectEntryBlock = RedirectEntryBlock(self._enc)

        # self.articleEntryBlock = ArticleEntryBlock(self._enc)
        # self.clusterFormat = ClusterBlock(self._enc)
        file.close()

    def get_fname(self):
        slash = self.filename.rfind('/')
        if self.filename.rfind('\\') > slash:
            slash = self.filename.rfind('\\')
        return self.filename[slash + 1:self.filename.rfind('.')]

    def get_fpath(self):
        return self.filename

    def _read_offset(self, file, index, field_name, field_format, length):
        # move to the desired position in the file

        if index != 0xffffffff:
            file.seek(self.header_fields[field_name] + int(length * index))

            # and read and return the particular format
            read = file.read(length)
            # return unpack("<" + field_format, self.file.read(length))[0]
            return unpack("<" + field_format, read)[0]
        return None

    def _read_url_offset(self, file, index):
        return self._read_offset(file, index, "urlPtrPos", "Q", 8)

    def _read_title_offset(self, file, index):
        return self._read_offset(file, index, "titlePtrPos", "L", 4)

    def _read_cluster_offset(self, file, index):
        return self._read_offset(file, index, "clusterPtrPos", "Q", 8)

    def _read_directory_entry(self, file, offset):
        """
        Read a directory entry using an offset.
        :return: a DirectoryBlock - either as Article Entry or Redirect Entry
        """

        file.seek(offset)  # move to the desired offset

        # retrieve the mimetype to determine the type of block
        fields = unpack("<H", file.read(2))

        # get block class
        if fields[0] == 0xffff:
            directory_block = RedirectEntryBlock(self._enc)
        else:
            directory_block = ArticleEntryBlock(self._enc)
        # unpack and return the desired Directory Block
        return directory_block.unpack_from_file(file, offset)

    def read_directory_entry_by_index(self, file, index):
        """
        Read a directory entry using an index.
        :return: a DirectoryBlock - either as Article Entry or Redirect Entry
        """
        # find the offset for the given index

        offset = self._read_url_offset(file, index)
        if offset is not None:
            # read the entry at that offset
            directory_values = self._read_directory_entry(file, offset)
            # set the index in the list of values
            directory_values["index"] = index
            return directory_values  # and return all these directory values

    def _read_blob(self, file, cluster_index, blob_index):
        # get the cluster offset
        offset = self._read_cluster_offset(file, cluster_index)
        # get the actual cluster data
        cluster_data = ClusterData(file, offset, self._enc)
        # return the data read from the cluster at the given blob index
        return cluster_data.read_blob(blob_index)

    def _get_article_by_index(self, file, index, follow_redirect=True):
        # get the info from the DirectoryBlock at the given index
        entry = self.read_directory_entry_by_index(file, index)
        if entry is not None:
            # check if we have a Redirect Entry
            if 'redirectIndex' in entry.keys():
                # if we follow up on redirects, return the article it is
                # pointing to
                if follow_redirect:
                    return self._get_article_by_index(file, entry['redirectIndex'],
                                                      follow_redirect)
                # otherwise, simply return no data
                # and provide the redirect index as the metadata.
                else:
                    return Article(None, entry['namespace'],
                                   entry['redirectIndex'])
            else:  # otherwise, we have an Article Entry
                # get the data and return the Article
                data = self._read_blob(file, entry['clusterNumber'],
                                       entry['blobNumber'])
                return Article(data, entry['namespace'],
                               self.mimetype_list[entry['mimetype']])
        else:
            return None

    def _get_entry_by_url(self, file, namespace, url, linear=False):
        if linear:  # if we are performing a linear search ...
            # ... simply iterate over all articles
            for idx in range(self.header_fields['articleCount']):
                # get the info from the DirectoryBlock at that index
                entry = self.read_directory_entry_by_index(file, idx)
                # if we found the article ...
                if entry['url'] == url and entry['namespace'] == namespace:
                    # return the DirectoryBlock entry and index of the entry
                    return entry, idx
            # return None, None if we could not find the entry
            return None, None
        else:
            front = middle = 0
            end = len(self)
            title = full_url(namespace, url)

            found = False
            # continue as long as the boundaries don't cross and
            # we haven't found it
            while front <= end and not found:
                middle = floor((front + end) / 2)  # determine the middle index
                entry = self.read_directory_entry_by_index(file, middle)
                found_title = full_url(entry['namespace'], entry['url'])
                if found_title == title:
                    found = True  # flag it if the item is found
                else:
                    if found_title < title:  # if the middle is too early ...
                        # move the front index to middle
                        # (+ 1 to ensure boundaries can be crossed)
                        front = middle + 1
                    else:  # if the middle falls too late ...
                        # move the end index to middle
                        # (- 1 to ensure boundaries can be crossed)
                        end = middle - 1
            if found:
                # return the tuple with directory entry and index
                # (note the comma before the second argument)
                return self.read_directory_entry_by_index(file, middle), middle
            return None, None

    def get_article_by_url(self, file, namespace, url, follow_redirect=True):
        entry, idx = self._get_entry_by_url(file, namespace, url)  # get the entry
        if idx:  # we found an index and return the article at that index
            return self._get_article_by_index(
                file, idx, follow_redirect=follow_redirect)

    def get_main_page(self, file):
        """
        Get the main page of the ZIM file.
        """
        main_page = self._get_article_by_index(file, self.header_fields['mainPage'])
        if main_page is not None:
            return main_page

    def metadata(self, file):
        """
        Retrieve the metadata attached to the ZIM file.
        :return: a dict with the entry url as key and the metadata as value
        """
        metadata = {}
        # iterate backwards over the entries
        for i in range(self.header_fields['articleCount'] - 1, -1, -1):
            entry = self.read_directory_entry_by_index(file, i)  # get the entry
            if entry['namespace'] == 'M':  # check that it is still metadata
                # turn the key to lowercase as per Kiwix standards
                m_name = entry['url'].lower()
                # get the data, which is encoded as an article
                metadata[m_name] = self._get_article_by_index(file, i)[0]
            else:  # stop as soon as we are no longer looking at metadata
                break
        return metadata

    def __len__(self):  # retrieve the number of articles in the ZIM file
        return self.header_fields['articleCount']

    def get_articles(self, file):
        """
        Create an iterator generator to retrieve all articles in the ZIM file.
        :return: a yielded entry of an article, containing its full URL,
                  its title, and the index of the article
        """
        r_list = []
        for idx in range(self.header_fields['articleCount']):
            # get the Directory Entry
            entry = self.read_directory_entry_by_index(file, idx)
            if entry['namespace'] == "A":
                # add the full url to the entry
                entry['fullUrl'] = full_url(entry['namespace'], entry['url'])
                r_list.append((entry['fullUrl'], entry['title'], idx))
        return r_list

    @staticmethod
    def search_article(file, zim, location):
        is_article = True  # assume an article is requested, for now
        if location in ["/", "/index.htm", "/index.html",
                        "/main.htm", "/main.html"]:
            # ... return the main page as the article
            article = zim.get_main_page()
        else:
            # The location is given as domain.com/namespace/url/parts/ ,
            # as used in the ZIM link or, alternatively, as domain.com/page.htm
            _, namespace, *url_parts = location.split("/")

            # are we dealing with an address bar request, eg. /article_name.htm
            if len(namespace) > 1:
                url = namespace  # the namespace is then the URL
                namespace = "A"  # and the namespace is an article
            else:
                # combine all the url parts together again
                url = "/".join(url_parts)
            # get the desired article

            article = zim.get_article_by_url(file, namespace, url)
            # we have an article when the namespace is A
            # (i.e. not a photo, etc.)
            is_article = (namespace == "A")
        if is_article:
            result = article.data  # we have an actual article
            # decode its contents into a string using its encoding
            result = result.decode(encoding='utf-8')
        else:
            # just a binary blob, so use it as such
            result = article.data
        return result
