from platform       import system as platform_system

class Terminal:
	@staticmethod
	def GetTerminalSize():
		"""Returns the terminal size as tuple (width, height) for Windows, Mac OS (Darwin), Linux, cygwin (Windows), MinGW32/64 (Windows)."""
		platform = platform_system()
		if (platform == "Windows"):
			size = Terminal.__GetTerminalSizeOnWindows()
		elif ((platform in ["Linux", "Darwin"]) or
		      platform.startswith("CYGWIN") or
		      platform.startswith("MINGW32") or
		      platform.startswith("MINGW64")):
			size = Terminal.__GetTerminalSizeOnLinux()
		if (size is None):
			size = (80, 25) # default size
		return size

	@staticmethod
	def __GetTerminalSizeOnWindows():
		try:
			from ctypes import windll, create_string_buffer
			from struct import unpack as struct_unpack

			hStdError =     windll.kernel32.GetStdHandle(-12)                  # stderr handle = -12
			stringBuffer =  create_string_buffer(22)
			result =        windll.kernel32.GetConsoleScreenBufferInfo(hStdError, stringBuffer)
			if result:
				(bufx, bufy, curx, cury, wattr, left, top, right, bottom, maxx, maxy) = struct_unpack("hhhhHhhhhhh", stringBuffer.raw)
				width =   right - left + 1
				height =  bottom - top + 1
				return (width, height)
		except:
			pass

		return Terminal.__GetTerminalSizeWithTPut()

	@staticmethod
	def __GetTerminalSizeOnLinux():
		import os

		def ioctl_GWINSZ(fd):
			"""GetWindowSize of file descriptor."""
			try:
				from fcntl    import ioctl      as fcntl_ioctl
				from struct   import unpack     as struct_unpack
				from termios  import TIOCGWINSZ

				return struct_unpack('hh', fcntl_ioctl(fd, TIOCGWINSZ, '1234'))
			except:
				pass

		#               STDIN              STDOUT             STDERR
		cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
		if not cr:
			try:

				fd = os.open(os.ctermid(), os.O_RDONLY)
				cr = ioctl_GWINSZ(fd)
				os.close(fd)
			except:
				pass
		if not cr:
			try:
				cr = (os.environ['LINES'], os.environ['COLUMNS'])
			except:
				return None
		return (int(cr[1]), int(cr[0]))

	@staticmethod
	def __GetTerminalSizeWithTPut():
		from shlex      import split as shlex_split
		from subprocess import check_output

		try:
			width =   int(check_output(shlex_split('tput cols')))
			height =  int(check_output(shlex_split('tput lines')))
			return (width, height)
		except:
			pass
