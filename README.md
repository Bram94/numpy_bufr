# numpy_bufr
A numpy-based and very efficient BUFR decoder. 

It is created with the aim to decode data from weather radars, provided by the DWD in BUFR format. The structure of the decoder is however such that it should be able to decode many types of BUFR files.
This might however require adding support for other BUFR operators, as this package currently supports only the minimum amount of operators that is required to decode the DWD radar files.

Because the decoder expands the data into an array of bits (stored in uint8 format), its use of memory is not efficient. Memory usage will be at least 8 times larger than that required to open the file. This is something to take into account when you want to decode very large files.

The folder 'examples' contains an example script for decoding DWD radar data.
