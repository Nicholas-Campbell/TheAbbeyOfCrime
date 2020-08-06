"""Functions for converting PC image files (e.g. GIF, PNG) to CPC format

Author: Nicholas Campbell
Last updated: 2020-08-06
"""

# Exceptions
class ListSizeError(Exception):
	def __init__(self, message):
		self.message = message
	def __str__(self):
		return(self.message)

def encode_pixels(pixels):
	"""Encode a set of pixels into a byte in the format used by the Amstrad CPC's
screen modes. Currently only Modes 0 and 1 are supported.

The encoding format is available from the URL below:
http://www.cpctech.org.uk/docs/graphics.html

Parameters:
    pixels (list): The set of pixels to encode. The first pixel in the list is
        the leftmost pixel, and the last pixel is the rightmost pixel. Each
        pixel represents a value corresponding to an ink number (0-15 for Mode
        0). The screen mode to use is determined by the number of pixels in the
        list (Mode 0 encodes 2 pixels per byte; Mode 1 encodes 4 pixels per
        byte).

Returns:
    int: A byte containing the encoded pixels.

Raises:
    TypeError: The set of pixels to encode was not supplied as a list or a
        tuple.
    ListSizeError: The list does not contain an appropriate number of pixels.
"""
	# Check that the list of pixels to encode is a list or a tuple
	if type(pixels) not in (list, tuple):
		raise TypeError('pixels must be a list or a tuple')

	# Check that the list is of the correct length; a byte can hold 2 encoded
	# pixels in Mode 0, or 4 in Mode 1
	elif len(pixels) not in (2,4):
		raise ListSizeError('List of pixels to encode must consist of 2 or 4 '
			+ 'values')

	# Get the maximum allowed value for a pixel
	else:
		if len(pixels) == 2:
			max_pixel_value = 15
		elif len(pixels) == 4:
			max_pixel_value = 3

	# Check that all of the specified pixels contain valid values
	for index in range(len(pixels)):
		if pixels[index] not in range(0,max_pixel_value + 1):
			raise ValueError('Pixel {0} '.format(index) + 'does not contain a '
				+ 'value between 0 and {0}'.format(max_pixel_value))

	# Encode the pixels

	# If 2 pixels are supplied, then encode them for Mode 0
	if len(pixels) == 2:
		# Mode 0 uses a palette of 16 colours (4 bits), so each byte encodes
		# ink values for 2 pixels, where each pixel consists of 4 bits numbered
		# 0-3 (3 is the leftmost bit, 0 is the rightmost bit). The pixel data
		# is encoded as follows (L = leftmost pixel, R = rightmost pixel):
		#
		# L0 R0 L2 R2 L1 R1 L3 R3

		# Encode the bits for each pixel
		encoded_pixel = ((pixels[0] & 0x08) >> 2
			| (pixels[0] & 0x04) << 3
			| (pixels[0] & 0x02) << 2
			| (pixels[0] & 0x01) << 7)
		encoded_pixel |= ((pixels[1] & 0x08) >> 3
			| (pixels[1] & 0x04) << 2
			| (pixels[1] & 0x02) << 1
			| (pixels[1] & 0x01) << 6)

	# If 4 pixels are supplied, then encode them for Mode 1
	elif len(pixels) == 4:
		# Mode 1 uses a palette of 4 colours (2 bits), so each byte encodes
		# ink values for 4 pixels, where each pixel consists of 2 bits numbered
		# 0-1 (1 is the leftmost bit, 0 is the rightmost bit). The pixel data
		# is encoded as follows (P0 = leftmost pixel, P3 = rightmost pixel):
		#
		# P0,0 P1,0 P2,0 P3,0 P0,1 P1,1 P2,1 P3,1

		# Encode the bits for each pixel
		encoded_pixel = ((pixels[0] & 0x02) << 2
			| (pixels[0] & 0x01) << 7)
		encoded_pixel |= ((pixels[1] & 0x02) << 1
			| (pixels[1] & 0x01) << 6)
		encoded_pixel |= ((pixels[2] & 0x02)
			| (pixels[2] & 0x01) << 5)
		encoded_pixel |= ((pixels[3] & 0x02) >> 1
			| (pixels[3] & 0x01) << 4)

	# Return the byte value containing the encoded pixels
	return encoded_pixel


