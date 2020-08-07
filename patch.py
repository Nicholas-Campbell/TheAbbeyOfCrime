"""Apply patches to a disk image of the Spanish Amstrad CPC game La Abadía del
Crimen by Opera Soft and save the patched version as a disk image file and/or a
snapshot for use in an emulator

Author: Nicholas Campbell
Last updated: 2020-08-06
"""

# Import modules

from copy import copy, deepcopy
import os
import sys
try:
	from PIL import Image
except ModuleNotFoundError as ex:
	print('The PIL module could not be found. Please check that the Pillow '
		+ 'library has\n'
		+ 'been installed.')
	quit()

from cpcdiskimage import DiskImage
import cpcimage
from cpcsnapshot import Snapshot

# Define filepaths used for reading and writing files
from config import *

display_debug_info = False	# Set to True to display additional information
							# that is helpful for debugging the patched
							# version in an emulator

# Exceptions
class SizeError(Exception):
	def __init__(self, message):
		self.message = message
	def __str__(self):
		return(self.message)


# Functions
def _validate_cpc_palette(palette, screen_mode):
	"""Check if a palette of Amstrad CPC firmware ink colours is valid.

Parameters:
    palette (list): The palette of firmware ink colours. The maximum number of
        values in the palette depends on the specified screen mode (16 colours
        for Mode 0, 4 colours for Mode 1, 2 colours for Mode 2).
    screen_mode (int): The screen mode to use (0-2).

Returns:
	True if there are no errors found in the palette.

Raises:
	SizeError: The palette is either empty or contains too many values for the
        specified screen mode.
	ValueError: The screen mode is not a valid value (the Amstrad CPC has three
        screen modes numbered 0-2), or the palette contains an invalid value
        (the Amstrad CPC's firmware colours are numbered from 0-26).
    """
	if screen_mode == 0:
		max_colours = 16
	elif screen_mode == 1:
		max_colours = 4
	elif screen_mode == 2:
		max_colours = 2
	else:
		raise ValueError('screen_mode must be between 0 and 2')

	if len(palette) not in range(1,max_colours + 1):
		raise SizeError('Palette must contain between 1 and {0} values'.format(
			max_colours))
	else:
		for colour in palette:
			if colour not in range(0,27):
				raise ValueError('Palette contains an invalid colour '
					+ '{0}'.format(colour))
	return True

