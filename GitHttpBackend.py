# -*- coding: utf8 -*-
#!/usr/bin/env python
'''
Module provides WSGI-based methods for handling HTTP Get and Post requests that
are specific only to git-http-backend's Smart HTTP protocol.

See __version__ statement below for indication of what version of Git's
Smart HTTP server this backend is (designed to be) compatible with.

Copyright (c) 2010  Daniel Dotsenko <dotsa@hotmail.com>

This file is part of git_http_backend.py Project.

git_http_backend.py Project is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 2.1 of the License, or
(at your option) any later version.

git_http_backend.py Project is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with git_http_backend.py Project.  If not, see <http://www.gnu.org/licenses/>.
'''

__version__=(1,7,0,4) # the number has no significance for this code's functionality.
# The number means "I was looking at sources of that version of Git while coding"

class RPCHandler():
	'''
	Implementation of a WSGI handler (app) specifically capable of responding
	to git-http-backend (Git Smart HTTP) RPC calls sent over HTTP POST.

	This is a layer that responds to HTTP POSTs to URIs like:
		/repo_folder_name/git-upload-pack?service=upload-pack (or same for receive-pack)

	This is a second step in the RPC dialog. Another handler for HTTP GETs to
	/repo_folder_name/info/refs (as implemented in a separate WSGI handler below)
	must reply in a specific way in order for the Git client to decide to talk here.
	'''
	def __init__(self, repo_fs_path):
		self.path_prefix = repo_fs_path

	def __call__(self, environ, start_response):
		"""
		WSGI Response producer for HTTP POST Git Smart HTTP requests.

		Reads commands and data from HTTP POST's body.

		returns an iterator obj with contents of git command's response to stdout
		"""
		# TODO: Handle 100-Continue here

		start_response("200 Ok", [('Content-type', 'text/plain')])
		return ['']

class InfoRefsHandler():
	'''
	Implementation of a WSGI handler (app) specifically capable of responding
	to git-http-backend (Git Smart HTTP) /info/refs call over HTTP GET.

	This is the fist step in the RPC dialog. We have to reply with right content
	to show to Git client that we are an "intelligent" server.

	The "right" content is special header and custom top 2 rows of data in the response.
	'''
	def __init__(self, repo_fs_path):
		self.path_prefix = repo_fs_path

	def __call__(self, environ, start_response):
		"""WSGI Response producer for HTTP GET Git Smart HTTP /info/refs request."""
		# TODO: Handle 100-Continue here

		command = r'git receive-pack --stateless-rpc --advertise-refs "/cygdrive/c/tmp/testgitrepo.git"'
		commandProcess = self.get_command_subprocess(command)
		out, err = commandProcess.communicate()

		method = 'upload-pack'
		if not err:
			print 'serving good.'
			start_response("200 Ok", [('Content-type', 'application/x-git-%s-advertisement' % method)])
			advert = '# service=git-%s\n' % upload-pack
			return [
				hex(len(advert)+4)[2:].rjust(4,'0') + advert ,
				'0000\n',
				out
				]

		start_response("200 Ok", [('Content-type', 'text/plain')])
		return ['']

def process_GET(self, environ, start_response):
	length= int(environ.get('CONTENT_LENGTH', '0') or '0')
