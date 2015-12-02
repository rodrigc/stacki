# @SI_Copyright@
#                             www.stacki.com
#                                  v2.0
# 
#      Copyright (c) 2006 - 2015 StackIQ Inc. All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#  
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#  
# 2. Redistributions in binary form must reproduce the above copyright
# notice unmodified and in its entirety, this list of conditions and the
# following disclaimer in the documentation and/or other materials provided 
# with the distribution.
#  
# 3. All advertising and press materials, printed or electronic, mentioning
# features or use of this software must display the following acknowledgement: 
# 
# 	 "This product includes software developed by StackIQ" 
#  
# 4. Except as permitted for the purposes of acknowledgment in paragraph 3,
# neither the name or logo of this software nor the names of its
# authors may be used to endorse or promote products derived from this
# software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY STACKIQ AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL STACKIQ OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# @SI_Copyright@
#
# @Copyright@
#  				Rocks(r)
#  		         www.rocksclusters.org
#  		         version 5.4 (Maverick)
#  
# Copyright (c) 2000 - 2010 The Regents of the University of California.
# All rights reserved.	
#  
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#  
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#  
# 2. Redistributions in binary form must reproduce the above copyright
# notice unmodified and in its entirety, this list of conditions and the
# following disclaimer in the documentation and/or other materials provided 
# with the distribution.
#  
# 3. All advertising and press materials, printed or electronic, mentioning
# features or use of this software must display the following acknowledgement: 
#  
# 	"This product includes software developed by the Rocks(r)
# 	Cluster Group at the San Diego Supercomputer Center at the
# 	University of California, San Diego and its contributors."
# 
# 4. Except as permitted for the purposes of acknowledgment in paragraph 3,
# neither the name or logo of this software nor the names of its
# authors may be used to endorse or promote products derived from this
# software without specific prior written permission.  The name of the
# software includes the following terms, and any derivatives thereof:
# "Rocks", "Rocks Clusters", and "Avalanche Installer".  For licensing of 
# the associated name, interested parties should contact Technology 
# Transfer & Intellectual Property Services, University of California, 
# San Diego, 9500 Gilman Drive, Mail Code 0910, La Jolla, CA 92093-0910, 
# Ph: (858) 534-5815, FAX: (858) 534-7345, E-MAIL:invent@ucsd.edu
#  
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# @Copyright@

import os
import time
import socket
import string
import re
import fnmatch
import syslog
import pwd
import types
import sys
import json
import marshal
import hashlib
import subprocess
import stack
from stack.cond import EvalCondExpr
from stack.attr import *
import stack.graph
import stack.ip
from stack.exception import *
from stack.bool import *
import xml
from xml.sax import saxutils
from xml.sax import handler
from xml.sax import make_parser
from xml.sax._exceptions import SAXParseException


_logPrefix = ''
def Log(message, level=syslog.LOG_INFO):
	"""
	Send a message to syslog
	"""
	syslog.syslog(level, '%s%s' % (_logPrefix, message))

def Debug(message, level=syslog.LOG_DEBUG):
	"""If the environment variable STACKDEBUG is set,
	send a message to syslog and stderr."""
	if 'STACKDEBUG' in os.environ and \
		str2bool(os.environ['STACKDEBUG']):
		m = ''
		p = ''
		for c in message.strip():
			if c in string.whitespace and p in string.whitespace:
				pass
			else:
				if c == '\n':
					m += ' '
				else:
					m += c
			p = c
		Log(message, level)
		sys.__stderr__.write('%s\n' % m)
		


class OSArgumentProcessor:
	"""An Interface class to add the ability to process os arguments."""

	def getOSNames(self, args=None):
		"""Returns a list of OS names.  For each arg in the ARGS list
		normalize the name to one of either 'linux' or 'sunos' as
		they are the only supported OSes.  If the ARGS list is empty
		return a list of all supported OS names.
		"""

		list = []
		for arg in args:
			s = arg.lower()
			if s in [ 'centos', 'redhat' ]:
				list.append('redhat')
			elif s in [ 'solaris', 'sunos' ]:
				list.append('sunos')
			elif s in [ 'ubuntu' ]:
				list.append('ubuntu')
			elif s in [ 'vmware' ]:
				list.append('vmware')
			elif s in [ 'xenserver' ]:
				list.append('xenserver')
			else:
				raise CommandError(self, 'unknown os "%s"' % arg)
		if not list:
			list.append('redhat')
			list.append('sunos')
			list.append('ubuntu')
			list.append('vmware')
			list.append('xenserver')

		return list
	

class MembershipArgumentProcessor:
	"""An Interface class to add the ability to process membership
	arguments."""
	
	def getMembershipNames(self, args=None):
		"""Returns a list of membership names from the database.
		For each arg in the ARGS list find all the membership
		names that match the arg (assume SQL regexp).  If an
		arg does not match anything in the database we raise an
		exception.If the ARGS list is empty return all membership names.
		"""
		list = []
		if not args:
			args = [ '%' ] # find all memberships
		for arg in args:
			rows = self.db.execute(
				"""select membership from appliances where
				name like '%s'""" % arg)
			if rows == 0 and arg == '%': # empty table is OK
				continue
			if rows < 1:
				raise CommandError(self, 'unknown membership "%s"' % arg)
			for name, in self.db.fetchall():
				list.append(name)
		return list

		
	
class ApplianceArgumentProcessor:
	"""An Interface class to add the ability to process appliance
	arguments."""
		
	def getApplianceNames(self, args=None):
		"""Returns a list of appliance names from the database.
		For each arg in the ARGS list find all the appliance
		names that match the arg (assume SQL regexp).  If an
		arg does not match anything in the database we raise
		an exception. If the ARGS list is empty return all appliance names.
		"""	
		list = []
		if not args:
			args = [ '%' ] # find all appliances
		for arg in args:
			rows = self.db.execute("""select name from appliances 
				where name like '%s'""" % arg)
			if rows == 0 and arg == '%': # empty table is OK
				continue
			if rows < 1:
				raise CommandError(self, 'unknown appliance "%s"' % arg)
			for name, in self.db.fetchall():
				list.append(name)
		return list


class BoxArgumentProcessor:
	"""An Interface class to add the ability to process box arguments."""
		
	def getBoxNames(self, args=None):
		"""Returns a list of box names from the database.
		For each arg in the ARGS list find all the box
		names that match the arg (assume SQL regexp).  If an
		arg does not match anything in the database we raise an
		exception.  If the ARGS list is empty return all box names.
		"""
		list = []
		if not args:
			args = [ '%' ] # find all boxes

		for arg in args:
			rows = self.db.execute("""select name from
				boxes where name like '%s'""" % arg)
			if rows == 0 and arg == '%': # empty table is OK
				continue
			if rows < 1:
				if arg == '%':
					# special processing for when the table
					# is empty
					continue
				else:
					raise CommandError(self,
						'unknown box "%s"' % arg)

			for name, in self.db.fetchall():
				list.append(name)

		return list


	def getBoxPallets(self, box = 'default'):
		"""Returns a list of pallets for a box"""

		#
		# make sure 'box' exists
		#
		self.getBoxNames([ box ])	

		pallets = []

		rows = self.db.execute("""select r.name, r.version, r.rel,
			r.arch from
			rolls r, boxes b, stacks s where b.name = '%s' and
			b.id = s.box and s.roll = r.id""" % box)

		for name, version, rel, arch in self.db.fetchall():
			pallets.append((name, version, rel, arch))

		return pallets
		

class NetworkArgumentProcessor:
	"""An Interface class to add the ability to process network (subnet)
	argument."""
	
	def getNetworkNames(self, args=None):
		"""Returns a list of network (subnet) names from the database.
		For each arg in the ARGS list find all the network
		names that match the arg (assume SQL regexp).  If an
		arg does not match anything in the database we raise
		an exception.  If the ARGS list is empty return all network names.
		"""
		list = []
		if not args:
			args = [ '%' ] # find all networks
		for arg in args:
			rows = self.db.execute("""select name from subnets
				where name like '%s'""" % arg)
			if rows == 0 and arg == '%': # empty table is OK
				continue
			if rows < 1:
				raise CommandError(self, 'unknown network "%s"' % arg)
			for name, in self.db.fetchall():
				list.append(name)
		return list

	def getNetworkName(self, netid):
		"""Returns a network (subnet) name from the database that
		is associated with the id 'netid'.
		"""
		if not netid:
			return ''

		rows = self.db.execute("""select name from subnets where
			id = %s""" % netid)

		if rows > 0:
			netname, = self.db.fetchone()
		else:
			netname = ''

		return netname
	
class CartArgumentProcessor:
        """An Interface class to add the ability to process cart arguments."""

        def getCartNames(self, args, params):
	
		list = []
		if not args:
			args = [ '%' ] # find all cart names
		for arg in args:
			rows = self.db.execute("""
                        	select name from carts
                                where name like binary '%s'
				""" % arg)
			if rows == 0 and arg == '%': # empty table is OK
				continue
			if rows < 1:
				raise CommandError(self, 'unknown cart "%s"' % arg)
			for (name, ) in self.db.fetchall():
				list.append(name)
		return list

        
