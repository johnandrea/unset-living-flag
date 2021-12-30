# unset-living-flag
Modify RootsMagic database so that anyone with many descendant generations is set to non-living.

Please run initially on a test database or a copy of an operational database.

- Requires Python 3.6+
- RootsMagic version 7 and 8

## Usage ##
```
unset-living-flag.py  datafile.rmgc  >report.out
```

## Settings ## 
Within the program are variables for different operations:

Anyone with more than this many generations of descendants will have their "living" flag set to false.

OLDEST_GEN = 4

Set to false to prevent database changes.

MAKE_CHANGES = True

Show the genertion count for every person, ie. not just those being changed

PRINT_EVERY_PERSON = False
