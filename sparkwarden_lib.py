#---------------------------------------------------------------------
# 
#---------------------------------------------------------------------

__all__ = ['build_file_list','list_to_xlsx','select_from_list','LF','clsFileNode','Message_Writer','get_text_from_file','ProgressBar']

#---------------------------------------------------------------------
# 
#---------------------------------------------------------------------

__author__ = 'Gary D. Smith <https://github.com/sparkwarden>'
__version__ = '1.0'
__date__ = '2024/04/28'

"""
Description: Utility library containing message writer, file list builder,
and list-to-excel functions.

Tested with Python 3.10
Operating System: iPadOS 17.4
iOS Python apps: Pythonista, a-Shell

Required modules:
 openpyxl - to generate excel report file.
 
"""

#---------------------------------------------------------------------
#
#---------------------------------------------------------------------

import pathlib
import datetime
import io
import sys
import openpyxl

from operator import attrgetter
import mimetypes
import time
import re
from datetime import timedelta


LF = '\n'

#-------------------------------------------------------------
# 
#-------------------------------------------------------------

class MY_Timer:
	def __init__(self, starting_time=time.time(), timer_label='Elapsed Time: '):
		self.starting_time = starting_time
		self.ending_time = starting_time
		self.elapsed = 0
		self.timer_label = timer_label
	
	def calc_elapsed(self):
		self.ending_time = time.time()
		self.elapsed = timedelta(seconds=self.ending_time - self.starting_time)
		
	def as_str(self) -> str:
		_msg = f'{LF}<{self.__class__.__name__}> {self.timer_label} elapsed: {self.elapsed}'
		return _msg
		
	def __repr__(self) -> str:
		return self.as_str()
		
#-------------------------------------------------------------
# 
#-------------------------------------------------------------

class ProgressBar(object):
	#
	# https://stackoverflow.com/questions/3160699/python-progress-bar
	#
	# Example:
	#
	#	progress = ProgressBar(num_steps, fmt=ProgressBar.FULL)
	#
	#	for i in range(num_steps):
	#
	#		progress()
	#		do_stuff()
	#
	# progress.close()
	#
		
	DEFAULT = 'Progress: %(bar)s %(percent)3d%%'
	FULL = '%(bar)s %(current)d/%(total)d (%(percent)3d%%)'
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	def __init__(self, total, width=40, fmt=DEFAULT, symbol=chr(9632),\
		output=sys.stdout,interval_length=1,label=''):
			self.total = total
			self.width = width
			self.symbol = symbol
			self.output = output
			self.fmt = re.sub(r'(?P<name>%\(.+?\))d',\
				r'\g<name>%dd' % len(str(total)), fmt)
			self.current = 0
			
			self.interval_length = interval_length
			self.interval_count = 0
			
			self.is_done=False
			
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------

	def _update(self):
		
		if self.current >= self.total:
			percent = 1.0
			self.current = self.total
		else:
			percent = self.current / float(self.total)
		size = int(self.width * percent)
		remaining = self.total - self.current
	
		bar = '[' + self.symbol * size + ' ' * (self.width - size) + ']'
		args = {
			'total': self.total,
			'bar': bar,
			'current': self.current,
			'percent': percent * 100,
			'remaining': remaining
		}
		
		print('\r' + self.fmt % args, file=self.output, end='')
		
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	def __call__(self):
		
		if not self.is_done:
			if self.interval_count >= self.interval_length:
				self.interval_count = 0
			else:
				self.current += 1
				self.interval_count += 1
			self._update()
			
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------

	def close(self):
		if not self.is_done:
			self.current = self.total
			self.interval_length=1
			self()
			print('', file=self.output)
			self.is_done = True
		

#-------------------------------------------------------------
# 
#-------------------------------------------------------------

