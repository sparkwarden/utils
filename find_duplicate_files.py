#-------------------------------------------------------------
# Identify duplicate files for a selected directory.
#-------------------------------------------------------------

import hashlib
import pathlib
import filecmp
import argparse

from sparkwarden_lib import Message_Writer
from sparkwarden_lib import select_from_list
from sparkwarden_lib import build_file_list
from sparkwarden_lib import ProgressBar
from sparkwarden_lib import clsFileNode
from sparkwarden_lib import MY_Timer
from sparkwarden_lib import LF


class Parse_Arg:
	program =  __file__
	description = ''
	curdir = str(pathlib.Path().cwd())
	arg_default_list = []
	node_list = []
	arg_parsed_dict = {}
	
	def __init__(self, name, default_value, is_required=False, help_text=''):
		self.name = name
		self.default_value = default_value
		self.is_required = is_required
		self.help_text = ''
		
		Parse_Arg.node_list_add(self)
	
	@classmethod
	def get_arg_by_name(cls, name:str):
		ret_arg = None
		print()
		print('cls.arg_parsed_dict')
		print(cls.arg_parsed_dict)
		print()
		
		for k,v in cls.arg_parsed_dict.items():
			if k == name:
				ret_arg = v
				break
			
		return ret_arg
			
		
	
	def as_dict(self):
		return self.__dict__
	
	def as_str(self):
		d = self.as_dict()
		_msg = f'\n\n<{__class__.__name__}> '
		for k,v in d.items():
			_msg += f'\n{k}: {v} '
		return _msg
	
	def __repr__(self) -> str:
		return self.as_str()
		
	@classmethod
	def node_list_add(cls, obj):
		if obj not in cls.node_list:
			cls.node_list.append(obj)
			
	@classmethod
	def setup(cls, arg_list=[]):
		cls.arg_default_list = arg_list
		cls.set_arg_parsed_dict()
		
		
	@classmethod
	def set_arg_parsed_dict(cls):
		parser = argparse.ArgumentParser(description=cls.description)
	
		for nd in cls.node_list:
			parser.add_argument(nd.name, required=nd.is_required, \
				default=nd.default_value, help=nd.help_text)
		
		results = parser.parse_args()
		cls.arg_parsed_dict = results.__dict__
		
		
#-------------------------------------------------------------
# 
#-------------------------------------------------------------

def select_dir(start_dir=pathlib.Path().cwd()) -> str:
	
	resdir = start_dir
	
	while True:
		
		p = pathlib.Path(resdir)
		
		path_node_list = []
		path_node_str_list = ['[.]','[..]']
		
		for child in p.iterdir():
			path_node_list.append(child)
			
		for node in path_node_list:
			if node.is_dir():
				_node_name = str(node.name)
				path_node_str_list.append('['+_node_name+']')
		
		titlestr=f'Select directory relative to:{LF}{resdir}'
		dirstr = select_from_list(choice_list=path_node_str_list,\
			title=titlestr,prompt='')
	
		selected_dir = str(dirstr).strip('[]')
		
		if selected_dir == '.':
			pass
		if selected_dir == '..':
			resdir = str(pathlib.Path(resdir).parent)
		else:
			resdir = str(pathlib.Path(resdir).joinpath(selected_dir))
		
		yn = 'n'
		yn = str(input(f'{LF}You selected {resdir}. Done? [Y/N]:')).lower()
		if yn == 'y':
			break
			
	return resdir

#-------------------------------------------------------------
# 
#-------------------------------------------------------------

def get_file_hash(file_path, chunksize):
	hash_md5 = hashlib.md5()
	with open(file_path, "rb") as f:
		for chunk in iter(lambda: f.read(chunksize), b""): 
			hash_md5.update(chunk)
	return hash_md5.hexdigest()
	
#-------------------------------------------------------------
# 
#-------------------------------------------------------------

