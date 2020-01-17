This repo contains the programming assignment for Chris Pyatt and Simon Lam.

The repo contains 6 files. The main program is parser.py which pulls data from a given list of APIs and displays trends over time. There are also two test CSVs for testing without internet connection, this README, and a Jupyter notebook that runs the stats analysis separately. If needed, there is also a .sh file listing all the dependencies needed for this script, to aid installation.

======

## Parser.py 

------

Run a test with:

  python parser.py --test
  
or

  python parser.py --testOffline
  
------

Otherwise, supply an input dataset using the [-i] option, a column variable to plot on the x axis with [-x], another for the y axis with [-y], and one by which to group the data (e.g. by practice) with [-g]. You may also choose which graphs to plot and display, using the [--plots] option.

Use the [-h] option for more info.
