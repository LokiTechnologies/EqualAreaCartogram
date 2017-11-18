# EqualAreaCartogram
A Python script that converts a Shapefile, GeoJSON, or CSV to an equal area cartogram SVG

### TL;DR
Convert Choropleths to Equal Area Hex Gridmaps.

_Dense hexmap_
![Dense Hexmap](https://raw.githubusercontent.com/rishsriv/equalareacartogram/master/demo_images/demo_dense.png "Dense Hexmap")

_Sparse hexmap_
![Sparse Hexmap](https://raw.githubusercontent.com/rishsriv/equalareacartogram/master/demo_images/demo_sparse.png "Sparse Hexmap")

### Usage
```python
from eqcart import Cartogram
#input_filepath can be the location of a GeoJSON, SHP, CSV, or Excel File
cart = Cartogram(input_filepath, name_of_column_w_unique_ids, num_x_grid, num_y_grid)
cart.make_hex_svg(output_filepath)
```

For more details on usage, see [this notebook](https://github.com/rishsriv/equalareacartogram/blob/master/Demo.ipynb)

### Input
The input file can be any of the following formats:
- CSV/Excel*
- SHP
- GeoJSON

\*if a csv or excel file is used as input, `latitude` and `longitude` columns that represent the latitude and longitude of each area must be present. If you do not know what the latitude and longitude of each area are, use this handy [Google Spreadsheets tool](https://chrome.google.com/webstore/detail/geocode-cells/pkocmaboheckpkcbnnlghnfccjjikmfc?hl=en) and export the end result as a CSV.

### Heuristic
For details on implementation, see [this notebook](https://github.com/rishsriv/equalareacartogram/blob/master/Under%20the%20hood.ipynb)

1. Get the x_coord (latitude) and y_coord (longitude) of each area 
2. Normalize the x_coords and y_coords to align all points into a rectangular grid with a length that width that you define. This will create a matrix that is something like the image below

![Pre-Shunt Grid](https://raw.githubusercontent.com/rishsriv/equalareacartogram/master/demo_images/grid_pre_shunt.png "Equal Area Cartogram UK")

3. If a bin (i.e., an x-y coordinate pair) has more than 1 point, select a point from the bin and shunt it to a neighbouring bin if neighbouring bin is empty. If no neighbouring bin is empty find a direction (up, down, left, or right) with the most proportion of empty spaces, shift all existing points in that direction by 1, and then move the selected point into that direction

4. Iterate 3. until all bins only have 1 point in them. This will lead to a matrix that is something like the image below
![Post-Shunt Grid](https://raw.githubusercontent.com/rishsriv/equalareacartogram/master/demo_images/grid_post_shunt.png "Post-Shunt Grid")

5. Convert the matrix obtained from point 4 into an SVG with hexagon polygons. The code for this is based on the excellent [chorogrid library](https://github.com/Prooffreader/chorogrid) by David Taylor.
![Hex Map](./demo_images/map.svg)

### Motivation
Choropleths fail to adequately highlight geographically small areas. This becomes particularly pertinent when covering elections, where each constituency has the same weight regardless of its geographical size. Equal area cartograms solve this problem, and have been used fairly effectively by a number of news organizations - as shown in the image below (taken from [Richard Brath's excellent blog] (https://richardbrath.wordpress.com/2015/10/15/equal-area-cartograms-and-multivariate-labels/))

![Equal Area Cartogram UK](https://raw.githubusercontent.com/rishsriv/equalareacartogram/master/demo_images/ukequalareatilemaps.png "Equal Area Cartogram UK")

However, making equal area cartograms can be a time consuming process - particularly for relatively obscure regions where well-designed SVGs of equal area cartograms are not easily available. While there is an [R implementation] (https://github.com/sassalley/hexmapr) for producing these, I could not find a Python implementation. Moreover, the R implementation above creates a contiguous map. This is advantageous for some situations, but can completely destroy resemblance to the real geography of an area for others.
