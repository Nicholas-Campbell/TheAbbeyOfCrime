"""Extract data from an original disk image of the Spanish Amstrad CPC game La
Abadía del Crimen by Opera Soft and save it as PNG images and Z80 assembler
text files

Author: Nicholas Campbell
Last updated: 2020-08-06
"""

# Import modules
from copy import copy
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


def validate_dir(filepath):
	"""Check if the directory in a filepath exists, and if it does not exist, then
create it.

Parameters:
    filepath (str): The filepath to check.

Returns:
    str: The filepath that was checked.
    """
	dir = os.path.split(filepath)[0]
	if dir != '' and not os.path.isdir(dir):
		os.makedirs(dir)
	return filepath


# Functions for converting graphical data from the Amstrad CPC

def convert_cpc_screen_to_png(screen_data, palette):
	"""Convert an image in Amstrad CPC format to a PNG file using the specified
palette. The image is assumed to be in Mode 0, 80 bytes in width and 200 bytes
in height, which is the Amstrad CPC's standard screen size.

Parameters:
    screen_data (bytearray): The image in Amstrad CPC format.
	palette (list (int)): The ink values used in the image, using Amstrad CPC
        firmware ink colours.

Returns:
    PIL.Image.Image: The converted image.
    """
	# 'P' mode = 8-bit pixels mapped to a colour palette, 320x200 size, 0 =
	# black background
	png_image = Image.new('P', (320, 200), 0)
	rgb_palette = cpcimage.convert_cpc_palette_to_rgb(palette)
	png_image.putpalette(rgb_palette)

	for y in range(0,200):
		# Calculate the address to retrieve the encoded byte
		screen_ptr = (y%8)*0x800 + (y//8)*80

		for x in range(0,80):
			(left_pixel, right_pixel) = cpcimage.decode_pixels(
				screen_data[screen_ptr], 0)
			png_image.putpixel((x*4, y), left_pixel)
			png_image.putpixel((x*4 + 1, y), left_pixel)
			png_image.putpixel((x*4 + 2, y), right_pixel)
			png_image.putpixel((x*4 + 3, y), right_pixel)
			screen_ptr += 1

	return png_image

def convert_cpc_sprite_to_png(sprite_data, size, palette):
	"""Convert a sprite in Amstrad CPC format to a PNG file using the specified
screen mode and palette. The sprite is assumed to be drawn in Mode 1.

Parameters:
    screen_data (bytearray): The sprite data in Amstrad CPC format.
    size (list): A 2-element list or tuple containing the width and height of
        the sprite in bytes. Each byte contains data for 4 pixels in Mode 1.
	palette (list (int)): The ink values used in the image, using Amstrad CPC
        firmware ink colours.

Returns:
    PIL.Image.Image: The converted image.
    """
	# Check that the list of pixels to encode is a list or a tuple
	if type(size) not in (list, tuple):
		raise TypeError('size must be a list or a tuple and contain 2 elements')

	# 'P' mode = 8-bit pixels mapped to a colour palette, 0 = black background
	width = size[0]
	height = size[1]
	png_image = Image.new('P', (width*4, height), 0)
	rgb_palette = cpcimage.convert_cpc_palette_to_rgb(palette)
	png_image.putpalette(rgb_palette)

	sprite_ptr = 0
	for y in range(0,height):
		for x in range(0,width):
			pixels = cpcimage.decode_pixels(sprite_data[sprite_ptr], 1)
			png_image.putpixel((x*4, y), pixels[0])
			png_image.putpixel((x*4 + 1, y), pixels[1])
			png_image.putpixel((x*4 + 2, y), pixels[2])
			png_image.putpixel((x*4 + 3, y), pixels[3])
			sprite_ptr += 1

	return png_image


# Functions for writing Z80 assembler code to files

def write_intro_text_to_asm_file(file_handle):
	"""Write the text that is displayed on the scroll at the beginning of the game as
Z80 assembler code to a file.

Parameters:
    file_handle: A file object for writing to the file.
    """
	comments = '; La Abadía del Crimen - introduction text'
	write_scroll_text_to_asm_file(file_handle, intro_text_area[0], comments)

def write_ending_text_to_asm_file(file_handle):
	"""Write the text that is displayed on the scroll when the game is completed
successfully as Z80 assembler code to a file.

Parameters:
    file_handle: A file object for writing to the file.
    """
	comments = '; La Abadía del Crimen - ending text'
	write_scroll_text_to_asm_file(file_handle, ending_text_area[0], comments)

def write_scroll_text_to_asm_file(file_handle, start_addr, comments=None):
	"""Read text in La Abadía del Crimen that is displayed on a scroll, either at the
beginning of a game, or when the game is completed successfully, and write it
as Z80 assembler code to a file.

Parameters:
    file_handle: A file object for writing to the file.
    start_addr (int): The address in the Amstrad CPC's memory to start reading
        text.
    comments (str) (optional): Comments to write at the beginning of the file.
        This must be appropriately formatted (i.e. each line must begin with a
        semi-colon).
"""
	snapshot_ptr = start_addr
	org_addr = copy(start_addr)
	if start_addr >= 0x10000:
		org_addr = ((start_addr - 0x10000) & 0x3fff) + 0x4000

	# Write comments
	if comments:
		file_handle.write(comments + '\n;\n')
	file_handle.write('; Byte 13 (&0D) indicates the end of a line\n'
		+ '; Byte 26 (&1A) indicates the end of the text\n'
		+ '; w is used as a substitute for the letter ñ\n\n'
	)

	# Write the 'org' directive to tell the Z80 assembler what address to
	# assemble the text to
	file_handle.write('org &{0:0x}\n\n'.format(org_addr))

	# Write the text to the source code file, one line at a time
	line = ''

	# Byte 0x1a indicates the end of the text
	byte = 0
	while byte != 0x1a:
		byte = abadia_sna.memory[snapshot_ptr]

		# Byte 0x0d indicates a new line of text
		if byte == 0x0d:
			z80_assembler_str = 'db '

			# Work out the formatting of the 'db' directive to write to the
			# source code file, depending on whether or not the line of text is
			# blank
			if line != '':
				z80_assembler_str += '"' + line + '",'
			z80_assembler_str += '13'
			file_handle.write(z80_assembler_str + '\n')
			line = ''

		# Any other byte is treated as part of the text
		else:
			line += chr(byte)
		snapshot_ptr += 1

	# Write the final end-of-text byte (0x1a) to the source code file
	file_handle.write('db 26\n')

def write_intro_font_to_asm_file(file_handle):
	"""Write the data for the font used in the introduction and ending as Z80
assembler code to a file.

Parameters:
    file_handle: A file object for writing to the file.
"""
	snapshot_ptr = intro_font_table_area[0]

	# Write comments
	file_handle.write(
		'; La Abadía del Crimen - character data for font used in introduction and\n\
; ending\n\
\n\
; Table of pointers to data for each character\n\
;\n\
; If a character does not have any data, then the pointer is set to zero\n\n\
')

	# Write the 'org' directive to tell the Z80 assembler what address to
	# assemble the table of pointers to character data to
	file_handle.write('org &{0:0x}\n\n'.format(intro_font_table_area[0]))

	# Read the table of pointers to character data
	#
	# Store the start address of the data for each character in a dictionary
	# for use later on
	character_data_ptr = {}

	for char in range(32,125):
		char_ptr = (abadia_sna.memory[snapshot_ptr]
			+ (abadia_sna.memory[snapshot_ptr+1] * 256))
		if char_ptr != 0:
			character_data_ptr[char] = char_ptr
			file_handle.write(
				'dw char{0:d}_data ;{1}\n'.format(char, chr(char)))
		else:
			file_handle.write('dw 0\n')
		snapshot_ptr += 2

	# Write comments
	file_handle.write('\n; Character data for font used in introduction\n\
;\n\
; Each character is 15 pixels high and up to 16 pixels wide. Each byte of the\n\
; character data stores the coordinates to plot a pixel. The x-coordinate (0-15)\n\
; is stored in bits 0-3, and the y-coordinate (0-14) is stored in bits 4-7.\n\
;\n\
; If the y-coordinate is 15 (i.e. the hex value of the byte is &Fx), this marks\n\
; the end of the data for that character, and the x-coordinate stores the width\n\
; of the character.\n\n\
')

	# Write the 'org' directive to tell the Z80 assembler what address to
	# assemble the character data to
	file_handle.write('org &{0:x}\n\n'.format(intro_font_data_area[0]))

	# Write the data for each character, if it is defined
	snapshot_ptr = intro_font_data_area[0]
	char_offset = 0
	line_offset = 0
	line = ''

	while snapshot_ptr <= intro_font_data_area[1]:
		if char_offset == 0:
			char_found = False
			for char in character_data_ptr:
				if character_data_ptr[char] == snapshot_ptr:
					file_handle.write('char{0:d}_data: ;{1}\n'.format(
						char, chr(char)))
					char_found = True
			if not char_found:
				file_handle.write('; Unused character data\n')

		byte = abadia_sna.memory[snapshot_ptr]

		if line_offset == 0:
			if line != '':
				line += '\n'
			line += '\tdb '
		else:
			line += ','

		line += '&{0:02x}'.format(byte)
		snapshot_ptr += 1
		char_offset += 1
		line_offset += 1
		if line_offset == 16:
			line_offset = 0

		# Check if the end of the data for the current character has been
		# reached
		if byte & 0xf0 == 0xf0:
			file_handle.write(line + '\n')
			char_offset = 0
			line_offset = 0
			line = ''

	file_handle.write(line + '\n')

def write_canonical_hours_to_asm_file(file_handle):
	"""Write a list of canonical hours as Z80 assembler code to a file.

Parameters:
    file_handle: A file object for writing to the file.
"""
	snapshot_ptr = canonical_hours_area[0]

	# Write comments
	file_handle.write('; La Abadía del Crimen - list of canonical hours\n\
;\n\
; Punctuation marks are used in parts of the text in order to display the\n\
; appropriate canonical hour using only 7 characters. The font is redefined\n\
; accordingly so that the appropriate characters are displayed instead of the\n\
; corresponding punctuation marks\n\n\
')

	# Write the 'org' directive to tell the Z80 assembler what address to
	# assemble the list of canonical hours to
	file_handle.write('org &{0:0x}\n\n'.format(snapshot_ptr))

	# Read the list of canonical hours and write them to the source code file
	#
	# Each canonical hour consists of seven characters
	for canonical_hour in range(0,7):
		line = "db '" + abadia_sna.memory[snapshot_ptr:
			snapshot_ptr+7].decode('ascii') + "'"

		# Add comments to certain canonical hours, as some of their characters
		# are represented by punctuation marks in order to display them using
		# seven characters
		if canonical_hour == 5:
			line += '\t;VISPERAS'
		elif canonical_hour == 6:
			line += '\t;COMPLETAS'

		file_handle.write(line + '\n')
		snapshot_ptr += 7

def write_game_font_to_asm_file(file_handle):
	"""Write the data for the font used during the game as Z80 assembler code to a
file.

Parameters:
    file_handle: A file object for writing to the file.
"""
	snapshot_ptr = game_font_area[0]

	# Write comments
	file_handle.write('; La Abadía del Crimen - character data for font used in game\n\
;\n\
; Some punctuation marks are redefined to represent more than one character\n\
; for use by the canonical hour texts. The letter W is also redefined to Ñ\n\n\
')

	# Write the 'org' directive to tell the Z80 assembler what address
	# to assemble the character data to
	file_handle.write('org &{0:x}\n\n'.format(snapshot_ptr))

	for char in range(45,91):
		line = 'char{0}_data: db '.format(char)
		for i in range(0,8):
			if i > 0:
				line += ','
			line += '&{0:02x}'.format(abadia_sna.memory[snapshot_ptr])
			snapshot_ptr += 1
		line += '\t;' + chr(char)

		file_handle.write(line + '\n')

def write_game_text_to_asm_file(file_handle):
	"""Write the data for the messages that are used within the game as Z80 assembler
code to a file. The game contains a dictionary of words, each represented by a
number from 0 to 248, and a list of messages, with each word in the message
being stored as its corresponding number in the dictionary. Punctuation marks
are also stored as numbers.

Parameters:
    file_handle: A file object for writing to the file.
"""
	snapshot_ptr = dictionary_area[0]

	# Write comments relating to the dictionary
	file_handle.write(
"; La Abadía del Crimen - dictionary of 'words' used in the messages that are\n\
; displayed during the game\n\
;\n\
; There are a number of restrictions:\n\
;\n\
; * Numbering of the words begins from 0, and the last character of each word\n\
;   must have bit 7 set (by adding 128 to it)\n\
; * The letter Ñ is replaced with W\n\
; * Use upper case letters only\n\
; * The maximum number of words permitted is 249\n\
; * Word 6 (AAA) must not be altered, as the game modifies it internally\n\
;\n\
; Each 'word' does not have to be a full word; parts of words can be combined\n\
; to create a full word by using byte 249 (e.g. 'BIEN', 'VENID', 'O' ->\n\
; 'BIENVENIDO'\n\n\
")

	# Write the 'org' directive to tell the Z80 assembler what address to
	# assemble the dictionary to
	file_handle.write('org &{0:0x}\n\n'.format(dictionary_area[0]))

	# Read the list of words in the dictionary one at a time
	#
	# The dictionary can contain a maximum of 249 words; entries 250-254 are
	# used for punctuation, and entry 255 is used as an end-of-message marker
	dictionary = [None] * 256

	for word_index in range(0,249):
		word = ''
		byte = 0

		while True:
			# Read the next letter of the current word
			byte = abadia_sna.memory[snapshot_ptr]

			# A zero byte marks the end of the dictionary
			if byte == 0:
				break
			else:
				snapshot_ptr += 1

			# The final letter of each word has bit 7 set
			if byte & 0x80 == 0x80:
				word += chr(byte & 0x7f)
				dictionary[word_index] = word
				break
			else:
				word += chr(byte)

		# Work out the formatting of the 'db' directive to write to the source
		# code file, depending on the length of the word
		line = 'word{0}: db '.format(word_index)
		if word:
			if len(word) == 1:
				line += "'" + word + "'+128"
			else:
				line += ("'" + word[0:len(word)-1] + "','"
					+ word[len(word)-1] + "'+128"
				)

			# Add a comment to word 6 to warn the user that it must not be
			# altered, as the game modifies it internally
			if word_index == 6:
				line += '\t; Do not alter this word!'

			file_handle.write(line + '\n')

	# Add punctuation marks to the dictionary, as used by the game
	word_index = 250
	for punctuation in ['¿','?',';','.',',']:
		dictionary[word_index] = punctuation
		word_index += 1

	# Write comments relating to the in-game scrolling messages
	file_handle.write(
'\n; Encoded text used in scrolling messages\n\
;\n\
; Each byte represents the number of the corresponding word in the dictionary.\n\
; The following bytes are also used:\n\
;\n\
; * 249 (&F9) - do not add a space after the current word\n\
; * 250 (&FA) - inverted question mark (¿)\n\
; * 251 (&FB) - question mark (?)\n\
; * 252 (&FC) - semicolon (;)\n\
; * 253 (&FD) - full stop (.)\n\
; * 254 (&FE) - comma (,)\n\
; * 255 (&FF) - end of message\n\n\
')

	snapshot_ptr = messages_area[0]
	source_code_column_max = 79	# Maximum line length to use in source code
								# file

	# Write the 'org' directive to tell the Z80 assembler what address
	# to assemble the character data to
	file_handle.write('org &{0:x}\n\n'.format(messages_area[0]))

	# There are 56 messages in total, numbered from 0-55
	for message_index in range(0,56):
		line = '; Message {0} - '.format(message_index)
		message = ''
		message_bytes = []
		byte = 0
		add_leading_space = False
		start_new_line = False

		# Flag for setting word wrap when writing the messages to the source
		# code file
		message_word_wrap = True

		while True:
			byte = abadia_sna.memory[snapshot_ptr]
			snapshot_ptr += 1
			message_bytes.append(byte)

			# Byte 0xf9 (249) indicates that a space should not be added after
			# the current word; this is used for joining two or more words
			# together (e.g. 'BIEN', 'VENID', 'O' -> 'BIENVENIDO')
			if byte == 0xf9:
				add_leading_space = False

			# Bytes 0xfa to 0xfe inclusive (250-254) are used for punctuation
			# marks
			elif byte in range(0xfa,0xff):
				message += dictionary[byte]

				# There appears to be a bug in the game; if an inverted
				# question mark (¿) is used, it is always followed by a space
				if byte == 0xfa:
					add_leading_space = True

			# Byte 0xff indicates the end of the message
			elif byte == 0xff:
				break

			# Any other value is treated as a word from the dictionary
			else:
				if add_leading_space:
					message += ' '
				message += dictionary[byte]
				add_leading_space = True

		# Replace the letter W in the message with Ñ
		message = message.replace('W', 'Ñ')

		# Write the message text in a comment, and split it across more than
		# one line if the message is long enough and word wrap is set
		message_words = message.split(' ')
		line = '; Message {0} -'.format(message_index)
		for word in message_words:
			if ((len(line) + len(word)+1 > source_code_column_max)
				and message_word_wrap):
				file_handle.write(line + '\n')
				line = '; '
			line += ' ' + word
		file_handle.write(line + '\n')

		# Write the sequence of word numbers that the message consists of to
		# the source code file
		line = ''
		current_line = 'db '
		byte = 0
		message_bytes_index = 0
		line_index = 0	# Position of byte in current line

		# Byte 0xff indicates the end of the message
		while byte != 0xff:
			byte = message_bytes[message_bytes_index]
			byte_str = str(byte)

			# Start a new line if appending the next byte makes the line too
			# long and word wrap is set
			if (len(current_line) + len(byte_str)+1) > source_code_column_max:
				line += current_line + '\n'
				current_line = 'db '
				line_index = 0
			if line_index > 0:
				current_line += ','
			current_line += byte_str

			message_bytes_index += 1
			line_index += 1

		line += current_line
		file_handle.write(line + '\n\n')

def write_score_text_to_asm_file(file_handle):
	"""Write the text that is displayed with the player's final score upon failure to
complete the game as Z80 assembler code to a file.

Parameters:
    file_handle: A file object for writing to the file.
"""
	snapshot_ptr = score_text_area[0]

	# Write comments
	file_handle.write(
"; La Abadía del Crimen - text used when displaying the player's final score\n\
; upon failure to complete the game\n\n")

	# Write the 'org' directive to tell the Z80 assembler what address to
	# assemble the text to
	file_handle.write('org &{0:0x}\n\n'.format(snapshot_ptr))

	file_handle.write(
'; Do not alter the length of the string below (15 bytes)!\n'
		+ 'db "' + abadia_sna.memory[snapshot_ptr:snapshot_ptr+15].decode(
			encoding='latin_1')
		+ '",255\n\n\
')
	file_handle.write(
'; The game copies the final score to the first three bytes of the string below,\n\
; so do not alter them!\n\
ld hl,&300e\n\
ld (&2d97),hl\n\
call &4fee\n\
')
	snapshot_ptr += 25
	file_handle.write(
		'db "' + abadia_sna.memory[snapshot_ptr:snapshot_ptr+15].decode(
			encoding='latin_1')
		+ '",255\n\n\
ld hl,&400c\n\
ld (&2d97),hl\n\
call &4fee\n\
')
	snapshot_ptr += 25
	file_handle.write('db "'
		+ abadia_sna.memory[snapshot_ptr:snapshot_ptr+19].decode(
			encoding='latin_1')
		+ '",255\n\n\
ld hl,&8006\n\
ld (&2d97),hl\n\
call &4fee\n\
')
	snapshot_ptr += 29
	file_handle.write('db "'
		+ abadia_sna.memory[snapshot_ptr:snapshot_ptr+26].decode(
			encoding='latin_1')
		+ '",255\n')


# ------------
# Main program
# ------------

# Check that the name of the disk image file has been provided in the
# command line arguments
if len(sys.argv) != 2:
	script_name = sys.argv[0]
	print('Usage: python {0} dsk_image_file\n'.format(script_name))
	print('Example:')
	print('  python {0} abadia.dsk'.format(script_name))
	print('  Read the disk image abadia.dsk and extract data from it.')
	quit()
else:
	dsk_filepath = sys.argv[1]

# Check that the disk image file exists
if not os.path.exists(dsk_filepath):
	print('ERROR: Disk image {0} does not exist!'.format(dsk_filepath),
		file=sys.stderr)
	quit()

# Check that the disk image can be opened and read
try:
	print('Reading disk image {0}...'.format(dsk_filepath))
	abadia_dsk = DiskImage(dsk_filepath)
except OSErrpr:
	print('ERROR: Unable to read disk image {0}!'.format(dsk_filepath),
		file=sys.stderr)
	quit()

# Create an Amstrad CPC snapshot to store the data that will be read from the
# disk image
abadia_sna = Snapshot(ram_size=128)


# --------------------------------
# Extract data from the disk image
# --------------------------------

# Read the loading screen from the disk image
#
# The loading screen starts at track 1, sector 0x21 and is 64 sectors in length
# (0x4000 bytes in total)
print('Extracting loading screen from {0}...'.format(dsk_filepath))
loading_screen_data = read_sectors(abadia_dsk, 1, 0x21, 64)

# Read the program data from the disk image
#
# The data is stored on the disk in such a way that the data between 0x4000
# and 0x7fff is intended for bank 0xc7 of the CPC's RAM; the data for bank 0xc0
# (in the main 64KiB of RAM) is stored at another location on the disk
print('Extracting game code from {0}...'.format(dsk_filepath))
abadia_sna = read_game_data_into_snapshot(abadia_dsk, abadia_sna)

# Convert the loading screen to a PNG image
png_loading_screen = convert_cpc_screen_to_png(loading_screen_data,
	loading_screen_palette)

# Write the loading screen as a PNG image, using a 4-bit colour palette and
# optimising it to be as small as possible
print('Writing loading screen to {0}...'.format(png_loading_screen_filepath))
try:
	png_loading_screen.save(validate_dir(png_loading_screen_filepath),
		optimize=True, dpi=(72,72), bits=4)
except OSError:
	print('ERROR: Unable to write file {0}!'.format(
		png_loading_screen_filepath), file=sys.stderr)
	quit()

# Extract the status bar from the program data and convert it to a PNG image
print('Extracting status bar...')
status_bar_width = 64
status_bar_height = 32
status_bar_data = abadia_sna.memory[0x1e328:
	0x1e328 + (status_bar_width * status_bar_height)]
png_status_bar = convert_cpc_sprite_to_png(status_bar_data,
	(status_bar_width, status_bar_height), game_palette)

# Write the PNG image, using a 4-bit colour palette and optimising it to be
# as small as possible
print('Writing status bar to {0}...'.format(
	png_status_bar_filepath))
try:
	png_status_bar.save(validate_dir(png_status_bar_filepath), optimize=True,
		dpi=(72,72), bits=4)
except OSError:
	print('ERROR: Unable to write file {0}!'.format(
		png_loading_screen_filepath), file=sys.stderr)
	quit()

# Write the Z80 assembler source code files that are used in the patch
#
# Each entry in the source_code_files_to_write list is a tuple containing
# the following elements:
# * The filepath of the source code file to write
# * The name of the function that writes the corresponding file
# * A description of the data being written; this is used when writing a
#   message to the console
source_code_files_to_write = [
	(intro_text_original_filepath, 'write_intro_text_to_asm_file',
		'text in introduction'),
	(intro_font_original_filepath, 'write_intro_font_to_asm_file',
		'font in introduction'),
	(game_text_original_filepath, 'write_game_text_to_asm_file',
		'dictionary and messages'),
	(canonical_hours_original_filepath, 'write_canonical_hours_to_asm_file',
		'canonical hours'),
	(game_font_original_filepath, 'write_game_font_to_asm_file',
		'font in game'),
	(score_text_original_filepath, 'write_score_text_to_asm_file',
		'score text'),
	(ending_text_original_filepath, 'write_ending_text_to_asm_file',
		'text in ending')
]
for file in source_code_files_to_write:
	try:
		file_to_write = file[0]

		# Check if the directory to write the file to exists; if it does
		# not exist, then create it
		validate_dir(file_to_write)

		# Attempt to write the Z80 source code file
		print('Writing {0} to {1}...'.format(file[2], file_to_write))
		with open(file_to_write, 'w', encoding='utf8') as file_handle:
			# Call the corresponding function that generates the source code
			locals()[file[1]](file_handle)
	except OSError:
		print('ERROR: Unable to open file {0} for writing!'.format(
			file_to_write), file=sys.stderr)
		quit()