class clsFileNode:
	"""
	Models file attributes and behavior.
	"""

	dir_set = set()
	filetype_set = set()
	
	filenode_list = []
	sorted_filenode_list = []
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	def __new__(cls, path):
		return super().__new__(cls)
		
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	def __init__(self,path):
		
		_cls = clsFileNode
		
		self.path = path
		p = pathlib.Path(path)
		self.parents = list(p.parents)
		_stat = p.stat()
		self.drive = str(p.drive) 	# file drive, used mainly on windows
		self.ext = str(p.suffix)		# file extension
		self.parentdir = str(p.parent) # parent directory
		self.filename = str(p.name)		# filename, stem + suffix
		
		_dt_fmt = '{:%Y-%m-%d %H:%M:%S}'
		_dt_fmt = '%a %b %d %H:%M:%S %Y'
		
		_created = time.ctime(_stat.st_ctime)
		_modified = time.ctime(_stat.st_mtime)
		_accessed = time.ctime(_stat.st_atime)
	
		self.dt_created = datetime.datetime.strptime(_created, _dt_fmt)
		self.dt_modified = datetime.datetime.strptime(_modified, _dt_fmt)
		self.dt_accessed = datetime.datetime.strptime(_accessed, _dt_fmt)
		
		self.dt_str_created = _dt_fmt.format(_created)
		self.dt_str_modified =_dt_fmt.format(_modified)
		self.dt_str_accessed = _dt_fmt.format(_accessed)
		
		self.filesize = _stat.st_size
		
		self.sortkey = self.path
		
		try:
			_file_type = mimetypes.types_map[self.ext]
		except (KeyError, Exception):
			_file_type = ''
		finally:
			self.filetype = _file_type
			
		#self.filetype = _cls.get_filetype(self.path)

		self.is_symlink = p.is_symlink()
		self.is_hardlink = _stat.st_nlink > 1
		
		self.is_in_trash = (self.path.find('.Trash') > 0)
		#self.is_dupe_candidate = False
		#self.is_dupe = False
		
		_cls.dir_set.add(self.parentdir)
		_cls.filetype_set.add(self.filetype)
			
		self.text_content = ''
		
		if self not in clsFileNode.filenode_list:
			_cls.filenode_list.append(self)
			_cls.sorted_filenode_list.append(self)
			
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
			
	def set_text_content(self):
		p = pathlib.Path(self.path)
		if self.filetype.startswith('text'):
			self.text_content = p.read_text(encoding='utf-8')
		else:
			self.text_content = ''
			
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
			
	def as_dict(self) -> dict:
		d = {}
		d['path'] = self.path
		d['filesize'] = self.filesize
		d['filetype'] = self.filetype
		d['is_symlink'] = self.is_symlink
		d['is_hardlink'] = self.is_hardlink
		d['is_in_trash'] = self.is_in_trash
		return d
		
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	@classmethod
	def sort_nodes(cls,sort_reversed=False):
		_filenodes = cls.filenode_list
		cls.sorted_filenode_list = sorted(_filenodes,key=attrgetter('sortkey'),reverse=sort_reversed)
		
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	@classmethod
	def get_filenode_from_path(cls,path):
		retnode = None
		
		_ret_node_list = [fn for fn in cls.filenode_list if fn.path == path]
		if len(_ret_node_list) == 1:
			retnode = _ret_node_list[0]
			
		return retnode
			
#-------------------------------------------------------------
# 
#-------------------------------------------------------------