def convert_png_to_cpc_screen(image, palette):
	"""Convert an image to Amstrad CPC screen format using the specified palette. The
image is assumed to be in Mode 0, 320 pixels in width and 200 pixels in height,
which matches the Amstrad CPC's standard screen size.

Parameters:
    image (PIL.Image.Image): The image to convert.
    palette (list (int)): The ink values used in the converted image, using
        Amstrad CPC firmware ink colours.

Returns:
	bytearray: The converted image in Amstrad CPC Mode 0 screen format.
    """
	if image.size != (320,200):
		print('ERROR: The image to convert must be 320 pixels wide by 200 '
			+ "pixels high, to match the Amstrad CPC's standard screen size.",
			file=sys.stderr)
		quit()

	# Check that the Amstrad CPC palette to use is valid
	_validate_cpc_palette(palette, 0)

	# Convert the image to a 256-colour palette
	image = image.quantize(256)

	# Convert each colour in the palette to its nearest equivalent firmware
	# value on the CPC (from 0 to 26)
	image_rgb_palette = image.getpalette()
	image_cpc_palette = cpcimage.convert_rgb_palette_to_cpc(image_rgb_palette)

	# Read the screen pixel by pixel and convert it to the CPC's Mode 0 screen
	# format
	#
	# A normal CPC screen occupies a block of 0x4000 bytes and consists of 25
	# rows, each containing 8 lines (i.e. 200 lines in total), and each line
	# consists of 80 bytes
	screen_data = bytearray(0x4000)

	try:
		for y in range(0,200):
			# Calculate the address to store the encoded byte
			screen_data_ptr = (y%8)*0x800 + (y//8)*80

			for x in range(0,80):
				# Get the palette index values of 2 pixels and encode them in a
				# single byte used by the CPC's Mode 0
				x_pixel = x*4
				pixel_cpc_colour = image_cpc_palette[
					image.getpixel((x_pixel,y))]
				left_pixel = palette.index(pixel_cpc_colour)

				x_pixel += 2
				pixel_cpc_colour = image_cpc_palette[
					image.getpixel((x_pixel,y))]
				right_pixel = palette.index(pixel_cpc_colour)

				screen_data[screen_data_ptr] = \
					cpcimage.encode_pixels((left_pixel, right_pixel))
				screen_data_ptr += 1

		# Return the converted screen
		return screen_data

	# If a pixel is converted to a CPC colour that is not used in the palette
	# that has been defined for the screen, then display an error message
	except ValueError as error:
		print('ERROR: Pixel {0}, {1} has a colour ({2}) that does not \
correspond to any entry in the Amstrad CPC palette for this screen. The CPC \
palette in use is {3}.'.format(x_pixel, y, pixel_cpc_colour, palette),
			file=sys.stderr)
		quit()

def convert_png_to_cpc_sprite(image, palette):
	"""Convert an image to Amstrad CPC sprite using the specified palette. The
image is assumed to be in Mode 1.

Parameters:
    image (PIL.Image.Image): The image to convert.
    palette (list (int)): The ink values used in the converted image, using
        Amstrad CPC firmware ink colours.

Returns:
	bytearray: The converted image in Amstrad CPC Mode 0 sprite format.
	"""
	# Check that the Amstrad CPC palette to use is valid
	_validate_cpc_palette(palette, 1)

	# Convert the image to a 256-colour palette
	image = image.quantize(256)

	# Convert each colour in the palette to its nearest equivalent firmware
	# value on the CPC (from 0 to 26)
	image_rgb_palette = image.getpalette()
	image_cpc_palette = cpcimage.convert_rgb_palette_to_cpc(image_rgb_palette)

	# Read the new sprite pixel by pixel and convert it to the CPC's Mode 1
	# screen format
	sprite_width = image.width//4
	sprite_height = image.height
	sprite_data = bytearray(sprite_width * sprite_height)
	sprite_data_ptr = 0

	try:
		for y in range(0,sprite_height):
			for x in range(0,sprite_width):
				# Get the palette index values of 4 pixels and encode them in a
				# single byte used by the CPC's Mode 1
				pixels = [0] * 4
				for pixel_index in range(0,4):
					x_pixel = x*4 + pixel_index
					pixel_cpc_colour = image_cpc_palette[
						image.getpixel((x_pixel,y))]
					pixels[pixel_index] = palette.index(pixel_cpc_colour)

				sprite_data[sprite_data_ptr] = cpcimage.encode_pixels(pixels)
				sprite_data_ptr += 1

		# Return the converted screen
		return sprite_data

	# If a pixel is converted to a CPC colour that is not used in the palette
	# that has been defined for the screen, then display an error message
	except ValueError as error:
		print('ERROR: Pixel {0}, {1} has a colour ({2}) that does not \
correspond to any entry in the Amstrad CPC palette for this screen. The CPC \
palette in use is {3}.'.format(x_pixel, y, pixel_cpc_colour, palette),
			file=sys.stderr)
		quit()

def assemble_source_code(source_code_filepath, object_code_filepath,
	message=None):
	"""Assemble a Z80 assembler source code file.

Parameters:
    source_code_filepath (str): The filepath of the Z80 assembler source code
        file to assemble.
	object_code_filepath (str): The filepath of the assembled object code
        binary file.
    message (str): A description of the source code that is being assembled.

Returns:
    bytearray: The binary data for the object code that was assembled.
    """
	# If no message was supplied, print the default message
	if message is not None and message != '':
		print('Assembling {0} ({1}) to {2}...'.format(message,
		source_code_filepath, object_code_filepath))

	# Check that the Z80 source code file exists
	if not os.path.exists(source_code_filepath):
		print('ERROR: Source code file {0} does not exist!'.format(
			source_code_filepath), file=sys.stderr)
		quit()

	# Attempt to assemble the Z80 source code
	#
	# If the source code assembled successfully, the assembler returns a value
	# of zero. If the assembly failed for any reason, it returns a non-zero
	# value, and the command prompt or the assembler should display an
	# appropriate error message
	return_value = os.system(assembler_filepath + ' ' + source_code_filepath
		+ ' ' + object_code_filepath)
	if return_value != 0:
		quit()

	# Read the output binary file and store it as an array of bytes
	try:
		with open(object_code_filepath, 'rb') as binary_file:
			file_length = os.stat(object_code_filepath).st_size
			binary_data = bytearray(binary_file.read(file_length))
	except OSError:
		print('ERROR: Unable to read file {0}!'.format(object_code_filepath),
			file=sys.stderr)
		quit()

	# Return the contents of the output binary file
	return binary_data

def write_sectors(start_track, start_sector, data, reverse_data=True):
	"""Write one or more sectors to a La Abadía del Crimen disk image file.

Parameters:
    start_track (int): The track number of the first sector to write.
    start_sector (int): The sector ID of the first sector to write.
	data (bytearray): The data to write to the disk image.
	reverse_data (bool): The program data is stored on the disk image in
        reverse order. If this flag is set to True, the data will be written
        to the disk image in reverse order.
    """
	# Calculate the number of sectors that need to be written to the disk image
	number_of_sectors_to_write = (len(data)-1)//0x100 + 1
	data_to_write = copy(data)

	# Reverse the data if the corresponding flag is set
	if reverse_data:
		data_to_write.reverse()

	# Write the sectors to the disk image
	track = start_track
	sector = start_sector
	data_offset = 0

	for i in range(0,number_of_sectors_to_write):
		abadia_dsk.write_sector(track, sector,
			data_to_write[data_offset:data_offset+256])
		sector += 1
		data_offset += 0x100
		if sector > 0x2f:
			sector = 0x21
			track += 1


# ------------
# Main program
# ------------

new_dsk_filepath = None
new_snapshot_filepath = None

# Process command line arguments
#
# Check that a valid number of arguments have been supplied, and if not,
# display a message detailing the expected arguments
if len(sys.argv) not in range (3,5):
	script_name = sys.argv[0]
	print(('Usage: python {0} original_disk_image_file [patched_disk_image_file] '
		+ '[patched_snapshot_file]\n').format(script_name))
	print('Examples:')
	print('  python {0} abadia.dsk abbey.dsk'.format(script_name))
	print('  Read the disk image abadia.dsk and write a patched disk image to '
		+ 'abbey.dsk.\n')
	print('  python {0} abadia.dsk abbey.sna'.format(script_name))
	print('  Read the disk image abadia.dsk and write a patched snapshot to '
		+ 'to abbey.sna.\n')
	print('  python {0} abadia.dsk abbey.dsk abbey.sna'.format(script_name))
	print('  Read the disk image abadia.dsk and write a patched disk image to '
		+ 'abbey.dsk\n  and a patched snapshot to abbey.sna.')
	quit()

# Process the command line arguments and retrieve the filepaths for the
# original disk image, the patched disk image, and/or the patched snapshot
else:
	original_dsk_filepath = sys.argv[1]
	for index in range(2,len(sys.argv)):
		filename, extension = os.path.splitext(sys.argv[index])
		if extension.lower() == '.dsk':
			if new_dsk_filepath:
				print('ERROR: More than one filename has been specified for '
					+ 'patched disk image!', file=sys.stderr)
				quit()
			else:
				new_dsk_filepath = sys.argv[index]
		elif extension.lower() == '.sna':
			if new_snapshot_filepath:
				print('ERROR: More than one filename has been specified for '
					+ 'patched snapshot!', file=sys.stderr)
				quit()
			new_snapshot_filepath = sys.argv[index]
		else:
			print(('ERROR: {0} is not a valid extension for either an Amstrad '
				+ 'CPC disk image or a snapshot!').format(extension.lower()),
				file=sys.stderr)
			quit()

# Check that the original disk image file exists
if not os.path.exists(original_dsk_filepath):
	print('ERROR: Disk image {0} does not exist!'.format(original_dsk_filepath),
		file=sys.stderr)
	quit()

# Read the original disk image file
print('Reading disk image {0}...'.format(original_dsk_filepath))
abadia_dsk = DiskImage(original_dsk_filepath)

# Create snapshots of both the original game and the patched version
abadia_sna_original = Snapshot(ram_size=128)
abadia_sna_original = read_game_data_into_snapshot(abadia_dsk,
	abadia_sna_original)
abadia_sna_patched = deepcopy(abadia_sna_original)

# Import the new loading screen
print('Importing new loading screen {0}...'.format(
	new_loading_screen_filepath))
new_loading_screen = Image.open(new_loading_screen_filepath)
new_loading_screen_data = convert_png_to_cpc_screen(new_loading_screen,
	loading_screen_palette)

# Import the new status bar
print('Importing new status bar {0}...'.format(new_status_bar_filepath))
new_status_bar = Image.open(new_status_bar_filepath)

# Check that the dimensions of the status bar image are correct (256 pixels
# wide by 32 pixels high)
if new_status_bar.size != (256,32):
	print('ERROR: Image {0} is not the correct size; it must be 256 \
pixels in width by 32 pixels in height.'.format(new_status_bar_filepath))
	quit()
new_status_bar_data = convert_png_to_cpc_sprite(new_status_bar, game_palette)

# Assemble the Z80 source code files and insert the object code into the
# snapshot
#
# Each entry in the source_code_files_to_assemble list is a tuple containing
# the following elements:
# * The filepath of the source code file to assemble
# * The filepath of the assembled object code
# * A description of the source code that is being assembled
# * Another tuple containing the expected start and end addresses of the
#   object code in memory
source_code_files_to_assemble = [
	(intro_font_patched_filepath, intro_font_patched_bin_filepath,
		'font in introduction', intro_font_table_area),
	(intro_text_patched_filepath, intro_text_patched_bin_filepath,
		'text in introduction', intro_text_area_patched),
	(game_font_patched_filepath, game_font_patched_bin_filepath,
		'font in game', game_font_area),
	(canonical_hours_patched_filepath, canonical_hours_patched_bin_filepath,
		'canonical hours', canonical_hours_area),
	(game_text_patched_filepath, game_text_patched_bin_filepath,
		'dictionary and messages', dictionary_area),
	(score_text_patched_filepath, score_text_patched_bin_filepath,
		'score text', score_text_area),
	(ending_text_patched_filepath, ending_text_patched_bin_filepath,
		'text in ending', ending_text_area)
]
for file in source_code_files_to_assemble:
	file_to_write = file[1]

	# Check if the directory to write the object file to exists; if it
	# does not exist, then create it
	dir = os.path.split(file_to_write)[0]
	if dir != '' and not os.path.isdir(dir):
		os.makedirs(dir)

	assemble_source_code(file[0], file[1], file[2])
	object_file_length = os.stat(file_to_write).st_size
	abadia_sna_patched.insert_file(file[1], file[3][0])

	# Display additional information about the assembled file to check if it
	# has exceed the memory address limit assigned to this block of code
	#
	# Some code is permitted to exceed the limit because some blocks overlap
	# with another block, and the patched version of the game reassigns blocks
	# to different memory addresses
	if display_debug_info:
		print(('{0}: length {1} (&{1:X}) bytes; ends at &{2:04X}, '
			+ 'limit is &{3:04X}\n').format(file[1], object_file_length,
			file[3][0] + object_file_length - 1, file[3][1]))

# When assembling the font that is used in the introduction, there are two
# separate parts (the table of pointers to the data for each character, and
# the block of character data itself), but the assembler fills the memory in
# between the two areas with zeroes, so it is necessary to copy a block of
# bytes from the unpatched snapshot between 0x68c7 and 0x6946 to the patched
# version
abadia_sna_patched.memory[0x68c7:intro_font_data_area[0]] = \
	abadia_sna_original.memory[0x68c7:intro_font_data_area[0]]

# At some points in the game (e.g. when retiring to your cell each night, or
# saving positions to disc), you are asked to confirm the action by pressing
# one of two keys (S or N in the original version). The 'S' key needs to be
# changed accordingly
abadia_sna_patched.memory[0x0571] = yes_key_number
abadia_sna_patched.memory[0x5081] = ord(yes_key_letter)
abadia_sna_patched.memory[0x5e98] = yes_key_number

# The word at 0x24e6 sets the start address of the text in the introduction
abadia_sna_patched.memory[0x24e6] = intro_text_area_patched[0]%256
abadia_sna_patched.memory[0x24e7] = intro_text_area_patched[0]//256

# The byte at 0x6754 in the CPC's main 64KiB of RAM controls the width of a
# space in the font that is displayed on the scrolls at the beginning of the
# game and when the game is completed successfully
abadia_sna_patched.memory[0x6754] = intro_font_space_width

# Copy the new loading screen and status bar to the snapshot
abadia_sna_patched.insert_bytes(new_loading_screen_data, 0xc000)
abadia_sna_patched.insert_bytes(new_status_bar_data, 0x1e328)


# ----------------------------------------------------
# Insert data into the snapshot and write a disk image
# ----------------------------------------------------

# Write the new loading screen to the disk image file
write_sectors(1, 0x21, new_loading_screen_data)

# Write the patched program data to the disk image file
write_sectors(5, 0x25, abadia_sna_patched.memory[0x8000:0xc000])
write_sectors(13, 0x2d, abadia_sna_patched.memory[0x0400:0x4000])
write_sectors(33, 0x21, abadia_sna_patched.memory[0x4000:0x8000])

write_sectors(28, 0x21, abadia_sna_patched.memory[0x10000:0x14000])
write_sectors(23, 0x21, abadia_sna_patched.memory[0x14000:0x18000])
write_sectors(18, 0x21, abadia_sna_patched.memory[0x18000:0x1c000])
write_sectors(9, 0x29, abadia_sna_patched.memory[0x1c000:0x20000])

# Write the new disk image file
try:
	print('Writing patched disk image to {0}...'.format(
		new_dsk_filepath))
	file = open(new_dsk_filepath, 'wb')
	file.write(abadia_dsk.header)
	file.write(abadia_dsk.track_info_block)
	file.close()
except OSError:
	print('ERROR: Unable to write disk image file {0}!'.format(
		new_dsk_filepath), file=sys.stderr)
	quit()

# Set up the inks, screen mode and register values for the snapshot of the
# patched version
abadia_sna_patched.set_firmware_border(0)
abadia_sna_patched.set_firmware_inks(loading_screen_palette)
abadia_sna_patched.set_screen_mode(0)
abadia_sna_patched.set_z80_register('PC', 0x0400)
abadia_sna_patched.set_z80_register('SP', 0x00fe)

# Write the snapshot
print('Writing patched snapshot to {0}...'.format(new_snapshot_filepath))
try:
	abadia_sna_patched.write(new_snapshot_filepath)
except OSError:
	print('ERROR: Unable to write snapshot {0}!'.format(new_snapshot_filepath),
		file=sys.stderr)
	quit()

# Compare bytes in the patched snapshot with another (original) snapshot
if display_debug_info:
	snapshot_en_original_filepath = 'abadia_en.sna'
	abadia_en_original_sna = Snapshot(snapshot_en_original_filepath,
		ram_size=128)

	for i in range(0x0400,0x1edff):
		if abadia_en_original_sna.memory[i] != abadia_sna_patched.memory[i]:
			print('{0:04X}: original: {1:02X}; patched: {2:02X}'.format(i,
				abadia_en_original_sna.memory[i], abadia_sna_patched.memory[i]))
