# -*- coding: utf-8 -*-
"""
Created on Sat Feb 10 12:04:20 2018

@author: bramv
"""
import gzip
import bz2
import numpy as np

from . import decode_metadata
from .tables import load_tables
from .tables.tables import get_descr_full
from . import bufr_functions as bf



"""This is a very efficient numpy-based decoder for BUFR files. It is aimed at decoding volumetric radar data provided by the DWD, but it should be 
sufficiently general to handle much more formats. It works at least for edition 3, but is also expected to work with edition 4.
Two things that are at least not yet supported, are BUFR files with multiple subsets in section 4, and a section 2 in the BUFR file. If a section 2
is present, then it is simply skipped (but the decoding of the other sections should still succeed).
Further, only a few operators are supported yet, but it shouldn't be that difficult to include support for more operators.
Also, compression within the BUFR file is not handled yet.

Decoding of the BUFR starts by converting the content to a 1D array of bits (uint8 type, implying that 8 times more memory is used than originally).
Next, the meta data is obtained, which includes a list of the descriptors that are present in section 4. 
When decoding section 4, which contains the data, one important reason for the efficiency of the decoder is the way in which loops (indicated by replication
operators) are treated: 
    First, the size of the data that is contained in the loop in determined, which is the number of bits contained in the loop.
Next the data for each loop (and possible nested loops) is put in a different array, which is reshaped in such a way that the last dimension includes the
descriptors for one iteration of the loop. This allows efficient slicing of the data when actually decoding it, which is the final step.

A drawback of this method is that it is not very memory efficient, among others because the BUFR is converted to an array of bits (as mentioned above), but
also because the data for each nested loop is stored in a different array (see the function get_bits_in_loops). If memory usage becomes important, then the first
step to reduce memory usage should likely be finding a more efficient way to store data for different nested loops.

A DWD-specific piece of code decompresses bz2-compressed data. If other types of compression are carried out, then the appropriate decompression must be included.


Part of the code is based on/ copied from the package trollbufr, created by Alex Maul: https://github.com/alexmaul/trollbufr
That's completely the case for the script load_tables, and for a large part for the script decode_metadata.
"""
class DecodeBUFR():
    def __init__(self, table_path, table_type = 'eccodes'): 
        """table_type must be one of 'eccodes' and 'libdwd'.
        table_path is the path to the tables.
        """
        self.table_path = table_path
        self.table_type = table_type
        
        self.tables = None
    
    
    
    def __call__(self, filepath, table_path = None, table_type = None, read_mode='all'):
        """Returns the meta data contained in the BUFR, a full description of the data descriptors, the decoded data, and the decoded data for descriptors 
        that are included inside loops.
        The read_mode specifies which part of the BUFR is decoded. It can be one 'all','outside_loops', or a list with descriptors. 
        read_mode='all' means that the whole file is decoded, and read_mode='outside_loops' means that only the part of the data that is 
        located outside loops is decoded. This can be useful when only some information about the data is needed, and not the data itself.
        If you provide a list of descriptors for read_mode, then inside loops only data for these descriptors will be decoded. 
        """
        #If you want to overwrite the default table path and type, specified during the initialization of the class, then table_path and table_type
        #should differ from None.
        if not table_path is None: self.table_path = table_path
        if not table_type is None: self.table_type = table_type
        self.read_mode = read_mode
              
        with open(filepath, 'rb') as f:
            self.content = f.read()
        if filepath.endswith('.bz2'):
            self.content = bz2.decompress(self.content)
    
        uints = bf.bytes_to_array(self.content)
        self.data_bits=np.unpackbits(uints)
        
        self.get_metadata_and_divide_BUFR_into_sections()
        
        self.load_tables()
        self.replace_sequence_descriptors()
        
        self.get_full_description()
        
        self.decode_section4()
        return self.metadata, self.full_description, self.data, self.data_loops
        
        
        
    
        
    def get_metadata_and_divide_BUFR_into_sections(self):
        """Divide the BUFR into sections
        """
        n = self.content.index(b'BUFR')*8 #Starting point of the BUFR message, is apparently not always zero
        
        sections_metadata = (0, 1, 3) #Sections from which metadata needs to be retrieved
        self.metadata = {}
        self.sec_lengths = {0:64,5:32} #In number of bits
        self.secs = {}
        for j in range(6): #Section 2 is not present
            if j==2 and self.metadata['sect2']==0: 
                continue #Section 2 is not present in this case
            
            if not j in self.sec_lengths:
                self.sec_lengths[j] = bf.bits_to_n(self.data_bits[n:n+24])*8 #Section lengths are always given in 24 bits
            self.secs[j] = self.data_bits[n:n+self.sec_lengths[j]]
            
            n += self.sec_lengths[j]
            
            if j in sections_metadata:
                if j==0: self.metadata.update(decode_metadata.decode_sect0(self.secs[j]))
                if j==1: self.metadata.update(decode_metadata.decode_sect1(self.secs[j], self.metadata['edition']))
                if j==3: self.metadata.update(decode_metadata.decode_sect3(self.secs[j], self.sec_lengths[j]))
                
    def get_full_description(self):
        #The widths stated in the full description are those given in table B, which might not be the actual data widths, if they are modified by operators.
        self.full_description = get_descr_full(self.tables,self.metadata['descr'])

    def load_tables(self):
        """Load the self.tables that are required to interpret the self.data descriptors, and to decode the self.data in section 4
        """
        self.tables = load_tables.load_differ(self.tables,self.metadata,self.table_path,self.table_type)

    def replace_sequence_descriptors(self):
        """Replace sequence descriptors (those for which the first digit (F) is 3) by the sequence of descriptors that they represent, which are 
        given in table D
        """
        while any([i.startswith('3') for i in self.metadata['descr']]):
            new_descr = []
            for i in self.metadata['descr']:
                if i[0]=='3':
                    descr_sequence = self.tables.tab_d[int(i)]
                    for j in descr_sequence:
                        new_descr.append(format(j, '06'))
                else:
                    new_descr.append(i)
            self.metadata['descr'] = new_descr.copy()

        
                
    def decode_section4(self): 
        """Here the decoding of section 4 of the BUFR takes place, which contains the data. The decoding is dictated by the list with descriptors given in
        self.metadata['descr']. These descriptors consists of 6 digits, and have the FXY format. Here, F is given by the first digit, and represents the
        type of descriptor. X is given by the next 2 digits, and represent the class of the descriptor. Y is given by the final 3 digits, and represents the
        number of the descriptor within that class.
        
        If F==1, then the descriptor is a replication operator, implying that a loop is present. The way in which loops are handled is important for the 
        efficiency of the decoder, and finding a good method is not so easy, especially since nested loops can be present.
        Here loops are handled by first determining info over the number of iterations, size of the loop, and some other parameters, whereafter the data
        in each loop is isolated from the rest. This data is reshaped in such a way (function self.get_bits_in_loops) that the last dimension contains the 
        data for one iteration of the loop. This allows efficient slicing when decoding the data in the loop.
        Nested loops are handled by assigning to each (nested) loop a different loop ID, and repeating a similar treatment for all nested loops.
        ID=0 refers to the 1D array with all bits from section 4.
        """
        self.bits = {0:self.secs[4]} #Contains all bits from section 4 that are included in the loop, reshaped into a (i+1)-dimensional array.
        self.start_descr = {0:0} #Contains the start index of the first descriptor in the loop, i.e. the index of that descriptor in self.metadata['descr']
        self.start_n = {0:0} #Contains for each loop the bit index at which it starts, where the value for loop i refers to the last dimension in 
        #self.bits[i-1].
        self.n_descr = {0:len(self.metadata['descr'])} #Number of descriptors included in the loop, excluding a possible delayed replication descriptor that
        #describes the number of descriptors immediately after the loop operator.
        self.loopdescr_widths = {} #Data width (in bits) of the delayed replication descriptors that give the number of loop iterations. Is zero if not present.
        self.d_indices = {0:0} #Descriptor indices for the list self.metadata['descr']
        self.n_it = {0:1} #Number of iterations per loop
        self.n_bits = {0:len(self.secs[4])} #Number of bits in a loop, excluding bits used for a possible delayed replication descriptor.
        self.loop_parameters = [self.bits, self.start_descr, self.start_n, self.n_descr, self.loopdescr_widths, self.d_indices, self.n_it, self.n_bits]
        
        self.base_loop_i = 1 #A base loop is defined as a complete series of nested loops, from the outer most one to the inner most one. For each base loop,
        #the data for the descriptors that are present in the loop is stored in the dictionary self.data_loops[self.base_loop_i].
        self.n = 32 #Bit index for the 1D array self.secs[4]. The first 4 octets in self.secs[4] are not used to represent data
        
        self.data = {} #Contains data for descriptors that are not placed in loops. The data for each descriptor is put in a list, because a descriptor might
        #be listed more than once in self.metadata['descr']
        self.data_loops = {self.base_loop_i:{}} #Contains data for descriptors that are contain in loops. This data is not put in self.data, because
        #it was found that some descriptors appear both inside and outside a loop, where the value outside the loop might be an average of values
        #inside the loop.
        
        self.redefining_refval = False; self.redefining_refval_width = 0
        self.widths = {}; self.scales = {}; self.refvals = {}
        self.add_width = 0; self.add_scale = 0
        while True:
            d = self.metadata['descr'][self.d_indices[0]]; d_int = int(d)
                         
            if d[0]=='0':
                if not d in self.data: self.data[d] = []
                
                self.decode_element_descriptor(d, d_int)
                self.d_indices[0] += 1
                
            elif d[0]=='1': 
                """First get information about the loop, including its size, before decoding the data.
                """
                self.get_loop_info(1, d, d_int)
                if self.read_mode!='outside_loops':
                    self.get_bits_in_loops() #Obtain the (i+1)-dimensional array that contains all data present in the loop, where i refers to the loop index.
                    self.decode_data_in_loops()
                
                self.d_indices[0] += self.n_descr[1] + 1 + (1 if self.loopdescr_widths[1]>0 else 0)
                self.n = self.start_n[1]+self.n_bits[1]
                
                for i in self.loop_parameters:
                    #Remove all keys in the dictionaries that refer to values for the loops. This is necessary when there exists more
                    #than one loop (i.e. more than one 'base' loop, excluding nested loops), to prevent that values for the previous 
                    #loop(s) are used.
                    for j in list(i.keys()):
                        if j>0:
                            del i[j]
                            
                self.base_loop_i += 1
                self.data_loops[self.base_loop_i] = {}
                                    
            elif d[0]=='2':
                self.evaluate_operator(d) 
                self.d_indices[0] += 1
                
            if self.d_indices[0]==self.n_descr[0]:
                break
                
                                        
    
    def decode_element_descriptor(self, d, d_int, decode_data=True):
        if not self.redefining_refval:
            #In this case the descriptor represents an element
            typ = self.tables.tab_b[d_int].typ
            self.widths[d] = self.tables.tab_b[d_int].width + self.add_width
            self.scales[d] = self.tables.tab_b[d_int].scale + self.add_scale
            if not d in self.refvals:
                #Prevent that a redefined reference value gets overwritten
                self.refvals[d] = self.tables.tab_b[d_int].refval
            
            if decode_data:
                bits = self.secs[4][self.n:self.n+self.widths[d]]
                if np.all(bits==1):
                    #This usually indicates that the value is missing
                    self.data[d].append(None)
                else:     
                    if typ=='string':
                        str_bytes = np.packbits(bits)
                        self.data[d].append(str(str_bytes[str_bytes>0],'utf-8'))
                    else:
                        self.data[d].append((bf.bits_to_n(bits)+self.refvals[d])/10**self.scales[d])
                    
            self.n += self.widths[d]
        else:
            #Redefine the reference value
            self.refvals[d] = bf.bits_to_n(self.secs[4][self.n:self.n+self.redefining_refval_width],signed=True)
                
            self.n += self.redefining_refval_width
            
            
    def evaluate_operator(self, d):
        """In this case the descriptor represents an operator. 
        See the file operator.TABLE in the table directory for their interpretation.
        """
        if d[1:3]=='01':
            #Change self.add_width
            self.add_width = 0 if d[3:]=='000' else int(d[3:])-128
        elif d[1:3]=='02':
            #Change self.add_scale
            self.add_scale = 0 if d[3:]=='000' else int(d[3:])-128
        elif d[1:3]=='03':
            if d[3:]!='255':
                self.redefining_refval = True                
                self.redefining_refval_width = int(d[3:])
            else:
                self.redefining_refval = False
                
                
    def get_loop_info(self, i, d, d_int):
        """In the loop operator (FXY), X gives the number of descriptors that is included in the loop, 
        i.e. '110000' means that 10 descriptors are included. Y gives the the number of iterations in the loop, 
        and is zero when this number is set by a delayed descriptor of the format '031YYY'.
       
        This function determines the number of descriptors involved in the loop, the number of iterations, the total number
        of bits involved in the loop, and a few other required parameters. These include the index of the first descriptor in the loop
        for the list self.metadata['list'], the number of bits used for a possible delayed replication descriptor, and self.start_n,
        which gives for a loop i the index of the first bit contained in the loop, relative to the last dimension of self.bits[i-1].

        Further, also the width, scale and refval of the descriptor are determined in this process, such that this does not need to
        be done anymore in the function self.decode_data_in_loops.
        
        A loop can contain nested loops, and if such a nested loop is encountered, then this function is simply called again from within this function,
        with i increased by 1.
        """        
        
        self.n_descr[i] = int(d[1:3])
        self.start_descr[i] = self.d_indices[i-1]+1 if d[3:]!='000' else self.d_indices[i-1]+2
        #A possible delayed replication descriptor is not included in the number of descriptors inside the loop
        
        if d[3:]=='000':
            #Get the number of iterations from the delayed descriptor
            delayed_descr = self.metadata['descr'][self.d_indices[i-1]+1]
            self.loopdescr_widths[i] = self.tables.tab_b[int(delayed_descr)].width
            self.n_it[i] = bf.bits_to_n(self.secs[4][self.n:self.n+self.loopdescr_widths[i]])
        else:
            self.n_it[i] = int(d[3:])
            self.loopdescr_widths[i] = 0
        self.n += self.loopdescr_widths[i]
        
        self.start_n[i] = self.n if i==1 else self.n-np.sum([self.start_n[j] for j in self.start_n if j<i])
        
        
        self.d_indices[i] = self.start_descr[i]
        while True:  
            d = self.metadata['descr'][self.d_indices[i]]; d_int = int(d)
            
            if d[0]=='0':
                self.decode_element_descriptor(d, d_int, decode_data=False)
                self.d_indices[i] += 1
                
            elif d[0]=='1':
                """First get information about the number of descriptors in the loop, the number of iterations and the total number
                of bits that is involved in the loop, before proceeding.
                """
                self.get_loop_info(i+1, d, d_int)
                self.d_indices[i] += self.n_descr[i+1] + (2 if d[3:]=='000' else 1)
                self.n += int(self.n_bits[i+1]*(1-1/self.n_it[i+1]))
                #Add the number of bits contained in the inner loop(s). Correct for the fact that the first iteration of the inner loop
                #was already added to self.n
                                 
            elif d[0]=='2':
                self.evaluate_operator(d)
                self.d_indices[i] += 1
                
            if self.d_indices[i]-self.start_descr[i]==self.n_descr[i]:
                break
                
        self.n_bits[i] = (self.n-np.sum([self.start_n[j] for j in self.start_n if j<=i]))*self.n_it[i]
        
    def get_bits_in_loops(self):
        """Isolate the bits that are present in a (nested) loop, and reshape them in an (i+1)-dimensional array, where i is the loop ID.
        """
        for i in self.start_n:
            if i==0: continue
        
            new_shape = self.bits[i-1].shape[:-1]+(self.n_it[i],int(self.n_bits[i]/self.n_it[i]))
            self.bits[i] = np.reshape(self.bits[i-1][...,self.start_n[i]:self.start_n[i]+self.n_bits[i]], new_shape)
            
    def decode_data_in_loops(self):
        """Decode the data that is present in the loops. The data for each descriptor has a dimensionality that is 1 lower than the dimensionality of the
        loop in which it resides, because during the decoding process, summation takes place over the last dimension.
        """
        for i in self.bits:
            if i==0: continue
            n = 0
            
            d_list = self.metadata['descr'][self.start_descr[i]:self.start_descr[i]+self.n_descr[i]]
            for d in d_list:
                d_int = int(d)
                
                if d[0]=='0' and not d[:3]=='031': #Prevent the evaluation of delayed replication operators
                    
                    if isinstance(self.read_mode,str) or d in self.read_mode:
                        #if self.read_mode is not a string, then it should be a list with descriptors for which data should be decoded.
                        typ = self.tables.tab_b[d_int].typ
                        if typ=='string':
                            raise Exception('Decoding strings in loops is not (yet) supported')
                        else:
                            self.data_loops[self.base_loop_i][d] = (bf.bits_to_n(self.bits[i][...,n:n+self.widths[d]])+self.refvals[d])/10**self.scales[d]
                            
                    n += self.widths[d]
                        
                elif d[0]=='1':
                    #Skip the bits that belong to the loop, because they are treated when treating the next loop
                    #Also skip the bits for a possible delayed replication descriptor
                    n += self.n_bits[i+1] + self.loopdescr_widths[i+1] 
                    
                """No evaluation of operators is required anymore, because the width, scale and refval have already been determined
                during evaluation of the function self.get_loop_info.
                """