def decode_pixels(byte, screen_mode):
	"""Decode a byte in the format used by the Amstrad CPC's screen modes to a set of
pixels. Currently only Modes 0 and 1 are supported.

The encoding format is available from the URL below:
http://www.cpctech.org.uk/docs/graphics.html

Parameters:
    byte (int): The byte to decode.
    screen_mode (int): The screen mode used to decode the byte (0-2).

Returns:
    list(int): A list containing the values of the decoded pixels.

Raises:
	ValueError: The screen byte is not a valid value (it must be between 0-255),
        or the screen mode is not a valid value (the Amstrad CPC has three
        screen modes numbered 0-2).
"""
	# Check that the value of the byte supplied is valid
	if byte not in range(0,256):
		raise ValueError('byte must be between 0 and 255')

	# Check that the screen mode is a valid value (i.e. 0-2)
	elif screen_mode not in (0,1):
		raise ValueError('Only screen Modes 0 and 1 are currently supported')

	# Decode the pixels

	# If Mode 0 is selected, then the byte contains 2 encoded pixels, each with
	# a value between 0-15
	if screen_mode == 0:
		pixels = [0] * 2

		# Mode 0 uses a palette of 16 colours (4 bits), so each byte encodes
		# ink values for 2 pixels, where each pixel consists of 4 bits numbered
		# 0-3 (3 is the leftmost bit, 0 is the rightmost bit). The pixel data
		# is encoded as follows (L = leftmost pixel, R = rightmost pixel):
		#
		# L0 R0 L2 R2 L1 R1 L3 R3
		pixels[0] = ((byte & 0x02) << 2
			| (byte & 0x20) >> 3
			| (byte & 0x08) >> 2
			| (byte & 0x80) >> 7)
		pixels[1] = ((byte & 0x01) << 3
			| (byte & 0x10) >> 2
			| (byte & 0x04) >> 1
			| (byte & 0x40) >> 6)

	# If Mode 1 is selected, then the byte contains 4 encoded pixels, each with
	# a value between 0-3
	elif screen_mode == 1:
		pixels = [0] * 4

		# Mode 1 uses a palette of 4 colours (2 bits), so each byte encodes
		# ink values for 4 pixels, where each pixel consists of 2 bits numbered
		# 0-1 (1 is the leftmost bit, 0 is the rightmost bit). The pixel data
		# is encoded as follows (P0 = leftmost pixel, P3 = rightmost pixel):
		#
		# P0,0 P1,0 P2,0 P3,0 P0,1 P1,1 P2,1 P3,1
		pixels[0] = ((byte & 0x08) >> 2
			| (byte & 0x80) >> 7)
		pixels[1] = ((byte & 0x04) >> 1
			| (byte & 0x40) >> 6)
		pixels[2] = ((byte & 0x02)
			| (byte & 0x20) >> 5)
		pixels[3] = ((byte & 0x01) << 1
			| (byte & 0x10) >> 4)

	# Return the set of decoded pixels
	return pixels


def convert_rgb_palette_to_cpc(palette):
	"""Convert a list of RGB palette values obtained via Pillow to the
corresponding firmware ink colours.

Parameters:
    palette (list): The palette of RGB values to be converted. The length of
		the list must be a multiple of 3. There are 3 entries for each colour
		in the palette (red, green and blue).

Returns:
    list: A list of 256 values, with each element containing the Amstrad CPC
		firmware ink colour value that best matches the RGB values that were
		converted.

Raises:
    ListSizeError: The palette of firmware ink colours does not contain the
correct number of values.
"""
	if len(palette)%3 != 0:
		raise ListSizeError('Palette does not contain correct number of values')

	cpc_palette = [0] * 256

	for palette_index in range(0,len(palette)//3):
		rgb_red = palette[palette_index*3]
		if rgb_red <= 85:
			cpc_red = 0
		elif rgb_red <= 170:
			cpc_red = 1
		else:
			cpc_red = 2

		rgb_green = palette[palette_index*3 + 1]
		if rgb_green <= 85:
			cpc_green = 0
		elif rgb_green <= 170:
			cpc_green = 1
		else:
			cpc_green = 2

		rgb_blue = palette[palette_index*3 + 2]
		if rgb_blue <= 85:
			cpc_blue = 0
		elif rgb_blue <= 170:
			cpc_blue = 1
		else:
			cpc_blue = 2

		cpc_palette[palette_index] = cpc_blue + (cpc_red*3) + (cpc_green*9)

	return cpc_palette


def convert_cpc_palette_to_rgb(palette):
	"""Convert a list containing firmware ink colours to an RGB palette for use with
Pillow.

Parameters:
    palette (list): The palette of firmware ink colours to be converted. A
        maximum of 16 values is permitted.

Returns:
    list: A list of 48 RGB values, with each group of 3 values representing the
        red, green and blue components of the corresponding Amstrad CPC
        firmware ink colour.

Raises:
    ListSizeError: The palette of firmware ink colours contains too many values.
"""
	# Check that the list of colours to convert is a list or a tuple
	if type(palette) not in (list, tuple):
		raise TypeError('palette must be a list or a tuple')

	# Check that the list is of the correct length; the maximum number of
	# colours in the palette is 16 (as used in the Amstrad CPC's Mode 0)
	elif len(palette) not in range(1,17):
		raise ListSizeError('Palette must contain between 1 and 16 values')

	# Check that all of the specified firmware ink colours contain valid
	# values; all ink colours must be between 0 and 26
	for index in range(len(palette)):
		if palette[index] not in range(0,27):
			raise ValueError('Ink {0} '.format(index) + 'of palette does not '
				+ 'contain a value between 0 and 26')

	rgb_palette = [0] * len(palette)*3

	for palette_index in range(0,len(palette)):
		cpc_green = palette[palette_index] // 9
		cpc_red = (palette[palette_index] - cpc_green*9) // 3
		cpc_blue = (palette[palette_index] - cpc_green*9 - cpc_red*3)

		if cpc_red == 0:
			rgb_red = 0
		elif cpc_red == 1:
			rgb_red = 128
		else:
			rgb_red = 255

		if cpc_green == 0:
			rgb_green = 0
		elif cpc_green == 1:
			rgb_green = 128
		else:
			rgb_green = 255

		if cpc_blue == 0:
			rgb_blue = 0
		elif cpc_blue == 1:
			rgb_blue = 128
		else:
			rgb_blue = 255

		rgb_palette[palette_index*3:(palette_index+1)*3] = \
			[rgb_red, rgb_green, rgb_blue]

	return rgb_palette