class Message_Writer:
	"""
	Output Messages to File.
	"""
	
	node_list = []
	
	PRN_SCREEN_AND_FILE = 1
	PRN_SCREEN_ONLY = 2
	PRN_FILE_ONLY = 3
	PRN_FLUSH_LOG_THRESHOLD = 100
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	def __new__(cls, name, prefix, prn_flag=1):
		return super().__new__(cls)
		
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	def __init__(self, name, prefix, prn_flag=1):
		
		_cls = Message_Writer
		
		self.is_active = False
		self.name = name
		self.prn_flag = prn_flag
		self.msg_cnt = 0
			
		self.msgfilepath = _cls.get_output_path_with_dt(prefix)
			
		self.msgbuf = io.StringIO()
			
		if self not in _cls.node_list:
			_cls.node_list.append(self)
			msg = f'\nmessage writer [{self.name}] starting. . .\n'
			with open(self.msgfilepath,'w',encoding='utf-8') as f:
				f.write('')
				self.write_msg(msg)
		else:
			raise Exception ('message writer already established')
			
		self.is_active = True
		
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	@staticmethod
	def get_output_path_with_dt(prefix='msgr', ext='.log',\
		_timefmt='%Y%m%d_%H%m%S%f'):
		_path = ''.join([prefix, '_', datetime.datetime.now().strftime(_timefmt), ext])
		return _path
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	@classmethod
	def get_writer_by_name(cls, name):
		"""
		return writer node by name.
		"""
		
		_node_list = [nd for nd in cls.node_list if nd.name == name]
		retnode = None
		if len(_node_list) > 0:
			retnode = _node_list[0]
		return retnode
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	def write_msg(self, *args):
		"""
		write msg to buffer.
		"""
		_arg_str = ''
		for arg in args:
			_arg_str += str(arg)
		
		_cls = Message_Writer
		
		if self.msg_cnt >= _cls.PRN_FLUSH_LOG_THRESHOLD:
			self.flushbuf()
		
		if self.prn_flag == _cls.PRN_SCREEN_AND_FILE:
			self.msgbuf.write(_arg_str)
			sys.stdout.write(_arg_str)
		elif self.prn_flag == _cls.PRN_SCREEN_ONLY:
			sys.stdout.write(_arg_str)
		else:
			self.msgbuf.write(_arg_str)
			
		self.msg_cnt+=1
		
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
			
	def flushbuf(self):
		"""
		write the msgbuf to file.
		"""
		with open(self.msgfilepath,'a',encoding='utf-8') as f:
			f.write(self.msgbuf.getvalue())
		self.msg_cnt = 0
		
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------

	def close_writer(self):
		self.write_msg(f'\nmessage writer [{self.name}] closing. . .')
		self.flushbuf()
		self.msgbuf.close()
		self.is_active = False
	
	#-------------------------------------------------------------
	# 
	#------------------------------------------------------------
		
	@classmethod
	def setup(cls):
		cls.node_list.clear()
		
	#-------------------------------------------------------------
	# 
	#------------------------------------------------------------
		
	@classmethod
	def shutdown(cls):
		for lg in cls.node_list:
			if lg.is_active:
				lg.close_writer()
				
	
#-------------------------------------------------------------
# 
#-------------------------------------------------------------

def get_text_from_file(path):
	text_rows = []
	with open(path, 'r', encoding='utf-8') as tf:
		text_rows = tf.readlines()
	return text_rows

#-------------------------------------------------------------
# 
#-------------------------------------------------------------

def select_from_list(choice_list,title='',prompt=f'{LF}:'):
	"""
	A text-based dialog to display a numbered list of choices.
	User inputs number to determine choice.
	
	parameters:
		choice_list - list of strings.
		title - string, dialog title.
		prompt - string, input prompt.
		
	returns:
		the_choice - string chosen from choice_list.
	"""
		
	frame_vert = chr(9475)
	frame_horz = chr(9473)
	topleft=chr(9487)
	topright=chr(9491)
	bottomleft=chr(9495)
	bottomright=chr(9499)
	fill_char=' '
	frame_width = 50

	_topline = topleft+''.rjust(frame_width-2,frame_horz)+topright
	_bottomline = bottomleft+''.rjust(frame_width-2,frame_horz)+bottomright
	
	print(f'{title}')
	print(f'{_topline}')
	for choice_num, choice in enumerate(choice_list,start=1):
		_choice_label = f' {choice_num}:{choice}'
		_fill_size = frame_width-2-len(_choice_label)
		_filler = ''.rjust(_fill_size,fill_char)
		_thisline = f'{frame_vert}{_choice_label}{_filler}{frame_vert}'
		print(f'{_thisline}')
	print(f'{_bottomline}')
		
	default_choice_num = 1
	the_choice = choice_list[default_choice_num-1]
	while True:
		my_choice=input(prompt)
		_my_choice = str(my_choice).lower()
		_my_choice_int = 0
		if _my_choice.isnumeric():
			_my_choice_int = int(_my_choice)
			if (_my_choice_int > 0) and (_my_choice_int <= len(choice_list)):
				the_choice = choice_list[_my_choice_int-1]
				break
			else:
				print(f'{LF}Invalid Choice Num:{_my_choice_int}')
				the_choice = choice_list[default_choice_num-1]
		elif (_my_choice is None) or (_my_choice =='') or (_my_choice == 'x'):
			the_choice = 'x'
			break
		else:
			print(f'{LF}Invalid Choice:{my_choice}')
			
	return the_choice
			
#-------------------------------------------------------------
# 
#-------------------------------------------------------------