class RollArgumentProcessor:
	"""An Interface class to add the ability to process pallet arguments."""
	
	def getRollNames(self, args, params):
		"""Returns a list of (name, version, release) tuples from the pallet
		table in the database.  If the PARAMS['version'] is provided
		only pallets of that version are included otherwise no filtering
		on version number is performed.  If the ARGS list is empty then
		all pallet names are returned.  SQL regexp can be used in 
		both the version parameter and arg list, but must expand to 
		something.
		"""

		if 'version' in params:
			version = params['version']
		else:
			version = '%' # SQL wildcard

		if 'release' in params:
			rel = params['release']
		else:
			rel = '%' # SQL wildcard
	
		list = []
		if not args:
			args = [ '%' ] # find all pallet names
		for arg in args:
			rows = self.db.execute("""select distinct name,version,rel
				from rolls where name like binary '%s' and 
				version like binary '%s' and 
				rel like binary '%s' """ % (arg, version, rel))
			if rows == 0 and arg == '%': # empty table is OK
				continue
			if rows < 1:
				raise CommandError(self, 'unknown pallet "%s"' % arg)
			for (name, ver, rel) in self.db.fetchall():
				list.append((name, ver, rel))
				
		return list


class HostArgumentProcessor:
	"""An Interface class to add the ability to process host arguments."""
	
	def getHostnames(self, names=[], managed_only=False, subnet=None, order='asc'):
		"""Expands the given list of names to valid cluster 
		hostnames.  A name can be a hostname, IP address, our
		group (membership name), or a MAC address. Any combination of
		these is valid.
		If the names list is empty a list of all hosts in the cluster
		is returned.
		
		The following groups are recognized:
		
		rackN - All non-frontend host in rack N
		appliancename - All appliances of a given type (e.g. compute)
		[ cond ] - Ad-Hoc attribute/cond groups
			(e.g. [ appliance=="compute" ])

		The 'managed_only' flag means that the list of hosts will
		*not* contain hosts that traditionally don't have ssh login
		shells (for example, the following appliances usually don't
		have ssh login access: 'Ethernet Switches', 'Power Units',
		'Remote Management')
		"""

		adhoc    = False
		hostList = []
		hostDict = {}

                #
                # list the frontend first
                #
            	frontends = self.db.select("""
                	n.name from
			nodes n, appliances a where a.name = "frontend"
			and a.id = n.appliance order by rack, rank %s
                        """ % order)
                                
                #
                # now get the backend appliances
                #
                backends = self.db.select("""
                	n.name from
			nodes n, appliances a where a.name != "frontend"
			and a.id = n.appliance order by rack, rank %s
                        """ % order)

                hosts = [ ]

                if frontends:
                        hosts.extend(frontends)
                if backends:
                        hosts.extend(backends)

		for host, in hosts:

			# If we have a list of hostnames (or groups) then
			# disable all the hosts first and selectively
			# turn them on later.
			# Otherwise just enable all the hosts.
			#
			# The hostList is used to preserve the SQL sort order
			# in the output, and the hostDict use use to map
			# the hosts on/off in the returned host list
			#
			# If the subnet names a network the hostname
			# stored in the hostDict will be the name of that
			# interface rather than the name in the nodes table
			
			hostList.append(host)
			
			if names:
				hostDict[host] = None
			else:
				hostDict[host] = self.db.getNodeName(host,
                                                                     subnet)
				

		if names:
			
			# Environment, Appliance, and Rack grouping are special 
                        # since we can just say things like "compute" "rack1".
			# To force all code through ad-hoc grouping convert
			# any hostnames in this format to the general purpose
			# code.

                        environments = [ ]
			for e, in self.db.select("""
                        	distinct environment 
	                        from environment_attributes
                                """):
                                
                                environments.append(e)

			appliances  = []
			memberships = []
			for (name, membership) in self.db.select("""
				name, membership from appliances
				"""):
                                
				appliances.append(name)
				memberships.append(membership)

			racks = []
			for (rack,) in self.db.select("""
                                distinct(rack) from nodes
				"""):
				racks.append(rack)
			list = []
			for host in names:
                                if host in environments:
                                        host = '[environment=="%s"]' % host
                                        adhoc = True
				elif host in appliances:
					host = '[appliance=="%s"]' % host
					adhoc = True
				elif host in memberships:
					host = '[membership=="%s"]' % host
					adhoc = True
				elif host.find('rack') == 0:
					for i in racks:
						if host.find('rack%s' % i) == 0:
							try:
								isinstance(int(i),int)
								host = '[rack==%s]' % int(i)
								adhoc = True
							except ValueError:
								host = '[rack=="%s"]' % i
								adhoc = True
				elif host[0] == '[':
					adhoc = True

				list.append(host)
				
			names = list	# names is now the new ad-hoc syntax


		# If we have any Ad-Hoc groupings we need to load the attributes
		# for every host if the nodes tables.  Since this is a lot of
		# work handle the common case and avoid the work when just
		# a list of hosts.
		#
		# Also load the attributes if the managed_only argument is true
		# since we need to looked the managed attribute.

		hostAttrs  = {}
		if adhoc or managed_only:
			for host in hostList:
				hostAttrs[host] = self.db.getHostAttrs(host)
			

		# Finally iterate over all the host/groups

		list     = []
		explicit = {}
		for name in names:

			# ad-hoc group
			
			if name[0] == '[': # group
				for host in hostList:
					exp = name[1:-1]
					try:
						res = EvalCondExpr(exp,
								   hostAttrs[host])
					except SyntaxError:
						raise CommandError(self, 'group syntax "%s"' % exp)
					if res:
						s = self.db.getHostname(host, subnet)
						hostDict[host] = s
						if host not in explicit:
							explicit[host] = False
#					Debug('group %s is %s for %s' %
#				      (exp, res, host))

			# glob regex hostname

			elif '*' in name or '?' in name or '[' in name:
				for host in fnmatch.filter(hostList, name):
					s = self.db.getHostname(host, subnet)
					hostDict[host] = s
					if host not in explicit:
						explicit[host] = False
					

			# simple hostname
						
			else:
				host = self.db.getHostname(name)
				explicit[host] = True
				hostDict[host] = self.db.getHostname(name, subnet)


		# Preserving the SQL ordering build the list of hostname
		# selected.
		#
		# For each sorted host in the hostList include host if
		# the is an entry in the hostDict (interface name).
		#
		# If called with managed_only==True, filter out all
		# unmanaged hosts unless they explicitly appear in
		# the names list.  This effectively enforces the
		# filtering only on groups.

		list = []
		for host in hostList:
			
			if not hostDict[host]:
				continue

			if managed_only:
				managed = str2bool(hostAttrs[host]['managed'])
				if not managed and not explicit.get(host):
					continue
			
			list.append(hostDict[host])


                        
		return list


class PartitionArgumentProcessor:
	"""An Interface class to add the ability to process a partition 
	argument."""
	
	def partsizeCompare(self, x, y):
		xsize = x[0]
		ysize = y[0]

		suffixes = [ 'KB', 'MB', 'GB', 'TB', 'PB' ]

		xsuffix = xsize[-2:].upper()
		ysuffix = ysize[-2:].upper()

		try:
			xindex = suffixes.index(xsuffix)
		except:
			xindex = -1

		try:
			yindex = suffixes.index(ysuffix)
		except:
			yindex = -1

		if xindex < yindex:
			return 1
		elif xindex > yindex:
			return -1
		else:
			try:
				xx = float(xsize[:-2])
				yy = float(ysize[:-2])

				if xx < yy:
					return 1
				elif xx > yy:
					return -1
			except:
				pass

		return 0


	def getPartitionsDB(self, host):
		partitions = []

           	for (size, mnt, device) in self.db.select("""
                	p.partitionsize, p.mountpoint,
			p.device from partitions p, nodes n where
			p.node = n.id and n.name = '%s' order by device
                        """ % host):
                        
			if mnt in [ '', 'swap' ]:
				continue
			if len(mnt) > 0 and mnt[0] != '/':
				continue
			partitions.append((size, mnt, device))

		return partitions


	def getLargestPartition(self, host, disk=None):
		#
		# get the mountpoint for the largest partition for a host
		#
		maxmnt = None
		sizelist = []

		if not disk:
			sizelist = self.getPartitionsDB(host)
		else:
			for (size, mnt, device) in self.getPartitionsDB(host):
				dev = re.split('[0-9]+$', device)

				if len(dev) <= 1:
					continue 

				if dev[0] != disk:
					continue

				sizelist.append((size, mnt, device))

		if len(sizelist) > 0:
			sizelist.sort(self.partsizeCompare)
			(maxsize, maxmnt, device) = sizelist[0]

		return maxmnt


	def getPartitions(self, hostname='localhost', partition=None):
		#
		# get a list of partitions (mount points), that match
		# the argument 'partition'. 'partition' can be a regular
		# expression
		#
		partitions = []

		if partition:
			host = self.db.getHostname(hostname)
			parts = self.getPartitionsDB(host)
			pattern = re.compile(partition)

			for (size, mnt, device) in parts:
				if pattern.search(mnt):
					partitions.append(mnt)
			
		return partitions


	def getDisks(self, host):
		disks = {}
		disks['boot'] = []
		disks['data'] = []
		bootdisk = None
		alldisks = []

		#
		# first find the boot disk
		#
                for (device, mnt) in self.db.select("""
			p.device, p.mountpoint from
			partitions p, nodes n where p.node = n.id and
			n.name = '%s' order by p.device""" % host):
                        
			dev = re.split('[0-9]+$', device)
			disk = dev[0]

			if disk not in alldisks:
				alldisks.append(disk)

			if mnt and mnt == '/':
				bootdisk = disk

		#
		# now put the drives into their correct bins
		#
		for disk in alldisks:
			if disk == bootdisk:
				disktype = 'boot'
			else:
				disktype = 'data'

			if disk not in disks[disktype]:
				disks[disktype].append(disk)
				
		return disks