#		print environ['wsgi.input'].read(length)
#		body = StringIO()
#		body.write( environ['wsgi.input'].read(length) )
#		body.write('\nLast line\n')
#		# environ['wsgi_input'] = body
#		body.seek(0)
	command = r'git receive-pack --stateless-rpc --advertise-refs "/cygdrive/c/tmp/testgitrepo.git"'
	commandProcess = self.get_command_subprocess(command)
	out, err = commandProcess.communicate()

	method = 'upload-pack'
	if not err:
		print 'serving good.'
		start_response("200 Ok", [('Content-type', 'application/x-git-%s-advertisement' % method)])
		advert = '# service=git-%s\n' % upload-pack
		return [
			hex(len(advert)+4)[2:].rjust(4,'0') + advert ,
			'0000\n',
			out
			]
	else:
		start_response("200 Ok", [('Content-type', 'text/plain')])
		return ['']

	def process_unsupported(self, *args, **kw):
		start_response("200 Ok", [('Content-type', 'text/plain')])
		return ["don't understand"]

	def get_command_subprocess(commandline):
		"""
		 commandline - may be a string, or a list.
		 Returns:
		 Popen object with .communicate(), .stdin, .stdout, .stderr - file-like
		"""
		return subprocess.Popen(commandline, bufsize = 1,
			stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		# additonal arguments to consider # cwd = workingpath, universal_newlines = True

	def test(self):
		command = r'git receive-pack --stateless-rpc --advertise-refs "/cygdrive/c/tmp/testgitrepo.git"'
		commandProcess = self.get_command_subprocess(command)
		print 'Output:\n%s\n\nErrors:\n%s' % (commandProcess.communicate())

	def __init__(self):
		self.handlerfn = {
			'POST': self.process_POST,
			'GET': self.process_GET,
		}
		self.SERVICES = [
				["POST", 'service_rpc',      "(.*?)/git-upload-pack$",  'upload-pack'],
				["POST", 'service_rpc',      "(.*?)/git-receive-pack$", 'receive-pack']
			]

	def __call__(self, environ, start_response):
		method = environ.get('REQUEST_METHOD','GET')
		return self.handlerfn.get(method, self.process_unsupported)(environ, start_response)

def assemble_WSGI_git_app(path_prefix = '.', repo_uri_marker = ''):
	'''
	Assembles basic WSGI-compatible application providing functionality of git-http-backend.

	path_prefix (Defaults to '.' = "current" directory)
		The path to the folder that will be the root of served files. Accepts relative paths.

	repo_uri_marker (Defaults to '')
		Acts as a "virtual folder" separator between decorative URI portion and
		the actual (relative to path_prefix) path that will be appended to
		path_prefix and used for pulling an actual file.

		the URI does not have to start with contents of repo_uri_marker. It can
		be preceeded by any number of "virtual" folders. For --repo_uri_marker 'my'
		all of these will take you to the same repo:
			http://localhost/my/HEAD
			http://localhost/admysf/mylar/zxmy/my/HEAD
		This WSGI hanlder will cut and rebase the URI when it's time to read from file system.

		Default of '' means that no cutting marker is used, and whole URI after FQDN is
		used to find file relative to path_prefix.

	returns WSGI application instance.
	'''

	# local modules
	from StaticWSGIServer import StaticWSGIServer
	from WSGIHandlerSelector import WSGIHandlerSelector
	from WSGICannedHTTPHandlers import CannedHTTPHandlers
	# from GitHttpBackend import RPCHandler as GitRPCHandler, InfoRefsHandler as GitInfoRefsHandler


	canned_handlers = CannedHTTPHandlers()
	selector = WSGIHandlerSelector(canned_handlers = canned_handlers)
	generic_handler = StaticContentServer(path_prefix, canned_handlers = canned_handlers)
#	git_inforefs_handler = GitInfoRefsHandler(path_prefix)
#	git_rpc_handler = GitRPCHandler(path_prefix)

	## TESTING SETTINGS:
	# from wsgiref import simple_server
	# app = simple_server.demo_app
	# selector.add('^.*$',app)

	if repo_uri_marker:
		marker_regex = '^(?P<decorative_path>.*?)(?:/'+ repo_uri_marker.decode('utf8') + '/)'
	else:
		marker_regex = ''
#	selector.add(marker_regex + '(?P<working_path>.*)/info/refs$', GET = git_inforefs_handler, HEAD = git_inforefs_handler)
#	selector.add(marker_regex + '(?P<working_path>.*)/git-(?P<git_command>.+)$', POST = git_rpc_handler) # regex is "greedy" it will skip all cases of /git- until it finds last one.
	selector.add(marker_regex + '(?P<working_path>.*)$', GET = generic_handler, HEAD = generic_handler)
	# selector.add('^.*$', GET = generic_handler) # if none of the above yield anything, serve everything.

	return selector
