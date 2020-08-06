"""DiskImage class for handling Amstrad CPC and Spectrum +3 disk images

The specification of the Amstrad CPC disk image format is available at the
following URL:
<https://www.cpcwiki.eu/index.php/Format:DSK_disk_image_file_format>

Author: Nicholas Campbell
Last updated: 2020-08-06
"""

import os

class DiskImage():
	# Exceptions for this class
	class FileFormatError(Exception):
		def __init__(self, message):
			self.message = message
		def __str__(self):
			return(self.message)

	class InvalidTrackError(Exception):
		def __init__(self, track):
			self.track = track
		def __str__(self):
			return('Track {0} does not exist on this disk image'.format(
				self.track))

	class TrackDataError(Exception):
		def __init__(self, track):
			self.track = track
		def __str__(self):
			return('Track {0} has no data'.format(self.track))

	class InvalidSectorError(Exception):
		def __init__(self, track, sector):
			self.track = track
			self.sector = sector
		def __str__(self):
			return('Sector 0x{0:02X} not found in track {1}'.format(
				self.sector, self.track))

	class SectorWriteError(Exception):
		def __init__(self, track, sector, message):
			self.track = track
			self.sector = sector
			self.message = message
		def __str__(self):
			error_message = ('Unable to write data to '
				+ 'track {0}, sector 0x{1:0X}').format(self.track, self.sector)
			if (self.message != ''):
				error_message += '; ' + self.message
			return(error_message)

	@property
	def number_of_tracks(self):
		return self.header[0x30]

	# Methods

	def __init__(self, filepath):
		"""Create a new disk image object using a disk image file.

Parameters:
    filepath (str): The disk image file to read.
        """
		# Read the disk information black at the beginning of the disk image
		# file, which is 256 bytes long
		with open(filepath, 'rb') as dsk_file:
			self.header = bytearray(dsk_file.read(256))

			# Amstrad CPC extended disk image files are identified by the ASCII
			# string 'EXTENDED CPC DSK File\r\n' in the first 23 bytes of the
			# file
			if self.header[0:23].decode('latin_1') != \
				'EXTENDED CPC DSK File\r\n':
				raise DiskImage.FileFormatError(('{0} is not an Amstrad CPC '
					+ 'disk image file').format(repr(filepath)))

			# The disk image file is valid, so read the rest of the file
			else:
				self.track_info_block = bytearray(dsk_file.read(
					(os.stat(filepath).st_size) - 256))

	def _validate_track_number(self, track):
		"""Validate a track number that is passed to various methods in this class.

Parameters:
    track (int): The track number.

Raises:
    TypeError: The track number is not specified as an integer.
    DiskImage.InvalidTrackError: There is no track with this number in this disk
        image.
		"""
		if type(track) is not int:
			raise TypeError('Track number must be an integer')
		elif track not in range(0, self.number_of_tracks):
			raise DiskImage.InvalidTrackError(track)

	def get_track_info_block_size(self, track):
		"""Return the size in bytes of the track information block in the disk image file
that corresponds to the specified track, including the header (which is 0x100
bytes in length).

Parameters:
    track (int): The track number.

Returns:
    int: The size of the track information block in bytes.

Raises:
    DiskImage.TrackDataError: There is no data for this track, or the track
        information block contains corrupted data.
		"""
		self._validate_track_number(track)
		return (self.header[0x34 + track] * 0x100)

	def get_track_info_block_offset(self, track):
		"""Return the offset of the track information block in the disk image file that
corresponds to the specified track.

Parameters:
    track (int): The track number.

Returns:
    int: The offset of the track information block.

Raises:
    DiskImage.TrackDataError: There is no data for this track.
		"""
		self._validate_track_number(track)
		if self.get_track_info_block_size(track) == 0:
			raise DiskImage.TrackDataError(track)

		track_info_block_offset = 0
		for i in range(0, track):
			track_info_block_offset += \
				self.get_track_info_block_size(i)
		return track_info_block_offset

	def get_sector_info(self, track):
		"""Return information about the sectors of the specified track.

Parameters:
    track (int): The track number.

Returns:
    list: A list of tuples containing information about each sector of the
        track (track/cylinder number (C), side/head number (H), sector ID (R),
		sector size (N), FDC status register 1 (ST1), FDC status register 2
		(ST2), actual size of sector data in disk image file).
		"""
		self._validate_track_number(track)

		# If there is no data for the specified track, then return an empty
		# list
		if self.get_track_info_block_size(track) == 0:
			return []

		# Get the number of sectors in this track
		number_of_sectors = self.track_info_block[
			self.get_track_info_block_offset(track) + 0x15]

		# Read information about each sector from the track information block
		# and store it in the sector information list
		sector_info = [None] * number_of_sectors
		track_info_block_ptr = self.get_track_info_block_offset(track) + 0x18

		for sector in range(0, number_of_sectors):
			sector_info[sector] = \
				(self.track_info_block[track_info_block_ptr],
				self.track_info_block[track_info_block_ptr + 1],
				self.track_info_block[track_info_block_ptr + 2],
				self.track_info_block[track_info_block_ptr + 3],
				self.track_info_block[track_info_block_ptr + 4],
				self.track_info_block[track_info_block_ptr + 5],
				(self.track_info_block[track_info_block_ptr + 6]) +
					(self.track_info_block[track_info_block_ptr + 7] * 0x100)
				)
			track_info_block_ptr += 8
		return sector_info


	def read_sector(self, track, sector):
		"""Read a sector from the disk image.

Parameters:
    track (int): The track number where the sector is located.
    sector (int): The sector ID number to read.

Returns:
    bytearray: The data that was read from the specified sector.

Raises:
	DiskImage.TrackDataError: The specified track does not contain any data.
    DiskImage.InvalidSectorError: The sector ID number does not exist on the
        specified track.
        """
		self._validate_track_number(track)
		if self.get_track_info_block_size(track) == 0:
			raise DiskImage.TrackDataError(track)

		sector_info = self.get_sector_info(track)
		sector_block_ptr = self.get_track_info_block_offset(track) + 0x100

		# Read the sector information list
		for i in range(0,len(sector_info)):
			# If the sector number is found, then read and return the data
			# block for that sector
			if sector_info[i][2] == sector:
				return self.track_info_block[sector_block_ptr:
					(sector_block_ptr + 128 * 2**(sector_info[i])[3])]

			# If the sector number is not found, move the sector block pointer
			# to the data block for the next sector
			sector_block_ptr += (sector_info[i])[6]

		# If the sector number does not exist in this track, then raise an
		# exception
		raise DiskImage.InvalidSectorError(track, sector)


	def write_sector(self, track, sector, data):
		"""Write a sector to the disk image.

Parameters:
    track (int): The track number where the sector is located.
    sector (int): The sector ID number to read.
    data (bytearray): The data to write to the sector.

Raises:
    DiskImage.TrackDataError: The specified track does not contain any data.
    DiskImage.SectorWriteError: The data could not be written to the specified
        sector.
    DiskImage.InvalidSectorError: The sector ID number does not exist on the
        specified track.
        """
		self._validate_track_number(track)
		if self.get_track_info_block_size(track) == 0:
			raise DiskImage.TrackDataError(track)

		sector_info = self.get_sector_info(track)
		sector_block_ptr = self.get_track_info_block_offset(track) + 0x100

		# Read the sector information list
		for i in range(0,len(sector_info)):
			# If the sector number is found, then try to write the block of
			# data to the sector
			if sector_info[i][2] == sector:
				# Check that the size of the block of data to write to the
				# sector matches its size on the disk image; if it doesn't,
				# then raise an exception
				if len(data) != sector_info[i][6]:
					raise DiskImage.SectorWriteError(track, sector,
						('length of data to write ({0:,} bytes)'.format(len(data))
						+ ' does not match actual size of sector data in disk '
						+ 'image ({0:,} bytes)'.format(sector_info[i][6])))
				else:
					self.track_info_block[sector_block_ptr:
						sector_block_ptr+len(data)] = data
					return

			# If the sector number is not found, move the sector block pointer
			# to the data block for the next sector
			sector_block_ptr += (sector_info[i])[6]

		# If the sector number does not exist in this track, then raise an
		# exception
		raise DiskImage.InvalidSectorError(track, sector)