class DocStringHandler(handler.ContentHandler,
	handler.DTDHandler,
	handler.EntityResolver,
	handler.ErrorHandler):
	
	def __init__(self, name='', users=[]):
		handler.ContentHandler.__init__(self)
		self.text			= ''
		self.name			= name
		self.users			= users
		self.section			= {}
		self.section['description']	= ''
                self.section['optarg']		= []
                self.section['reqarg']		= []
		self.section['optparam']	= []
		self.section['reqparam']	= []
		self.section['example']		= []
		self.section['related']		= []
		self.parser = make_parser()
		self.parser.setContentHandler(self)

	def getDocbookText(self):
		s  = ''
		s += '<section id="stack-%s" xreflabel="%s">\n' % \
			(string.join(self.name.split(' '), '-'), self.name)
		s += '<title>%s</title>\n' % self.name
		s += '<cmdsynopsis>\n'
		s += '\t<command>stack %s</command>\n' % self.name
		for ((name, type, opt, rep), txt) in self.section['arg']:
			if opt:
				choice = 'opt'
			else:
				choice = 'req'
			if rep:
				repeat = 'repeat'
			else:
				repeat = 'norepeat'
			s += '\t<arg rep="%s" choice="%s">%s</arg>\n' % \
				(repeat, choice, name)
		for ((name, type, opt, rep), txt) in self.section['param']:
			if opt:
				choice = 'opt'
			else:
				choice = 'req'
			if rep:
				repeat = 'repeat'
			else:
				repeat = 'norepeat'
			s += '\t<arg rep="%s" choice="%s">' % (repeat, choice)
			s += '%s=<replaceable>%s</replaceable>' % (name, type)
			s += '</arg>\n'
		s += '</cmdsynopsis>\n'
		s += '<para>\n'
		s += saxutils.escape(self.section['description'])
		s += '\n</para>\n'
		if self.section['arg']:
			s += '<variablelist><title>arguments</title>\n'
			for ((name, type, opt, rep), txt) in \
				self.section['arg']:
				s += '\t<varlistentry>\n'
				if opt:
					term = '<optional>%s</optional>' % name
				else:
					term = name
				s += '\t<term>%s</term>\n' % term
				s += '\t<listitem>\n'
				s += '\t<para>\n'
				s += saxutils.escape(txt)
				s += '\n\t</para>\n'
				s += '\t</listitem>\n'
				s += '\t</varlistentry>\n'
			s += '</variablelist>\n'
		if self.section['param']:
			s += '<variablelist><title>parameters</title>\n'
			for ((name, type, opt, rep), txt) in \
				self.section['param']:
				s += '\t<varlistentry>\n'
				if opt:
					optStart = '<optional>'
					optEnd   = '</optional>'
				else:
					optStart = ''
					optEnd   = ''
				key = '%s=' % name
				val = '<replaceable>%s</replaceable>' % type
				s += '\t<term>%s%s%s%s</term>\n' % \
					(optStart, key, val, optEnd)
				s += '\t<listitem>\n'
				s += '\t<para>\n'
				s += saxutils.escape(txt)
				s += '\n\t</para>\n'
				s += '\t</listitem>\n'
				s += '\t</varlistentry>\n'
			s += '</variablelist>\n'
		if self.section['example']:
			s += '<variablelist><title>examples</title>\n'
			for (cmd, txt) in self.section['example']:
				s += '\t<varlistentry>\n'
				s += '\t<term>\n'
				if 'root' in self.users:
					s += '# '
				else:
					s += '$ '
				s += 'stack %s' % cmd
				s += '\n\t</term>\n'
				s += '\t<listitem>\n'
				s += '\t<para>\n'
				s += saxutils.escape(txt)
				s += '\n\t</para>\n'
				s += '\t</listitem>\n'
				s += '\t</varlistentry>\n'
			s += '</variablelist>\n'
		if self.section['related']:
			s += '<variablelist><title>related commands</title>\n'
			for related in self.section['related']:
				s += '\t<varlistentry>\n'
				s += '\t<term>'
				s += '<xref linkend="stack-%s">' % \
					string.join(related.split(' '), '-')
				s += '</term>\n'
				s += '\t<listitem>\n'
				s += '\t<para>\n'
				s += '\n\t</para>\n'
				s += '\t</listitem>\n'
				s += '\t</varlistentry>\n'
			s += '</variablelist>\n'
		s += '</section>'
		return s

	
	def getUsageText(self, colors):
                if colors:
                        bold   = colors['bold']['code']
                        unbold = colors['reset']['code']
                else:
                	bold   = ''
                        unbold = ''
                
		s = ''
		for (name, type, rep, txt) in self.section['reqarg']:
                        if rep:
                                dots = ' ...'
                        else:
                                dots = ''
			s += '{%s%s%s%s} ' % (bold, name, unbold, dots)
		for (name, type, rep, txt) in self.section['optarg']:
                        if rep:
                                dots = ' ...'
                        else:
                                dots = ''
			s += '[%s%s%s%s] ' % (bold, name, unbold, dots)
		for (name, type, rep, txt) in self.section['reqparam']:
                        if rep:
                                dots = ' ...'
                        else:
                                dots = ''
			s += '{%s%s%s=%s%s} ' % (bold, name, unbold, type, dots)
		for (name, type, rep, txt) in self.section['optparam']:
                        if rep:
                                dots = ' ...'
                        else:
                                dots = ''
			s += '[%s%s%s=%s%s] ' % (bold, name, unbold, type, dots)
		if s and s[-1] == ' ':
			return s[:-1]
		else:
			return s
	
	def getPlainText(self, colors=None):
		if 'root' in self.users:
			prompt = '#'
		else:
			prompt = '$'

                if colors:
                        bold   = colors['bold']['code']
                        unbold = colors['reset']['code']
                else:
                	bold   = ''
                        unbold = ''
                
		s  = ''
		s += 'stack %s %s' % (self.name, self.getUsageText(colors))
		s += '\n\n%sDescription%s\n' % (bold, unbold)
		s += self.section['description']
		if self.section['reqarg'] or self.section['optarg']:
			s += '\n%sArguments%s\n\n' % (bold, unbold)
			for (name, type, rep, txt) in self.section['reqarg']:
                                if rep:
                                        dots = ' ...'
                                else:
                                        dots = ''
                                s += '\t{%s%s%s%s}\n%s\n' % (bold, name, unbold, dots, txt)
			for (name, type, rep, txt) in self.section['optarg']:
                                if rep:
                                        dots = ' ...'
                                else:
                                        dots = ''
				s += '\t[%s%s%s%s]\n%s\n' % (bold, name, unbold, dots, txt)
		if self.section['reqparam'] or self.section['optparam']:
			s += '\n%sParameters%s\n\n' % (bold, unbold)
			for (name, type, rep, txt) in self.section['reqparam']:
                                if rep:
                                        dots = ' ...'
                                else:
                                        dots = ''
				s += '\t{%s%s%s=%s%s}\n%s\n' % (bold, name, unbold, type, dots, txt)
			for (name, type, rep, txt) in self.section['optparam']:
                                if rep:
                                        dots = ' ...'
                                else:
                                        dots = ''
				s += '\t[%s%s%s=%s%s]\n%s\n' % (bold, name, unbold, type, dots, txt)
		if self.section['example']:
			s += '\n%sExamples%s\n\n' % (bold, unbold)
			for (cmd, txt) in self.section['example']:
				s += '\t%s stack %s\n' % (prompt, cmd)
				s += '%s\n' % txt
		if self.section['related']:
			s += '\n%sRelated Commands%s\n\n' % (bold, unbold)
			for related in self.section['related']:
				s += '\tstack %s\n' % related
		return s
		
	def getParsedText(self):
		return '%s' % self.section
		
	def getSphinxText(self):
		cli = "stack %s" % self.name
		lnk = '.'.join(self.name.split()).strip()
		s = '.. _%s:\n\n' % lnk
		s = s + '%s\n' % self.name + '-' * len(self.name) +'\n\n'
		s = s + 'Usage\n'
		s = s + '"""""\n\n'
		cmd = "stack %s %s" % (self.name, self.getUsageText().strip())
		s = s + '``%s``\n\n' % cmd.strip()

		if self.section['description']:
			s = s + 'Description\n'
			s = s + '"""""""""""\n'
			s = s + self.section['description'] + '\n\n'

		if self.section['arg']:
			s = s + 'Arguments\n'
			s = s + '"""""""""\n'
			for ((name, type, opt, rep), txt) in \
				self.section['arg']:
				if opt:
					s += '``[%s]``\n' % name
				else:
					s += '``{%s}``\n' % name
				s += '%s\n\n' % txt
			s = s + '\n'

		if self.section['param']:
			s = s + 'Parameters\n'
			s = s + '""""""""""\n'
			for ((name, type, opt, rep), txt) in \
				self.section['param']:
				if opt:
					s += '``[%s=%s]``\n' % (name, type)
				else:
					s += '``{%s=%s}``\n' % (name, type)
				s += '%s\n' % txt
			s = s + '\n'

		if self.section['example']:
			s = s + 'Examples\n'
			s = s + '""""""""\n\n'
			for (cmd, txt) in self.section['example']:
				s += '``stack %s``\n\n' % cmd.strip()
				if txt:
					s += '%s\n\n' % txt
			s = s + '\n'

		if self.section['related']:
			s = s + 'Related\n'
			s = s + '"""""""\n\n'
			for related in self.section['related']:
				r = '.'.join(related.split())
				s += ':ref:`%s`\n\n' % r.strip()

		s = s + '\n'
		return s

	def getMarkDown(self):
		s = '## %s\n\n' % self.name
		s = s + '### Usage\n\n'
		cmd = "stack %s %s" % (self.name, self.getUsageText().strip())
		s = s + '`%s`\n\n' % cmd.strip()

		if self.section['description']:
			s = s + '### Description\n\n'
			s = s + self.section['description'].strip() + '\n\n'

		if self.section['arg']:
			s = s + '### Arguments\n\n'
			for ((name, type, opt, rep), txt) in \
				self.section['arg']:
				if opt:
					s += '* `[%s]`\n' % name
				else:
					s += '* `{%s}`\n' % name
				s += '\n   %s\n\n' % txt.strip()
			s = s + '\n'

		if self.section['param']:
			s = s + '### Parameters\n'
			for ((name, type, opt, rep), txt) in \
				self.section['param']:
				if opt:
					s += '* `[%s=%s]`\n' % (name, type)
				else:
					s += '* `{%s=%s}`\n' % (name, type)
				s += '\n   %s\n' % txt.strip()
			s = s + '\n'

		if self.section['example']:
			s = s + '### Examples\n\n'
			for (cmd, txt) in self.section['example']:
				s += '* `stack %s`\n' % cmd.strip()
				if txt:
					s += '\n   %s\n' % txt.strip()
				s += '\n'
			s = s + '\n'

		if self.section['related']:
			s = s + '### Related\n'
			for related in self.section['related']:
				r = '-'.join(related.split()).strip()
				s += '[%s](%s)\n\n' % (related,r)

		s = s + '\n'
		return s

	def startElement(self, name, attrs):
		if not self.section['description']:
			self.section['description'] = self.text
		self.key  = None
		self.text = ''
		if name in [ 'arg', 'param' ]:
                        type = attrs.get('type')
			if not type:
				type = 'string'
			try:
				optional = int(attrs.get('optional'))
			except:
				if name == 'arg':
					optional = 0
				if name == 'param':
					optional = 1
			try:
				repeat = int(attrs.get('repeat'))
			except:
				repeat = 0
			name = attrs.get('name')
			self.key = (name, type, optional, repeat)
		elif name == 'example':
			self.key = attrs.get('cmd')
		
	def endElement(self, tag):
		if tag == 'docstring':
			# we are done so sort the param and related lists
			self.section['reqparam'].sort()
			self.section['optparam'].sort()
			self.section['related'].sort()
                elif tag == 'arg':
                        name, type, optional, repeat = self.key
                        if optional:
                                self.section['optarg'].append((name, type, repeat, self.text))
                        else:
                                self.section['reqarg'].append((name, type, repeat, self.text))
                elif tag == 'param':
                        name, type, optional, repeat = self.key
                        if optional:
                                self.section['optparam'].append((name, type, repeat, self.text))
                        else:
                                self.section['reqparam'].append((name, type, repeat, self.text))
                elif tag == 'example':
			self.section['example'].append((self.key, self.text))
		else:
			if tag in self.section:
				self.section[tag].append(self.text)
		
	def characters(self, s):
		self.text += s
			
			

