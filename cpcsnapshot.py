"""Tools for manipulating Amstrad CPC snapshots.

The specification of the Amstrad CPC snapshot format is available at the
following URL:
<https://www.cpcwiki.eu/index.php/Snapshot>

Author: Nicholas Campbell
Last updated: 2020-08-06
"""

import os

class Snapshot():
	# Exceptions for this class
	class FileFormatError(Exception):
		def __init__(self, message):
			self.message = message
		def __str__(self):
			return(self.message)

	class InvalidZ80RegisterError(Exception):
		def __init__(self, register):
			self.register = register
		def __str__(self):
			return(repr(self.register) + ' is not a valid Z80 register')

	class ListSizeError(Exception):
		def __init__(self, min_length, max_length):
			self.min_length = min_length
			self.max_length = max_length
		def __str__(self):
			return('List must contain between {0:d} and {1:d} items'.format(
				self.min_length, self.max_length))

	# Lists of valid 8-bit and 16-bit Z80 registers, in the order specified in
	# the Amstrad CPC snapshot specification
	z80_registers_8bit = ['F', 'A', 'C', 'B', 'E', 'D', 'L', 'H', 'R', 'I',
		"F'", "A'", "C'", "B'", "E'", "D'", "L'", "H'"]
	z80_registers_16bit = ['AF', 'BC', 'DE', 'HL', 'IX', 'IY', 'SP', 'PC',
		"AF'", "BC'", "DE'", "HL'"]

	# Table for converting hardware ink values to their corresponding firmware
	# ink values
	firmware_inks = [
		13,27,19,25, 1, 7,10,16,28,29,24,26, 6, 8,15,17,
		30,31,18,20, 0, 2, 9,11, 4,22,21,23, 3, 5,12,14]

	def __init__(self, filepath=None, ram_size=64):
		"""Create a new snapshot object.

Parameters:
    filepath (str, optional): An existing Amstrad CPC snapshot file to copy
        into the new snapshot.
    ram_size (int, optional): The size of the snapshot RAM in kibibytes. The
        only valid values are 64 (i.e. 64KiB or 65,536 bytes) and 128 (i.e.
        128KiB or 131,072 bytes).
        """
		# The memory size of a snapshot must be either 64KiB or 128KiB
		if ram_size not in [64, 128]:
			raise ValueError("'ram_size' must be either 64 or 128")

		# If no filepath is specified, then create a blank 64KiB snapshot
		if filepath is None:
			self.header = bytearray(256)
			self.memory = bytearray(ram_size * 1024)
			self.header[0x10] = 2	# Set snapshot version
			self.header[0x6b] = ram_size

			# Insert the 'MV - SNA' ASCII string into the first eight bytes of
			# the header; this identifies a file as an Amstrad CPC snapshot
			self.header[0:8] = 'MV - SNA'.encode('ascii')

			# Set the default CRTC registers
			self.set_crtc_registers(
				[63,40,46,142,38,0,25,30,0,7,0,0,48,0,192,0])

			# Set the border and all inks to black (hardware ink 20)
			self.set_inks([20] * 16)
			self.set_border(20)

			# Use screen MODE 1 and disable both the upper and lower ROMs
			self.set_screen_mode(1)
			self.disable_lower_rom()
			self.disable_upper_rom()

			# Disable interrupts
			self.disable_interrupts()

			# Set the PPI control word register, which controls the status of
			# PPI ports A-C (whether they are input or output)
			self.header[0x59] = 0x82

		# If a filepath is specified, then copy it into the new snapshot
		else:
			# Read the header of the snapshot file, which is 256 bytes long
			with open(filepath, 'rb') as sna_file:
				self.header = bytearray(sna_file.read(256))

				# Amstrad CPC snapshot files are identified by the ASCII
				# string 'MV - SNA' in the first eight bytes of the file
				if self.header[0:8].decode('latin_1') != 'MV - SNA':
					raise Snapshot.FileFormatError(('{0} is not an '
						+ 'Amstrad CPC snapshot file').format(repr(filepath)))

				# Currently, only version 2 Amstrad CPC snapshot files are
				# supported
				self.version = self.header[0x10]
				if self.version != 2:
					raise Snapshot.FileFormatError('Only version 2 '
						+ 'Amstrad CPC snapshot files are supported')

				# The snapshot file is valid, so read the rest of the file
				self.memory = bytearray(sna_file.read(
					(os.stat(filepath).st_size) - 256))


	# ----------------------
	# Z80 register functions
	# ----------------------

	def _get_z80_register_offset(register):
		"""Internal function to find the location of a Z80 register in the snapshot
header.

Parameters:
    register (str): The name of the register (e.g. A, BC', E, HL, R, IX, SP).

Returns:
    int: The offset of the register in the snapshot header.

Raises:
    Snapshot.InvalidZ80RegisterError: The name of the register is not valid.
        """
		# Check if an 8-bit register has been specified
		try:
			register_index = Snapshot.z80_registers_8bit.index(register)
			if register_index <= 9:
				offset = register_index + 0x11
			else:
				offset = register_index + 0x1c
			return(offset)
		except ValueError:
			pass

		# Check if a 16-bit register has been specified
		try:
			register_index = Snapshot.z80_registers_16bit.index(register)
			if register_index <= 3:
				offset = register_index*2 + 0x11
			elif register_index <= 7:
				offset = register_index*2 + 0x15
			else:
				offset = register_index*2 + 0x16
			return(offset)
		except ValueError:
			pass

		# If the specified register can't be found, then raise an exception
		raise Snapshot.InvalidZ80RegisterError(register)

	def get_z80_register(self, register):
		"""Get the value of a Z80 register from the snapshot.

Parameters:
    register (str): The name of the register (e.g. A, BC', E, HL, R, IX, SP).

Returns:
    int: The value of the register (0-255 for an 8-bit register, or 0-65535
    for a 16-bit register.

Raises:
    Snapshot.InvalidZ80RegisterError: The name of the register is not valid.
        """
		# Check the specified register is an 8-bit register
		if register in Snapshot.z80_registers_8bit:
			return(self.header[Snapshot._get_z80_register_offset(register)])

		# Check if it is a 16-bit register
		elif register in Snapshot.z80_registers_16bit:
			offset = Snapshot._get_z80_register_offset(register)
			return(self.header[offset] + 256*self.header[offset+1])

		# If the specified register can't be found, then raise an exception
		else:
			raise Snapshot.InvalidZ80RegisterError(register)

	def get_z80_registers(self):
		"""Get the values of all Z80 registers from the snapshot.

Parameters:
    None.

Returns:
    dict: A dictionary of register names and their corresponding values.
        """
		z80_registers = {}
		for register in Snapshot.z80_registers_8bit:
			z80_registers[register] = self.get_z80_register(register)
		for register in Snapshot.z80_registers_16bit:
			z80_registers[register] = self.get_z80_register(register)
		return z80_registers

	def set_z80_register(self, register, value):
		"""Set the value of a Z80 register in the snapshot.

Parameters:
    register (str): The name of the register (e.g. A, BC', E, HL, R, IX, SP).
    value (int): The value of the register to set.

Returns:
    Nothing.

Raises:
    Snapshot.InvalidZ80RegisterError: The name of the register is not valid.
    ValueError: The value to set is not valid.
        """

		# Check that the specified Z80 register is valid
		try:
			offset = Snapshot._get_z80_register_offset(register)
		except Snapshot.InvalidZ80RegisterError:
			raise Snapshot.InvalidZ80RegisterError(register)

		# Set the value of the specified Z80 register, and raise an exception
		# if the value is invalid
		if register in Snapshot.z80_registers_8bit:
			if value not in range(0, 256):
				raise ValueError('Value of 8-bit register to set must be in '
					+ 'range (0, 256)')
			else:
				self.header[offset] = value
		else:
			if value not in range(0, 65536):
				raise ValueError('Value of 16-bit register to set must be in '
					+ 'range(0, 65536)')
			else:
				self.header[offset] = value % 256
				self.header[offset+1] = value // 256


	# -------------------
	# Interrupt functions
	# -------------------

	def enable_interrupts(self):
		"""Enable maskable interrupts by setting bit 0 of the IFF0 flag to 1.

Parameters:
    None.

Returns:
    Nothing.
        """
		self.header[0x1b] = (self.header[0x1b] & 0xfe) | 0x01
		self.header[0x1c] = (self.header[0x1b] & 0xfe) | 0x01

	def disable_interrupts(self):
		"""Disable maskable interrupts by setting bit 0 of the IFF0 flag to 0.

Parameters:
    None.

Returns:
    Nothing.
        """
		self.header[0x1b] = (self.header[0x1b] & 0xfe)
		self.header[0x1c] = (self.header[0x1b] & 0xfe)

	# -------------
	# Ink functions
	# -------------

	def _validate_hardware_ink_colour(colour):
		"""Internal function to check if a hardware ink colour is valid.

Hardware ink colours can be specified either by using a value between 0-31
(0-0x1f), or 0x40-0x5f (which is the format used in the OUT Z80 command when
defining inks).

Parameters:
    colour (int): The hardware ink colour.

Returns:
    bool: True if the colour is valid, False if it is invalid.
        """
		if colour in range(0,0x20) or colour in range(0x40,0x60):
			return True
		else:
			return False

	def get_ink(self, ink):
		"""Get the hardware colour of an ink.

Parameters:
    ink (int): The number of the ink to get the colour of (0-15).

Returns:
    int: The colour of the specified ink (0-31).

Raises:
    ValueError: The number of the ink is not valid.
        """
		return(self.header[(ink + 0x2f)] & 0x3f)

	# get_hardware_ink is an alias of get_ink
	get_hardware_ink = get_ink

	def get_firmware_ink(self, ink):
		"""Get the firmware colour of an ink.

Parameters:
    ink (int): The number of the ink to get the colour of (between 0-15).

Returns:
    int: The colour of the specified ink.

Raises:
    ValueError: The number of the ink is not valid.
        """
		return(Snapshot.firmware_inks[self.header[(ink + 0x2f)] & 0x3f])

	def get_inks(self):
		"""Get the hardware colours of all 16 inks.

Parameters:
    None.

Returns:
    list: A list of the hardware colours of all 16 inks. The values of the
    colours are 0-31.
        """
		inks = [0] * 16
		for ink in range(0, 16):
			inks[ink] = self.get_ink(ink)
		return(inks)

	# get_hardware_inks is an alias of get_inks
	get_hardware_inks = get_inks

	def get_firmware_inks(self):
		"""Get the firmware colours of all 16 inks.

Parameters:
    None.

Returns:
    list: A list of the firmware colours of all 16 inks. The values of the
        colours are 0-31.
        """
		inks = [0] * 16
		for ink in range(0, 16):
			inks[ink] = self.get_firmware_ink(ink)
		return(inks)

	def get_border(self):
		"""Get the hardware colour of the border.

Parameters:
    None.

Returns:
    int: The hardware colour of the border (0-31).
        """
		return(self.header[0x3f] & 0x3f)

	# get_hardware_border is an alias of get_border
	get_hardware_border = get_border

	def get_firmware_border(self):
		"""Get the firmware colour of the border.

Parameters:
    None.

Returns:
    int: The firmware colour of the border (0-31).
        """
		return(Snapshot.firmware_inks[self.get_border()])

	def set_ink(self, ink, colour):
		"""Set the colour of an ink using hardware values.

Hardware ink colours can be specified either by using a value between 0-31
(0-0x1f), or 0x40-0x5f (which is the format used in the OUT Z80 command when
defining inks).

Parameters:
    ink (int): The number of the ink to set (0-15).
    colour (int): The colour of the ink to set (0-31 or 0x40-0x5f).

Returns:
    Nothing.

Raises:
    ValueError: Either the number or the colour of the ink to set is not
        valid.
        """

		# Check that the ink number and colour are both valid
		if ink not in range(0, 16):
			raise ValueError('Invalid value specified for ink; '
				+ 'value must be between 0 and 15')
		elif colour not in range(0, 32):
			raise ValueError('Invalid colour specified for ink; '
				+ 'value must be between 0 and 31')

		# If they are both valid, then set the ink to the specified colour
		else:
			self.header[ink + 0x2f] = colour

	# set_hardware_ink is an alias of set_ink
	set_hardware_ink = set_ink

	def set_inks(self, inks):
		"""Set the colours of several inks using hardware values.

Hardware ink colours can be specified either by using a value between 0-31
(0-0x1f), or 0x40-0x5f (which is the format used in the OUT Z80 command when
defining inks).

Parameters:
    inks (list): A list of the hardware colours of the inks to set. The list
        can contain between 1-16 items, and the first item in the list is ink
        0.

Returns:
    Nothing.

Raises:
    TypeError: inks is not a list.
    Snapshot.ListSizeError: The size of the list of inks to set is incorrect.
    ValueError: The colour of an ink to set is not valid.
        """
		# Check that the inks are specified as a list
		if type(inks) is not list:
			raise TypeError('Inks must be specified as a list')

		# The list of inks must be between 1 and 16 items long
		if (len(inks) not in range(1,17)):
			raise Snapshot.ListSizeError(1, 16)
		else:
			for ink in range(len(inks)):
				colour = inks[ink]
				if Snapshot._validate_hardware_ink_colour(colour) is False:
					raise ValueError(('Invalid colour specified for ink '
						+ '{0}; value must be between 0 and 31').format(ink))
				else:
					self.set_ink(ink, colour)

	# set_hardware_inks is an alias of set_inks
	set_hardware_inks = set_inks

	def set_firmware_ink(self, ink, colour):
		"""Set the colour of an ink using firmware values.

Parameters:
    ink (int): The number of the ink to set (0-15).
    colour (int): The colour of the ink to set (0-31).

Returns:
    Nothing.

Raises:
    ValueError: Either the number or the colour of the ink to set is not
        valid.
        """
		# Check that the ink number and colour are both valid
		if ink not in range(0, 16):
			raise ValueError('Invalid value specified for ink; '
				+ 'value must be between 0 and 15')
		elif colour not in range(0, 32):
			raise ValueError('Invalid colour specified for ink; '
				+ 'value must be between 0 and 31')

		# If they are both valid, then set the ink to the specified colour
		else:
			self.header[ink + 0x2f] = self.header[ink + 0x2f] = \
				Snapshot.firmware_inks.index(colour)

	def set_firmware_inks(self, inks):
		"""Set the colours of all inks using firmware values.

Parameters:
    inks (list): A list of the firmware colours of the inks to set. The list
        can contain between 1-16 items, and the first item in the list is ink
        0.

Returns:
    Nothing.

Raises:
    TypeError: inks is not passed as a list.
    Snapshot.ListSizeError: The size of the list is incorrect.
    ValueError: The colour of an ink to set is not valid.
        """
		# Check that the inks are specified as a list
		if type(inks) is not list:
			raise TypeError('Inks must be specified as a list')

		# The list of inks must be between 1 and 16 items long
		if (len(inks) not in range(1,17)):
			raise Snapshot.ListSizeError(1, 16)
		else:
			for ink in range(len(inks)):
				colour = inks[ink]
				if colour not in range(0,32):
					raise ValueError(('Invalid colour specified for ink '
						+ '{0}; value must be between 0 and 31').format(ink))
				else:
					self.header[ink + 0x2f] = \
						Snapshot.firmware_inks.index(colour)

	def set_border(self, colour):
		"""Set the colour of the border using hardware values.

Hardware ink colours can be specified either by using a value between 0-31
(0-0x1f), or 0x40-0x5f (which is the format used in the OUT Z80 command when
defining inks).

Parameters:
    colour (int): The colour to set the border to (0-31 or 0x40-0x5f).

Returns:
    Nothing.

Raises:
    ValueError: The colour to set the border to is not valid.
        """
		if Snapshot._validate_hardware_ink_colour(colour) is False:
			raise ValueError('Invalid colour specified for border; '
				+ 'value must be between 0 and 31')
		else:
			self.header[0x3f] = colour

	# set_hardware_border is an alias of set_border
	set_hardware_border = set_border

	# Set the border colour using firmware values
	def set_firmware_border(self, colour):
		"""Set the colour of the border using firmware values.

Parameters:
    colour (int): The colour to set the border to (0-31).

Returns:
    Nothing.

Raises:
    ValueError: The colour to set the border to is not valid.
        """
		if Snapshot._validate_hardware_ink_colour(colour) is False:
			raise ValueError('Invalid colour specified for border; '
				+ 'value must be between 0 and 31')
		else:
			self.header[0x3f] = Snapshot.firmware_inks.index(colour)

	# ---------------------
	# Screen mode functions
	# ---------------------

	# Get the screen mode
	def get_screen_mode(self):
		"""Get the screen mode of the snapshot.

Parameters:
    None.

Returns:
    int: The screen mode (0-3).
        """

		return(self.header[0x40] & 0x03)

	def set_screen_mode(self, screen_mode):
		"""Set the screen mode of the snapshot.

The following modes are valid (these are equivalent to the MODE command used
in Locomotive BASIC):
* 0: 160x200 pixels, 16 colours
* 1: 320x200 pixels, 4 colours
* 2: 640x200 pixels, 2 colours

MODE 3 also exists, but in practice, it is never used (its resolution is
160x200 pixels and it only offers 4 colours).

Parameters:
    screen_mode (int): The screen mode to use (0-3).

Returns:
    Nothing.

Raises:
    ValueError: The value of the screen mode is not valid.
        """
		if screen_mode not in range(0,4):
			raise ValueError('Invalid value specified for screen mode; '
				+ 'value must be between 0 and 3')
		else:
			self.header[0x40] = (self.header[0x40] & 0xfc) | screen_mode


	# -----------------------------------------
	# ROM configuration and selection functions
	# -----------------------------------------

	def get_rom_status(self):
		"""Get the status of the lower and upper ROMs.

Parameters:
    None.

Returns:
    tuple: A 2-item tuple containing the status of the lower ROM (item 0) and
        upper ROM (item 1). True means the ROM is enabled, and False means the
        ROM is disabled.
        """
		# Set default status values
		lower_rom_enabled = True
		upper_rom_enabled = True

		# The status of the lower ROM is stored in bit 2 of the mode and ROM
		# configuration register of the gate array (0 = enabled, 1 = disabled)
		if self.header[0x40] & 0x04:
			lower_rom_enabled = False

		# The status of the upper ROM is stored in bit 3 of the mode and ROM
		# configuration register of the gate array (0 = enabled, 1 = disabled)
		if self.header[0x40] & 0x08:
			upper_rom_enabled = False

		return(lower_rom_enabled, upper_rom_enabled)

	def enable_lower_rom(self):
		"""Enable the lower ROM.

When enabled, the lower ROM is mapped to addresses 0x0-0x3fff.

Parameters:
    None.

Returns:
    Nothing.
        """
		self.header[0x40] = (self.header[0x40] & 0xfb)

	def disable_lower_rom(self):
		"""Disable the lower ROM.

Parameters:
    None.

Returns:
    Nothing.
        """
		self.header[0x40] = (self.header[0x40] & 0xfb) | 0x04

	def enable_upper_rom(self):
		"""Enable the upper ROM.

When enabled, the upper ROM is mapped to addresses 0xc000-0xffff.

Parameters:
    None.

Returns:
    Nothing.
        """
		self.header[0x40] = (self.header[0x40] & 0xf7)

	def disable_upper_rom(self):
		"""Disable the upper ROM.

Parameters:
    None.

Returns:
    Nothing.
        """
		self.header[0x40] = (self.header[0x40] & 0xf7) | 0x08

	def get_upper_rom_number(self):
		"""Get the number of the currently selected upper ROM.

Parameters:
    None.

Returns:
    int: The currently selected upper ROM.
        """
		return(self.header[0x55])

	def set_upper_rom_number(self, upper_rom_number):
		"""Select an upper ROM.

0 is the number for Locomotive BASIC, and 7 is the number for AMSDOS (the
Amstrad CPC's disc operating system). Other values can also be used, but the
ROMs need to be configured in an emulator.

Parameters:
    upper_rom_number: The number of the upper ROM to select (0-255).

Returns:
    Nothing.

Raises:
    ValueError: The upper ROM number is not valid.
        """
		if upper_rom_number not in range(0, 256):
			raise ValueError('Invalid value specified for upper ROM number; '
				+ 'value must be between 0 and 255')
		else:
			self.header[0x55] = upper_rom_number

	def get_machine_type(self):
		"""Get the type of Amstrad CPC machine specified in the snapshot.

Parameters:
    None.

Returns:
    int: A number representing the machine type (0-3).
        """
		return(self.header[0x6d])

	def set_machine_type(self, machine_type):
		"""Specify the type of Amstrad CPC machine in the snapshot.

Valid values for version 2 Amstrad CPC snapshots are:
* 0: CPC464
* 1: CPC664
* 2: CPC6128
* 3: Unknown

Parameters:
    machine_type (int): A number representing the machine type (0-3).

Returns:
    Nothing.

Raises:
    ValueError: The machine type number is not valid.
        """
		if machine_type not in range(0,3):
			raise ValueError('Invalid value specified for machine type; '
				+ 'value must be between 0 and 2')
		else:
			self.header[0x6d] = machine_type

	# -----------------------
	# CRTC register functions
	# -----------------------

	def get_crtc_register(self, register):
		"""Get the value of a CRTC register from the snapshot.

Parameters:
    register (int): The number of the CRTC register (0-17).

Returns:
    int: The value of the specified CRTC register (0-255).

Raises:
    ValueError: The number of the CRTC register is not valid.
        """
		if register not in range(0, 18):
			raise ValueError('Invalid value specified for CRTC register; '
				+ 'value must be between 0 and 17')
		else:
			return(self.header[(register + 0x43)])

	def get_crtc_registers(self):
		"""Get the values of all 18 CRTC registers from the snapshot.

Parameters:
    None.

Returns:
    list: A list of the values of all 18 CRTC registers.
        """
		crtc_registers = [0] * 18
		for register in range(0, 18):
			crtc_registers[register] = self.get_crtc_register(register)
		return(crtc_registers)

	def set_crtc_register(self, register, value):
		"""Set the value of a CRTC register.

Parameters:
    register (int): The number of the CRTC register to set (0-17).
    value (int): The value to set the CRTC register to (0-255).

Returns:
    Nothing.

Raises:
    ValueError: Either the number of the CRTC register or the value to set it
        to are not valid.
        """
		if register not in range(0, 18):
			raise ValueError('Invalid value specified for CRTC register; '
				+ 'value must be between 0 and 17')
		elif value not in range(0, 256):
			raise ValueError('Value of CRTC register to set must be in '
				+ 'range (0, 256)')
		else:
			self.header[register + 0x43] = value

	def set_crtc_registers(self, registers):
		"""Set the values of several CRTC registers.

Parameters:
    registers (list): A list of the values of the CRTC registers to set. The
        list can contain between 1-18 items, and the first item in the list is
        CRTC register 0.

Returns:
    Nothing.

Raises:
    TypeError: registers is not a list.
    Snapshot.ListSizeError: The size of the list of CRTC registers to set is
        incorrect.
    ValueError: The value of a CRTC register to set is not valid.
        """
		# Check that the register values are specified as a list
		if type(registers) is not list:
			raise TypeError('CRTC register values must be specified as a list')

		# The list of register values must be between 1 and 18 items long
		if (len(registers) not in range(1,18)):
			raise Snapshot.ListSizeError(1, 18)
		else:
			for register in range(len(registers)):
				value = registers[register]
				if value not in range(0,256):
					raise ValueError(('Invalid value specified for CRTC '
						+ 'register {0};'
						+ 'value must be between 0 and 255').format(register))
				else:
					self.set_crtc_register(register, value)

	# Get the size of the RAM used in this snapshot, in kilobytes
	def get_ram_size(self):
		"""Get the size of the RAM in the snapshot.

Parameters:
    None.

Returns:
    int: The size of the snapshot RAM in kibibytes (i.e. 64 = 64KiB or 65,536
        bytes; 128 = 128KiB or 131,072 bytes).
        """
		return self.header[0x6b]

	def insert_bytes(self, bytes, start_offset):
		end_offset = len(bytes) + start_offset - 1

		if start_offset < 0x10000 and end_offset >= 0x10000:
			raise MemoryError('Bytes to insert do not fit into main 64KB of '
				+ 'snapshot RAM')
		elif start_offset >= 0x10000 and end_offset >= len(self.memory):
			raise MemoryError('Bytes to insert do not fit into snapshot RAM')

		self.memory[start_offset:start_offset+len(bytes)] = bytes

	def insert_file(self, filepath, start_offset):
		"""Read a file and insert it into the snapshot.

Parameters:
    filepath (str): The file to insert.
    start_offset (int): The start address in RAM where the file is to be
        inserted. To insert a file into the additional 64KB of RAM, use
        addresses from 0x10000 to 0x1ffff.

    Returns:
        Nothing.

    Raises:
        MemoryError: The file will not fit into the available RAM, or the
            file is being inserted into the main 64KB block of RAM but it will
            not fit into this block.
        """
		file_size = os.stat(filepath).st_size
		end_offset = file_size + start_offset - 1

		# If the end address of the file in memory exceeds the available RAM,
		# then raise an exception
		if (end_offset) >= len(self.memory):
			raise MemoryError('File {0} cannot fit into snapshot RAM'.
				format(repr(filepath)))

		# If the file is being inserted into the main 64KB of RAM, and the
		# end address exceeds 0xffff (i.e. it extends into additional RAM
		# banks), then raise an exception
		elif ((start_offset < 0x10000) and (end_offset >= 0x10000) and
			len(self.memory) >= 0x10000):
			raise MemoryError(('File {0} does not fit into main 64KB of '
				+ 'snapshot RAM').format(repr(filepath)))

		else:
			file_to_insert = open(filepath, 'rb')
			end_offset = start_offset + file_size - 1
			self.memory[start_offset:end_offset+1] = \
				bytearray(file_to_insert.read(file_size))
			file_to_insert.close()

	def write(self, filepath):
		"""Write the snapshot to a file.

Parameters:
    filepath (str): The path to write the file to.

Returns:
    Nothing.
    """
		file = open(filepath, 'wb')
		file.write(self.header)
		file.write(self.memory)
		file.close()