def list_to_xlsx(xls_list,xls_path) -> None:
	"""
	Write list to excel .xlsx file
	"""
	
	wb = openpyxl.Workbook()
	ws = wb.active
	
	for row in xls_list:
		ws.append(row)

	wb.save(xls_path)
		
#-------------------------------------------------------------
# 
#-------------------------------------------------------------
'''
def build_dir_list(startdir:str=None, ptrnstr='*.*') -> list:
	"""
	Return a list of files recursively, starting with
	[startdir] directory, matching [ptrnstr] search pattern.
	"""
	_dir_list = []
	_dir_disp_list = []
	
	if startdir is None:
		_startdir = str(pathlib.Path().cwd())
	else:
		_startdir = startdir
	
	p = pathlib.Path(_startdir)
	
	glob_list = p.rglob(ptrnstr)
	
	for path in glob_list:
		_path = str(path)
		p = pathlib.Path(_path)
		
		if p.is_dir(): 
			d = {}
			d['disp_dir'] = str(p.name)
			d['dir'] = _path
			_dir_disp_list.append(d)
			
	if len(_dir_disp_list) == 0:
		d = {}
		p = pathlib.Path(_startdir)
		d['disp_dir'] = '.'
		d['dir'] = _startdir
		_dir_disp_list.append(d)
		
		d = {}
		p = pathlib.Path(_startdir).parent
		d['disp_dir'] = '..'
		d['dir'] = str(p)
		_dir_disp_list.append(d)
		
	
	
	return _dir_list
'''

def build_file_list(startdir:str=None, ptrnstr='*.*') -> list:
	"""
	Return a list of files recursively, starting with
	[startdir] directory, matching [ptrnstr] search pattern.
	"""
	_file_list = []
	
	if startdir is None:
		_startdir = str(pathlib.Path().cwd())
	else:
		_startdir = startdir
	
	p = pathlib.Path(_startdir)
	
	glob_list = p.rglob(ptrnstr)
	
	for path in glob_list:
		_path = str(path)
		p = pathlib.Path(_path)
		
		if p.is_file(): 
			_file_list.append(_path)
	
	return _file_list

#-------------------------------------------------------------
# 
#-------------------------------------------------------------


		
def main(msgr):
	
	#-------------------------------------------------------------
	# 
	#------------------------------------------------------------
	
	curdir = str(pathlib.Path().cwd())
	
	msgr.write_msg(f'{LF} curdir: {curdir} {LF}')
	
	file_list = build_file_list(curdir, '*.py')
	
	for filepath in file_list:
		fn = clsFileNode(filepath)
		fn.sortkey = str(fn.filename).lower()
	
	msgr.write_msg(f'{LF} {len(file_list)} [.py] files in {curdir} dir tree. {LF}')
	
	clsFileNode.sort_nodes()
	
	for fn in clsFileNode.sorted_filenode_list:
		_matches_found = False
		#_valid_file_type = False
		_match_strs = ['__new__']
		_source_str = ''
		_parentdir = str(fn.parentdir).lower()
		_is_save_file = (('archive' in _parentdir) or ('save' in _parentdir))
		if _is_save_file:
			continue
		
		if str(fn.filetype).startswith('text'):
			fn.set_text_content()
			_source_str = str(fn.text_content).lower()
			for s in _match_strs:
				if s in _source_str:
					_matches_found = True
				
		if _matches_found:
			msgr.write_msg(f'{LF} {LF} path: {fn.path} match_found: {_matches_found}')
	
	#-------------------------------------------------------------
	# 
	#------------------------------------------------------------
	
	
#-------------------------------------------------------------
# 
#------------------------------------------------------------

if __name__ == "__main__":
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	timer = MY_Timer()
	
	fileprefix = str(pathlib.Path(__file__).stem)
	
	Message_Writer.setup()
	
	msgr = Message_Writer(name='root',prefix=fileprefix)
	
	msgr.write_msg(f'{LF}program {__file__} started. {LF}')
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	main(msgr)
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	timer.calc_elapsed()
	
	msgr.write_msg(f'{LF} {timer.as_str()}')
	
	msgr.write_msg(LF)
	msgr.write_msg(f'{LF}program {__file__} completed. {LF}')
	
	msgr.close_writer()
	
	Message_Writer.shutdown()
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