class DatabaseConnection:

	"""Wrapper class for all database access.  The methods are based on
	those provided from the MySQLdb library and some other Stack
	specific methods are added.  All StackCommands own an instance of
	this object (self.db).
	"""

	def __init__(self, db):

		# self.database : object returned from orginal connect call
		# self.link	: database cursor used by everyone else
		if db:
			self.database = db
			self.link     = db.cursor()
		else:
			self.database = None
			self.link     = None

                # Optional envinormnet variable STACKCACHE can be used
                # to disable database caching.  Default is to cache.
                
                caching = os.environ.get('STACKCACHE')
                if caching:
                        caching = str2bool(caching)
                else:
                        caching = True
                self.cache   = {}
                self.caching = caching


        def enableCache(self):
                self.caching = True

        def disableCache(self):
                self.caching = False
                self.clearCache()

        def clearCache(self):
                self.cache = {}

        def select(self, command):
		if not self.link:
                        return [ ]
                
		from _mysql_exceptions import *

                rows = [ ]
                
                m = hashlib.md5()
                m.update(command.strip())
                k = m.hexdigest()

#                print 'select', k
                if k in self.cache:
                	rows = self.cache[k]
#                        print >> sys.stderr, '-\n%s\n%s\n' % (command, rows)
                else:
                        try:
                        	self.execute('select %s' % command)
                        	rows = self.fetchall()
                        except (OperationalError, ProgrammingError):
                                # Permission error return the empty set
                                # Syntax errors throw exceptions
                                rows = [ ]
                                
                        if self.caching:
                                self.cache[k] = rows

                return rows

                                        
	def execute(self, command):
                command = command.strip()

                if command.find('select') == -1:
                        self.clearCache()
                                                
		if self.link:
			t0 = time.time()
			result = self.link.execute(command)
                        t1 = time.time()
                        Debug('SQL EX: %.3f %s' % ((t1-t0), command))
			return result
                
		return None

	def fetchone(self):
		if self.link:
			row = self.link.fetchone()
#			Debug('SQL F1: %s' % row.__repr__())
			return row
		return None

	def fetchall(self):
		if self.link:
			rows = self.link.fetchall()
