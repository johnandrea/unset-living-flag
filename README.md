# unset-living-flag
Modify RootsMagic database so that anyone with many descendant generations is set to non-living.

Please run initially on a test database or a copy of an operational database.

- Requires Python 3.6+
- RootsMagic version 7 and 8

## Usage ##
```
unset-living-flag.py  datafile.rmgc  >report.out
```

## Options ## 

--max-gen MAXGEN
Anyone with more than this many generations of descendants will have their "living" flag set to false.

--dry-run
Do not change the database.

--verbose
Show the genertion count for every person, ie. not just those being changed