def find_duplicate_files(selected_files, chunksize=4096):
	file_hash_dict = {}
	duplicate_files = []
	
	progress = ProgressBar(len(selected_files), fmt=ProgressBar.FULL)
	
	for path in selected_files:
		
		progress()
		
		file_path = path
		file_hash = get_file_hash(path,chunksize)

		if file_hash in file_hash_dict:
			duplicate_files.append((file_path, file_hash_dict[file_hash]))
		else:
			file_hash_dict[file_hash] = file_path
				
	progress.close()
	
	return duplicate_files

#-------------------------------------------------------------
# 
#-------------------------------------------------------------

def dupl_main(msgr):
	
	arg_list = [
			Parse_Arg(name='-ChunkSize', default_value=4096, is_required=False, help_text=''),
			Parse_Arg(name='-MinFileSize', default_value=1, is_required=False, help_text=''),
			Parse_Arg(name='-InclDirUserInput', default_value=False, is_required=False, help_text=''),
			Parse_Arg(name='-InclDirList', default_value=[Parse_Arg.curdir], is_required=False, help_text=''),
			Parse_Arg(name='-ExclDirList', default_value=[], is_required=False,help_text='')
		]
	
	Parse_Arg.setup(arg_list)
	
	#pargs = Parse_Arg.get_parsed_args()
	#msgr.write_msg(f'{LF} {pargs}')
	
	chunksize = Parse_Arg.get_arg_by_name('ChunkSize')
	msgr.write_msg(f'{LF}chunksize: {chunksize}')
	min_file_size = Parse_Arg.get_arg_by_name('MinFileSize')
	
	curdir = str(pathlib.Path().cwd())
	
	yn = 'n'
	yn = str(input(f'{LF}Use {curdir} as selected directory? [Y/N]:')).lower()
	if yn == 'y':
		selected_dir = curdir
	else:
		selected_dir = select_dir()
		
	msgr.write_msg(f'{LF}Scanning for duplicate files...{LF}{LF}')
		
	file_path_list = build_file_list(selected_dir)
	
	selected_files = []
	for path in file_path_list:
		fn = clsFileNode(path)
		fn_dict = fn.as_dict()
		fn_include = (fn_dict['filesize'] >= min_file_size)
		if fn_include:
			selected_files.append(path)
	
	
	duplicate_candidates = find_duplicate_files(selected_files, chunksize)
	duplicate_pair_list = []
	if duplicate_candidates:
		for file1, file2 in duplicate_candidates:
			if filecmp.cmp(file1, file2, shallow=False):
				duplicate_pair_list.append((file1, file2))
		
	msgr.write_msg(f'{LF}Scanning complete.')
	
	return duplicate_pair_list

		
#-------------------------------------------------------------
# 
#-------------------------------------------------------------


def main():
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	program_path = __file__
	fileprefix = str(pathlib.Path(program_path).stem)
	
	Message_Writer.setup()
	
	msgr = Message_Writer(name='root',prefix=fileprefix)
	
	msgr.write_msg(f'{LF}program {program_path} started. {LF}')
	
	
	
	
	timer = MY_Timer()
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	duplicate_pair_list = dupl_main(msgr)
	
	duplicate_count = len(duplicate_pair_list)
	if duplicate_count > 0:
		msgr.write_msg(f'{LF}{duplicate_count} Duplicate(s) Found')
		for file1, file2 in duplicate_pair_list:
			msgr.write_msg(f'{LF} {"-" * 60}')
			msgr.write_msg(f'{LF}Duplicate')
			msgr.write_msg(f'{LF} {file1}')
			msgr.write_msg(f'{LF} {file2}')
			msgr.write_msg(f'{LF} {"-" * 60}')
	else:
		msgr.write_msg(LF)
		msgr.write_msg('No duplicates found')
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	timer.calc_elapsed()
	
	msgr.write_msg(f'{LF} {timer.as_str()}')
	
	msgr.write_msg(LF)
	msgr.write_msg(f'{LF}program {program_path} completed. {LF}')
	
	msgr.close_writer()
	
	Message_Writer.shutdown()
	

if __name__ == "__main__":
	main()
	
	
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