#			for row in rows:
#				Debug('SQL F*: %s' % row.__repr__())
			return rows
		return None
		

	def getHostOS(self, host):
                """
                Return the OS name for the given host.
                """

                # Since this is called for all host on every
                # command run (licensing does this) grab everyone
                # in one select and cache a dictionary.
                #
                # Two levels of caching here:
                # 1) low level select() cache
                # 2) method level 'HostOS' cache
                #
                # The first level clearly isn't used, since the
                # second prevents the select() from being
                # repeated.
                
		dict = self.cache.get('host-os-dict')
                if not dict:
                        dict = {}
                	for (name, os) in self.select("""
				n.name, b.os from
				boxes b, nodes n where
				n.box=b.id
                        	"""):
                        	dict[name] = os
                if self.caching:
                	self.cache['host-os-dict'] = dict

                os = dict.get(host)
                if not os:
                        os = 'redhat'
		return os

        def getHostAppliance(self, host):
                """
                Returns the appliance for a given host.
                """

		dict = self.cache.get('host-appliance-dict')
                if not dict:
                        dict = {}
                        for (name, appliance) in self.select("""
                        	n.name, a.name from
                                nodes n, appliances a where
                                n.appliance = a.id
                                """):
                                dict[name] = appliance
                if self.caching:
                	self.cache['host-appliance-dict'] = dict

                return dict.get(host)
                

	def getHostRoutes(self, host, showsource=0):

		host = self.getHostname(host)
		routes = {}
		
		# global
                
		for (n, m, g, s) in self.select("""
                        network, netmask, gateway, subnet from
			global_routes
                        """):
			if s:
				for dev, in self.select("""
                                        net.device from
				       	subnets s, networks net, nodes n where
					s.id = %s and s.id = net.subnet and
					net.node = n.id and n.name = '%s'
					and net.device not like 'vlan%%' 
					""" % (s, host)):
                                        g = dev
			if showsource:
                        	routes[n] = (m, g, 'G')
                        else:
                        	routes[n] = (m, g)

		# os
				
		for (n, m, g, s) in self.select("""
			r.network, r.netmask, r.gateway,
			r.subnet from os_routes r, nodes n where
			r.os='%s' and n.name='%s'
			"""  % (self.getHostOS(host), host)):
			if s:
                                for dev, in self.select("""
                                        net.device from
					subnets s, networks net, nodes n where
					s.id = %s and s.id = net.subnet and
					net.node = n.id and n.name = '%s' 
					and net.device not like 'vlan%%'
					""" % (s, host)):
                                        g = dev
			if showsource:
				routes[n] = (m, g, 'O')
                        else:
				routes[n] = (m, g)

		# appliance

                for (n, m, g, s) in self.select("""
			r.network, r.netmask, r.gateway,
			r.subnet from
			appliance_routes r,
			nodes n,
			appliances app where
			n.appliance=app.id and 
			r.appliance=app.id and n.name='%s'
                        """ % host):
			if s:
				for dev, in self.select("""
                                        net.device from
					subnets s, networks net, nodes n where
					s.id = %s and s.id = net.subnet and
					net.node = n.id and n.name = '%s' 
					and net.device not like 'vlan%%'
					""" % (s, host)):
                                        g = dev
			if showsource:
				routes[n] = (m, g, 'A')
                        else:
				routes[n] = (m, g)

		# host
                
		for (n, m, g, s) in self.select("""
			r.network, r.netmask, r.gateway,
			r.subnet from node_routes r, nodes n where
			n.name='%s' and n.id=r.node
                        """ % host):
			if s:
				for dev, in self.select("""
                                        net.device from
					subnets s, networks net, nodes n where
					s.id = %s and s.id = net.subnet and
					net.node = n.id and n.name = '%s'
					and net.device not like 'vlan%%'
					""" % (s, host)):
                                        g = dev
			if showsource:
				routes[n] = (m, g, 'H')
                        else:
				routes[n] = (m, g)

		return routes


	def getIntrinsicAttrs(self):
		"""
                Return a list of (scope, attr, value) tuples for all the
		global intrinsic attributes.
		"""

                list = self.cache.get('intrinsic-attrs-list')
                if not list:
                        list = []
			for (ip, host, subnet, netmask) in self.select("""
				n.ip, if(n.name, n.name, nd.name), 
                                s.address, s.mask from 
                                networks n, appliances a, subnets s, nodes nd 
                                where 
                                n.node=nd.id and nd.appliance=a.id and 
                                a.name='frontend' and n.subnet=s.id and 
                                s.name='private'
                                """):
                                list.append((None, 'Kickstart_PrivateKickstartHost',
                                             ip))
				list.append((None, 'Kickstart_PrivateAddress',
                                             ip))
				list.append((None, 'Kickstart_PrivateHostname',
                                             host))
				ipg = stack.ip.IPGenerator(subnet, netmask)
				list.append((None, 'Kickstart_PrivateBroadcast',
                                             '%s' % ipg.broadcast()))

			for (ip, host, zone, subnet, netmask) in self.select("""
				n.ip, if(n.name, n.name, nd.name), 
                                s.zone, s.address, s.mask from 
                                networks n, appliances a, subnets s, nodes nd 
                                where 
                                n.node=nd.id and nd.appliance=a.id and
				a.name='frontend' and n.subnet=s.id and 
                                s.name='public'
                                """):
				list.append((None, 'Kickstart_PublicAddress',
                                             ip))
				list.append((None, 'Kickstart_PublicHostname',
                                             '%s.%s' % (host, zone)))
				ipg = stack.ip.IPGenerator(subnet, netmask)
				list.append((None, 'Kickstart_PublicBroadcast',
                                             '%s' % ipg.broadcast()))

			for (name, subnet, netmask, zone) in self.select("""
				name, address, mask, zone from 
                                subnets
				"""):
				if name == 'private':
					ipg = stack.ip.IPGenerator(subnet, 
                                                                   netmask)
					list.append((None,
                                                     'Kickstart_PrivateDNSDomain', 
                                                     zone))
					list.append((None, 
                                                     'Kickstart_PrivateNetwork',
                                                     subnet))
					list.append((None, 
                                                     'Kickstart_PrivateNetmask',
						     netmask))
					list.append((None, 
                                                     'Kickstart_PrivateNetmaskCIDR', 
						     '%s' % ipg.cidr()))
				elif name == 'public':
					ipg = stack.ip.IPGenerator(subnet, 
                                                                   netmask)
                                        list.append((None,
                                                     'Kickstart_PublicDNSDomain', 
                                                     zone))
					list.append((None, 
                                                     'Kickstart_PublicNetwork',
                                                     subnet))
					list.append((None, 
                                                     'Kickstart_PublicNetmask',
                                                     netmask))
					list.append((None, 
                                                     'Kickstart_PublicNetmaskCIDR', 
						     '%s' % ipg.cidr()))

			list.append((None, 'release', stack.release))
			list.append((None, 'version', stack.version))

                        if self.caching:
                        	self.cache['intrinsic-attrs-list'] = list
        
		return list

	
	def getHostIntrinsicAttrs(self, host):
		"""
                Return a list of (scope, attr, value) tuples for all the
		HOST intrinsic attributes.
		"""

                dict = self.cache.get('host-intrinsic-attrs-dict')
                if not dict:
                        dict = {}
                        for (name, rack, rank, cpus) in self.select("""
                        	name,rack,rank,cpus from nodes
                                """):
                                dict[name] = [ (None, 'rack', rack),
                                               (None, 'rank', rank),
                                               (None, 'cpus', cpus) ]

                        for (name, box, appliance, membership) in \
				self.select(""" n.name, b.name,
                                a.name, a.membership from
				nodes n, boxes b, appliances a where
				n.appliance=a.id and n.box=b.id """):

                                dict[name].extend(
                                        [ (None, 'box', box),
                                          (None, 'appliance', appliance),
                                          (None, 'membership', membership)
                                        ])
                                
                        for (name, zone, address) in self.select("""
				n.name, s.zone, nt.ip from
				networks nt, nodes n, subnets s where
				nt.main=true and nt.node=n.id and
				nt.subnet=s.id
                                """):
                                dict[name].append((None, 'hostaddr', address))
                                dict[name].append((None, 'domainname', zone))

                        if self.caching:
                                self.cache['host-intrinsic-attrs-dict'] = dict

                attrs = dict[host]
                attrs.append((None, 'os', self.getHostOS(host)))
		attrs.append((None, 'hostname', host))

		return attrs


	def getHostAttrs(self, host, showsource=False, slash=False, filter=None):
		"""Return a dictionary of KEY x VALUE pairs for the host
		specific attributes for the given host.
		"""

                host = self.getHostname(host)
                dict = self.cache.get('host-attrs-dict')
                if not dict:
                        dict = {}

                        
                        # Global Attributes

                        G = {}
                        rows = self.select("""
				scope, attr, value, shadow from 
                                global_attributes
                                """)
                        if not rows:
				rows = self.select("""
					scope, attr, value from 
                                        global_attributes
					""")
			for row in rows:
				if len(row) == 4:
					(s, a, v, x) = row
					if x:
						v = x
				else:
					(s, a, v) = row
                                G[ConcatAttr(s, a, slash=True)] = v

                	# OS Attributes

                        O = {}
			rows = self.select("""
				os, scope, attr, value, shadow from
                                os_attributes
                                """)
			if not rows:
				rows = self.select("""
					os, scope, attr, value from
					os_attributes
					""")
			for row in rows:
				if len(row) == 5:
					(o, s, a, v, x) = row
					if x:
						v = x
				else:
					(o, s, a, v) = row
                                if o not in O:
                                        O[o] = {}
                                O[o][ConcatAttr(s, a, slash=True)] = v

	                # Environment Attributes

                        E = {}
                        rows = self.select("""
				environment, scope, attr, value, shadow from
                                environment_attributes
				""")
                        if not rows:
                                rows = self.select("""
					environment, scope, attr, value from
					environment_attributes
					""")
                        for row in rows:
                        	if len(row) == 5:
	                                (e, s, a, v, x) = row
                                        if x:
        	                                v = x
                                else:
                                        (e, s, a, v) = row
                                if e not in E:
                                        E[e] = {}
                                E[e][ConcatAttr(s, a, slash=True)] = v
			
			# Appliance Attributes

                        A = {}
                        rows = self.select("""
					app.name, 
                                        a.scope, a.attr, a.value, a.shadow from
                                        appliance_attributes a, appliances app 
                                        where
                                        a.appliance=app.id
                                        """)
                        if not rows:
                                rows = self.select("""
					app.name,
                                        a.scope, a.attr, a.value from
                                        appliance_attributes a, appliances app 
                                        where
                                        a.appliance=app.id
                                        """)
                        for row in rows:
	                        if len(row) == 5:
        	                        (app, s, a, v, x) = row
                                	if x:
                                        	v = x
                                else:
                                        (app, s, a, v) = row
                                if app not in A:
                                        A[app] = {}
                                A[app][ConcatAttr(s, a, slash=True)] = v

			# Host Attributes
                        H = {}
			rows = self.select("""
				n.name, 
                                a.scope, a.attr, a.value, a.shadow from
				node_attributes a, nodes n where
                                n.id=a.node
				""")
			if not rows:
				rows = self.select("""
					n.name, 
                                        a.scope, a.attr, a.value from
					node_attributes a, nodes n where 
                                        n.id=a.node
					""")
			for row in rows:
				if len(row) == 5:
					(h, s, a, v, x) = row
					if x:
						v = x
				else:
					(h, s, a, v) = row
                                if h not in H:
                                        H[h] = {}
                                H[h][ConcatAttr(s, a, slash=True)] = v

                        for h, in self.select('name from nodes'):

				if h not in H:
					H[h] = {}

                                app  = self.getHostAppliance(h)
                                os   = self.getHostOS(h)

		                try:
                            		env = H[h]['environment']
		                except:
		                        try:
                		                env = O[os]['environment']
		                        except:
		                                try:
		                                        env = A[app]['environment']
		                                except:
                		                        try:
                                		                env = G['environment']
		                                        except:
                		                                env = None

		                # Build the attribute dictionary for the host
		                d = {}
        		        for (key, value) in G.items():
	                	        (s, a) = SplitAttr(key)
        	                	d[key] = (s, a, value, 'G')
	          	      	if os in O:
        	        	        for (key, value) in O[os].items():
                	        	        (s, a) = SplitAttr(key)
                        	        	d[key] = (s, a, value, 'O')
		                if app in A:
        		                for (key, value) in A[app].items():
                		                (s, a) = SplitAttr(key)
                        		        d[key] = (s, a, value, 'A')
		                if env and env in E:
        		                for (key, value) in E[env].items():
                		                (s, a) = SplitAttr(key)
                        		        d[key] = (s, a, value, 'E')
		                if h in H:
        		                for (key, value) in H[h].items():
                		                (s, a) = SplitAttr(key)
                        		        d[key] = (s, a, value, 'H')
					for (s, a, v) in self.getIntrinsicAttrs():
						d[ConcatAttr(s, a, slash=True)] = (s, a, v, 'I')
					for (s, a, v) in self.getHostIntrinsicAttrs(h):
						d[ConcatAttr(s, a, slash=True)] = (s, a, v, 'I')

                                dict[h] = d

                        if self.caching:
                        	self.cache['host-attrs-dict'] = dict

                # Create the attr dictionary that gets returned
		
		attrs = {}
		for (k, (scope, attr, value, source)) in dict[host].items():
			key = ConcatAttr(scope, attr, slash)
			if showsource:
				attrs[key] = (value, source)
			else:
				attrs[key] = value


                
		# If we have a filter delete all attributes that
		# do not have FILTER as their prefix.  Enforce
		# the filter being a complete (sub)scope by adding
		# a period to the end if one is missing.  Handle
		# case where filter is a complete attribute name.
					
		if filter:
			for attr in attrs.keys():

				if filter == attr: # exact match
					continue

				if filter[-1] != '.':
					p = '%s.' % filter
				else:
					p = filter
				if attr.find(p) == 0:
					continue # (sub)scope match
				
				del attrs[attr] # no match

		return attrs


	def getHostAttr(self, host, key, showsource=False):
		"""Return the value for the host specific attribute KEY or
		None if it does not exist.
		"""

		host   = self.getHostname(host)
                attrs  = self.getHostAttrs(host, showsource=True, slash=True)
                (s, a) = SplitAttr(key)
                attr   = ConcatAttr(s, a, slash=True)

                if attr in attrs:
                        (value, source) = attrs[attr]
                else:
                        value = source = None

                if showsource:
                        return (value, source)
                else:
                        return value
		

	def getNodeName(self, hostname, subnet=None):

		if not subnet:
			return hostname

                result = None
                
		for (netname, zone) in self.select("""
                        net.name, s.zone from
			nodes n, networks net, subnets s where n.name = '%s'
			and net.node = n.id and net.subnet = s.id and
			s.name = '%s'
                        """ % (hostname, subnet)):

                        # If interface exists, but name is not set
			# infer name from nodes table, and append
			# dns zone
			if not netname:
				netname = hostname
			result = '%s.%s' % (netname, zone)
                
		return result


	def getHostname(self, hostname=None, subnet=None):
		"""Returns the name of the given host as referred to in
		the database.  This is used to normalize a hostname before
		using it for any database queries."""

		# Look for the hostname in the database before trying
		# to reverse lookup the IP address and map that to the
		# name in the nodes table.  This should speed up the
		# installer w/ the restore pallet

		if hostname and self.link:
			rows = self.link.execute("""select * from nodes where
				name='%s'""" % hostname)
			if rows:
				return self.getNodeName(hostname, subnet)

		if not hostname:					
			hostname = socket.gethostname()

			if hostname == 'localhost':
				if self.link:
					return ''
				else:
					return 'localhost'
		try:

			# Do a reverse lookup to get the IP address.
			# Then do a forward lookup to verify the IP
			# address is in DNS.  This is done to catch
			# evil DNS servers (timewarner) that have a
			# catchall address.  We've had several users
			# complain about this one.  Had to be at home
			# to see it.
			#
			# If the resolved address is the same as the
			# hostname then this function was called with
			# an ip address, so we don't need the reverse
			# lookup.
			#
			# For truly evil DNS (OpenDNS) that have
			# catchall servers that are in DNS we make
			# sure the hostname matches the primary or
			# alias of the forward lookup Throw an Except,
			# if the forward failed an exception was
			# already thrown.


			addr = socket.gethostbyname(hostname)
			if not addr == hostname:
				(name, aliases, addrs) = socket.gethostbyaddr(addr)
				if hostname != name and hostname not in aliases:
					raise NameError

		except:
			if hostname == 'localhost':
				addr = '127.0.0.1'
			else:
				addr = None

		if not addr:
			if self.link:
				self.link.execute("""select name from nodes
					where name="%s" """ % hostname)
				if self.link.fetchone():
					return self.getNodeName(hostname, subnet)

				#
				# see if this is a MAC address
				#
				self.link.execute("""select nodes.name from
					networks,nodes where
					nodes.id = networks.node and
					networks.mac = '%s' """ % (hostname))
				try:
					hostname, = self.link.fetchone()
					return self.getNodeName(hostname, subnet)
				except:
					pass

				#
				# see if this is a FQDN. If it is FQDN,
				# break it into name and domain.
				#
				n = hostname.split('.')
				if len(n) > 1:
					name = n[0]
					domain = string.join(n[1:], '.')
					cmd = 'select n.name from nodes n, '	+\
						'networks nt, subnets s where '	+\
						'nt.subnet=s.id and '		+\
						'nt.node=n.id and '		+\
						's.zone="%s" and ' % (domain)+   \
						'(nt.name="%s" or n.name="%s")'  \
						% (name, name)

					self.link.execute(cmd)
				try:
					hostname, = self.link.fetchone()
					return self.getNodeName(hostname, subnet)
				except:
					pass

				# Check if the hostname is a basename
				# and the FQDN is in /etc/hosts but
				# not actually registered with DNS.
				# To do this we need lookup the DNS
				# search domains and then do a lookup
				# in each domain.  The DNS lookup will
				# fail (already has) but we might
				# find an entry in the /etc/hosts
				# file.
				#
				# All this to handle the case when the
				# user lies and gives a FQDN that does
				# not really exist.  Still a common
				# case.
				
				try:
					fin = open('/etc/resolv.conf', 'r')
				except:
					fin = None
				if fin:
					domains = []
					for line in fin.readlines():
						tokens = line[:-1].split()
						if len(tokens) == 0:
							continue
						if tokens[0] == 'search':
							domains = tokens[1:]
					for domain in domains:
						try:
							name = '%s.%s' % (hostname, domain)
							addr = socket.gethostbyname(name)
							hostname = name
							break
						except:
							pass
					if addr:
						return self.getHostname(hostname)

					fin.close()
				
				raise CommandError(self, 'cannot resolve host "%s"' % hostname)
					
		
		if addr == '127.0.0.1': # allow localhost to be valid
			if self.link:
				return self.getHostname(subnet=subnet)
			else:
				return 'localhost'
			
		if self.link:
			# Look up the IP address in the networks table
			# to find the hostname (nodes table) of the node.
			#
			# If the IP address is not found also see if the
			# hostname is in the networks table.  This last
			# check handles the case where DNS is correct but
			# the IP address used is different.
			rows = self.link.execute('select nodes.name from '
				'networks,nodes where '
				'nodes.id=networks.node and ip="%s"' % (addr))
			if not rows:
				rows = self.link.execute('select nodes.name ' 
					'from networks,nodes where '
					'nodes.id=networks.node and '
					'networks.name="%s"' % (hostname))
				if not rows:
					raise CommandError(self, 'host "%s" is not in cluster'
						% hostname)
			hostname, = self.link.fetchone()

		return self.getNodeName(hostname, subnet)


		

