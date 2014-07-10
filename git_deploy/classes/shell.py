"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

__author__="Adam Schubert"
__date__ ="$6.7.2014 0:03:47$"

class Shell:

  """
   * method colorize string
   * @param string $string String to colorize
   * @param string $foreground_color color of text
   * @param string $background_color color of background
   * @return string
  """
  @staticmethod
  def color(string, foreground_color = None, background_color = None):
    foreground_colors = {}
    background_colors = {}
    foreground_colors['black'] = '0;30'
    foreground_colors['dark_gray'] = '1;30'
    foreground_colors['blue'] = '0;34'
    foreground_colors['light_blue'] = '1;34'
    foreground_colors['green'] = '0;32'
    foreground_colors['light_green'] = '1;32'
    foreground_colors['cyan'] = '0;36'
    foreground_colors['light_cyan'] = '1;36'
    foreground_colors['red'] = '0;31'
    foreground_colors['light_red'] = '1;31'
    foreground_colors['purple'] = '0;35'
    foreground_colors['light_purple'] = '1;35'
    foreground_colors['brown'] = '0;33'
    foreground_colors['yellow'] = '1;33'
    foreground_colors['light_gray'] = '0;37'
    foreground_colors['white'] = '1;37'

    background_colors['black'] = '40'
    background_colors['red'] = '41'
    background_colors['green'] = '42'
    background_colors['yellow'] = '43'
    background_colors['blue'] = '44'
    background_colors['magenta'] = '45'
    background_colors['cyan'] = '46'
    background_colors['light_gray'] = '47'
    
    
    colored_string = '';

    if foreground_color in foreground_colors:
      colored_string += "\033[" + foreground_colors[foreground_color] + "m"

    if background_color in background_colors:
      colored_string += "\033[" + background_colors[background_color] + "m"

    colored_string += string + "\033[0m"

    return colored_string;
