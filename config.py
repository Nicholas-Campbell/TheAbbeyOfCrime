"""Filepaths, configuration variables and functions used by the Python scripts for
patching the Spanish Amstrad CPC game La Abadía del Crimen by Opera Soft.
"""

# Import modules
import cpcdiskimage
from cpcsnapshot import Snapshot

# Filenames to use for extracting images from a disk image of the original
# (Spanish) version of La Abadía del Crimen
png_loading_screen_filepath = r'images/abadia_loading_screen_es.png'
png_status_bar_filepath = r'images/abadia_status_bar_es.png'

# Filenames to use for the modified images that will be used in the patched
# (English) version of La Abadía del Crimen
new_loading_screen_filepath = r'images/abadia_loading_screen_en.png'
new_status_bar_filepath = r'images/abadia_status_bar_en.png'

# Filenames to use for writing Z80 assembler source code files for data
# extracted from the original version of La Abadía del Crimen
intro_font_original_filepath = r'asm/intro_font_es.asm'
intro_text_original_filepath = r'asm/intro_text_es.asm'
canonical_hours_original_filepath = r'asm/canonical_hours_es.asm'
game_font_original_filepath = r'asm/game_font_es.asm'
game_text_original_filepath = r'asm/game_text_es.asm'
score_text_original_filepath = r'asm/score_text_es.asm'
ending_text_original_filepath = r'asm/ending_text_es.asm'

# Filenames to use for writing Z80 assembler source code and binary files for
# the patched version of La Abadía del Crimen
intro_font_patched_filepath = r'asm/intro_font_en.asm'
intro_font_patched_bin_filepath = r'bin/intro_font_en.bin'
intro_text_patched_filepath = r'asm/intro_text_en.asm'
intro_text_patched_bin_filepath = r'bin/intro_text_en.bin'
canonical_hours_patched_filepath = r'asm/canonical_hours_en.asm'
canonical_hours_patched_bin_filepath = r'bin/canonical_hours_en.bin'
game_font_patched_filepath = r'asm/game_font_en.asm'
game_font_patched_bin_filepath = r'bin/game_font_en.bin'
game_text_patched_filepath = r'asm/game_text_en.asm'
game_text_patched_bin_filepath = r'bin/game_text_en.bin'
score_text_patched_filepath = r'asm/score_text_en.asm'
score_text_patched_bin_filepath = r'bin/score_text_en.bin'
ending_text_patched_filepath = r'asm/ending_text_en.asm'
ending_text_patched_bin_filepath = r'bin/ending_text_en.bin'

# Filepath of the Z80 assembler to use for assembling source code
assembler_filepath = 'pasmo.exe'

# Palettes used by the loading screen and game, using the Amstrad CPC's
# firmware ink values
#
# http://cpctech.cpc-live.com/docs/garray.html contains a list of firmware
# and hardware ink colours
loading_screen_palette = [16,0,26,25,10,6,1,2,8,7,15,5,13,3,14,23]
game_palette = [10,15,25,0]

# The width in pixels of a space in the font used in the introduction text; the
# value used in the original version of the game is 10
intro_font_space_width = 8

# The key number to press to confirm that you and Adso wish to go to sleep each
# night; the value used in the original game is 43 (S, as in "sí" (yes))
#
# See http://cpctech.cpc-live.com/docs/keyboard.html for an explanation of how
# the keys on a British Amstrad CPC keyboard are numbered
yes_key_number = 43

# The letter that corresponds to the above key
yes_key_letter = 'Y'

# Areas of game code that will be patched
#
# Each tuple contains the start and end addresses of each area
intro_font_table_area = (0x680c,0x72ff)	# Overlaps with area used for storing
										# font data
intro_font_data_area = (0x6947,0x72ff)
intro_text_area = (0x7300,0x7882)
canonical_hours_area = (0x4fbc,0x4fec)
game_font_area = (0xb400,0xb56f)
dictionary_area = (0xb580,0xbeff)		# Overlaps with area used for storing
										# scrolling messages
messages_area = (0xbb00,0xbeff)
score_text_area = (0x4305,0x436e)
ending_text_area = (0x1ee58,0x1f9ff)

# Move the introduction text to a higher address in memory in order to
# accommodate extra characters in the font
intro_text_area_patched = (0x7360,0x7882)


# Functions used by both the extraction and patching routines

def read_sectors(dsk_image_file, start_track, start_sector,
	number_of_sectors_to_read, reverse_data=True):
	"""Read one or more sectors from the La Abadía del Crimen disk image file.

Parameters:
	dsk_image_file (cpcdiskimage.DiskImage): The disk image to read.
    start_track (int): The track number of the first sector to read.
    start_sector (int): The sector ID of the first sector to read.
    number_of_sectors_to_read (int): The number of sectors to read.
	reverse_data (bool): The program data is stored on the disk image in
        reverse order. If this flag is set to True, the data will be reversed
        again so that it is returned with the bytes in the correct order.

Returns:
    bytearray: The data read from the disk image file.
	"""
	data = bytearray()
	track = start_track
	sector = start_sector

	for i in range(0,number_of_sectors_to_read):
		data += dsk_image_file.read_sector(track, sector)
		sector += 1
		if sector > 0x2f:
			sector = 0x21
			track += 1

	if reverse_data:
		data.reverse()
	return data

def read_game_data_into_snapshot(disk_image_file, snapshot):
	"""Read the code for La Abadía del Crimen from the specified disk image and
store it in an Amstrad CPC snapshot.

Parameters:
    disk_image_file(cpcdiskimage.DiskImage): The disk image to read.
	snapshot(cpcsnapshot.Snapshot): The snapshot to copy the game code to.

Returns:
    cpcsnapshot.Snapshot: A new snapshot containing the game code.
    """
	program_data = read_sectors(disk_image_file, 5, 0x25, 188)
	program_data_bank_c6 = read_sectors(disk_image_file, 18, 0x21, 64)
	program_data_bank_c5 = read_sectors(disk_image_file, 23, 0x21, 64)
	program_data_bank_c4 = read_sectors(disk_image_file, 28, 0x21, 64)
	program_data_bank_c0 = read_sectors(disk_image_file, 33, 0x21, 64)

	# Copy the data into the snapshot
	snapshot.memory[0x400:0xc000] = program_data
	snapshot.memory[0x1c000:0x20000] = snapshot.memory[0x4000:0x8000]
	snapshot.memory[0x4000:0x8000] = program_data_bank_c0
	snapshot.memory[0x10000:0x14000] = program_data_bank_c4
	snapshot.memory[0x14000:0x18000] = program_data_bank_c5
	snapshot.memory[0x18000:0x1c000] = program_data_bank_c6

	return snapshot
