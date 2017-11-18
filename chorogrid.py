#!/usr/bin/python
#This is a modified version of a file from David Taylor's excellent chorogrid library
#The original library is hosted at https://github.com/Prooffreader/chorogrid

import xml.etree.ElementTree as ET
import pandas as pd
import re
from math import sqrt
from IPython.display import SVG, display

class Chorogrid(object):
    def __init__(self, df, ids, colors, id_column='abbrev'):
        self.df = df
        comparison_set = set(self.df[id_column])
        invalid = set(ids).difference(comparison_set)
        missing = comparison_set.difference(set(ids))
        if len(invalid) > 0:
            print('WARNING: The following are not recognized', ' ids: {}'.format(invalid))
        if len(missing) > 0:
            print('WARNING: The following ids in the csv are not ', 'included: {}'.format(missing))
        self.colors = list(colors)
        self.ids = list(ids)
        self.svglist = []
        assert id_column in self.df.columns, ("{} is not a column in"
            " {}".format(id_column, csv_path))
        self.id_column = id_column
        self.df[id_column] = self.df[id_column].astype(str)
        self.title = ''
        self.additional_svg = []
        self.additional_offset = [0, 0]
        
    def _update_default_dict(self, default_dict, dict_name, kwargs):
        if dict_name in kwargs.keys():
            kwarg_dict = kwargs[dict_name]
            for k, v in kwarg_dict.items():
                assert k in default_dict.keys(), ("kwarg {} specified invalid"
                    " key".format(dict_name))
                if k == 'font-size' and type(k) is int:
                    default_dict[k] = str(v) + 'px'
                else:
                    default_dict[k] = v
        return default_dict
    def _dict2style(self, dict_):
        to_return = []
        for k,v in dict_.items():
            to_return.append(k + ':' + str(v) + ';')
        to_return[-1] = to_return[-1][:-1]
        return ''.join(to_return)
    def _make_svg_top(self, width, height):
        self.svg = ET.Element('svg', xmlns="http://www.w3.org/2000/svg", 
            version="1.1", viewbox="0 0 %s %s"%(width, height))
        
    def _draw_title(self, x, y):
        if len(self.title) > 0:
            font_style = self._dict2style(self.title_font_dict)
            _ = ET.SubElement(self.svg, "text", id="title", x=str(x),  y=str(y), style=font_style)
            _.text = self.title
    def _determine_font_colors(self, kwargs):
        if 'font_colors' in kwargs.keys():
            fc = kwargs['font_colors']
            if type(fc) is str:
                font_colors = [fc] * len(self.ids)
            elif type(fc) is list:
                font_colors = fc
            elif type(fc) is dict:
                font_colors = [fc[x] for x in self.colors]
        else:
            font_colors = ['#000000'] * len(self.ids)
        return font_colors
    def _calc_hexagon(self, x, y, w, true_rows):
        if true_rows:
            h = w/sqrt(3)
            return "{},{} {},{} {},{} {},{} {},{} {},{}".format(
              x, y, x+w/2, y-h/2, x+w, y, x+w, y+h, x+w/2, y+1.5*h, x, y+h)
        else:
            ww = w/2
            hh = w * sqrt(3) / 2
            return "{},{} {},{} {},{} {},{} {},{} {},{}".format(
              x, y, x+ww, y, x+ww*3/2, y-hh/2, x+ww, y-hh, x, y-hh, x-ww/2, y-hh/2)
            
    def done_and_overlay(self, other_chorogrid, show=True, save_filename=None):
        svgstring = ET.tostring(self.svg).decode('utf-8')
        svgstring = svgstring.replace('</svg>', ''.join(self.additional_svg) + '</svg>')
        svgstring = svgstring.replace(">", ">\n")
        svgstring = svgstring.replace("</svg>", "")
        svgstring_overlaid = ET.tostring(other_chorogrid.svg).decode('utf-8')
        svgstring_overlaid = svgstring_overlaid.replace('</svg>', 
                                 ''.join(other_chorogrid.additional_svg) + '</svg>')
        svgstring_overlaid = svgstring_overlaid.replace(">", ">\n")
        svgstring_overlaid = re.sub('<svg.+?>', '', svgstring_overlaid)
        svgstring += svgstring_overlaid
        if save_filename is not None:
            if save_filename[-4:] != '.svg':
                save_filename += '.svg'
            with open(save_filename, 'w+', encoding='utf-8') as f:
                f.write(svgstring)
        if show:
            display(SVG(svgstring))
            
    def done(self, show=False, save_filename=None):
        svgstring = ET.tostring(self.svg).decode('utf-8')
        svgstring = svgstring.replace('</svg>', ''.join(self.additional_svg) + '</svg>')
        svgstring = svgstring.replace(">", ">\n")
        if save_filename is not None:
            if save_filename[-4:] != '.svg':
                save_filename += '.svg'
            with open(save_filename, 'wb') as f:
                f.write(svgstring.encode("utf-8"))
        if show is True:
            display(SVG(svgstring))
   
    def draw_hex(self, draw_text=False, x_column='hex_x', y_column='hex_y', true_rows=True, **kwargs):
        font_dict = {'font-style': 'normal', 'font-weight': 'normal', 'font-size': '10px', 
                     'line-height': '125%', 'text-anchor': 'middle', 'font-family': 'sans-serif', 
                     'letter-spacing': '0px', 'word-spacing': '0px', 'fill-opacity': 1, 
                     'stroke': 'none', 'stroke-width': '1px', 'stroke-linecap': 'butt', 
                     'stroke-linejoin': 'miter', 'stroke-opacity': 1}
        spacing_dict = {'margin_left': 10, 'margin_top': 10, 'margin_right': 10,  'margin_bottom': 10,  
                        'cell_width': 15, 'title_y_offset': 0, 'name_y_offset': 0, 'roundedness': 3,  
                        'stroke_width': 0, 'stroke_color': '#ffffff', 'missing_color': '#a0a0a0', 
                        'gutter': 1, 'missing_font_color': '#000000'}
        
        font_dict = self._update_default_dict(font_dict, 'font_dict', kwargs)
        spacing_dict = self._update_default_dict(spacing_dict, 
                                                 'spacing_dict', kwargs)
        font_colors = self._determine_font_colors(kwargs)
        font_style = self._dict2style(font_dict)
        if true_rows:
            total_width = (spacing_dict['margin_left'] + 
                           (self.df[x_column].max()+1.5) * 
                           spacing_dict['cell_width'] + 
                           (self.df[x_column].max()-1) *
                           spacing_dict['gutter'] + 
                           spacing_dict['margin_right'])
            total_height = (spacing_dict['margin_top'] + 
                            (self.df[y_column].max()*0.866 + 0.289) *
                            spacing_dict['cell_width'] + 
                            (self.df[y_column].max()-1) *
                            spacing_dict['gutter'] + 
                            spacing_dict['margin_bottom'])
        else:
            total_width = (spacing_dict['margin_left'] + 
                           (self.df[x_column].max()*0.75 + 0.25) * 
                           spacing_dict['cell_width'] + 
                           (self.df[x_column].max()-1) *
                           spacing_dict['gutter'] + 
                           spacing_dict['margin_right'])
            total_height = (spacing_dict['margin_top'] + 
                            (self.df[y_column].max() + 1.5) *
                            spacing_dict['cell_width'] + 
                            (self.df[y_column].max()-1) *
                            spacing_dict['gutter'] + 
                            spacing_dict['margin_bottom'])
        self._make_svg_top(total_width, total_height)
        w = spacing_dict['cell_width']
        for i, id_ in enumerate(self.df[self.id_column]):
            if id_ in self.ids:
                this_color = self.colors[self.ids.index(id_)]
                this_font_color = font_colors[self.ids.index(id_)]
            else:
                this_color = spacing_dict['missing_color']
                this_font_color = spacing_dict['missing_font_color']
            across = self.df[x_column].iloc[i]
            down = self.df[y_column].iloc[i]
            # offset odd rows to the right or down
            x_offset = 0
            y_offset = 0
            if true_rows:
                if down % 2 == 1:
                    x_offset = w/2
                x = (spacing_dict['margin_left'] + 
                     x_offset + across * (w + spacing_dict['gutter']))
                y = (spacing_dict['margin_top'] + 
                    down * (1.5 * w / sqrt(3) + spacing_dict['gutter']))
            else:
                x_offset = 0.25 * w # because northwest corner is to the east of westmost point
                if across % 2 == 1:
                    y_offset = w*0.866/2
                x = (spacing_dict['margin_left'] + 
                     x_offset + across * 0.75 * (w + spacing_dict['gutter']))
                y = (spacing_dict['margin_top'] + 
                    y_offset + down * (sqrt(3) / 2 * w + spacing_dict['gutter']))
       
            this_font_style = font_style + ';fill:{}'.format(this_font_color)
            ET.SubElement(self.svg, "polygon", id=id_, points=self._calc_hexagon(x, y, w, true_rows))
            if draw_text == True:
                _ = ET.SubElement(self.svg, "text", id="text{}".format(id_), x=str(x+w/2), 
                    y=str(y + spacing_dict['name_y_offset']), style=this_font_style)
                _.text =str(id_)