class Command:
	"""Base class for all Stack commands the general command line form
	is as follows:

		stack ACTION COMPONENT OBJECT [ <ARGNAME ARGS> ... ]
		
		ACTION(s):
			add
			create
			list
			load
			sync
	"""

	MustBeRoot = 1
	
	def __init__(self, database):
		"""Creates a DatabaseConnection for the StackCommand to use.
		This is called for all commands, including those that do not
		require a database connection."""

		self.db = DatabaseConnection(database)

		self.text = ''
		
		self.output = []
        
		self.arch = os.uname()[4]
		if self.arch in [ 'i386', 'i486', 'i586', 'i686' ]:
			self.arch = 'i386'

		self.os = os.uname()[0].lower()
		if self.os == 'linux':
			self.os = 'redhat'
		
		self._args   = None
		self._params = None

		self.rc = None # return code
		self.level = 0

                # Look up terminal colors safely using tput, uncolored if
                # this fails.
                
                self.colors = {
                        'bold': { 'tput': 'bold', 'code': '' },
                        'reset': { 'tput': 'sgr0', 'code': '' },
                        'beginline': { 'tput': 'smul', 'code': ''},
                        'endline': { 'tput': 'rmul', 'code': ''}
                        }
                if sys.stdout.isatty():
			for key in self.colors.keys():
				c = 'tput %s' % self.colors[key]['tput']
                	        try:
	                        	p = subprocess.Popen(c.split(),
        	                                             stdout=subprocess.PIPE)
                	        except:
                        	        continue
	                       	(o, e) = p.communicate()
        	               	if p.returncode == 0:
                	       		self.colors[key]['code'] = o


        def fillParams(self, names, params=None):
		"""Returns a list of variables with either default
		values of the values in the PARAMS dictionary.
		
		NAMES - list of (KEY, DEFAULT) tuples.
			KEY - key name of PARAMS dictionary
			DEFAULT - default value if key in not in dict
		PARAMS - optional dictionary
                REQUIRED - optional boolean (True means param is required)
		
		For example:
		
		(svc, comp) = self.fillParams(
			('service', None),
			('component', None))
			
		Can also be written as:
		
		(svc, comp) = self.fillParams(('service',), ('component', ))
		"""

		# make sure names is a list or tuple
		
		if not type(names) in [ types.ListType, types.TupleType ]:
			names = [ names ]

		# for each element in the names list make sure it is also
		# a tuple.  If the second element (default value) is missing
		# use None.  If the third element is missing assume the
                # parameter is not required.
                		
		pdlist = []
		for e in names:
			if type(e) in [ types.ListType, types.TupleType]:
                                if len(e) == 3:
                                        tuple = ( e[0], e[1], e[2] )
                                elif len(e) == 2:
                                        tuple = ( e[0], e[1], False )
                                elif len(e) == 1:
                                        tuple = ( e[0], None, False )
                                else:
                                        assert len(e) in [ 1, 2, 3 ]
			else:
				tuple = ( e[0], None, False )
			pdlist.append(tuple)
				
		if not params:
			params = self._params

		list = []
		for (key, default, required) in pdlist:
			if key in params:
				list.append(params[key])
			else:
                                if required:
                                        raise ParamRequired(self, key)
				list.append(default)

		return list


	def call(self, command, args=[]):
		"""
		Similar to the command method but uses the output-format=binary
		to run a command and return a list of dictionary rows.
		"""
		# Do a copy of the args list
		a = args[:]
		a.append('output-format=binary')
		s = self.command(command, a)
 		if s:
			return marshal.loads(s)
		return [ ]

		
	def command(self, command, args=[]):
		"""Import and run a Stack command.
		Returns and output string."""

		modpath = 'stack.commands.%s' % command
		__import__(modpath)
		mod = eval(modpath)

		try:
			o = getattr(mod, 'Command')(self.db.database)
			name = string.join(string.split(command, '.'), ' ')
		except AttributeError:
			return ''

		# Call the command and store the return code in the
		# class member self.rc so the caller can check
		# the return code.  The actual text is what we return.

		self.rc = o.runWrapper(name, args, self.level + 1)
		return o.getText()


	def loadPlugins(self):
		dict	= {}
		graph	= stack.graph.Graph()
		
		loadedModules = []
		dir = eval('%s.__path__[0]' % self.__module__)
		for file in os.listdir(dir):
			if file.split('_')[0] != 'plugin':
				continue

			# Find either the .py or .pyc but only load each
			# module once.  This also plugins to be compiled
			# and does not require source code releases.

			if os.path.splitext(file)[1] not in [ '.py', '.pyc']:
				continue

			module = '%s.%s' % (self.__module__, 
				os.path.splitext(file)[0])

			if module in loadedModules:
				continue
			loadedModules.append(module)

			__import__(module)
			module = eval(module)
			try:
				o = getattr(module, 'Plugin')(self)
			except AttributeError:
				continue
			
			# All nodes point to TAIL.  This insures a fully
			# connected graph, otherwise partial ordering
			# will fail

			if graph.hasNode(o.provides()):
				plugin = graph.getNode(o.provides())
			else:
				plugin = stack.graph.Node(o.provides())
			dict[plugin] = o

			if graph.hasNode('TAIL'):
				tail = graph.getNode('TAIL')
			else:
				tail = stack.graph.Node('TAIL')
			graph.addEdge(stack.graph.Edge(plugin, tail))
			
			for pre in o.precedes():
				if graph.hasNode(pre):
					tail = graph.getNode(pre)
				else:
					tail = stack.graph.Node(pre)
				graph.addEdge(stack.graph.Edge(plugin, tail))
					
			for req in o.requires():
				if graph.hasNode(req):
					head = graph.getNode(req)
				else:
					head = stack.graph.Node(req)
				graph.addEdge(stack.graph.Edge(head, plugin))
			
		list = []
		for node in PluginOrderIterator(graph).run():
			if node in dict:
				list.append(dict[node])

		return list

		
	def runPlugins(self, args='', plugins=None):
		if not plugins:
			plugins = self.loadPlugins()
                results = [ ]
		for plugin in plugins:
                        Log('run %s' % plugin)
                        retval = plugin.run(args)
                        if not retval == None:
                                results.append((plugin.provides(), retval))
                return results



	def runImplementation(self, name, args=None):

		list = []
		loadedModules = []
		dir = eval('%s.__path__[0]' % self.__module__)
		for file in os.listdir(dir):
			base, ext = os.path.splitext(file)

			if base != 'imp_%s' % name:
				continue

			# Find either the .py or .pyc but only load each
			# module once.  This also plugins to be compiled
			# and does not require source code releases.

			if ext not in [ '.py', '.pyc']:
				continue

		 	module = '%s.%s' % (self.__module__, base)
		 	__import__(module)
		 	module = eval(module)
		 	try:
		 		o = getattr(module, 'Implementation')(self)
		 	except AttributeError:
		 		continue

			return o.run(args)



	def isRootUser(self):
		"""Returns TRUE if running as the root account."""
		if os.geteuid() == 0:
			return 1
		else:
			return 0
			
	def isApacheUser(self):
		"""Returns TRUE if running as the apache account."""
		try:
			if os.geteuid() == pwd.getpwnam('apache')[3]:
				return 1
		except:
			pass
		return 0
		
	
	def str2bool(self, s):
		return str2bool(s)

	def bool2str(self, b):
		return bool2str(b)

	
	def strWordWrap(self, line, indent=''):
		if 'COLUMNS' in os.environ:
			cols = os.environ['COLUMNS']
		else:
			cols = 80
		l = 0
		s = ''
		for word in line.split(' '):
			if l + len(word) < cols:
				s += '%s ' % word
				l += len(word) + 1 # space
			else:
				s += '\n%s%s ' % (indent, word)
				l += len(indent) + len(word) + 1 # space
		return s
			
	def clearText(self):
		"""Reset the output text buffer."""
		self.text = ''
		
	def addText(self, s):
		"""Append a string to the output text buffer."""
		if s:
			self.text += s
		
	def getText(self):
		"""Returns the output text buffer."""
		return self.text	

	def beginOutput(self):
		"""Reset the output list buffer."""
		self.output = []
		
	def addOutput(self, owner, vals):
		"""Append a list to the output list buffer."""

		# VALS can be a list, tuple, or primitive type.


		list = [ '%s' % owner ]
		
		if type(vals) == types.ListType:
			list.extend(vals)
		if type(vals) == types.TupleType:
			for e in vals:
				list.append(e)
		else:
			list.append(vals)
			
		self.output.append(list)
		
		
	def endOutput(self, header=[], padChar='-', trimOwner=True):
		"""Pretty prints the output list buffer."""

		# Handle the simple case of no output, and bail out
		# early.  We do this to avoid printing out nothing
		# but a header w/o any rows.

		if not self.output:
			return
			
		# The OUTPUT-FORMAT option can change the default from
		# human readable text to something else.  Currently
		# supports:
		#
		# json		- text json
		# python	- text python
		# binary	- marshalled python
		# text		- default (for humans)
		
		format = self._params.get('output-format')
		if not format:
			format = 'text'

		if format in [ 'json', 'python', 'binary' ]:
                        if not header: # need to build a generic header
                                if len(self.output) > 0:
                                        rows = len(self.output[0])
                                else:
                                        rows = 0
                                header = [ ]
                                for i in range(0, rows):
                                        header.append('col-%d' % i)
			list = []
			for line in self.output:
				dict = {}
				for i in range(0, len(header)):
					if header[i]:
						key = header[i]
						val = line[i]
                                                if key in dict:
                                                        if not type(dict[key]) ==types.ListType:
                                                                dict[key] = [ dict[key] ]
                                                        dict[key].append(val)
                                                else:
                                                        dict[key] = val
				list.append(dict)
			if format == 'python':
				self.addText('%s' % list)
			elif format == 'binary':
				self.addText(marshal.dumps(list))
			else:
				self.addText(json.dumps(list))
			return

		if format == 'null':
			return


		# Loop over the output and check if there is more than
		# one owner (usually a hostname).  We have only one owner
		# there is no reason to display it.  The caller can use
		# trimOwner=False to disable this optimization.

		if trimOwner:
			owner = ''
			self.startOfLine = 1
			for line in self.output:
				if not owner:
					owner = line[0]
				if not owner == line[0]:
					self.startOfLine = 0
		else:
			self.startOfLine = 0
			
		# Add the trailing ':' to the owner column of
		# each line of the output.  Do this here so
		# we don't also add it to the header row.
			
		for line in self.output:
			if line[0]:
				line[0] += ':'
		
		# Add the header to the output and start formatting.  We
		# keep the header optional and separate from the output
		# so the above decision (startOfLine) can be made.

 		if header:
			list = []
			for field in header:
				if field:
					list.append(field.upper())
				else:
					list.append('')
			output = [ list ]
			output.extend(self.output)
		else:
			output = self.output
			
		colwidth = []
		for line in output:
			for i in range(0, len(line)):
				if len(colwidth) <= i:
					colwidth.append(0)
				if type(line[i]) != types.StringType:
					if line[i] == None:
						itemlen = 0
					else:
						itemlen = len(repr(line[i]))
				else:
					itemlen = len(line[i])
 				if itemlen > colwidth[i]:
					colwidth[i] = itemlen

                isHeader = False
		if header:
                        isHeader = True
			if 'output-header' in self._params:
				if not str2bool(self._params['output-header']):
					output = output[1:]
                                        isHeader = False

		# Allow the OUTPUT-COL command line parameter to be used to
		# filter the set of columns returned.  This is used to customize
		# output for easier parsing in shell scripts.  If you use it
		# consider using/creating a report command instead.  This will
		# only disable columns and will not change the order.  To use
		# just list the header names comma separated.  Even better,
		# don't use this.
		#
		# ex:
		#
		# $ stack list pallet output-col=name,version

		if header:
			if 'output-col' in self._params:
				cols = self._params['output-col'].split(',')
			else:
				cols = header
			outputCols = []
			for name in header[self.startOfLine:]:
				outputCols.append(name in cols)
		else:
			outputCols = None # actually means do everything
				

                o = ''
		for line in output:
			list = []
			for i in range(self.startOfLine, len(line)):
				if line[i] in [ None, 'None:' ]:
					s = ''
				else:
					s = str(line[i])
				if padChar != '':
					if s:
						o = s.ljust(colwidth[i])
					else:
						o = ''.ljust(colwidth[i],
							padChar)
				else:
					o = s
                                if isHeader:
                                        o = '%s%s%s' % (self.colors['bold']['code'],
                                                        o,
                                                        self.colors['reset']['code'])
				list.append(o)
			self.addText('%s\n' % self.outputRow(list, outputCols))
                        isHeader = False


	def outputRow(self, list, colmap=None):
		if colmap:
			filteredList = []
			for i in range(0, len(colmap)):
				if colmap[i]:
					filteredList.append(list[i])
			list = filteredList
		return string.join(list, ' ')
				
		
	def usage(self):
		if self.__doc__:
			handler = DocStringHandler()
			parser = make_parser()
			parser.setContentHandler(handler)
			try:
				parser.feed('<docstring>%s</docstring>' %
					self.__doc__)
			except:
				return '-- invalid doc string --'
			return handler.getUsageText(self.colors)
		else:
			return '-- missing doc string --'

		
	def help(self, command, flags={}):
		if not self.__doc__:
			return

		if self.MustBeRoot:
			users = [ 'root', 'apache' ]
		else:
			users = []
			
		if 'format' in flags:
			format = flags['format'].lower()
		else:
			format = 'plain'
		
		if format == 'raw':
			i = 1
			for line in self.__doc__.split('\n'):
				self.addText('%d:%s\n' % (i, line))
				i += 1
                                
		else:
			handler = DocStringHandler(command, users)
			parser = make_parser()
			parser.setContentHandler(handler)
			parser.feed('<docstring>%s</docstring>' % self.__doc__)
			if format == 'docbook':
				self.addText(handler.getDocbookText())
			elif format == 'parsed':
				self.addText(handler.getParsedText())
			elif format == 'sphinx':
				self.addText(handler.getSphinxText())
			elif format == 'md':
				self.addText(handler.getMarkDown())
			else:
				self.addText(handler.getPlainText(self.colors))


        def hasAccess(self, name):

                allowed = False
                gid     = os.getgid()
                groups  = os.getgroups()
                
                if gid not in groups:
                        # Installer has no supplemental groups so we need to
                        # include the default group.
                        # Outside the installer it is already in the
                        # supplemental list.
                	groups.append(gid)

                rows =  self.db.select('command, groupid from access')
                if rows:
                        for c,g in rows:
                        	if g in groups:
                        		if fnmatch.filter([ name ], c):
	                                	allowed = True
                else:

                        # If the access table does not exist fallback
                        # onto the previous MustBeRoot style access
                        # control.
                        #
                        # This is also the case for the installer.

                        if self.MustBeRoot:
                                if self.isRootUser() or self.isApacheUser():
                        		allowed = True
                        else:
                                allowed = True
                        
                return allowed

                        
	def runWrapper(self, name, argv, level=0):
		"""Performs various checks and logging on the command before 
		the run() method is called.  Derived classes should NOT
		need to override this."""

                username = pwd.getpwuid(os.geteuid())[0]

		self.level = level
		
		if argv:
			command = '%s %s' % (name, string.join(argv,' '))
		else:
			command = name

		global _logPrefix
		_logPrefix = ''
		for i in range(0, self.level):
			_logPrefix += '        '

		Log('user %s called "%s"' % (username, command))

		# Split the args and flags apart.  Args have no '='
		# with the exception of select statements (special case), and
		# flags have one or more '='.
		
		dict = {} # flags
		list = [] # arguments


		# Allow ad-hoc groups (e.g. [ rack == 0 ] ) to be split 
		# across several arguments, this prevents the need to
		# quote them into a single argument.
		#
		# We only do this when we find an argument and starts with
		# '['.  So the '[' character is safe anywhere else on the 
		# command line.  But if you start an argument with one it
		# need to be closed eventually.

		s = ''
		n = 0
		l = []
		ingroup = False
		for arg in argv:
			if not arg:
				continue

			if   arg[0] == '[' and arg[-1] != ']':
				s += '%s' % arg
				n += 1
				if n == 1:
					ingroup = True
			elif arg[0] != '[' and arg[-1] == ']':
				s += '%s' % arg
				n -= 1
				if n <= 0:
					l.append(s)
					ingroup = False
			elif ingroup:
				s += ' %s' % arg
			else:
				l.append(arg)
		argv = l

		# Convert the argument vector into a list of
		# arguments and a dictionary of parameters.
		# A parameter is a key=val string and an
		# argument is anything else.  Parameters can
		# be before, after, or even in between arguments.

		for arg in argv:
			if not arg:
				continue
			if arg[0] == '[': # ad-hoc group
				list.append(arg)
			elif len(arg.split('=',1)) == 2:
				(key, val) = arg.split('=', 1)
				dict[key] = val
			else:
				list.append(arg)

		if list and list[0] == 'help':
			self.help(name, dict)
		else:
                        if not self.hasAccess(name):
				raise CommandError(self, 'user "%s" does not have access "%s"' %
                                      (username, name))
			else:
				self._argv   = argv # raw arg list
				self._args   = list # required arguments
				self._params = dict # optional parameters

				rc = self.run(self._params, self._args)
				
				# if a command does not explicitly return
				# assume it succeeded, otherwise use the
				# actual return code.

				if rc is None:
					return True
				return rc


	def run(self, flags, args):
		"""All derived classes should override this method.
		This method is called by the stack command line as the
		entry point into the Command object.
		
		flags: dictionary of key=value flags
		args: list of string arguments"""
		
		pass



