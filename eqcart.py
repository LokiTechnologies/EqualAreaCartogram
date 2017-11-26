import geopandas as gpd
import pandas as pd
from chorogrid import Chorogrid
from bs4 import BeautifulSoup
import json

class Cartogram(object):
    """ An object which makes equal-area hexgrid cartograms, instantiated with:
            input_fname: the path to a csv, excel, geojson, or shp file
            id_col: a unique attribute/column in the input file that will be used as the id of an SVG
            num_x_grid: the width of the hexgrid
            num_y_grid: the height of the hexgrid

        Methods (introspect to see arguments)
           make_hex_svg: make choropleth

           done: save and/or display the result in IPython notebook
           done_with_overlay: overlay two Chorogrid objects
    """

    def __init__(self, input_fname, id_col, num_x_grid, num_y_grid):
        self.df = self.read_file(input_fname)
        assert id_col in self.df.columns, ("{} is not a column in {}".format(id_col, input_fname))
        self.index_col = id_col
        self.num_x_grid = num_x_grid
        self.num_y_grid = num_y_grid
        self.coord_points = {}
        self.x_coords_points = {}
        self.y_coords_points = {}
        self.point_position = {}

        if "latitude" not in self.df.columns or "longitude" not in self.df.columns:
            self.df['centroid'] = self.df['geometry'].apply(lambda x: x.centroid)
            self.df['longitude'] = self.df['centroid'].apply(lambda x: x.coords.xy[0][0])
            self.df['latitude'] = self.df['centroid'].apply(lambda x: x.coords.xy[1][0])
        self.max_longitude = self.df['longitude'].max()
        self.max_latitude = self.df['latitude'].max()
        self.min_longitude = self.df['longitude'].min()
        self.min_latitude = self.df['latitude'].min()

    # methods called from within methods, beginning with underscore
    def _initialize_grid(self):
        # initializes the grid
        assert (self.num_x_grid * self.num_y_grid) > self.df.shape[0], "Too few dimensions"
        xmax, xmin = self.df['longitude'].max(), self.df['longitude'].min()
        ymax, ymin = self.df['latitude'].max(), self.df['latitude'].min()
        x_range = xmax - xmin
        y_range = ymax - ymin

        self.df["x_bin"] = self.df["longitude"].apply(lambda x: int(self.num_x_grid * (x - xmin) / x_range))
        self.df["y_bin"] = self.df["latitude"].apply(lambda y: int(self.num_y_grid * (ymax - y) / y_range))

    def read_file(self, fname):
        if fname.endswith(".csv"):
            df = pd.read_csv(fname)
        elif fname.endswith(".xls") or fname.endswith(".xlsx"):
            df = pd.read_excel(fname)
        else:
            try:
                df = gpd.read_file(fname)
            except Exception as e:
                raise Exception(e)
        return df

    def _is_valid(self):
        # checks is any square in the grid has more than 1 point assigned to it
        for coord in self.coord_points:
            if len(self.coord_points[coord]) > 1:
                return False
        return True

    def _delete_old_point(self, x, y, ac_to_shunt):
        # deletes a point from the grid
        self.coord_points[str(x) + "_" + str(y)].remove(ac_to_shunt)
        self.x_coords_points[x].remove(ac_to_shunt)
        self.y_coords_points[y].remove(ac_to_shunt)

    def _update_new_point(self, x, y, ac_to_shunt):
        # adds a point to the grid
        self.point_position[ac_to_shunt] = {"x_bin": x, "y_bin": y}
        if str(x) + "_" + str(y) not in self.coord_points:
            self.coord_points[str(x) + "_" + str(y)] = []
        self.coord_points[str(x) + "_" + str(y)].append(ac_to_shunt)
        if x not in self.x_coords_points:
            self.x_coords_points[x] = []
        self.x_coords_points[x].append(ac_to_shunt)

        if y not in self.y_coords_points:
            self.y_coords_points[y] = []
        self.y_coords_points[y].append(ac_to_shunt)

    def _shunt_point(self, coord):
        # moves a point in the grid
        x, y = coord.split('_')
        ac_to_shunt = self.coord_points[coord][1]
        x = int(x)
        y = int(y)

        # check if a neighbouring bin is empty and move to neighbouring bin
        for point in [(min(x + 1, self.num_x_grid), y), (min(x + 1, self.num_x_grid), min(y + 1, self.num_y_grid)),
                      (min(x + 1, self.num_x_grid), max(0, y - 1)),
                      (max(0, x - 1), y), (max(0, x - 1), min(y + 1, self.num_y_grid)), (max(0, x - 1), max(0, y - 1)),
                      (x, min(y + 1, self.num_y_grid)), (x, max(0, y - 1))]:
            if len(self.coord_points.get(str(point[0]) + "_" + str(point[1]), [])) == 0:
                # delete old point
                self._delete_old_point(x, y, ac_to_shunt)

                # add new point
                self._update_new_point(point[0], point[1], ac_to_shunt)
                return

        # move to a neighbouring bin in the direction that is most sparse
        prop_x_plus_empty = 1. * len(
            [i for i in range(x + 1, 51) if len(self.coord_points.get(str(i) + "_%d" % y, [])) == 0]) / (
                                self.num_x_grid - x) if x != self.num_x_grid else 0
        prop_x_minus_empty = 1. * len(
            [i for i in range(x - 1, -1, -1) if len(self.coord_points.get(str(i) + "_%d" % y, [])) == 0]) / (
                                 x) if x != 0 else 0

        prop_y_plus_empty = 1. * len(
            [i for i in range(y + 1, 41) if len(self.coord_points.get("%d_" % x + str(i), [])) == 0]) / (
                                self.num_y_grid - y) if y != self.num_y_grid else 0
        prop_y_minus_empty = 1. * len(
            [i for i in range(y - 1, -1, -1) if len(self.coord_points.get("%d_" % x + str(i), [])) == 0]) / (
                                 y) if y != 0 else 0

        self._delete_old_point(x, y, ac_to_shunt)
        if prop_x_plus_empty is max(prop_x_plus_empty, prop_x_minus_empty, prop_y_plus_empty, prop_y_minus_empty):
            for idx in range(x + 1, 51)[::-1]:
                if str(idx) + "_" + str(y) in self.coord_points:
                    for ac in self.coord_points[str(idx) + "_" + str(y)]:
                        self._delete_old_point(idx, y, ac)
                        self._update_new_point(min(idx + 1, self.num_x_grid), y, ac)

            self._update_new_point(min(x + 1, self.num_x_grid), y, ac_to_shunt)
            return
        if prop_x_minus_empty is max(prop_x_plus_empty, prop_x_minus_empty, prop_y_plus_empty, prop_y_minus_empty):
            for idx in range(x - 1, -1, -1)[::-1]:
                if str(idx) + "_" + str(y) in self.coord_points:
                    for ac in self.coord_points[str(idx) + "_" + str(y)]:
                        self._delete_old_point(idx, y, ac)
                        self._update_new_point(max(idx - 1, 0), y, ac)

            self._update_new_point(max(x - 1, 0), y, ac_to_shunt)
            return
        if prop_y_plus_empty is max(prop_x_plus_empty, prop_x_minus_empty, prop_y_plus_empty, prop_y_minus_empty):
            for idx in range(y + 1, 41)[::-1]:
                if str(x) + "_" + str(idx) in self.coord_points:
                    for ac in self.coord_points[str(x) + "_" + str(idx)]:
                        self._delete_old_point(x, idx, ac)
                        self._update_new_point(x, min(idx + 1, self.num_y_grid), ac)

            self._update_new_point(x, min(y + 1, self.num_y_grid), ac_to_shunt)
            return
        if prop_y_minus_empty is max(prop_x_plus_empty, prop_x_minus_empty, prop_y_plus_empty, prop_y_minus_empty):
            for idx in range(y - 1, -1, -1)[::-1]:
                if str(x) + "_" + str(idx) in self.coord_points:
                    for ac in self.coord_points[str(x) + "_" + str(idx)]:
                        self._delete_old_point(x, idx, ac)
                        self._update_new_point(x, max(idx - 1, 0), ac)

            self._update_new_point(x, max(y - 1, 0), ac_to_shunt)
            return

    def _populate_new_grid(self):
        # shifts points in the grid such that no x, y pair in the grid has more than 1 point, while maintaining geographic resemblance
        self.point_position = self.df.set_index(self.index_col)[['x_bin', 'y_bin']].to_dict(orient='index')

        for point in self.point_position:
            if self.point_position[point]['x_bin'] not in self.x_coords_points:
                self.x_coords_points[self.point_position[point]['x_bin']] = []
            if self.point_position[point]['y_bin'] not in self.y_coords_points:
                self.y_coords_points[self.point_position[point]['y_bin']] = []
            self.x_coords_points[self.point_position[point]['x_bin']].append(point)
            self.y_coords_points[self.point_position[point]['y_bin']].append(point)

        for point, value in self.point_position.iteritems():
            if (str(value["x_bin"]) + "_" + str(value["y_bin"])) not in self.coord_points:
                self.coord_points[str(value["x_bin"]) + "_" + str(value["y_bin"])] = []
            self.coord_points[str(value["x_bin"]) + "_" + str(value["y_bin"])].append(point)

        while not self._is_valid():
            coord_to_shunt_from = max(self.coord_points, key=lambda x: len(self.coord_points[x]))
            ac_to_shunt = self.coord_points[coord_to_shunt_from][1]
            self._shunt_point(coord_to_shunt_from)

        self.df['hex_x'] = self.df[self.index_col].apply(lambda x: self.point_position[x]["x_bin"])
        self.df['hex_y'] = self.df[self.index_col].apply(lambda x: self.point_position[x]["y_bin"])

    def make_hex_svg(self, output_fname=None, show=False, draw_text=False):
        """ Outputs an SVG file of the hexgrid
            output_fname: the outputfilepath
            show: whether or not the output should be displayed in the ipython notebook
            draw_text: whether or not the id_col text should be drawn on the map
        """
        self._initialize_grid()
        self._populate_new_grid()
        cg = Chorogrid(self.df, self.df[self.index_col].tolist(), ['#eeeeee'] * len(self.df), id_column=self.index_col)
        cg.draw_hex(draw_text=draw_text)
        cg.done(save_filename=output_fname, show=show)
        self.total_width = cg.total_width
        self.total_height = cg.total_height
        self.svgstring = cg.svgstring
        return

    def _convert_coord_to_latlong(self, point):
        #converts the coordinate system to an approximate lat-long system
        #works fairly well for areas that are around the size of Europe, but not too well for larger areas
        point = [[float(j) for j in i.split(",")] for i in point]
        point = [[self.min_latitude + (self.max_latitude - self.min_latitude)*(i[0])/self.total_height,
                  self.min_longitude + (self.max_longitude - self.min_longitude)*(1.*self.total_width - i[1])/(self.total_width)] for i in point]
        return point

    def make_hex_geojson(self, output_fname):
        self.make_hex_svg()
        dom = BeautifulSoup(self.svgstring, "lxml")
        polygons = dom.findAll("polygon")
        features = []
        for polygon in polygons:
            features.append({"geometry": {
                "type": "Polygon",
                "coordinates": [self._convert_coord_to_latlong(polygon.attrs['points'].split())]
            },
            "type": "Feature",
            "id": polygon.attrs["id"],
            "properties": {}
        })
        
        geojson_dict = {"type": "FeatureCollection", "features": features}
        with open(output_fname, "wb") as f:
            json.dump(geojson_dict, f)