class Module:
	def __init__(self, command):
		self.owner = command
		self.db    = command.db

	def run(self, args):
		"""All derived classes should override this method. This
		is the entry point into the Plugin object."""
		pass


class Implementation(Module):
	"""Base class for all Stack command implementations."""
	pass

	
class Plugin(Module):
	"""Base class for all Stack command plug-ins."""
	
	def provides(self):
		"""Returns a unique string to identify the plug-in.  All
		Plugins must override this method."""

		return None
		
	def requires(self):
		"""Returns a list of plug-in identifiers that must be
		run before this Plugin.  This is optional for all 
		derived classes."""

		return []

	def precedes(self):
		"""Returns a list of plug-in identifiers that can only by
		run after this Plugin.  This is optional for all derived
		classes."""

		return []
		


class PluginOrderIterator(stack.graph.GraphIterator):
	"""Iterator for Partial Ordering of Plugins"""

	def __init__(self, graph):
		stack.graph.GraphIterator.__init__(self, graph)
		self.nodes = []
		self.time  = 0

	def run(self):
		stack.graph.GraphIterator.run(self)
		list = []
		self.nodes.sort()
		for time, node in self.nodes:
			list.append(node)
		list.reverse()
		return list

	def visitHandler(self, node, edge):
		stack.graph.GraphIterator.visitHandler(self, node, edge)
		self.time = self.time + 1

	def finishHandler(self, node, edge):
		stack.graph.GraphIterator.finishHandler(self, node, edge)
		self.time = self.time + 1
		self.nodes.append((self.time, node))

